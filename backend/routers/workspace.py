from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from models import get_db, User, Workspace, WorkspaceMember
from auth import get_current_user

router = APIRouter()

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MemberAdd(BaseModel):
    user_id: int
    role: str = "member"

# ── Create workspace ─────────────────────────────────
@router.post("/workspaces")
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Workspace).filter(Workspace.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Workspace name already exists")
    
    workspace = Workspace(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    # Add creator as admin
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="admin"
    )
    db.add(member)
    db.commit()
    
    return {"id": workspace.id, "name": workspace.name, "status": "success"}

# ── List user's workspaces ───────────────────────────
@router.get("/workspaces")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    ).all()
    
    result = []
    for m in memberships:
        workspace = db.query(Workspace).filter(Workspace.id == m.workspace_id).first()
        if workspace:
            member_count = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == workspace.id
            ).count()
            result.append({
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description or "",
                "role": m.role,
                "member_count": member_count,
                "created_at": workspace.created_at.strftime("%Y-%m-%d")
            })
    return result

# ── Add member ───────────────────────────────────────
@router.post("/workspaces/{workspace_id}/members")
async def add_member(
    workspace_id: int,
    payload: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if current user is admin of workspace
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.role == "admin"
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Only workspace admins can add members")
    
    # Check if user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == payload.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in workspace")
    
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=payload.user_id,
        role=payload.role
    )
    db.add(member)
    db.commit()
    
    return {"status": "success", "message": f"User {payload.user_id} added to workspace"}

# ── List members ─────────────────────────────────────
@router.get("/workspaces/{workspace_id}/members")
async def list_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    members = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id
    ).all()
    
    return [{
        "user_id": m.user_id,
        "email": m.user.email,
        "name": m.user.full_name,
        "role": m.role,
        "joined_at": m.joined_at.strftime("%Y-%m-%d")
    } for m in members]

# ── Delete workspace ─────────────────────────────────
@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.created_by == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    
    db.delete(workspace)
    db.commit()
    return {"status": "success", "message": f"Workspace '{workspace.name}' deleted"}