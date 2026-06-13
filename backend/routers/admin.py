# backend/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import re
import pandas as pd
from models import get_db, User, Incident, ChatSession, ChatMessage, EscalationTicket
from auth import get_current_user
from cache import cached, clear_prefix
from fastapi import Request
import time
from cache import _redis
from datetime import datetime, timedelta


router = APIRouter()

# ── Metrics (cached) ─────────────────────────────────
@router.get("/admin/metrics")
@cached("admin_metrics", ttl=60)
async def get_admin_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    severity: str = "ALL"
):
    """Get filtered metrics for admin dashboard."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Base queries
    query = db.query(Incident)
    if days > 0:
        query = query.filter(Incident.timestamp >= cutoff)
    if severity and severity != "ALL":
        query = query.filter(Incident.anomaly_description.ilike(f"%Severity: {severity}%"))
    
    total_incidents = query.count()
    resolved = query.filter(Incident.status == "resolved").count()
    open_count = query.filter(Incident.status == "open").count()
    critical = query.filter(Incident.anomaly_description.ilike("%CRITICAL%")).count()
    
    return {
        "users": db.query(User).count(),
        "incidents": total_incidents,
        "chats": db.query(ChatSession).count(),
        "resolved": resolved,
        "open": open_count,
        "critical": critical,
        "resolution_rate": round(resolved / total_incidents * 100, 1) if total_incidents > 0 else 0
    }

    
# ── Analytics data ────────────────────────────────────
@router.get("/admin/analytics/data")
async def get_analytics_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    severity: str = "ALL"
):
    """Fetches filtered incident data for the Analytics Dashboard."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(Incident).filter(Incident.timestamp >= cutoff)
    if severity and severity != "ALL":
        query = query.filter(Incident.anomaly_description.ilike(f"%Severity: {severity}%"))
    
    incidents = query.order_by(Incident.timestamp.desc()).all()
    
    return [{
        "date": i.timestamp.strftime("%Y-%m-%d"),
        "status": i.status,
        "description": i.anomaly_description
    } for i in incidents]

    

# ── Enhanced analytics ────────────────────────────────
@router.get("/admin/analytics/enhanced")
async def get_enhanced_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    severity: str = "ALL"
):
    """Enhanced analytics with trends, components, and MTTR by severity."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    from datetime import timedelta
    
    # Apply filters
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(Incident).filter(Incident.timestamp >= cutoff)
    if severity and severity != "ALL":
        query = query.filter(Incident.anomaly_description.ilike(f"%Severity: {severity}%"))
    
    incidents = query.all()
    
    if not incidents:
        return {
            "trend": [],
            "components": [],
            "mttr_by_severity": [],
            "heatmap": [],
            "total_filtered": 0,
            "period": f"Last {days} days",
            "severity_filter": severity
        }
    
    # Convert to DataFrame
    data = []
    for inc in incidents:
        severity_match = re.search(r'Severity:\s*([A-Z]+)', inc.anomaly_description or "")
        component_match = re.search(r'Component:\s*([^\n,]+)', inc.anomaly_description or "")
        
        sev = severity_match.group(1) if severity_match else "UNKNOWN"
        comp = component_match.group(1).strip() if component_match else "Unknown"
        
        resolution_hours = None
        if inc.resolved_at and inc.status == "resolved":
            resolution_hours = (inc.resolved_at - inc.timestamp).total_seconds() / 3600
        
        data.append({
            "date": inc.timestamp.strftime("%Y-%m-%d"),
            "hour": inc.timestamp.hour,
            "weekday": inc.timestamp.strftime("%A"),
            "severity": sev,
            "component": comp,
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
    mttr_data = []
    if not resolved.empty:
        mttr = resolved.groupby('severity')['resolution_hours'].agg(['mean', 'count']).round(1)
        mttr = mttr.reset_index()
        mttr.columns = ['severity', 'avg_hours', 'count']
        mttr_data = mttr.to_dict('records')
    
    # 4. Heatmap (Day of Week vs Hour)
    heatmap = df.groupby(['weekday', 'hour']).size().reset_index(name='incidents')
    heatmap_data = heatmap.to_dict('records')
    
    # 5. Severity Distribution
    severity_dist = df.groupby('severity').size().reset_index(name='count')
    severity_data = severity_dist.to_dict('records')
    
    # 6. Status Distribution
    status_dist = df.groupby('status').size().reset_index(name='count')
    status_data = status_dist.to_dict('records')
    
    return {
        "trend": trend_data,
        "components": component_data,
        "mttr_by_severity": mttr_data,
        "heatmap": heatmap_data,
        "severity_distribution": severity_data,
        "status_distribution": status_data,
        "total_filtered": len(incidents),
        "period": f"Last {days} days",
        "severity_filter": severity
    }

    
# ── Predictions ───────────────────────────────────────
@router.get("/admin/predictions")
async def get_incident_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    from agents.predictor import IncidentPredictor
    import re as regex
    incidents = db.query(Incident).all()
    if not incidents:
        return {"predictions": [], "risk_level": "LOW", "summary": "No data"}
    data = []
    for inc in incidents:
        sev = regex.search(r'Severity:\s*([A-Z]+)', inc.anomaly_description or "")
        comp = regex.search(r'Component:\s*([^\n,]+)', inc.anomaly_description or "")
        data.append({
            "date": inc.timestamp.strftime("%Y-%m-%d"),
            "hour": inc.timestamp.hour,
            "weekday": inc.timestamp.strftime("%A"),
            "severity": sev.group(1) if sev else "UNKNOWN",
            "component": comp.group(1).strip() if comp else "Unknown",
            "anomaly_type": inc.anomaly_description[:50] if inc.anomaly_description else "Unknown",
            "status": inc.status
        })
    predictor = IncidentPredictor()
    return predictor.analyze_patterns(data)

# ── Clusters ──────────────────────────────────────────
@router.get("/admin/clusters")
async def get_incident_clusters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    from agents.clustering import IncidentClusterer
    import re as regex
    incidents = db.query(Incident).order_by(Incident.timestamp.desc()).limit(200).all()
    if not incidents:
        return {"clusters": [], "summary": "No incidents"}
    data = []
    for inc in incidents:
        sev = regex.search(r'Severity:\s*([A-Z]+)', inc.anomaly_description or "")
        data.append({
            "id": inc.id,
            "anomaly_description": inc.anomaly_description or "",
            "root_cause": inc.root_cause or "",
            "severity": sev.group(1) if sev else "UNKNOWN",
            "component": "Unknown",
            "status": inc.status,
            "date": inc.timestamp.strftime("%Y-%m-%d")
        })
    clusterer = IncidentClusterer()
    clusters = clusterer.cluster_incidents(data)
    html = clusterer.render_clusters_html(clusters)
    return {"clusters": clusters, "html": html}

# ── User list ─────────────────────────────────────────
@router.get("/admin/users")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    from sqlalchemy import func
    users = db.query(
        User.id, User.full_name, User.email, User.is_admin, User.created_at,
        func.count(Incident.id).label('incident_count'),
        func.count(ChatSession.id).label('chat_count')
    ).outerjoin(Incident, Incident.user_id == User.id
    ).outerjoin(ChatSession, ChatSession.user_id == User.id
    ).group_by(User.id
    ).order_by(User.created_at.desc()
    ).limit(limit).all()
    result = []
    for u in users:
        result.append({
            "User ID": u.id,
            "Full Name": u.full_name,
            "Email": u.email,
            "Role": "Admin" if u.is_admin else "User",
            "Incidents": u.incident_count,
            "Chats": u.chat_count,
            "Joined": u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
        })
    return result

# ── User exists ───────────────────────────────────────
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
    clear_prefix("admin_metrics")
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
        "ID": i.id, "Date": i.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Raw Logs": i.raw_logs, "Anomaly Found": i.anomaly_description,
        "Root Cause": i.root_cause, "Remediation": i.remediation_action,
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
        "Session ID": m.session_id, "Time": m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Role": m.role.upper(), "Message Content": m.content
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
    ticket_id: int, payload: TicketAnswer,
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
        "Ticket ID": t.id, "Date": t.created_at.strftime("%Y-%m-%d %H:%M"),
        "Question": t.question, "Admin Answer": t.answer or "⏳ Pending Review...",
        "Status": "🟢 OPEN" if t.status == "open" else "✅ RESOLVED"
    } for t in tickets]

# ── Alert configuration ───────────────────────────────
class AlertConfigRequest(BaseModel):
    slack_webhook: Optional[str] = None
    teams_webhook: Optional[str] = None
    pagerduty_key: Optional[str] = None
    opsgenie_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    alert_emails: Optional[str] = None  # comma-separated

@router.post("/admin/alerts/configure")
async def configure_alerts(
    config: AlertConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    from agents.alerting import AlertManager
    mgr = AlertManager()
    
    smtp_config = {}
    if config.smtp_host: smtp_config["host"] = config.smtp_host
    if config.smtp_port: smtp_config["port"] = config.smtp_port
    if config.smtp_username: smtp_config["username"] = config.smtp_username
    if config.smtp_password: smtp_config["password"] = config.smtp_password
    if config.smtp_from: smtp_config["from_email"] = config.smtp_from
    if config.alert_emails: smtp_config["to_emails"] = [e.strip() for e in config.alert_emails.split(",") if e.strip()]
    
    mgr.configure(
        slack_url=config.slack_webhook,
        teams_url=config.teams_webhook,
        pagerduty_key=config.pagerduty_key,
        opsgenie_key=config.opsgenie_key,
        smtp_config=smtp_config if smtp_config else None
    )
    
    return {"status": "success", "message": "Alert configuration updated"}
    

@router.post("/admin/alerts/test")
async def test_alert(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    from agents.alerting import AlertManager
    mgr = AlertManager()
    test_data = {"id": "TEST", "anomaly_type": "Test", "severity": "LOW",
                 "affected_component": "Alert", "description": "Test alert",
                 "root_cause": "Testing", "remediation": "None", "timestamp": "Now"}
    return {"status": "success", "results": mgr.send_incident_alert(test_data)}


    
@router.get("/admin/rate-limit-status")
async def rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get current rate limit status for the user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    user_id = request.headers.get("authorization", request.client.host)
    key = f"rate_limit:{user_id}:{int(time.time() / 60)}"
    current = _redis.get(key)
    
    return {
        "current": int(current) if current else 0,
        "limit": 60,
        "window": "1 minute"
    }