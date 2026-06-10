import json

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass

    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        severity = anomaly.get("severity", "LOW")
        
        if severity == "CRITICAL":
            return {
                "root_cause": "Critical system failure requiring immediate database/network attention.",
                "confidence": 0.95,
                "evidence": ["Timeout/Critical flag in logs", "System health check failed"],
                "contributing_factors": ["System overload", "Resource exhaustion"]
            }
        elif severity == "HIGH":
            return {
                "root_cause": "Worker process encountered a fatal error during execution.",
                "confidence": 0.92,
                "evidence": ["Error logs detected", "Process termination signals"],
                "contributing_factors": ["Memory leak", "Invalid configuration"]
            }
        else:
            return {
                "root_cause": "System is experiencing unusual load or warnings.",
                "confidence": 0.85,
                "evidence": ["Warning flags in telemetry"],
                "contributing_factors": ["High traffic spike"]
            }

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()