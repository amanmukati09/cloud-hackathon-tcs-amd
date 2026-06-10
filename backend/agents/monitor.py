import requests
import json

class MonitorAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def detect_anomaly(self, logs: list[str]) -> dict:
        log_text = "\n".join(logs)
        
        system_prompt = (
            "You are an expert SRE monitoring agent. Analyze the following logs. "
            "Determine if there is an anomaly. Return ONLY a valid JSON object matching this exact structure: "
            '{"anomaly_detected": boolean, "anomaly_type": "string", "severity": "LOW/MEDIUM/HIGH/CRITICAL", "affected_component": "string", "description": "string"}'
        )
        
        prompt = f"{system_prompt}\n\nLogs:\n{log_text}"
        
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
            print(f"Monitor AI Error: {e}")
            
        # Fallback if AI fails to respond cleanly
        return {
            "anomaly_detected": True,
            "anomaly_type": "Unknown",
            "severity": "HIGH",
            "affected_component": "Unknown",
            "description": "AI analysis timed out or failed to parse. Manual inspection required."
        }

if __name__ == "__main__":
    monitor = MonitorAgent()
    print(monitor.detect_anomaly(["[ERROR] nginx worker crashed"]))