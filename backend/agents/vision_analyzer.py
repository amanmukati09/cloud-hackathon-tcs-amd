import requests, json, base64, io
from PIL import Image

class VisionAnalyzer:
    def __init__(self, ollama_url="http://localhost:11434", model="llava:7b"):
        self.ollama_url = ollama_url
        self.model = model

    def analyze_image(self, image_bytes: bytes) -> dict:
        image = Image.open(io.BytesIO(image_bytes))
        if image.width > 1024:
            ratio = 1024 / image.width
            new_height = int(image.height * ratio)
            image = image.resize((1024, new_height))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        prompt = (
            "You are an expert SRE analyzing a screenshot from a monitoring system or application. "
            "Describe exactly what you see: any error messages, log entries, dashboards, graphs, or system status. "
            "Then determine if there is an incident, its severity, affected system, and recommended immediate action. "
            "Return ONLY valid JSON:\n"
            '{"description": "detailed visual description", "incident_detected": bool, '
            '"severity": "LOW/MEDIUM/HIGH/CRITICAL", "affected_system": "string", '
            '"recommended_action": "immediate step", "extracted_logs": ["log line 1", "log line 2"]}'
        )

        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "images": [img_b64], "stream": False, "format": "json"},
                timeout=120
            )
            if res.status_code == 200:
                return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            print(f"Vision analysis error: {e}")
        return {"description": "Could not analyze image", "incident_detected": False, "severity": "UNKNOWN",
                "affected_system": "Unknown", "recommended_action": "Manual review", "extracted_logs": []}