# backend/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import re
import pandas as pd

from models import get_db, User, Incident, ChatSession, ChatMessage, EscalationTicket
from auth import get_current_user

router = APIRouter()

# ── Metrics ───────────────────────────────────────────
@router.get("/admin/metrics")
async def get_admin_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    return {
        "users": db.query(User).count(),
        "incidents": db.query(Incident).count(),
        "chats": db.query(ChatSession).count()
    }

# ── Analytics data ────────────────────────────────────
@router.get("/admin/analytics/data")
async def get_analytics_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    incidents = db.query(Incident).all()
    return [{
        "date": i.timestamp.strftime("%Y-%m-%d"),
        "status": i.status,
        "description": i.anomaly_description
    } for i in incidents]

# ── Enhanced analytics ────────────────────────────────
@router.get("/admin/analytics/enhanced")
async def get_enhanced_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")

    incidents = db.query(Incident).all()
    if not incidents:
        return {"trend": [], "components": [], "mttr_by_severity": [], "heatmap": []}

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

    daily = df.groupby('date').size().reset_index(name='count')
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    daily['rolling_avg'] = daily['count'].rolling(window=7, min_periods=1).mean().round(1)
    trend_data = daily[['date', 'count', 'rolling_avg']].tail(30).to_dict('records')
    for item in trend_data:
        item['date'] = item['date'].strftime("%Y-%m-%d")

    components = df.groupby('component').size().reset_index(name='incidents')
    components = components.sort_values('incidents', ascending=False).head(8)
    component_data = components.to_dict('records')

    resolved = df[df['resolution_hours'].notna()]
    mttr = resolved.groupby('severity')['resolution_hours'].agg(['mean', 'count']).round(1)
    mttr = mttr.reset_index()
    mttr.columns = ['severity', 'avg_hours', 'count']
    mttr_data = mttr.to_dict('records')

    heatmap = df.groupby(['weekday', 'hour']).size().reset_index(name='incidents')
    heatmap_data = heatmap.to_dict('records')

    return {
        "trend": trend_data,
        "components": component_data,
        "mttr_by_severity": mttr_data,
        "heatmap": heatmap_data
    }

# ── User list ─────────────────────────────────────────
@router.get("/admin/users")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    users = db.query(User).limit(limit).all()
    result = []
    for u in users:
        result.append({
            "User ID": u.id,
            "Full Name": u.full_name,
            "Email": u.email,
            "Role": "🛡️ ROOT" if u.is_admin else "👤 User",
            "Incidents Logged": db.query(Incident).filter(Incident.user_id == u.id).count(),
            "AI Chats": db.query(ChatSession).filter(ChatSession.user_id == u.id).count(),
            "Joined Date": u.created_at.strftime("%Y-%m-%d")
        })
    return result

# ── Check user exists ─────────────────────────────────
@router.get("/admin/users/{target_id}/exists")
async def user_exists(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    user = db.query(User).filter(User.id == target_id).first()
    return {"exists": user is not None}

# ── Delete user ───────────────────────────────────────
@router.delete("/admin/users/{target_id}")
async def delete_user(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    if current_user.id == target_id:
        raise HTTPException(status_code=400, detail="Cannot delete own account.")
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(target)
    db.commit()
    return {"status": "success", "message": f"User {target_id} purged."}

# ── User incidents (admin) ────────────────────────────
@router.get("/admin/users/{target_id}/incidents")
async def get_user_incidents_admin(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
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

# ── User chats (admin) ────────────────────────────────
@router.get("/admin/users/{target_id}/chats")
async def get_user_chats_admin(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    messages = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.user_id == target_id
    ).order_by(ChatSession.id.desc(), ChatMessage.timestamp.asc()).all()
    return [{
        "Session ID": m.session_id,
        "Time": m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Role": m.role.upper(),
        "Message Content": m.content
    } for m in messages]

# ── Escalations (admin) ───────────────────────────────
class TicketAnswer(BaseModel):
    answer: str

@router.get("/admin/escalations")
async def get_all_escalations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    tickets = db.query(EscalationTicket).order_by(
        EscalationTicket.status.desc(), EscalationTicket.created_at.desc()
    ).all()
    return [{
        "Ticket ID": t.id,
        "User": db.query(User).filter(User.id == t.user_id).first().email if db.query(User).filter(User.id == t.user_id).first() else "Unknown",
        "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED",
        "Question": t.question,
        "Answer": t.answer or ""
    } for t in tickets]

@router.post("/admin/escalations/{ticket_id}/answer")
async def answer_escalation(
    ticket_id: int,
    payload: TicketAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.answer = payload.answer
    ticket.status = "resolved"
    db.commit()

    from routers.notifications import create_notification
    ticket_owner = db.query(User).filter(User.id == ticket.user_id).first()
    if ticket_owner:
        create_notification(db, ticket_owner.id, "ticket_answered", "Ticket Answered",
                            f"Admin answered your escalation ticket #{ticket_id}")
    return {"status": "success"}

# ── User escalations ──────────────────────────────────
class TicketCreate(BaseModel):
    question: str

@router.post("/escalations")
async def create_escalation(
    ticket: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.add(EscalationTicket(user_id=current_user.id, question=ticket.question))
    admins = db.query(User).filter(User.is_admin == True).all()
    from routers.notifications import create_notification
    for admin in admins:
        create_notification(db, admin.id, "new_escalation", "New Support Ticket",
                            f"User {current_user.email} submitted a new escalation")
    db.commit()
    return {"status": "success"}

@router.get("/escalations/my")
async def get_my_escalations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tickets = db.query(EscalationTicket).filter(
        EscalationTicket.user_id == current_user.id
    ).order_by(EscalationTicket.created_at.desc()).all()
    return [{
        "Ticket ID": t.id,
        "Date": t.created_at.strftime("%Y-%m-%d %H:%M"),
        "Question": t.question,
        "Admin Answer": t.answer or "⏳ Pending Review...",
        "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED"
    } for t in tickets]