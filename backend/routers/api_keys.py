from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import hashlib
import secrets
from datetime import datetime, timedelta

from models import get_db, User, ApiKey
from auth import get_current_user

router = APIRouter()

class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None  # None = never expires

def generate_api_key() -> tuple:
    """Generate a new API key. Returns (full_key, hash, prefix)."""
    raw_key = f"aegis_{secrets.token_hex(24)}"  # aegis_ + 48 hex chars
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:15] + "..."  # Show first 12 chars + "..."
    return raw_key, key_hash, key_prefix

# ── Create API Key ───────────────────────────────────
@router.post("/api-keys")
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    raw_key, key_hash, key_prefix = generate_api_key()
    
    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)
    
    api_key = ApiKey(
        user_id=current_user.id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw_key,  # ⚠️ Only shown once!
        "prefix": key_prefix,
        "created_at": api_key.created_at.strftime("%Y-%m-%d %H:%M"),
        "expires_at": api_key.expires_at.strftime("%Y-%m-%d %H:%M") if api_key.expires_at else "Never"
    }

# ── List API Keys ────────────────────────────────────
@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active == True
    ).order_by(ApiKey.created_at.desc()).all()
    
    return [{
        "id": k.id,
        "name": k.name,
        "prefix": k.key_prefix,
        "is_active": k.is_active,
        "last_used": k.last_used_at.strftime("%Y-%m-%d %H:%M") if k.last_used_at else "Never",
        "created_at": k.created_at.strftime("%Y-%m-%d %H:%M"),
        "expires_at": k.expires_at.strftime("%Y-%m-%d %H:%M") if k.expires_at else "Never"
    } for k in keys]

# ── Revoke API Key ───────────────────────────────────
@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = False
    db.commit()
    
    return {"status": "success", "message": f"API key '{key.name}' revoked"}

# ── API Key Authentication Dependency ─────────────────
async def get_user_from_api_key(
    api_key: str = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """Authenticate using API key from header: Authorization: Bearer aegis_xxx"""
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    security = HTTPBearer()
    credentials: HTTPAuthorizationCredentials = await security(request)
    
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
    
    raw_key = credentials.credentials
    if not raw_key.startswith("aegis_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        api_key.is_active = False
        db.commit()
        raise HTTPException(status_code=401, detail="API key has expired")
    
    # Update last used
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    user = db.query(User).filter(User.id == api_key.user_id).first()
    return user