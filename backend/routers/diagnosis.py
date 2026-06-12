from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from models import get_db, User, Incident
from auth import get_current_user
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent
from guardrails import guard
from fastapi.concurrency import run_in_threadpool
import asyncio
from pydantic import BaseModel

router = APIRouter()

monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()

class AILimiter:
    def __init__(self, limit=2):
        self.limit = limit
        self._semaphore = None
    async def __aenter__(self):
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.limit)
        await self._semaphore.acquire()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()

ai_queue = AILimiter(2)

class IncidentRequest(BaseModel):
    logs: list[str]

class SimilarityRequest(BaseModel):
    logs: list[str]

def _safe_join(val):
    if not val: return "None"
    if isinstance(val, list): return ", ".join([str(item) for item in val])
    return str(val)

@router.post("/diagnose")
async def diagnose_incident(
    request: IncidentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    
    async with ai_queue:
        anomaly = await run_in_threadpool(monitor.detect_anomaly, safe_logs)
        if not anomaly.get("anomaly_detected"):
            return {"status": "ok", "anomaly_detected": False}
        root_cause = await run_in_threadpool(diagnosis.analyze_root_cause, anomaly, safe_logs)
        remed_plan = await run_in_threadpool(remediation.suggest_remediation, anomaly, root_cause)

    if guard.is_destructive(str(remed_plan)):
        remed_plan = {
            "immediate_actions": ["🚨 BLOCKED: AI suggested potentially destructive command."],
            "automated_actions": [],
            "escalation_needed": True,
            "estimated_recovery_time": "Manual",
            "prevention_measures": ["Review AI prompt safety limits."]
        }

    log_text = "\n".join(safe_logs)
    new_incident = Incident(
        user_id=current_user.id, raw_logs=log_text, status="open",
        anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
        root_cause=root_cause.get("root_cause") if isinstance(root_cause, dict) else str(root_cause),
        remediation_action=_safe_join(remed_plan.get("immediate_actions", [])),
        remediation_status="pending"
    )
    db.add(new_incident)
    db.commit()
    from routers.notifications import create_notification
    create_notification(db, current_user.id, "diagnosis_complete", "Diagnosis Complete", f"Incident #{new_incident.id} has been analyzed")
    db.refresh(new_incident)
    return {"incident_id": new_incident.id, "anomaly": anomaly, "root_cause": root_cause, "remediation": remed_plan}

@router.post("/upload-logs")
async def upload_log_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    all_logs, file_names, total_size = [], [], 0
    for file in files:
        if not file.filename.endswith(('.log', '.txt', '.out', '.LOG', '.TXT')):
            continue
        content = await file.read()
        total_size += len(content)
        if total_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Total file size exceeds 10MB limit")
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('latin-1')
            except:
                text = content.decode('utf-8', errors='ignore')
        lines = text.split('\n')
        all_logs.extend([line.strip() for line in lines if line.strip()])
        file_names.append(file.filename)
    return {
        "file_names": file_names,
        "total_lines": len(all_logs),
        "total_size_kb": round(total_size / 1024, 2),
        "logs": all_logs[:5000]
    }

@router.post("/incidents/similar")
async def find_similar_incidents(
    request: SimilarityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    safe_logs = []
    for log_line in request.logs:
        masked_line, _ = guard.mask_pii(log_line)
        safe_logs.append(masked_line)
    search_query = " ".join(safe_logs)
    try:
        from chroma_store import IncidentStore
        store = IncidentStore()
        results = store.search_similar(search_query, top_k=3)
        similar_incidents = []
        if results and results.get('ids') and results['ids'][0]:
            for i, incident_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results.get('distances') else 1.0
                similarity_score = max(0, min(100, (1 - distance) * 100))
                incident = db.query(Incident).filter(Incident.id == int(incident_id)).first()
                if incident:
                    similar_incidents.append({
                        "incident_id": incident.id,
                        "similarity": round(similarity_score, 1),
                        "date": incident.timestamp.strftime("%Y-%m-%d %H:%M"),
                        "anomaly": incident.anomaly_description[:100] + "..." if len(incident.anomaly_description) > 100 else incident.anomaly_description,
                        "root_cause": incident.root_cause[:100] + "..." if len(incident.root_cause) > 100 else incident.root_cause,
                        "status": incident.status
                    })
        return {"similar_incidents": similar_incidents}
    except Exception as e:
        print(f"Similarity search error: {e}")
        return {"similar_incidents": []}