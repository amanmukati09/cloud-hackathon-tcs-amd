from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

# Added ChatSession and ChatMessage imports here!
from models import User, Incident, ChatSession, ChatMessage, get_db
from auth import router as auth_router, get_current_user
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent
from agents.chat import ChatAgent

app = FastAPI(title="AegisAI Backend")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Router
app.include_router(auth_router)

# Initialize Agents
monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()
chat_agent = ChatAgent()

class IncidentRequest(BaseModel):
    logs: list[str]

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str

@app.post("/diagnose")
async def diagnose_incident(
    request: IncidentRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Full diagnosis pipeline (Protected)"""
    anomaly = monitor.detect_anomaly(request.logs)
    if not anomaly.get("anomaly_detected"):
        return {"status": "ok", "anomaly_detected": False}
        
    root_cause = diagnosis.analyze_root_cause(anomaly, request.logs)
    remed_plan = remediation.suggest_remediation(anomaly, root_cause)
    
    # Save the input logs
    log_text = "\n".join(request.logs)
    
    new_incident = Incident(
        user_id=current_user.id,
        raw_logs=log_text,
        status="open",
        anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
        root_cause=root_cause.get("root_cause"),
        remediation_action=", ".join(remed_plan.get("immediate_actions", [])),
        remediation_status="pending"
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    return {
        "incident_id": new_incident.id,
        "anomaly": anomaly,
        "root_cause": root_cause,
        "remediation": remed_plan
    }

@app.get("/my-incidents")
async def get_user_incidents(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get all incidents specific to the logged-in user"""
    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).order_by(Incident.timestamp.desc()).all()
    
    return [{
        "id": i.id, 
        "timestamp": i.timestamp, 
        "raw_logs": i.raw_logs, 
        "anomaly": i.anomaly_description, 
        "root_cause": i.root_cause,
        "remediation": i.remediation_action,
        "status": i.status
    } for i in incidents]

# --- NEW CHAT ENDPOINTS ---

@app.post("/chat/message")
async def send_chat_message(
    req: ChatRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    session_id = req.session_id
    
    # 1. Create a new session if one doesn't exist
    if not session_id:
        title = req.message[:30] + "..." if len(req.message) > 30 else req.message
        new_session = ChatSession(user_id=current_user.id, title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id

    # 2. Save User Message
    user_msg = ChatMessage(session_id=session_id, role="user", content=req.message)
    db.add(user_msg)
    
    # 3. Get AI Response
    ai_response = chat_agent.generate_response(req.message, [])
    
    # 4. Save AI Message
    ai_msg = ChatMessage(session_id=session_id, role="ai", content=ai_response)
    db.add(ai_msg)
    db.commit()

    # 5. Fetch full history for Gradio format [[user, ai], [user, ai]]
    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    
    chat_format = []
    temp_user = ""
    for m in msgs:
        if m.role == "user":
            temp_user = m.content
        else:
            chat_format.append([temp_user, m.content])
            temp_user = ""
            
    if temp_user: # Handle dangling user message just in case
        chat_format.append([temp_user, ""])

    return {"session_id": session_id, "history": chat_format}

@app.get("/chat/sessions")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get all past chat sessions for the sidebar"""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    # Return as {id: title} dict for Gradio Dropdown
    return {str(s.id): f"ID: {s.id} | {s.title}" for s in sessions}

@app.get("/chat/sessions/{session_id}")
async def get_chat_history(
    session_id: int,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Load a specific chat history"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        return []
        
    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    chat_format = []
    temp_user = ""
    for m in msgs:
        if m.role == "user":
            temp_user = m.content
        else:
            chat_format.append([temp_user, m.content])
            temp_user = ""
    return chat_format

# --- PROTECTED ADMIN ROUTES ---

@app.get("/admin/metrics")
async def get_admin_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch global platform metrics."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied: Root Admin required.")
    
    return {
        "users": db.query(User).count(),
        "incidents": db.query(Incident).count(),
        "chats": db.query(ChatSession).count()
    }

@app.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch user directory with their telemetry counts."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied: Root Admin required.")
    
    users = db.query(User).all()
    result = []
    for u in users:
        inc_count = db.query(Incident).filter(Incident.user_id == u.id).count()
        chat_count = db.query(ChatSession).filter(ChatSession.user_id == u.id).count()
        result.append({
            "User ID": u.id,
            "Full Name": u.full_name,
            "Email": u.email,
            "Role": "🛡️ ROOT" if u.is_admin else "👤 User",
            "Incidents Logged": inc_count,
            "AI Chats": chat_count,
            "Joined Date": u.created_at.strftime("%Y-%m-%d")
        })
    return result

@app.delete("/admin/users/{target_id}")
async def delete_user(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a user and cascade delete their incidents/chats."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied: Root Admin required.")
    if current_user.id == target_id:
        raise HTTPException(status_code=400, detail="Safety Protocol: You cannot delete your own Root account.")
        
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    db.delete(target)
    db.commit()
    return {"status": "success", "message": f"User {target_id} purged."}


@app.get("/admin/users/{target_id}/incidents")
async def get_user_incidents_admin(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Admin endpoint to read a specific user's incident logs."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied: Root Admin required.")
    
    incidents = db.query(Incident).filter(Incident.user_id == target_id).order_by(Incident.timestamp.desc()).all()
    return [{
        "ID": i.id,
        "Date": i.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Raw Logs": i.raw_logs,
        "Anomaly Found": i.anomaly_description,
        "Root Cause": i.root_cause,
        "Remediation": i.remediation_action,
        "Status": i.status
    } for i in incidents]

@app.get("/admin/users/{target_id}/chats")
async def get_user_chats_admin(target_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Admin endpoint to read a specific user's chat history."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied: Root Admin required.")
    
    messages = db.query(ChatMessage).join(ChatSession).filter(ChatSession.user_id == target_id).order_by(ChatSession.id.desc(), ChatMessage.timestamp.asc()).all()
    return [{
        "Session ID": m.session_id,
        "Time": m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Role": m.role.upper(),
        "Message Content": m.content
    } for m in messages]
    
    
# --- QA / ESCALATION TICKETING ROUTES ---

class TicketCreate(BaseModel):
    question: str

class TicketAnswer(BaseModel):
    answer: str

@app.post("/escalations")
async def create_escalation(ticket: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    new_ticket = EscalationTicket(user_id=current_user.id, question=ticket.question)
    db.add(new_ticket)
    db.commit()
    return {"status": "success"}

@app.get("/escalations/my")
async def get_my_escalations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    tickets = db.query(EscalationTicket).filter(EscalationTicket.user_id == current_user.id).order_by(EscalationTicket.created_at.desc()).all()
    return [{
        "Ticket ID": t.id, 
        "Date": t.created_at.strftime("%Y-%m-%d %H:%M"), 
        "Question": t.question, 
        "Admin Answer": t.answer or "⏳ Pending Review...", 
        "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED"
    } for t in tickets]

@app.get("/admin/escalations")
async def get_all_escalations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    tickets = db.query(EscalationTicket).order_by(EscalationTicket.status.desc(), EscalationTicket.created_at.desc()).all()
    result = []
    for t in tickets:
        user = db.query(User).filter(User.id == t.user_id).first()
        result.append({
            "Ticket ID": t.id,
            "User": user.email if user else "Unknown",
            "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED",
            "Question": t.question,
            "Answer": t.answer or ""
        })
    return result

@app.post("/admin/escalations/{ticket_id}/answer")
async def answer_escalation(ticket_id: int, payload: TicketAnswer, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import EscalationTicket
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.answer = payload.answer
    ticket.status = "resolved"
    db.commit()
    return {"status": "success"}
    
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)