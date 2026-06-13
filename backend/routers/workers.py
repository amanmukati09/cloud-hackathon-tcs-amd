from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import get_db, User
from auth import get_current_user
from workers.tasks import add_task, get_task_status
from guardrails import guard

router = APIRouter()

class AsyncDiagnosisRequest(BaseModel):
    logs: list[str]

@router.post("/async/diagnose")
async def async_diagnose(
    request: AsyncDiagnosisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a diagnosis task to background worker."""
    
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    
    def run_diagnosis():
        from agents.monitor import MonitorAgent
        from agents.diagnosis import DiagnosisAgent
        from agents.remediation import RemediationAgent
        from models import Incident

        monitor = MonitorAgent()
        diagnosis = DiagnosisAgent()
        remediation = RemediationAgent()
        
        anomaly = monitor.detect_anomaly(safe_logs)
        if not anomaly.get("anomaly_detected"):
            return {"status": "ok", "anomaly_detected": False}
        
        root_cause = diagnosis.analyze_root_cause(anomaly, safe_logs)
        remed_plan = remediation.suggest_remediation(anomaly, root_cause)
        
        # Save to DB
        log_text = "\n".join(safe_logs)
        new_incident = Incident(
            user_id=current_user.id, raw_logs=log_text, status="open",
            anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
            root_cause=root_cause.get("root_cause") if isinstance(root_cause, dict) else str(root_cause),
            remediation_action=", ".join(remed_plan.get("immediate_actions", [])),
            remediation_status="pending"
        )
        db.add(new_incident)
        db.commit()
        
        return {"incident_id": new_incident.id, "anomaly": anomaly, "root_cause": root_cause, "remediation": remed_plan}
    
    task_id = add_task("diagnosis", run_diagnosis)
    return {"task_id": task_id, "status": "pending", "message": "Diagnosis queued"}

@router.get("/async/task/{task_id}")
async def get_task(task_id: int):
    """Get status of a background task."""
    return get_task_status(task_id)