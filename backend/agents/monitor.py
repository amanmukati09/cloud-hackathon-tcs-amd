import json
import re

class MonitorAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass

    def detect_anomaly(self, logs: list[str]) -> dict:
        log_text = " ".join(logs).lower()
        
        if "critical" in log_text or "timeout" in log_text:
            return {
                "anomaly_detected": True,
                "anomaly_type": "critical_event",
                "severity": "CRITICAL",
                "affected_component": "system",
                "description": "Critical failure or timeout detected in logs."
            }
        elif "error" in log_text or "crash" in log_text:
            return {
                "anomaly_detected": True,
                "anomaly_type": "error_event",
                "severity": "HIGH",
                "affected_component": "nginx/server",
                "description": "Error event or worker crash detected."
            }
        elif "warning" in log_text or "spike" in log_text:
            return {
                "anomaly_detected": True,
                "anomaly_type": "warning",
                "severity": "MEDIUM",
                "affected_component": "resources",
                "description": "Resource warning or spike detected."
            }
            
        return {"anomaly_detected": False}

if __name__ == "__main__":
    monitor = MonitorAgent()
    print(monitor.detect_anomaly(["[ERROR] nginx worker crashed"]))