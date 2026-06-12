from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from models import get_db, User, Incident
from auth import get_current_user
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent
from guardrails import guard
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()

class WorkflowRequest(BaseModel):
    logs: list[str]
    auto_execute: bool = False

class ExecuteCommand(BaseModel):
    command: str
    incident_id: int

class AILimiter:
    def __init__(self, limit=1):
        self.limit = limit
        self._semaphore = None
    async def __aenter__(self):
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.limit)
        await self._semaphore.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()

ai_queue = AILimiter(1)

@router.post("/workflow/auto-remediate")
async def auto_remediate(
    request: WorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Full autonomous workflow: Analyze → Diagnose → Remediate → Execute."""
    
    # 🛡️ Mask PII
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    
    workflow_steps = []
    
    # Step 1: Monitor/Detect
    workflow_steps.append({"step": 1, "name": "🔍 Detecting anomalies...", "status": "running"})
    
    async with ai_queue:
        anomaly = await run_in_threadpool(monitor.detect_anomaly, safe_logs)
        
        if not anomaly.get("anomaly_detected"):
            workflow_steps[-1]["status"] = "completed"
            workflow_steps.append({"step": 2, "name": "✅ No anomaly detected", "status": "completed"})
            return {"workflow_steps": workflow_steps, "anomaly_detected": False}
        
        workflow_steps[-1]["status"] = "completed"
        workflow_steps.append({
            "step": 2, "name": f"⚠️ Anomaly found: {anomaly.get('anomaly_type')} ({anomaly.get('severity')})",
            "status": "completed", "detail": anomaly
        })
        
        # Step 2: Diagnose root cause
        workflow_steps.append({"step": 3, "name": "🔬 Analyzing root cause...", "status": "running"})
        root_cause = await run_in_threadpool(diagnosis.analyze_root_cause, anomaly, safe_logs)
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["detail"] = root_cause
        
        # Step 3: Generate remediation plan
        workflow_steps.append({"step": 4, "name": "⚙️ Generating remediation plan...", "status": "running"})
        remed_plan = await run_in_threadpool(remediation.suggest_remediation, anomaly, root_cause)
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["detail"] = remed_plan
    
    # Save incident
    log_text = "\n".join(safe_logs)
    new_incident = Incident(
        user_id=current_user.id, raw_logs=log_text, status="open",
        anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
        root_cause=root_cause.get("root_cause", "") if isinstance(root_cause, dict) else str(root_cause),
        remediation_action=", ".join(remed_plan.get("immediate_actions", [])),
        remediation_status="pending"
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    # Step 4: Execute diagnostic commands
    diagnostic_results = []
    if remed_plan.get("diagnostic_commands"):
        workflow_steps.append({"step": 5, "name": "🖥️ Running diagnostic commands...", "status": "running"})
        for cmd in remed_plan.get("diagnostic_commands", [])[:5]:  # Max 5 commands
            result = remediation.execute_remediation(cmd)
            diagnostic_results.append(result)
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["commands"] = diagnostic_results
    
    # Step 5: Auto-execute safe remediations if requested
    if request.auto_execute and remed_plan.get("automated_actions"):
        workflow_steps.append({"step": 6, "name": "🔧 Executing automated fixes...", "status": "running"})
        exec_results = []
        for action in remed_plan.get("automated_actions", [])[:3]:
            if isinstance(action, dict) and action.get("command"):
                if action.get("risk_level") in ["LOW", "MEDIUM"]:
                    result = remediation.execute_remediation(action["command"])
                    exec_results.append(result)
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["results"] = exec_results
    
    return {
        "incident_id": new_incident.id,
        "workflow_steps": workflow_steps,
        "anomaly_detected": True,
        "anomaly": anomaly,
        "root_cause": root_cause,
        "remediation": remed_plan,
        "diagnostic_results": diagnostic_results
    }

@router.post("/workflow/execute-command")
async def execute_command(
    request: ExecuteCommand,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a single remediation command."""
    # Verify incident exists
    incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    result = remediation.execute_remediation(request.command)
    return result