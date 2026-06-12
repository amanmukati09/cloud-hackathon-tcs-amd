import requests
import json
import re

class SentimentAnalyzer:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        # Quick keyword-based fallback (no API call needed)
        self.negative_keywords = [
            "urgent", "emergency", "critical", "broken", "crash", "crashed",
            "down", "failed", "failing", "error", "bug", "stuck", "can't",
            "cannot", "won't", "doesn't", "not working", "help", "asap",
            "frustrated", "annoying", "terrible", "awful", "worst"
        ]
        self.positive_keywords = [
            "thanks", "great", "awesome", "fixed", "resolved", "working",
            "perfect", "amazing", "love", "helpful", "excellent", "good"
        ]
    
    def quick_analyze(self, text: str) -> dict:
        """Fast keyword-based sentiment check (no LLM call)."""
        text_lower = text.lower()
        neg_count = sum(1 for word in self.negative_keywords if word in text_lower)
        pos_count = sum(1 for word in self.positive_keywords if word in text_lower)
        
        if neg_count > pos_count:
            score = -min(1.0, neg_count * 0.25)
        elif pos_count > neg_count:
            score = min(1.0, pos_count * 0.25)
        else:
            score = 0.0
        
        return self._format_result(score, neg_count, pos_count)
    
    def deep_analyze(self, text: str) -> dict:
        """LLM-powered sentiment analysis for nuanced understanding."""
        prompt = (
            "Analyze the sentiment of this message. Return ONLY a JSON object:\n"
            '{"sentiment": "POSITIVE/NEGATIVE/NEUTRAL", "score": -1.0 to 1.0, '
            '"urgency": "LOW/MEDIUM/HIGH/CRITICAL", "emotion": "frustrated/angry/anxious/'
            'satisfied/relieved/neutral/confused/grateful", "summary": "one-line explanation"}\n\n'
            f"Message: {text}"
        )
        
        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30
            )
            if res.status_code == 200:
                return json.loads(res.json().get("response", "{}"))
        except:
            pass
        
        return self.quick_analyze(text)
    
    def _format_result(self, score: float, neg: int, pos: int) -> dict:
        """Format sentiment result."""
        if score < -0.3:
            sentiment = "NEGATIVE"
            urgency = "HIGH" if score < -0.6 else "MEDIUM"
        elif score > 0.3:
            sentiment = "POSITIVE"
            urgency = "LOW"
        else:
            sentiment = "NEUTRAL"
            urgency = "LOW"
        
        emotions = {
            "NEGATIVE": "frustrated",
            "POSITIVE": "satisfied",
            "NEUTRAL": "neutral"
        }
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "urgency": urgency,
            "emotion": emotions.get(sentiment, "neutral"),
            "summary": f"Keyword analysis: {neg} negative, {pos} positive indicators",
            "needs_escalation": urgency in ["HIGH", "CRITICAL"]
        }
    
    def analyze_message(self, text: str, use_llm: bool = False) -> dict:
        """Analyze message sentiment (quick or deep)."""
        if use_llm:
            return self.deep_analyze(text)
        return self.quick_analyze(text)
    
    def render_sentiment_html(self, result: dict, message: str = "") -> str:
        """Render sentiment as HTML badge."""
        colors = {
            "NEGATIVE": "#ef4444",
            "POSITIVE": "#10b981",
            "NEUTRAL": "#6b7280"
        }
        emotions_emoji = {
            "frustrated": "😤", "angry": "😡", "anxious": "😰",
            "satisfied": "😊", "relieved": "😌", "neutral": "😐",
            "confused": "😕", "grateful": "🙏"
        }
        
        color = colors.get(result.get("sentiment", "NEUTRAL"), "#6b7280")
        emoji = emotions_emoji.get(result.get("emotion", "neutral"), "😐")
        
        html = f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px;background:rgba(30,41,59,0.6);border-radius:8px;border-left:3px solid {color};">
            <span style="font-size:1.5em;">{emoji}</span>
            <div>
                <span style="color:{color};font-weight:600;">{result.get('sentiment', 'NEUTRAL')}</span>
                <span style="color:#94a3b8;font-size:0.85em;margin-left:8px;">
                    Score: {result.get('score', 0)} | Urgency: {result.get('urgency', 'LOW')}
                </span>
                <br><small style="color:#64748b;">{result.get('summary', '')}</small>
            </div>
            {"<span style='background:#ef4444;color:white;padding:2px 8px;border-radius:10px;font-size:0.75em;'>⚠️ Escalate</span>" if result.get('needs_escalation') else ""}
        </div>
        """
        return html