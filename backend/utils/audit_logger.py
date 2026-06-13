# backend/utils/audit_logger.py

from sqlalchemy.orm import Session
from models import AuditLog, User

def log_action(
    db: Session,
    user: User,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: str = None,
    ip_address: str = None
):
    """Create an audit log entry."""
    try:
        log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Audit log error: {e}")