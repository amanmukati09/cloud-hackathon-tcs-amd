import requests
import json

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        context_str = json.dumps({"anomaly": anomaly, "root_cause": root_cause})
        
        system_prompt = (
            "You are an expert SRE remediation agent. Based on the anomaly and root cause provided, "
            "generate an incident response plan. Return ONLY a valid JSON object matching this exact structure: "
            '{"immediate_actions": ["string list"], "automated_actions": [{"action": "string", "risk_level": "LOW/MEDIUM/HIGH"}], "escalation_needed": boolean, "estimated_recovery_time": "string", "prevention_measures": ["string list"]}'
        )
        
        prompt = f"{system_prompt}\n\nIncident Context:\n{context_str}"
        
        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=120
            )
            if res.status_code == 200:
                response_text = res.json().get("response", "{}")
                return json.loads(response_text)
        except Exception as e:
            print(f"Remediation AI Error: {e}")
            
        return {
            "immediate_actions": ["Manual intervention required."],
            "automated_actions": [],
            "escalation_needed": True,
            "estimated_recovery_time": "Unknown",
            "prevention_measures": ["Investigate AI pipeline failure."]
        }

if __name__ == "__main__":
    remediation = RemediationAgent()