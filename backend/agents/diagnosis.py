import requests
import json
from typing import Optional

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
    
    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        """Analyze root cause of anomaly"""
        logs_text = "\n".join(logs[-15:])
        
        prompt = f"""Respond ONLY as valid JSON. No other text.

{{
  "root_cause": "brief explanation",
  "confidence": 0.95,
  "evidence": ["log line 1", "log line 2"],
  "contributing_factors": ["factor 1", "factor 2"]
}}"""
        
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
                print(f"DEBUG - Raw response: {text[:200]}")  # Print first 200 chars
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON parse error: {e}")
                return {
                    "root_cause": "Unable to parse response",
                    "confidence": 0.0,
                    "evidence": [],
                    "contributing_factors": []
                }
            except Exception as e:
                print(f"DEBUG - Error: {e}")
                return {
                    "root_cause": "Error",
                    "confidence": 0.0,
                    "evidence": [],
                    "contributing_factors": []
                }
        return {
            "root_cause": "Unable to determine",
            "confidence": 0.0,
            "evidence": [],
            "contributing_factors": []
        }

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()
    
    test_logs = [
        "[INFO] nginx started",
        "[WARNING] memory 85%",
        "[ERROR] worker crashed",
    ]
    
    anomaly = {
        "anomaly_type": "memory_high",
        "severity": "CRITICAL"
    }
    
    result = diagnosis.analyze_root_cause(anomaly, test_logs)
    print("✅ Result:")
    print(json.dumps(result, indent=2))
