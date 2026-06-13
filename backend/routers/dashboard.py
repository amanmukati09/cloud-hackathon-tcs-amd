from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import re
from datetime import datetime, timedelta

from models import get_db, User, Incident
from auth import get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    severity: Optional[str] = None
):
    """Get filtered dashboard summary."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(Incident).filter(Incident.timestamp >= cutoff)
    
    if severity and severity != "ALL":
        query = query.filter(Incident.anomaly_description.ilike(f"%Severity: {severity}%"))
    
    incidents = query.order_by(Incident.timestamp.desc()).all()
    
    # Calculate metrics
    total = len(incidents)
    resolved = sum(1 for i in incidents if i.status == "resolved")
    open_count = sum(1 for i in incidents if i.status == "open")
    critical = sum(1 for i in incidents if "CRITICAL" in (i.anomaly_description or "").upper())
    
    # Time series data
    daily_data = {}
    for inc in incidents:
        date_key = inc.timestamp.strftime("%Y-%m-%d")
        daily_data[date_key] = daily_data.get(date_key, 0) + 1
    
    dates = sorted(daily_data.keys())
    counts = [daily_data[d] for d in dates]
    
    # MTTR calculation
    resolved_incidents = [i for i in incidents if i.status == "resolved" and i.resolved_at]
    mttr_hours = 0
    if resolved_incidents:
        total_hours = sum(
            (i.resolved_at - i.timestamp).total_seconds() / 3600 
            for i in resolved_incidents
        )
        mttr_hours = round(total_hours / len(resolved_incidents), 1)
    
    return {
        "metrics": {
            "total_incidents": total,
            "resolved": resolved,
            "open": open_count,
            "critical": critical,
            "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
            "mttr_hours": mttr_hours
        },
        "timeline": {
            "dates": dates,
            "counts": counts
        },
        "period": f"Last {days} days"
    }

@router.get("/dashboard/top-incidents")
async def get_top_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 5
):
    """Get most common incident types."""
    incidents = db.query(Incident).order_by(Incident.timestamp.desc()).limit(200).all()
    
    # Extract incident types
    type_counts = {}
    for inc in incidents:
        match = re.search(r'Type:\s*([^|]+)', inc.anomaly_description or "")
        itype = match.group(1).strip() if match else "Unknown"
        type_counts[itype] = type_counts.get(itype, 0) + 1
    
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [{"type": t, "count": c} for t, c in sorted_types]

@router.get("/dashboard/recent-activity")
async def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent incident activity feed."""
    incidents = db.query(Incident).order_by(Incident.timestamp.desc()).limit(limit).all()
    
    return [{
        "id": i.id,
        "action": "resolved" if i.status == "resolved" else "detected",
        "title": f"Incident #{i.id}",
        "description": (i.anomaly_description or "Unknown")[:100],
        "severity": "HIGH" if "HIGH" in (i.anomaly_description or "") else "MEDIUM",
        "timestamp": i.timestamp.strftime("%Y-%m-%d %H:%M"),
        "time_ago": _time_ago(i.timestamp)
    } for i in incidents]

def _time_ago(dt):
    """Convert datetime to human-readable 'time ago'."""
    diff = datetime.utcnow() - dt
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    return f"{minutes}m ago"