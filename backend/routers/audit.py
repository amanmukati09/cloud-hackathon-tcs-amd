# backend/routers/audit.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db, User, AuditLog
from auth import get_current_user

router = APIRouter()

@router.get("/admin/audit-logs")
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get recent audit logs (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied.")
    
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [{
        "id": l.id,
        "user": l.user_email or "System",
        "action": l.action,
        "resource": f"{l.resource_type}#{l.resource_id}" if l.resource_type else "-",
        "details": l.details or "",
        "ip": l.ip_address or "-",
        "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for l in logs]