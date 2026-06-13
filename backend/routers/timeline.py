from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import get_db, User, Incident
from auth import get_current_user

router = APIRouter()

@router.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the visual timeline for an incident."""
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": "Incident not found"}
    
    # Check access
    if incident.user_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}
    
    # Build timeline events
    events = []
    
    # Event 1: Incident Created
    events.append({
        "time": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "title": "Incident Detected",
        "description": f"Logs submitted for analysis",
        "icon": "🔴",
        "color": "#ef4444",
        "type": "detection"
    })
    
    # Event 2: Diagnosis (if anomaly was detected)
    if incident.anomaly_description and "Type:" in (incident.anomaly_description or ""):
        severity = "Unknown"
        if "Severity:" in incident.anomaly_description:
            parts = incident.anomaly_description.split("Severity:")
            if len(parts) > 1:
                severity = parts[1].strip().split()[0]
        
        events.append({
            "time": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "title": f"Anomaly Identified ({severity})",
            "description": incident.anomaly_description[:150],
            "icon": "⚠️",
            "color": "#f59e0b" if severity in ["MEDIUM", "LOW"] else "#ef4444",
            "type": "diagnosis"
        })
    
    # Event 3: Root Cause Found
    if incident.root_cause:
        events.append({
            "time": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "title": "Root Cause Analyzed",
            "description": incident.root_cause[:150],
            "icon": "🔍",
            "color": "#3b82f6",
            "type": "root_cause"
        })
    
    # Event 4: Remediation Suggested
    if incident.remediation_action:
        events.append({
            "time": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "title": "Remediation Plan Created",
            "description": incident.remediation_action[:150],
            "icon": "🔧",
            "color": "#8b5cf6",
            "type": "remediation"
        })
    
    # Event 5: Resolution (if resolved)
    if incident.status == "resolved" and incident.resolved_at:
        resolution_time = incident.resolved_at - incident.timestamp
        hours = round(resolution_time.total_seconds() / 3600, 1)
        
        events.append({
            "time": incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S"),
            "title": f"Incident Resolved ({hours}h total)",
            "description": incident.resolution_notes or "No resolution notes provided",
            "icon": "✅",
            "color": "#10b981",
            "type": "resolution"
        })
    
    return {
        "incident_id": incident.id,
        "status": incident.status,
        "timeline": events
    }