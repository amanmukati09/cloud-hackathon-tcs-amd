from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent

app = FastAPI(title="Incident Diagnosis Agent")

# Initialize agents
monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()

class IncidentRequest(BaseModel):
    logs: list[str]

def get_db():
    return sqlite3.connect("data/incidents.db")

@app.post("/diagnose")
async def diagnose_incident(request: IncidentRequest):
    """Full diagnosis pipeline"""
    
    # Step 1: Detect anomaly
    anomaly = monitor.detect_anomaly(request.logs)
    
    if not anomaly.get("anomaly_detected"):
        return {"status": "ok", "anomaly_detected": False}
    
    # Step 2: Analyze root cause
    root_cause = diagnosis.analyze_root_cause(anomaly, request.logs)
    
    # Step 3: Suggest remediation
    remedi = remediation.suggest_remediation(anomaly, root_cause)
    
    # Step 4: Save to database
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO incidents 
        (status, anomaly_description, root_cause, remediation_action)
        VALUES (?, ?, ?, ?)
    """, (
        "open",
        json.dumps(anomaly),
        json.dumps(root_cause),
        json.dumps(remedi)
    ))
    incident_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "incident_id": incident_id,
        "anomaly": anomaly,
        "root_cause": root_cause,
        "remediation": remedi
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/incidents")
def list_incidents():
    conn = get_db()
    c = conn.cursor()
    incidents = c.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 10").fetchall()
    conn.close()
    
    return {"count": len(incidents), "incidents": incidents}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
