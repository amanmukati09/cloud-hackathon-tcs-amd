# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from models import get_db, User, ChatSession, ChatMessage, Incident
from auth import get_current_user
from agents.chat import ChatAgent
from guardrails import guard
from fastapi.concurrency import run_in_threadpool
import asyncio
from fastapi.responses import StreamingResponse
import json

router = APIRouter()
chat_agent = ChatAgent()

class AILimiter:
    def __init__(self, limit=2):
        self.limit = limit
        self._semaphore = None
    async def __aenter__(self):
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.limit)
        await self._semaphore.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()

ai_queue = AILimiter(2)

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str

class RenameRequest(BaseModel):
    new_title: str

# ── Send message (with multi‑turn history + USER‑FILTERED RAG) ──
@router.post("/chat/message")
async def send_chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if guard.is_prompt_injection(req.message):
        raise HTTPException(status_code=400, detail="Security Exception: Prompt injection attempt detected and blocked.")

    safe_message, _ = guard.mask_pii(req.message)
    security_context = guard.get_ollama_security_prompt()

    # ─── USER‑FILTERED RAG: Search ChromaDB ───
    rag_context = ""
    try:
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(safe_message, top_k=20)  # get more candidates for filtering

        if results and results.get('ids') and results['ids'][0]:
            rag_parts = []
            count_added = 0
            max_rag = 3 if not current_user.is_admin else 10  # 🎯 user‑specific limit

            for i, incident_id in enumerate(results['ids'][0]):
                if count_added >= max_rag:
                    break

                inc = db.query(Incident).filter(Incident.id == int(incident_id)).first()
                if not inc:
                    continue

                # 🎯 FILTER: standard user only sees their own incidents
                if not current_user.is_admin and inc.user_id != current_user.id:
                    continue

                similarity = round((1 - results['distances'][0][i]) * 100, 1)
                rag_parts.append(
                    f"Incident #{inc.id} ({inc.timestamp.strftime('%Y-%m-%d')}, "
                    f"{similarity}% match): "
                    f"Anomaly: {inc.anomaly_description or 'N/A'}. "
                    f"Root Cause: {inc.root_cause or 'N/A'}. "
                    f"Remediation: {inc.remediation_action or 'N/A'}. "
                    f"Status: {inc.status}."
                )
                count_added += 1

            if rag_parts:
                user_type = "ADMIN (all incidents)" if current_user.is_admin else "USER (your incidents only)"
                rag_context = "\n".join(
                    [f"[RELEVANT PAST INCIDENTS - {user_type}]",
                     *rag_parts,
                     "[/RELEVANT PAST INCIDENTS]"]
                )
    except Exception as e:
        print(f"RAG search failed: {e}")

    # Build enforced prompt
    if rag_context:
        enforced_prompt = f"{security_context}\n\n{rag_context}\n\nUser Request:\n{safe_message}"
    else:
        enforced_prompt = f"{security_context}\n\nUser Request:\n{safe_message}"

    # ── Session handling ──
    session_id = req.session_id
    if not session_id:
        title = safe_message[:50]
        if "error" in safe_message.lower():
            title = "🐛 Error Discussion"
        elif "anomaly" in safe_message.lower() or "diagnos" in safe_message.lower():
            title = "🔍 Incident Analysis"
        elif "hello" in safe_message.lower() or "hi" in safe_message.lower():
            title = "👋 General Chat"
        elif "log" in safe_message.lower():
            title = "📋 Log Analysis"
        elif "help" in safe_message.lower():
            title = "🆘 Support Request"
        else:
            title = safe_message[:40].strip() + ("..." if len(safe_message) > 40 else "")
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id

    user_msg = ChatMessage(session_id=session_id, role="user", content=safe_message)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # ── Fetch previous messages for multi‑turn context ──
    previous_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.id < user_msg.id
    ).order_by(ChatMessage.timestamp.asc()).all()
    history_for_llm = [{"role": m.role, "content": m.content} for m in previous_msgs]

    # ── Generate AI response ──
    async with ai_queue:
        ai_response = await run_in_threadpool(chat_agent.generate_response, enforced_prompt, history_for_llm)

    # ── Guardrails ──
    if guard.is_destructive(ai_response):
        ai_response = "🚨 SECURITY INTERVENTION: The AI generated a potentially destructive command. Output blocked."
    elif guard.is_native_refusal(ai_response):
        ai_response = "🚨 SECURITY EXCEPTION: This request violates AegisAI security guardrails. Incident has been logged."

    ai_msg = ChatMessage(session_id=session_id, role="ai", content=ai_response)
    db.add(ai_msg)
    db.commit()

    # ── Return full history ──
    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    chat_format, temp_user = [], ""
    for m in msgs:
        if m.role == "user":
            temp_user = m.content
        else:
            chat_format.append([temp_user, m.content])
            temp_user = ""
    if temp_user:
        chat_format.append([temp_user, ""])

    return {"session_id": session_id, "history": chat_format}

# ── List sessions ─────────────────────────────────────
@router.get("/chat/sessions")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    result = {}
    for s in sessions:
        title = s.title or "Untitled"
        title = title.replace('\n', ' ').strip()
        if len(title) > 50:
            title = title[:47] + "..."
        result[str(s.id)] = title
    return result

# ── Get session history ───────────────────────────────
@router.get("/chat/sessions/{session_id}")
async def get_chat_history(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        return []
    msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    chat_format, temp_user = [], ""
    for m in msgs:
        if m.role == "user":
            temp_user = m.content
        else:
            chat_format.append([temp_user, m.content])
            temp_user = ""
    return chat_format

# ── Search chat history ───────────────────────────────
@router.get("/chat/search")
async def search_chat_history(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not query or len(query.strip()) < 2:
        return {"results": []}
    search_term = f"%{query.strip()}%"
    messages = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.content.ilike(search_term)
    ).order_by(ChatMessage.timestamp.desc()).limit(20).all()

    results = []
    for msg in messages:
        session = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
        session_title = session.title if session else "Unknown Session"
        content = msg.content or ""
        idx = content.lower().find(query.strip().lower())
        if idx >= 0:
            start = max(0, idx - 40)
            end = min(len(content), idx + len(query) + 40)
            snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")
        else:
            snippet = content[:100]
        results.append({
            "session_id": msg.session_id,
            "session_title": session_title[:50],
            "message_id": msg.id,
            "role": msg.role.upper(),
            "snippet": snippet,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M"),
            "full_content": content[:200]
        })
    return {"results": results, "query": query.strip()}

# ── Delete session ────────────────────────────────────
@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()

    from routers.notifications import create_notification
    if session.user_id != current_user.id:
        create_notification(db, session.user_id, "chat_deleted",
                            "Chat session deleted by admin",
                            f"Your chat session '{session.title}' (ID: {session_id}) was deleted by an admin.")
    create_notification(db, current_user.id, "chat_deleted",
                        "Chat session deleted",
                        f"Chat session '{session.title}' (ID: {session_id}) has been deleted.")
    return {"status": "success", "message": f"Chat session {session_id} deleted"}

# ── Rename session ────────────────────────────────────
@router.put("/chat/sessions/{session_id}/rename")
async def rename_chat_session(
    session_id: int,
    payload: RenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    old_title = session.title
    new_title = payload.new_title.strip()
    if not new_title or len(new_title) > 100:
        raise HTTPException(status_code=400, detail="Title must be 1-100 characters")
    session.title = new_title
    db.commit()

    from routers.notifications import create_notification
    create_notification(db, current_user.id, "chat_renamed",
                        "Chat session renamed",
                        f"Session '{old_title}' renamed to '{new_title}' (ID: {session_id}).")
    return {"status": "success", "new_title": new_title}

# 🆕 MODEL SWITCHING ENDPOINTS

class ModelSwitchRequest(BaseModel):
    model: str

@router.get("/chat/models")
async def get_available_models():
    """List all available AI models."""
    return {
        "models": [
            {"id": "llama3", "name": "Llama 3", "description": "Fast, general purpose", "icon": "🦙"},
            {"id": "deepseek-r1:7b", "name": "DeepSeek R1", "description": "Best reasoning & analysis", "icon": "🧠"},
            {"id": "mistral:7b", "name": "Mistral 7B", "description": "Quick & efficient", "icon": "⚡"}
        ],
        "current": chat_agent.model
    }

@router.post("/chat/model/switch")
async def switch_model(
    req: ModelSwitchRequest,
    current_user: User = Depends(get_current_user)
):
    """Switch the AI model for the current user."""
    if chat_agent.set_model(req.model):
        return {"status": "success", "model": req.model}
    return {"status": "error", "message": f"Model '{req.model}' not available"}

@router.post("/chat/message/stream")
async def send_chat_message_stream(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Streaming chat endpoint – tokens sent as they're generated."""
    
    if guard.is_prompt_injection(req.message):
        raise HTTPException(status_code=400, detail="Security Exception")

    safe_message, _ = guard.mask_pii(req.message)
    security_context = guard.get_ollama_security_prompt()

    # RAG context (same as before)
    rag_context = ""
    try:
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(safe_message, top_k=20)
        if results and results.get('ids') and results['ids'][0]:
            rag_parts = []
            count_added = 0
            max_rag = 3 if not current_user.is_admin else 10
            for i, incident_id in enumerate(results['ids'][0]):
                if count_added >= max_rag:
                    break
                inc = db.query(Incident).filter(Incident.id == int(incident_id)).first()
                if not inc:
                    continue
                if not current_user.is_admin and inc.user_id != current_user.id:
                    continue
                rag_parts.append(f"Incident #{inc.id}: {inc.root_cause or 'N/A'}. Fix: {inc.remediation_action or 'N/A'}")
                count_added += 1
            if rag_parts:
                rag_context = "\n".join(["[RELEVANT PAST INCIDENTS]", *rag_parts, "[/RELEVANT PAST INCIDENTS]"])
    except:
        pass

    if rag_context:
        enforced_prompt = f"{security_context}\n\n{rag_context}\n\nUser Request:\n{safe_message}"
    else:
        enforced_prompt = f"{security_context}\n\nUser Request:\n{safe_message}"

    # Session handling
    session_id = req.session_id
    if not session_id:
        title = safe_message[:40].strip() + ("..." if len(safe_message) > 40 else "")
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id

    # Save user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=safe_message)
    db.add(user_msg)
    db.commit()

    # Fetch history
    previous_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.id < user_msg.id
    ).order_by(ChatMessage.timestamp.asc()).all()
    history_for_llm = [{"role": m.role, "content": m.content} for m in previous_msgs]

    # Stream response
    async def event_stream():
        full_response = ""
        async with ai_queue:
            for token in chat_agent.generate_response_stream(enforced_prompt, history_for_llm):
                full_response += token
                yield f"data: {json.dumps({'token': token, 'session_id': session_id})}\n\n"
        
        # Save full AI response
        if guard.is_destructive(full_response):
            full_response = "🚨 SECURITY INTERVENTION: Destructive command blocked."
        elif guard.is_native_refusal(full_response):
            full_response = "🚨 SECURITY EXCEPTION: Request violates guardrails."
        
        ai_msg = ChatMessage(session_id=session_id, role="ai", content=full_response)
        db.add(ai_msg)
        db.commit()
        
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")