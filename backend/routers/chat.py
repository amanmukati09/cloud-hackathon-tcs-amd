from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json, asyncio

from models import get_db, User, ChatSession, ChatMessage, Incident
from auth import get_current_user
from agents.chat import ChatAgent
from guardrails import guard
from fastapi.concurrency import run_in_threadpool
from cache import cached, clear_prefix
from utils.audit_logger import log_action

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

class ModelSwitchRequest(BaseModel):
    model: str

# ── Send message (multi‑turn + RAG + Sentiment) ──────
@router.post("/chat/message")
async def send_chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if guard.is_prompt_injection(req.message):
        raise HTTPException(status_code=400, detail="Security Exception")

    safe_message, _ = guard.mask_pii(req.message)
    security_context = guard.get_ollama_security_prompt()

    # RAG
    rag_context = ""
    try:
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(safe_message, top_k=20)
        if results and results.get('ids') and results['ids'][0]:
            rag_parts, cnt = [], 0
            max_rag = 3 if not current_user.is_admin else 10
            for i, iid in enumerate(results['ids'][0]):
                if cnt >= max_rag: break
                inc = db.query(Incident).filter(Incident.id == int(iid)).first()
                if not inc or (not current_user.is_admin and inc.user_id != current_user.id):
                    continue
                sim = round((1 - results['distances'][0][i]) * 100, 1)
                rag_parts.append(f"Incident #{inc.id} ({sim}% match): {inc.root_cause or 'N/A'}. Fix: {inc.remediation_action or 'N/A'}")
                cnt += 1
            if rag_parts:
                utype = "ADMIN" if current_user.is_admin else "USER"
                rag_context = f"[PAST INCIDENTS - {utype}]\n" + "\n".join(rag_parts)
    except Exception as e:
        print(f"RAG error: {e}")

    # Sentiment
    from agents.sentiment import SentimentAnalyzer
    sentiment = SentimentAnalyzer().analyze_message(safe_message)
    esc = "\n[⚠️ USER FRUSTRATED - be empathetic]" if sentiment.get("needs_escalation") else ""

    prompt_parts = [security_context, rag_context, esc, f"User Request:\n{safe_message}"]
    enforced_prompt = "\n\n".join([p for p in prompt_parts if p])

    # Session
    session_id = req.session_id
    if not session_id:
        title = safe_message[:40].strip() + ("..." if len(safe_message) > 40 else "")
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session); db.commit(); db.refresh(new_session)
        session_id = new_session.id
        
        # 🆕 Audit log
        log_action(db, current_user, "chat_created", 
                   resource_type="chat_session", 
                   resource_id=session_id)
        
        clear_prefix("chat_sessions")

    user_msg = ChatMessage(session_id=session_id, role="user", content=safe_message)
    db.add(user_msg); db.commit(); db.refresh(user_msg)

    # History
    prev = db.query(ChatMessage).filter(ChatMessage.session_id==session_id, ChatMessage.id<user_msg.id).order_by(ChatMessage.timestamp.asc()).all()
    hist = [{"role":m.role,"content":m.content} for m in prev]

    async with ai_queue:
        ai_resp = await run_in_threadpool(chat_agent.generate_response, enforced_prompt, hist)

    if guard.is_destructive(ai_resp):
        ai_resp = "🚨 Destructive command blocked."
    elif guard.is_native_refusal(ai_resp):
        ai_resp = "🚨 Security exception logged."

    ai_msg = ChatMessage(session_id=session_id, role="ai", content=ai_resp)
    db.add(ai_msg); db.commit()

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id==session_id).order_by(ChatMessage.timestamp.asc()).all()
    chat_fmt, tmp = [], ""
    for m in msgs:
        if m.role=="user": tmp=m.content
        else: chat_fmt.append([tmp,m.content]); tmp=""
    if tmp: chat_fmt.append([tmp,""])

    return {"session_id":session_id, "history":chat_fmt, "sentiment":sentiment}

# ── Streaming endpoint ────────────────────────────────
@router.post("/chat/message/stream")
async def send_chat_message_stream(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if guard.is_prompt_injection(req.message):
        raise HTTPException(status_code=400, detail="Security Exception")

    safe_message, _ = guard.mask_pii(req.message)
    security_context = guard.get_ollama_security_prompt()

    # RAG (simplified for streaming)
    rag_context = ""
    try:
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(safe_message, top_k=10)
        if results and results.get('ids') and results['ids'][0]:
            parts = []
            for i, iid in enumerate(results['ids'][0][:5]):
                inc = db.query(Incident).filter(Incident.id == int(iid)).first()
                if inc:
                    parts.append(f"#{inc.id}: {inc.root_cause or '?'} → {inc.remediation_action or '?'}")
            if parts:
                rag_context = "[PAST INCIDENTS]\n" + "\n".join(parts)
    except: pass

    # Sentiment
    from agents.sentiment import SentimentAnalyzer
    sentiment = SentimentAnalyzer().analyze_message(safe_message)
    esc = "\n[⚠️ USER FRUSTRATED]" if sentiment.get("needs_escalation") else ""

    prompt_parts = [security_context, rag_context, esc, f"User Request:\n{safe_message}"]
    enforced_prompt = "\n\n".join([p for p in prompt_parts if p])

    # Session
    session_id = req.session_id
    if not session_id:
        title = safe_message[:40].strip() + ("..." if len(safe_message) > 40 else "")
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session); db.commit(); db.refresh(new_session)
        session_id = new_session.id
        
        # 🆕 Audit log
        log_action(db, current_user, "chat_created", 
                   resource_type="chat_session", 
                   resource_id=session_id)
        
        clear_prefix("chat_sessions")

    user_msg = ChatMessage(session_id=session_id, role="user", content=safe_message)
    db.add(user_msg); db.commit(); db.refresh(user_msg)

    prev = db.query(ChatMessage).filter(ChatMessage.session_id==session_id, ChatMessage.id<user_msg.id).order_by(ChatMessage.timestamp.asc()).all()
    hist = [{"role":m.role,"content":m.content} for m in prev]

    async def event_stream():
        full = ""
        async with ai_queue:
            for token in chat_agent.generate_response_stream(enforced_prompt, hist):
                full += token
                yield f"data: {json.dumps({'token': token, 'session_id': session_id})}\n\n"

        if guard.is_destructive(full):
            full = "🚨 Destructive command blocked."
        elif guard.is_native_refusal(full):
            full = "🚨 Security exception logged."

        ai_msg = ChatMessage(session_id=session_id, role="ai", content=full)
        db.add(ai_msg); db.commit()

        yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'sentiment': sentiment})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ── Sentiment endpoint ────────────────────────────────
@router.post("/chat/analyze-sentiment")
async def analyze_sentiment(
    message: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    from agents.sentiment import SentimentAnalyzer
    a = SentimentAnalyzer()
    res = a.analyze_message(message)
    return {"result": res, "html": a.render_sentiment_html(res, message)}

# ── Model endpoints ───────────────────────────────────
@router.get("/chat/models")
async def get_available_models():
    return {
        "models": [
            {"id": "llama3", "name": "Llama 3", "icon": "🦙"},
            {"id": "deepseek-r1:7b", "name": "DeepSeek R1", "icon": "🧠"},
            {"id": "mistral:7b", "name": "Mistral 7B", "icon": "⚡"}
        ],
        "current": chat_agent.model
    }

@router.post("/chat/model/switch")
async def switch_model(
    req: ModelSwitchRequest,
    current_user: User = Depends(get_current_user)
):
    if chat_agent.set_model(req.model):
        return {"status": "success", "model": req.model}
    return {"status": "error", "message": f"Model '{req.model}' not available"}

# ── Sessions list (CACHED) ────────────────────────────
@router.get("/chat/sessions")
@cached("chat_sessions", ttl=30)
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    result = {}
    for s in sessions:
        title = (s.title or "Untitled").replace('\n', ' ').strip()
        if len(title) > 50: title = title[:47] + "..."
        result[str(s.id)] = title
    return result

# ── Session history ───────────────────────────────────
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
    if not session: return []
    msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    chat_fmt, tmp = [], ""
    for m in msgs:
        if m.role == "user": tmp = m.content
        else: chat_fmt.append([tmp, m.content]); tmp = ""
    return chat_fmt

# ── Search chat history ───────────────────────────────
@router.get("/chat/search")
async def search_chat_history(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not query or len(query.strip()) < 2:
        return {"results": []}
    term = f"%{query.strip()}%"
    msgs = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.content.ilike(term)
    ).order_by(ChatMessage.timestamp.desc()).limit(20).all()

    results = []
    for msg in msgs:
        sess = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
        stitle = sess.title if sess else "Unknown"
        content = msg.content or ""
        idx = content.lower().find(query.strip().lower())
        if idx >= 0:
            start = max(0, idx - 40)
            end = min(len(content), idx + len(query) + 40)
            snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")
        else:
            snippet = content[:100]
        results.append({
            "session_id": msg.session_id, "session_title": stitle[:50],
            "message_id": msg.id, "role": msg.role.upper(),
            "snippet": snippet, "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M"),
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
    
    # 🆕 Audit log
    log_action(db, current_user, "chat_deleted", 
               resource_type="chat_session", 
               resource_id=session_id)
    
    clear_prefix("chat_sessions")

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
    
    # 🆕 Audit log
    log_action(db, current_user, "chat_renamed", 
               resource_type="chat_session", 
               resource_id=session_id, 
               details=f"'{old_title}' → '{new_title}'")
    
    clear_prefix("chat_sessions")

    from routers.notifications import create_notification
    create_notification(db, current_user.id, "chat_renamed",
                        "Chat session renamed",
                        f"Session '{old_title}' renamed to '{new_title}' (ID: {session_id}).")
    return {"status": "success", "new_title": new_title}