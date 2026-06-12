import requests
import json

class CodeFixerAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate_fix(self, anomaly: dict, root_cause: dict, logs: list, language: str = "auto") -> dict:
        """Generate code fixes based on incident analysis."""
        context = json.dumps({
            "anomaly": anomaly,
            "root_cause": root_cause,
            "logs": logs[:10]
        })
        
        system_prompt = (
            "You are an expert SRE and software engineer. Based on the incident data, "
            "generate code fixes, configuration changes, and scripts to resolve the issue. "
            "Return ONLY valid JSON with this exact structure:\n"
            '{\n'
            '  "summary": "one-line summary of the fix",\n'
            '  "language": "python/bash/nginx/sql/yaml/etc",\n'
            '  "fixes": [\n'
            '    {\n'
            '      "title": "descriptive title",\n'
            '      "description": "what this fix does",\n'
            '      "code": "the actual code/script/config",\n'
            '      "language": "python/bash/etc",\n'
            '      "type": "immediate/long-term/prevention",\n'
            '      "risk": "LOW/MEDIUM/HIGH",\n'
            '      "rollback": "how to undo this change"\n'
            '    }\n'
            '  ],\n'
            '  "verification_steps": ["step to verify fix works"],\n'
            '  "estimated_implementation_time": "e.g. 15 minutes"\n'
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
            print(f"Code fixer error: {e}")
        
        return {
            "summary": "AI code generation unavailable",
            "language": "text",
            "fixes": [{
                "title": "Manual Review Required",
                "description": "AI could not generate code. Please review logs manually.",
                "code": "# Manual intervention required\n# Review the logs and root cause analysis",
                "language": "text",
                "type": "immediate",
                "risk": "LOW",
                "rollback": "N/A"
            }],
            "verification_steps": ["Review incident manually"],
            "estimated_implementation_time": "Unknown"
        }

    def render_fixes_html(self, fix_data: dict) -> str:
        """Render code fixes as beautiful HTML with syntax highlighting."""
        risk_colors = {"LOW": "#10b981", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}
        type_badges = {
            "immediate": "⚡ Immediate Fix",
            "long-term": "🔧 Long-term Fix",
            "prevention": "🛡️ Prevention"
        }
        
        html = """
        <style>
            .code-fix-card {
                background: rgba(30,41,59,0.8);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 14px;
                margin: 10px 0;
            }
            .code-fix-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            .code-fix-title {
                font-weight: 600;
                color: #f8fafc;
                font-size: 1em;
            }
            .code-fix-badge {
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.75em;
                font-weight: 600;
            }
            .code-block {
                background: #0d1117;
                color: #e6edf3;
                padding: 14px;
                border-radius: 8px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 0.85em;
                overflow-x: auto;
                white-space: pre-wrap;
                line-height: 1.5;
                margin: 8px 0;
                border: 1px solid rgba(255,255,255,0.05);
            }
            .code-lang {
                color: #58a6ff;
                font-size: 0.75em;
                margin-bottom: 4px;
            }
            .fix-description {
                color: #94a3b8;
                font-size: 0.85em;
                margin: 6px 0;
            }
            .rollback-info {
                color: #64748b;
                font-size: 0.8em;
                margin-top: 6px;
                padding: 6px 10px;
                background: rgba(0,0,0,0.2);
                border-radius: 6px;
                border-left: 2px solid #f59e0b;
            }
            .verify-step {
                color: #10b981;
                font-size: 0.85em;
                margin: 3px 0;
                padding-left: 16px;
            }
        </style>
        <div>
        """
        
        html += f"""
            <h3>🔧 Generated Code Fixes</h3>
            <p style="color:#94a3b8;margin-bottom:12px;">{fix_data.get('summary', '')}</p>
            <p style="color:#64748b;font-size:0.8em;">⏱️ Est. implementation: {fix_data.get('estimated_implementation_time', 'N/A')}</p>
        """
        
        for fix in fix_data.get("fixes", []):
            risk_color = risk_colors.get(fix.get("risk", "LOW"), "#10b981")
            type_label = type_badges.get(fix.get("type", "immediate"), "⚡ Immediate Fix")
            
            html += f"""
            <div class="code-fix-card">
                <div class="code-fix-header">
                    <span class="code-fix-title">{fix.get('title', 'Untitled Fix')}</span>
                    <span>
                        <span class="code-fix-badge" style="background:{risk_color}20;color:{risk_color};margin-right:4px;">
                            Risk: {fix.get('risk', 'LOW')}
                        </span>
                        <span class="code-fix-badge" style="background:rgba(56,189,248,0.15);color:#38bdf8;">
                            {type_label}
                        </span>
                    </span>
                </div>
                <div class="fix-description">{fix.get('description', '')}</div>
                <div class="code-lang">📄 {fix.get('language', 'text').upper()}</div>
                <div class="code-block"><code>{fix.get('code', '# No code generated')}</code></div>
                <div class="rollback-info">🔄 <strong>Rollback:</strong> {fix.get('rollback', 'N/A')}</div>
            </div>
            """
        
        html += '<h4 style="margin-top:16px;">✅ Verification Steps</h4>'
        for step in fix_data.get("verification_steps", []):
            html += f'<div class="verify-step">✓ {step}</div>'
        
        html += "</div>"
        return html