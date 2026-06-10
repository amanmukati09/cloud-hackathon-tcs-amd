import requests
import json

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
    
    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        """Suggest remediation actions"""
        
        prompt = f"""Respond ONLY as valid JSON. No other text.

{{
  "immediate_actions": ["action 1", "action 2"],
  "automated_actions": [{{"action": "restart service", "risk_level": "MEDIUM"}}],
  "escalation_needed": false,
  "estimated_recovery_time": "5 minutes",
  "prevention_measures": ["measure 1", "measure 2"]
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
                return json.loads(text)
            except:
                return {
                    "immediate_actions": [],
                    "automated_actions": [],
                    "escalation_needed": True,
                    "estimated_recovery_time": "Unknown",
                    "prevention_measures": []
                }
        return {
            "immediate_actions": [],
            "automated_actions": [],
            "escalation_needed": True,
            "estimated_recovery_time": "Unknown",
            "prevention_measures": []
        }

if __name__ == "__main__":
    remediation = RemediationAgent()
    
    anomaly = {"anomaly_type": "memory_high", "severity": "CRITICAL"}
    root_cause = {"root_cause": "memory leak", "confidence": 0.95}
    
    result = remediation.suggest_remediation(anomaly, root_cause)
    print("✅ Remediation Agent Result:")
    print(json.dumps(result, indent=2))
