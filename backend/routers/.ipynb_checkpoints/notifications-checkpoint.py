# backend/routers/notifications.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import get_db, User, Notification
from auth import get_current_user

router = APIRouter()

# ── Get notifications ─────────────────────────────────
@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

# ── Mark all read ─────────────────────────────────────
@router.post("/notifications/mark-read")
async def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}

# ── Helper to create notifications (used by other routers) ──
def create_notification(db: Session, user_id: int, notif_type: str, title: str, message: str = ""):
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message
    )
    db.add(notif)
    db.commit()