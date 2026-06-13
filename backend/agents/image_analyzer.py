import pytesseract
from PIL import Image
import io
import requests
import json

class ImageAnalyzer:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""

    def analyze_image_for_incidents(self, image_bytes: bytes) -> dict:
        """Analyze an image for potential incidents."""
        # Step 1: Extract text via OCR
        extracted_text = self.extract_text_from_image(image_bytes)
        if not extracted_text:
            return {
                "text_found": False,
                "analysis": "No text could be extracted from the image.",
                "severity": "UNKNOWN"
            }

        # Step 2: Send extracted text to LLM for analysis
        prompt = (
            "You are an SRE analyzing a screenshot from a monitoring system. "
            "Based on the extracted text, determine if there's an incident. "
            "Return ONLY valid JSON:\n"
            '{"incident_detected": bool, "summary": "brief description", '
            '"severity": "LOW/MEDIUM/HIGH/CRITICAL", "affected_system": "string", '
            '"recommended_action": "immediate step to take"}\n\n'
            f"Extracted text from image:\n{extracted_text[:2000]}"
        )

        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=60
            )
            if res.status_code == 200:
                result = json.loads(res.json().get("response", "{}"))
                result["text_found"] = True
                result["extracted_text"] = extracted_text[:500]
                return result
        except Exception as e:
            print(f"Image analysis error: {e}")

        return {
            "text_found": True,
            "extracted_text": extracted_text[:500],
            "incident_detected": False,
            "summary": "AI analysis unavailable",
            "severity": "UNKNOWN",
            "affected_system": "Unknown",
            "recommended_action": "Manual review required"
        }