import requests
import json
from datetime import datetime
from collections import Counter

class KnowledgeBaseAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def extract_article(self, incident_data: dict) -> dict:
        """Extract a knowledge base article from a resolved incident."""
        context = json.dumps(incident_data)
        
        system_prompt = (
            "You are an expert technical writer creating a knowledge base article from a resolved incident. "
            "Return ONLY valid JSON:\n"
            '{\n'
            '  "title": "concise article title",\n'
            '  "category": "Database/Network/Application/Security/Infrastructure/Other",\n'
            '  "tags": ["tag1", "tag2", "tag3"],\n'
            '  "symptoms": "what users observed",\n'
            '  "root_cause": "technical explanation",\n'
            '  "solution": "step-by-step fix",\n'
            '  "prevention": "how to prevent recurrence",\n'
            '  "difficulty": "Beginner/Intermediate/Advanced",\n'
            '  "estimated_time": "e.g., 15 minutes"\n'
            '}'
        )
        
        prompt = f"{system_prompt}\n\nIncident Data:\n{context}"
        
        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=120
            )
            if res.status_code == 200:
                return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            print(f"KB extraction error: {e}")
        
        return {
            "title": f"Incident #{incident_data.get('id', 'Unknown')} Resolution",
            "category": "General",
            "tags": ["incident"],
            "symptoms": incident_data.get("anomaly_description", "N/A"),
            "root_cause": incident_data.get("root_cause", "N/A"),
            "solution": incident_data.get("remediation", "N/A"),
            "prevention": "Monitor and review",
            "difficulty": "Intermediate",
            "estimated_time": "Varies"
        }

    def generate_from_all_resolved(self, incidents: list) -> list:
        """Generate knowledge base articles from all resolved incidents."""
        articles = []
        categories = Counter()
        
        for inc in incidents:
            if inc.get("status") == "resolved":
                article = self.extract_article(inc)
                article["source_incident_id"] = inc.get("id")
                article["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                articles.append(article)
                categories[article.get("category", "General")] += 1
        
        return articles

    def search_articles(self, articles: list, query: str, top_k: int = 5) -> list:
        """Simple keyword search across articles."""
        query_lower = query.lower()
        scored = []
        
        for article in articles:
            score = 0
            text = f"{article.get('title','')} {article.get('symptoms','')} {article.get('root_cause','')} {article.get('solution','')} {' '.join(article.get('tags',[]))}"
            text_lower = text.lower()
            
            # Simple scoring
            for word in query_lower.split():
                score += text_lower.count(word)
            
            if score > 0:
                scored.append((score, article))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored[:top_k]]

    def render_article_html(self, article: dict) -> str:
        """Render a knowledge base article as HTML."""
        difficulty_colors = {"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"}
        diff_color = difficulty_colors.get(article.get("difficulty", "Intermediate"), "#f59e0b")
        
        tags_html = " ".join([f'<span style="background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 8px;border-radius:10px;font-size:0.75em;">{tag}</span>' for tag in article.get("tags", [])])
        
        return f"""
        <div style="background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:16px;margin:8px 0;">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                <h3 style="color:#f8fafc;margin:0;">📄 {article.get('title', 'Untitled')}</h3>
                <span style="color:{diff_color};background:{diff_color}15;padding:3px 10px;border-radius:12px;font-size:0.75em;font-weight:600;">{article.get('difficulty', 'N/A')}</span>
            </div>
            <div style="margin:8px 0;">{tags_html}</div>
            <div style="color:#94a3b8;font-size:0.85em;margin:4px 0;">📂 Category: {article.get('category', 'General')}</div>
            <hr style="border-color:rgba(255,255,255,0.05);">
            <h4 style="color:#ef4444;">🔴 Symptoms</h4>
            <p style="color:#94a3b8;">{article.get('symptoms', 'N/A')}</p>
            <h4 style="color:#f59e0b;">🔍 Root Cause</h4>
            <p style="color:#94a3b8;">{article.get('root_cause', 'N/A')}</p>
            <h4 style="color:#10b981;">✅ Solution</h4>
            <p style="color:#94a3b8;">{article.get('solution', 'N/A')}</p>
            <h4 style="color:#38bdf8;">🛡️ Prevention</h4>
            <p style="color:#94a3b8;">{article.get('prevention', 'N/A')}</p>
            <div style="color:#64748b;font-size:0.75em;margin-top:8px;">⏱️ Est. time: {article.get('estimated_time', 'N/A')} | Source: Incident #{article.get('source_incident_id', '?')}</div>
        </div>
        """