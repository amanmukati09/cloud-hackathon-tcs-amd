from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from models import User, Incident, ChatSession, ChatMessage, get_db
from auth import router as auth_router, get_current_user
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent
from agents.chat import ChatAgent
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
import csv
import io
import re
from models import EscalationTicket, Notification
from fastapi import UploadFile, File
from typing import List


# 🛡️ Import the synchronized Security Guardrails
from guardrails import guard 

app = FastAPI(title="AegisAI Backend")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth_router)

monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()
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

class IncidentRequest(BaseModel):
    logs: list[str]

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str

def _safe_join(val):
    if not val: return "None"
    if isinstance(val, list): return ", ".join([str(item) for item in val])
    return str(val)

@app.post("/diagnose")
async def diagnose_incident(
    request: IncidentRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Full diagnosis pipeline (Protected, Threaded, & GDPR Compliant)"""
    
    # 🛡️ GUARDRAIL 1: Mask PII and Secrets from logs before processing
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    
    async with ai_queue:
        # 🚀 Pass the SAFE logs to the AI, never the raw logs
        anomaly = await run_in_threadpool(monitor.detect_anomaly, safe_logs)
        
        if not anomaly.get("anomaly_detected"):
            return {"status": "ok", "anomaly_detected": False}
            
        root_cause = await run_in_threadpool(diagnosis.analyze_root_cause, anomaly, safe_logs)
        remed_plan = await run_in_threadpool(remediation.suggest_remediation, anomaly, root_cause)

    # 🛡️ GUARDRAIL 2: Check if AI hallucinated a destructive command (FIXED NAME)
    if guard.is_destructive(str(remed_plan)):
        remed_plan = {
            "immediate_actions": ["🚨 BLOCKED: AI suggested potentially destructive command. Manual review required."],
            "automated_actions": [],
            "escalation_needed": True,
            "estimated_recovery_time": "Manual",
            "prevention_measures": ["Review AI prompt safety limits."]
        }
    
    # Save the SAFE logs to DB
    log_text = "\n".join(safe_logs)
    new_incident = Incident(
        user_id=current_user.id, raw_logs=log_text, status="open",
        anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
        root_cause=root_cause.get("root_cause") if isinstance(root_cause, dict) else str(root_cause),
        remediation_action=_safe_join(remed_plan.get("immediate_actions", [])),
        remediation_status="pending"
    )
    db.add(new_incident)
    db.commit()

    # Create notification for new incident
    create_notification(db, current_user.id, "diagnosis_complete", "Diagnosis Complete", f"Incident #{new_incident.id} has been analyzed")
        
    db.refresh(new_incident)
    
    return {"incident_id": new_incident.id, "anomaly": anomaly, "root_cause": root_cause, "remediation": remed_plan}



@app.post("/upload-logs")
async def upload_log_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload log files and return parsed contents."""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    all_logs = []
    file_names = []
    total_size = 0
    
    for file in files:
        # Validate file extension
        if not file.filename.endswith(('.log', '.txt', '.out', '.LOG', '.TXT')):
            continue
        
        # Read file content
        content = await file.read()
        total_size += len(content)
        
        # Limit total upload to 10MB
        if total_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Total file size exceeds 10MB limit")
        
        # Decode and split into lines
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('latin-1')
            except:
                text = content.decode('utf-8', errors='ignore')
        
        lines = text.split('\n')
        all_logs.extend([line.strip() for line in lines if line.strip()])
        file_names.append(file.filename)
    
    return {
        "file_names": file_names,
        "total_lines": len(all_logs),
        "total_size_kb": round(total_size / 1024, 2),
        "logs": all_logs[:5000]  # Limit to 5000 lines for preview
    }
# 🆕 SIMILARITY SEARCH ENDPOINT
class SimilarityRequest(BaseModel):
    logs: list[str]

@app.post("/incidents/similar")
async def find_similar_incidents(
    request: SimilarityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search ChromaDB for similar past incidents based on log patterns."""
    
    # 🛡️ GUARDRAIL: Mask PII before searching
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    
    # Combine logs into a search query
    search_query = " ".join(safe_logs)
    
    try:
        # Query ChromaDB
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(search_query, top_k=3)
        
        # Format results
        similar_incidents = []
        if results and results.get('ids') and results['ids'][0]:
            for i, incident_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results.get('distances') else 1.0
                similarity_score = max(0, min(100, (1 - distance) * 100))
                
                # Fetch incident details from SQLite
                incident = db.query(Incident).filter(Incident.id == int(incident_id)).first()
                if incident:
                    similar_incidents.append({
                        "incident_id": incident.id,
                        "similarity": round(similarity_score, 1),
                        "date": incident.timestamp.strftime("%Y-%m-%d %H:%M"),
                        "anomaly": incident.anomaly_description[:100] + "..." if len(incident.anomaly_description) > 100 else incident.anomaly_description,
                        "root_cause": incident.root_cause[:100] + "..." if len(incident.root_cause) > 100 else incident.root_cause,
                        "status": incident.status
                    })
        
        return {"similar_incidents": similar_incidents}
        
    except Exception as e:
        print(f"Similarity search error: {e}")
        return {"similar_incidents": []}
        
@app.get("/my-incidents")
async def get_user_incidents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    incidents = db.query(Incident).filter(Incident.user_id == current_user.id).order_by(Incident.timestamp.desc()).all()
    return [{"id": i.id, "timestamp": i.timestamp, "raw_logs": i.raw_logs, "anomaly": i.anomaly_description, "root_cause": i.root_cause, "remediation": i.remediation_action, "status": i.status} for i in incidents]

# --- CHAT ENDPOINTS ---

@app.post("/chat/message")
async def send_chat_message(req: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    # 🛡️ GUARDRAIL 3: Python Prompt Injection Shield
    if guard.is_prompt_injection(req.message):
        raise HTTPException(status_code=400, detail="Security Exception: Prompt injection attempt detected and blocked.")

    # 🛡️ LAYER 1: Hardcoded Regex PII Scrubbing
    safe_message, _ = guard.mask_pii(req.message)

    # 🛡️ LAYER 2: Give Ollama the security rules so it can evaluate complex attacks natively
    security_context = guard.get_ollama_security_prompt()
    enforced_prompt = f"{security_context}\n\nUser Request:\n{safe_message}"

    session_id = req.session_id
    if not session_id:
        # Create a smart title from the first message
        title = safe_message[:50]
        # Try to extract a meaningful title
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
            # Use first 40 chars of cleaned message
            title = safe_message[:40].strip() + ("..." if len(safe_message) > 40 else "")

    
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id

    user_msg = ChatMessage(session_id=session_id, role="user", content=safe_message)
    db.add(user_msg)
    
    async with ai_queue:
        ai_response = await run_in_threadpool(chat_agent.generate_response, enforced_prompt, [])
    
    # 🛡️ LAYER 3: Output Validation (Double check the AI didn't hallucinate something deadly)
    if guard.is_destructive(ai_response):
        ai_response = "🚨 SECURITY INTERVENTION: The AI generated a potentially destructive command. Output blocked."
    elif guard.is_native_refusal(ai_response):
        # 🚀 Normalize the LLM's generic apology into a strict Enterprise Audit Log
        ai_response = "🚨 SECURITY EXCEPTION: This request violates AegisAI security guardrails. Incident has been logged."

    ai_msg = ChatMessage(session_id=session_id, role="ai", content=ai_response)
    db.add(ai_msg)
    db.commit()

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    chat_format, temp_user = [], ""
    for m in msgs:
        if m.role == "user": temp_user = m.content
        else: chat_format.append([temp_user, m.content]); temp_user = ""
    if temp_user: chat_format.append([temp_user, ""])

    return {"session_id": session_id, "history": chat_format}


@app.get("/chat/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    # Return clean format without doubling
    result = {}
    for s in sessions:
        sid = str(s.id)
        title = s.title or "Untitled"
        # Clean up any newlines or extra spaces in title
        title = title.replace('\n', ' ').strip()
        if len(title) > 50:
            title = title[:47] + "..."
        result[sid] = title
    return result
    


@app.get("/chat/sessions/{session_id}")
async def get_chat_history(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session: return []
    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    chat_format, temp_user = [], ""
    for m in msgs:
        if m.role == "user": temp_user = m.content
        else: chat_format.append([temp_user, m.content]); temp_user = ""
    return chat_format

@app.get("/chat/search")
async def search_chat_history(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search across all chat messages for a keyword."""
    if not query or len(query.strip()) < 2:
        return {"results": []}
    
    search_term = f"%{query.strip()}%"
    
    # Search in user's chat messages
    messages = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.content.ilike(search_term)
    ).order_by(ChatMessage.timestamp.desc()).limit(20).all()
    
    results = []
    for msg in messages:
        # Get session title
        session = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
        session_title = session.title if session else "Unknown Session"
        
        # Get a snippet around the match
        content = msg.content or ""
        query_lower = query.strip().lower()
        content_lower = content.lower()
        idx = content_lower.find(query_lower)
        
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

# --- ADMIN / TICKETING ROUTES (Unchanged) ---
@app.get("/admin/metrics")
async def get_admin_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    return {"users": db.query(User).count(), "incidents": db.query(Incident).count(), "chats": db.query(ChatSession).count()}

@app.get("/admin/analytics/data")
async def get_analytics_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches raw incident data for the Executive Analytics Dashboard."""
    if not current_user.is_admin: 
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    incidents = db.query(Incident).all()
    # We only send the minimum data needed for graphing to keep the payload lightweight
    return [{
        "date": i.timestamp.strftime("%Y-%m-%d"), 
        "status": i.status, 
        "description": i.anomaly_description
    } for i in incidents]

    

@app.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), limit: int = 100):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    users = db.query(User).limit(limit).all()
    result = []
    for u in users:
        result.append({
            "User ID": u.id, "Full Name": u.full_name, "Email": u.email,
            "Role": "🛡️ ROOT" if u.is_admin else "👤 User",
            "Incidents Logged": db.query(Incident).filter(Incident.user_id == u.id).count(),
            "AI Chats": db.query(ChatSession).filter(ChatSession.user_id == u.id).count(),
            "Joined Date": u.created_at.strftime("%Y-%m-%d")
        })
    return result

@app.get("/admin/users/{target_id}/exists")
async def user_exists(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    user = db.query(User).filter(User.id == target_id).first()
    return {"exists": user is not None}

@app.delete("/admin/users/{target_id}")
async def delete_user(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    if current_user.id == target_id: raise HTTPException(status_code=400, detail="Cannot delete own account.")
    target = db.query(User).filter(User.id == target_id).first()
    if not target: raise HTTPException(status_code=404, detail="User not found.")
    db.delete(target)
    db.commit()
    return {"status": "success", "message": f"User {target_id} purged."}

@app.get("/admin/users/{target_id}/incidents")
async def get_user_incidents_admin(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    incidents = db.query(Incident).filter(Incident.user_id == target_id).order_by(Incident.timestamp.desc()).all()
    return [{"ID": i.id, "Date": i.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "Raw Logs": i.raw_logs, "Anomaly Found": i.anomaly_description, "Root Cause": i.root_cause, "Remediation": i.remediation_action, "Status": i.status} for i in incidents]

@app.get("/admin/users/{target_id}/chats")
async def get_user_chats_admin(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    messages = db.query(ChatMessage).join(ChatSession).filter(ChatSession.user_id == target_id).order_by(ChatSession.id.desc(), ChatMessage.timestamp.asc()).all()
    return [{"Session ID": m.session_id, "Time": m.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "Role": m.role.upper(), "Message Content": m.content} for m in messages]

class TicketCreate(BaseModel): question: str
class TicketAnswer(BaseModel): answer: str

@app.post("/escalations")
async def create_escalation(ticket: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    db.add(EscalationTicket(user_id=current_user.id, question=ticket.question))
    # Notify admins about new escalation
    admins = db.query(User).filter(User.is_admin == True).all()
    for admin in admins:
        create_notification(db, admin.id, "new_escalation", "New Support Ticket", f"User {current_user.email} submitted a new escalation")

    db.commit()
    return {"status": "success"}

@app.get("/escalations/my")
async def get_my_escalations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    tickets = db.query(EscalationTicket).filter(EscalationTicket.user_id == current_user.id).order_by(EscalationTicket.created_at.desc()).all()
    return [{"Ticket ID": t.id, "Date": t.created_at.strftime("%Y-%m-%d %H:%M"), "Question": t.question, "Admin Answer": t.answer or "⏳ Pending Review...", "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED"} for t in tickets]

@app.get("/admin/escalations")
async def get_all_escalations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    tickets = db.query(EscalationTicket).order_by(EscalationTicket.status.desc(), EscalationTicket.created_at.desc()).all()
    return [{"Ticket ID": t.id, "User": db.query(User).filter(User.id == t.user_id).first().email if db.query(User).filter(User.id == t.user_id).first() else "Unknown", "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED", "Question": t.question, "Answer": t.answer or ""} for t in tickets]

@app.post("/admin/escalations/{ticket_id}/answer")
async def answer_escalation(ticket_id: int, payload: TicketAnswer, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket: raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.answer = payload.answer
    ticket.status = "resolved"
    db.commit()

        # Notify the ticket owner that their question was answered
    ticket_owner = db.query(User).filter(User.id == ticket.user_id).first()
    if ticket_owner:
        create_notification(db, ticket_owner.id, "ticket_answered", "Ticket Answered", f"Admin answered your escalation ticket #{ticket_id}")

    
    return {"status": "success"}


# 🆕 INCIDENT RESOLUTION WORKFLOW
class ResolveIncident(BaseModel):
    resolution_notes: Optional[str] = None

@app.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    payload: ResolveIncident,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an incident as resolved with optional notes."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    
    if not incident:
        # Allow admin to resolve any incident
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.status == "resolved":
        raise HTTPException(status_code=400, detail="Incident already resolved")
    
    incident.status = "resolved"
    incident.remediation_status = "completed"
    incident.resolved_at = datetime.now(timezone.utc)  # 🔧 FIXED
    
    if payload.resolution_notes:
        incident.resolution_notes = payload.resolution_notes
    
    db.commit()

    # Create notification for resolution
    create_notification(db, current_user.id, "incident_resolved", "Incident Resolved", f"Incident #{incident_id} has been marked as resolved")

    # Calculate resolution time
    resolution_time = incident.resolved_at - incident.timestamp
    hours = resolution_time.total_seconds() / 3600
    
    return {
        "status": "success",
        "incident_id": incident.id,
        "resolution_time_hours": round(hours, 2)
    }



@app.get("/incidents/{incident_id}/details")
async def get_incident_details(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full details of a specific incident."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    
    if not incident:
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "id": incident.id,
        "timestamp": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_logs": incident.raw_logs,
        "anomaly": incident.anomaly_description,
        "root_cause": incident.root_cause,
        "remediation": incident.remediation_action,
        "status": incident.status,
        "resolution_notes": incident.resolution_notes or "",
        "resolved_at": incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if incident.resolved_at else None
    }


@app.get("/admin/mttr")
async def get_mttr_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Mean Time To Resolution metrics for admin dashboard."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    resolved_incidents = db.query(Incident).filter(
        Incident.status == "resolved",
        Incident.resolved_at != None
    ).all()
    
    if not resolved_incidents:
        return {
            "average_mttr_hours": 0,
            "total_resolved": 0,
            "fastest_hours": 0,
            "slowest_hours": 0
        }
    
    resolution_times = []
    for inc in resolved_incidents:
        delta = inc.resolved_at - inc.timestamp
        resolution_times.append(delta.total_seconds() / 3600)
    
    return {
        "average_mttr_hours": round(sum(resolution_times) / len(resolution_times), 2),
        "total_resolved": len(resolved_incidents),
        "fastest_hours": round(min(resolution_times), 2),
        "slowest_hours": round(max(resolution_times), 2)
    }

@app.get("/admin/analytics/enhanced")
async def get_enhanced_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enhanced analytics with trends, components, and MTTR by severity."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    from datetime import timedelta
    import pandas as pd
    
    incidents = db.query(Incident).all()
    if not incidents:
        return {
            "trend": [],
            "components": [],
            "mttr_by_severity": [],
            "heatmap": []
        }
    
    # Convert to DataFrame
    data = []
    for inc in incidents:
        severity_match = re.search(r'Severity:\s*([A-Z]+)', inc.anomaly_description or "")
        component_match = re.search(r'Component:\s*([^\n,]+)', inc.anomaly_description or "")
        
        severity = severity_match.group(1) if severity_match else "UNKNOWN"
        component = component_match.group(1).strip() if component_match else "Unknown"
        
        resolution_hours = None
        if inc.resolved_at and inc.status == "resolved":
            resolution_hours = (inc.resolved_at - inc.timestamp).total_seconds() / 3600
        
        data.append({
            "date": inc.timestamp.strftime("%Y-%m-%d"),
            "hour": inc.timestamp.hour,
            "weekday": inc.timestamp.strftime("%A"),
            "severity": severity,
            "component": component,
            "status": inc.status,
            "resolution_hours": resolution_hours
        })
    
    df = pd.DataFrame(data)
    
    # 1. 7-Day Rolling Average Trend
    daily = df.groupby('date').size().reset_index(name='count')
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    daily['rolling_avg'] = daily['count'].rolling(window=7, min_periods=1).mean().round(1)
    trend_data = daily[['date', 'count', 'rolling_avg']].tail(30).to_dict('records')
    for item in trend_data:
        item['date'] = item['date'].strftime("%Y-%m-%d")
    
    # 2. Top Affected Components
    components = df.groupby('component').size().reset_index(name='incidents')
    components = components.sort_values('incidents', ascending=False).head(8)
    component_data = components.to_dict('records')
    
    # 3. MTTR by Severity
    resolved = df[df['resolution_hours'].notna()]
    mttr = resolved.groupby('severity')['resolution_hours'].agg(['mean', 'count']).round(1)
    mttr = mttr.reset_index()
    mttr.columns = ['severity', 'avg_hours', 'count']
    mttr_data = mttr.to_dict('records')
    
    # 4. Heatmap (Day of Week vs Hour)
    heatmap = df.groupby(['weekday', 'hour']).size().reset_index(name='incidents')
    heatmap_data = heatmap.to_dict('records')
    
    return {
        "trend": trend_data,
        "components": component_data,
        "mttr_by_severity": mttr_data,
        "heatmap": heatmap_data
    }


@app.get("/incidents/export/csv")
async def export_incidents_csv(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export incidents as CSV file."""
    
    query = db.query(Incident).filter(Incident.user_id == current_user.id)
    
    if status_filter and status_filter != "all":
        query = query.filter(Incident.status == status_filter)
    
    incidents = query.order_by(Incident.timestamp.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Date", "Status", "Anomaly", "Root Cause", "Remediation", "Resolution Notes"])
    
    # Data rows
    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            inc.status.upper(),
            inc.anomaly_description[:200] if inc.anomaly_description else "",
            inc.root_cause[:200] if inc.root_cause else "",
            inc.remediation_action[:200] if inc.remediation_action else "",
            inc.resolution_notes[:200] if inc.resolution_notes else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aegis_incidents_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.get("/incidents/{incident_id}/export/pdf")
async def export_incident_pdf(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a single incident as a professional PDF report."""
    
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    
    if not incident:
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#38bdf8'),
        spaceAfter=30
    )
    story.append(Paragraph(f"🛡️ AegisAI Incident Report", title_style))
    story.append(Paragraph(f"Incident #{incident.id}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Status Badge
    status_color = "#10b981" if incident.status == "resolved" else "#f59e0b"
    status_text = "✅ RESOLVED" if incident.status == "resolved" else "🟢 OPEN"
    story.append(Paragraph(f"Status: <font color='{status_color}'><b>{status_text}</b></font>", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Incident Details Table
    details_data = [
        ["Field", "Details"],
        ["Date/Time", incident.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        ["Status", incident.status.upper()],
    ]
    
    if incident.resolved_at:
        details_data.append(["Resolved At", incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S")])
    
    table = Table(details_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#334155')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Sections
    sections = [
        ("📋 Raw Logs", incident.raw_logs or "No logs provided"),
        ("🔴 Anomaly Detection", incident.anomaly_description or "Not analyzed"),
        ("🔍 Root Cause Analysis", incident.root_cause or "Not determined"),
        ("⚙️ Remediation Actions", incident.remediation_action or "No actions specified"),
        ("📝 Resolution Notes", incident.resolution_notes or "No notes provided")
    ]
    
    for title, content in sections:
        story.append(Paragraph(title, styles['Heading3']))
        story.append(Paragraph(content.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("<i>Generated by AegisAI - Enterprise SRE Platform</i>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=aegis_incident_{incident_id}_report.pdf"}
    )

# # 🆕 NOTIFICATION SYSTEM
# class NotificationModel(Base):
#     __tablename__ = "notifications"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     type = Column(String)  # ticket_answered, new_incident, incident_resolved, diagnosis_complete
#     title = Column(String)
#     message = Column(Text)
#     is_read = Column(Boolean, default=False)
#     created_at = Column(DateTime, default=datetime.utcnow)


# 🆕 NOTIFICATION ENDPOINTS
@app.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch recent notifications for the current user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {
        "notifications": [{
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message or "",
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else ""
        } for n in notifications],
        "unread_count": unread_count
    }

@app.post("/notifications/mark-read")
async def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}

def create_notification(db: Session, user_id: int, notif_type: str, title: str, message: str = ""):
    """Helper function to create notifications (call this from other endpoints)."""
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message
    )
    db.add(notif)
    db.commit()

# --- DELETE & RENAME CHAT SESSIONS ---

@app.delete("/chat/sessions/{session_id}")
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

    # Delete messages and session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()

    # Notify the owner (unless they deleted it themselves)
    if session.user_id != current_user.id:
        create_notification(db, session.user_id, "chat_deleted",
            "Chat session deleted by admin",
            f"Your chat session '{session.title}' (ID: {session_id}) was deleted by an admin.")
    # Always notify the acting user (admin or owner)
    create_notification(db, current_user.id, "chat_deleted",
        "Chat session deleted",
        f"Chat session '{session.title}' (ID: {session_id}) has been deleted.")

    return {"status": "success", "message": f"Chat session {session_id} deleted"}


class RenameRequest(BaseModel):
    new_title: str

@app.put("/chat/sessions/{session_id}/rename")
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

    # Notify the owner
    create_notification(db, current_user.id, "chat_renamed",
        "Chat session renamed",
        f"Session '{old_title}' renamed to '{new_title}' (ID: {session_id}).")

    return {"status": "success", "new_title": new_title}

    
# --- DELETE INCIDENT ---

@app.delete("/incidents/{incident_id}")
async def delete_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")

    db.delete(incident)
    db.commit()

    # Notify the owner
    if incident.user_id != current_user.id:
        create_notification(db, incident.user_id, "incident_deleted",
            "Incident deleted by admin",
            f"Incident #{incident_id} was deleted by an admin.")
    create_notification(db, current_user.id, "incident_deleted",
        "Incident deleted",
        f"Incident #{incident_id} has been deleted.")

    return {"status": "success", "message": f"Incident {incident_id} deleted"}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)