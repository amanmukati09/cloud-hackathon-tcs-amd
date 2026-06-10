import requests
import json

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        log_text = "\n".join(logs)
        anomaly_str = json.dumps(anomaly)
        
        system_prompt = (
            "You are an expert SRE diagnostic agent. Based on the logs and the detected anomaly, identify the root cause. "
            "Return ONLY a valid JSON object matching this exact structure: "
            '{"root_cause": "detailed string", "confidence": float (0.0 to 1.0), "evidence": ["string list"], "contributing_factors": ["string list"]}'
        )
        
        prompt = f"{system_prompt}\n\nLogs:\n{log_text}\n\nAnomaly Context:\n{anomaly_str}"
        
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
            print(f"Diagnosis AI Error: {e}")
            
        return {
            "root_cause": "AI Diagnosis failed to process log context.",
            "confidence": 0.0,
            "evidence": ["System timeout"],
            "contributing_factors": ["Incomplete AI generation"]
        }

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()