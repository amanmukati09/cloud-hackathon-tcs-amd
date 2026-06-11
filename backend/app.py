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
    db.refresh(new_incident)
    
    return {"incident_id": new_incident.id, "anomaly": anomaly, "root_cause": root_cause, "remediation": remed_plan}

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
        title = safe_message[:30] + "..." if len(safe_message) > 30 else safe_message
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
    return {str(s.id): f"ID: {s.id} | {s.title}" for s in sessions}

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
async def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access Denied.")
    users = db.query(User).all()
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
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)