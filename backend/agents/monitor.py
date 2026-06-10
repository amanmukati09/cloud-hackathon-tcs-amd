import requests
import json
from typing import Optional

class MonitorAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
    
    def detect_anomaly(self, logs: list[str]) -> Optional[dict]:
        """Detect anomalies in logs"""
        logs_text = "\n".join(logs)
        
        prompt = f"""Analyze these logs for anomalies. Respond ONLY as JSON.

LOGS:
{logs_text}

JSON Response (no other text):
{{"anomaly_detected": boolean, "anomaly_type": "string", "severity": "CRITICAL/HIGH/MEDIUM/LOW", "affected_component": "string", "description": "string"}}"""
        
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        
        if response.status_code == 200:
            try:
                text = response.json()["response"].strip()
                return json.loads(text)
            except:
                return {"anomaly_detected": False}
        return {"anomaly_detected": False}

if __name__ == "__main__":
    monitor = MonitorAgent()
    
    test_logs = [
        "[INFO] nginx started",
        "[WARNING] memory: 90%",
        "[ERROR] worker crashed",
        "[ERROR] cpu: 95%"
    ]
    
    result = monitor.detect_anomaly(test_logs)
    print("✅ Monitor Agent Result:")
    print(json.dumps(result, indent=2))
