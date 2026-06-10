import json
import sqlite3
import random
from datetime import datetime, timedelta

INCIDENT_TEMPLATES = [
    {
        "logs": [
            "[INFO] nginx worker started",
            "[WARNING] memory usage: 85%",
            "[ERROR] worker process crashed",
            "[ERROR] cpu spike: 95%"
        ],
        "component": "nginx",
        "type": "crash"
    },
    {
        "logs": [
            "[INFO] database connection pool initialized",
            "[ERROR] connection timeout after 30s",
            "[ERROR] query failed: timeout",
            "[WARNING] 10 failed queries in last minute"
        ],
        "component": "database",
        "type": "timeout"
    },
    {
        "logs": [
            "[INFO] api service started",
            "[WARNING] response time: 5000ms",
            "[ERROR] high latency detected",
            "[ERROR] 50 requests queued"
        ],
        "component": "api",
        "type": "latency"
    },
    {
        "logs": [
            "[INFO] cache initialized",
            "[ERROR] memory exhausted",
            "[ERROR] eviction in progress",
            "[WARNING] cache hit rate dropped to 10%"
        ],
        "component": "cache",
        "type": "memory"
    },
    {
        "logs": [
            "[INFO] monitoring agent started",
            "[ERROR] disk usage: 98%",
            "[ERROR] no space for logs",
            "[CRITICAL] system running out of disk"
        ],
        "component": "storage",
        "type": "disk_full"
    },
]

def generate_incidents(count: int = 50):
    """Generate synthetic incidents"""
    conn = sqlite3.connect("data/incidents.db")
    c = conn.cursor()
    
    for i in range(count):
        template = random.choice(INCIDENT_TEMPLATES)
        
        # Vary the logs slightly
        logs = template["logs"].copy()
        if random.random() > 0.5:
            logs.append(f"[INFO] incident #{i+1} triggered")
        
        anomaly = {
            "anomaly_detected": True,
            "anomaly_type": template["type"],
            "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM"]),
            "affected_component": template["component"],
            "description": f"Synthetic incident: {template['type']}"
        }
        
        root_cause = {
            "root_cause": f"System component degradation in {template['component']}",
            "confidence": random.uniform(0.8, 1.0),
            "evidence": logs[-2:],
            "contributing_factors": ["High load", "Resource exhaustion"]
        }
        
        remediation = {
            "immediate_actions": ["Check service status", "Review logs"],
            "automated_actions": [{"action": "restart service", "risk_level": "MEDIUM"}],
            "escalation_needed": anomaly["severity"] == "CRITICAL",
            "estimated_recovery_time": "5 minutes",
            "prevention_measures": ["Increase monitoring", "Set up alerts"]
        }
        
        c.execute("""
            INSERT INTO incidents 
            (status, anomaly_description, root_cause, remediation_action)
            VALUES (?, ?, ?, ?)
        """, (
            random.choice(["open", "resolved"]),
            json.dumps(anomaly),
            json.dumps(root_cause),
            json.dumps(remediation)
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Generated {count} synthetic incidents")

if __name__ == "__main__":
    generate_incidents(50)
