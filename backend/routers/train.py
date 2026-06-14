from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from models import get_db, User, Incident
from auth import get_current_user
from agents.gpu_trainer import trainer as model_trainer
from gpu_utils import gpu_detector

router = APIRouter(prefix="/train", tags=["Model Training"])

class TrainingRequest(BaseModel):
    base_model: str = "llama3"
    num_epochs: int = 3
    use_all_incidents: bool = False       # admins can set True

@router.get("/status")
async def get_training_status(current_user: User = Depends(get_current_user)):
    """Training status (same for all users)."""
    return model_trainer.get_status()

@router.get("/gpu-info")
async def get_gpu_info(current_user: User = Depends(get_current_user)):
    config = gpu_detector.get_config()
    return {
        **config,
        "estimated_training_time": "10-15 minutes" if config["can_fine_tune"] else "30+ minutes (CPU)",
        "recommended_models": ["llama3", "mistral"] if config["can_fine_tune"] else ["tinyllama"]
    }

@router.post("/start")
async def start_training(
    req: TrainingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine the data scope
    if req.use_all_incidents and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can train on all incidents")

    query = db.query(Incident)
    if not req.use_all_incidents:
        query = query.filter(Incident.user_id == current_user.id)   # own incidents
    else:
        # admin using all incidents
        pass

    incidents = query.filter(
        Incident.root_cause.isnot(None),
        Incident.remediation_action.isnot(None)
    ).order_by(Incident.timestamp.desc()).limit(200).all()

    if not incidents:
        raise HTTPException(status_code=400, detail="No resolved incidents found for training")

    # Format training data
    training_data = []
    for inc in incidents:
        input_text = f"Logs: {inc.raw_logs[:500] if inc.raw_logs else 'N/A'}\nAnomaly: {inc.anomaly_description or 'N/A'}"
        output_text = f"Root Cause: {inc.root_cause or 'N/A'}\nRemediation: {inc.remediation_action or 'N/A'}"
        if inc.resolution_notes:
            output_text += f"\nResolution Notes: {inc.resolution_notes}"
        training_data.append({"input": input_text, "output": output_text})

    # Determine model suffix
    if req.use_all_incidents and current_user.is_admin:
        scope = "all"
    else:
        scope = f"user_{current_user.id}"

    print(f"📚 Training {len(training_data)} examples for scope={scope}")

    model_trainer.start_training(
        training_data=training_data,
        base_model=req.base_model,
        num_epochs=req.num_epochs,
        scope=scope,
        progress_callback=None
    )

    return {
        "status": "started",
        "message": f"Training started with {len(training_data)} examples. Model: {req.base_model} (scope: {scope})",
        "estimated_time": "10-15 minutes" if gpu_detector.get_config()["can_fine_tune"] else "30+ minutes"
    }

@router.post("/reset")
async def reset_training_status(current_user: User = Depends(get_current_user)):
    model_trainer.training_status = {
        "running": False, "progress": 0.0, "current_step": 0,
        "total_steps": 0, "loss": None, "message": "Idle",
        "started_at": None, "finished_at": None, "error": None,
        "output_model": None,
    }
    return {"status": "reset"}