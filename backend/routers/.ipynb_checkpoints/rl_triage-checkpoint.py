from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import get_db, User, Incident
from auth import get_current_user
from agents.rl_triage import rl_agent

router = APIRouter(prefix="/rl", tags=["RL Triage"])

class TrainRequest(BaseModel):
    limit: int = 200


@router.get("/priority-queue")
async def get_priority_queue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    incidents = db.query(Incident).filter(Incident.status == "open").order_by(Incident.timestamp.desc()).limit(50).all()
    
    if not incidents:
        return {"queue": [], "message": "No open incidents"}
    
    inc_data = []
    for inc in incidents:
        sev = "MEDIUM"
        if inc.anomaly_description:
            desc = inc.anomaly_description.upper()
            if "CRITICAL" in desc: sev = "CRITICAL"
            elif "HIGH" in desc: sev = "HIGH"
            elif "LOW" in desc: sev = "LOW"
        
        comp = "Other"
        desc_lower = (inc.anomaly_description or "").lower()
        if "database" in desc_lower or "sql" in desc_lower: comp = "Database"
        elif "nginx" in desc_lower: comp = "Nginx"
        elif "redis" in desc_lower or "cache" in desc_lower: comp = "Redis"
        elif "api" in desc_lower or "gateway" in desc_lower: comp = "API Gateway"
        elif "system" in desc_lower or "memory" in desc_lower or "cpu" in desc_lower: comp = "System"
        
        inc_data.append({
            "id": int(inc.id), 
            "severity": sev, 
            "component": comp, 
            "status": inc.status or "open", 
            "description": (inc.anomaly_description or "")[:100]
        })
    
    queue = rl_agent.get_priority_queue(inc_data)
    
    # Ensure all values are JSON serializable
    clean_queue = []
    for item in queue[:20]:
        clean_item = {}
        for k, v in item.items():
            if isinstance(v, (np.integer, np.int64)):
                clean_item[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                clean_item[k] = float(v)
            elif isinstance(v, np.ndarray):
                clean_item[k] = v.tolist()
            elif isinstance(v, tuple):
                clean_item[k] = list(v)
            else:
                clean_item[k] = v
        clean_queue.append(clean_item)
    
    return {"queue": clean_queue, "message": f"Prioritized {len(clean_queue)} incidents"}

    
    
@router.post("/train")
async def train_agent(req: TrainRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
    
    incidents = db.query(Incident).filter(
        Incident.status == "resolved", 
        Incident.resolved_at.isnot(None)
    ).limit(req.limit).all()
    
    if not incidents:
        return {"message": "No resolved incidents to train on"}
    
    inc_data = []
    for inc in incidents:
        # Extract REAL severity
        sev = "MEDIUM"
        desc = (inc.anomaly_description or "").upper()
        if "CRITICAL" in desc:
            sev = "CRITICAL"
        elif "HIGH" in desc:
            sev = "HIGH"
        elif "LOW" in desc:
            sev = "LOW"
        
        # Extract REAL component
        comp = "Other"
        desc_lower = (inc.anomaly_description or "").lower()
        if "database" in desc_lower or "sql" in desc_lower:
            comp = "Database"
        elif "nginx" in desc_lower:
            comp = "Nginx"
        elif "redis" in desc_lower or "cache" in desc_lower:
            comp = "Redis"
        elif "api" in desc_lower or "gateway" in desc_lower:
            comp = "API Gateway"
        elif "system" in desc_lower or "memory" in desc_lower or "cpu" in desc_lower:
            comp = "System"
        
        # Calculate resolution hours
        resolution_hours = 24
        if inc.resolved_at and inc.timestamp:
            delta = inc.resolved_at - inc.timestamp
            resolution_hours = delta.total_seconds() / 3600
        
        inc_data.append({
            "id": inc.id, 
            "severity": sev, 
            "component": comp, 
            "resolution_hours": resolution_hours
        })
    
    result = rl_agent.train_on_history(inc_data)
    
    # Return sample of what was trained
    sample_severities = {}
    sample_components = {}
    for inc in inc_data[:50]:
        sample_severities[inc["severity"]] = sample_severities.get(inc["severity"], 0) + 1
        sample_components[inc["component"]] = sample_components.get(inc["component"], 0) + 1
    
    return {
        **result,
        "sample_severities": sample_severities,
        "sample_components": sample_components
    }

    

@router.get("/stats")
async def get_rl_stats():
    return {"q_table_size": len(rl_agent.q_table), "epsilon": rl_agent.epsilon, "model_trained": len(rl_agent.q_table) > 10}