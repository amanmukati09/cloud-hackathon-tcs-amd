import requests
import json
from datetime import datetime

class RunbookGenerator:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate_runbook(self, incident_data: dict) -> dict:
        """Generate a runbook from incident data."""
        context = json.dumps(incident_data)
        
        system_prompt = (
            "You are an expert SRE creating runbooks for incident response. "
            "Based on the incident data, generate a detailed runbook. "
            "Return ONLY valid JSON with this exact structure:\n"
            '{\n'
            '  "title": "runbook title",\n'
            '  "severity": "LOW/MEDIUM/HIGH/CRITICAL",\n'
            '  "category": "e.g. Database, Network, Application",\n'
            '  "estimated_duration": "e.g. 15 minutes",\n'
            '  "prerequisites": ["list of prerequisites"],\n'
            '  "steps": [\n'
            '    {\n'
            '      "step": 1,\n'
            '      "phase": "Detection/Diagnosis/Remediation/Verification",\n'
            '      "action": "what to do",\n'
            '      "command": "exact command to run (optional)",\n'
            '      "expected_result": "what should happen",\n'
            '      "on_failure": "what to do if this step fails",\n'
            '      "duration": "e.g. 2 minutes"\n'
            '    }\n'
            '  ],\n'
            '  "rollback_steps": ["steps to undo changes"],\n'
            '  "validation_checks": ["how to verify issue is resolved"],\n'
            '  "lessons_learned": "summary of what we learned",\n'
            '  "last_updated": "date"\n'
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
                data = json.loads(res.json().get("response", "{}"))
                data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                return data
        except Exception as e:
            print(f"Runbook generator error: {e}")
        
        return {
            "title": incident_data.get("anomaly_type", "Unknown") + " Runbook",
            "severity": incident_data.get("severity", "MEDIUM"),
            "category": "General",
            "estimated_duration": "Unknown",
            "prerequisites": ["Access to affected system"],
            "steps": [{
                "step": 1,
                "phase": "Diagnosis",
                "action": "Review incident details manually",
                "command": "",
                "expected_result": "Understanding of the issue",
                "on_failure": "Escalate to senior engineer",
                "duration": "Variable"
            }],
            "rollback_steps": [],
            "validation_checks": ["Verify system is operational"],
            "lessons_learned": "AI runbook generation unavailable",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def render_runbook_html(self, runbook: dict) -> str:
        """Render runbook as beautiful HTML."""
        phase_colors = {
            "Detection": "#3b82f6",
            "Diagnosis": "#f59e0b",
            "Remediation": "#10b981",
            "Verification": "#8b5cf6"
        }
        severity_colors = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f59e0b",
            "MEDIUM": "#3b82f6",
            "LOW": "#10b981"
        }
        
        sev_color = severity_colors.get(runbook.get("severity", "MEDIUM"), "#3b82f6")
        
        html = f"""
        <style>
            .runbook-card {{
                background: rgba(30,41,59,0.8);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 16px;
                margin: 10px 0;
            }}
            .runbook-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                padding-bottom: 12px;
            }}
            .runbook-title {{
                font-size: 1.2em;
                font-weight: 700;
                color: #f8fafc;
            }}
            .runbook-meta {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin: 6px 0;
            }}
            .runbook-badge {{
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.75em;
                font-weight: 600;
            }}
            .runbook-step {{
                background: rgba(0,0,0,0.2);
                border-left: 3px solid {sev_color};
                border-radius: 6px;
                padding: 10px 14px;
                margin: 8px 0;
            }}
            .step-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 6px;
            }}
            .step-number {{
                background: {sev_color};
                color: white;
                width: 26px;
                height: 26px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 0.85em;
                flex-shrink: 0;
            }}
            .step-phase {{
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.7em;
                font-weight: 600;
                color: white;
            }}
            .step-command {{
                background: #0d1117;
                color: #e6edf3;
                padding: 10px 14px;
                border-radius: 6px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 0.82em;
                margin: 6px 0;
                white-space: pre-wrap;
                border: 1px solid rgba(255,255,255,0.05);
            }}
            .step-on-failure {{
                color: #f59e0b;
                font-size: 0.8em;
                margin-top: 4px;
                padding-left: 12px;
                border-left: 2px solid #f59e0b;
            }}
            .prereq-list, .rollback-list, .verify-list {{
                list-style: none;
                padding-left: 0;
            }}
            .prereq-list li, .rollback-list li, .verify-list li {{
                padding: 4px 0;
                color: #94a3b8;
                font-size: 0.85em;
            }}
            .prereq-list li:before {{
                content: "📋 ";
            }}
            .rollback-list li:before {{
                content: "🔄 ";
            }}
            .verify-list li:before {{
                content: "✅ ";
            }}
        </style>
        <div>
            <div class="runbook-card">
                <div class="runbook-header">
                    <div>
                        <div class="runbook-title">📋 {runbook.get('title', 'Untitled Runbook')}</div>
                        <div class="runbook-meta">
                            <span class="runbook-badge" style="background:{sev_color}20;color:{sev_color};">{runbook.get('severity', 'MEDIUM')}</span>
                            <span class="runbook-badge" style="background:rgba(56,189,248,0.15);color:#38bdf8;">{runbook.get('category', 'General')}</span>
                            <span class="runbook-badge" style="background:rgba(139,92,246,0.15);color:#8b5cf6;">⏱️ {runbook.get('estimated_duration', 'N/A')}</span>
                        </div>
                    </div>
                </div>
                
                <h4>📋 Prerequisites</h4>
                <ul class="prereq-list">
        """
        
        for prereq in runbook.get("prerequisites", []):
            html += f"<li>{prereq}</li>"
        
        html += """
                </ul>
                
                <h4>🔧 Recovery Steps</h4>
        """
        
        for step in runbook.get("steps", []):
            phase_color = phase_colors.get(step.get("phase", "Diagnosis"), "#3b82f6")
            html += f"""
                <div class="runbook-step">
                    <div class="step-header">
                        <span class="step-number">{step.get('step', '?')}</span>
                        <span class="step-phase" style="background:{phase_color};">{step.get('phase', 'Step')}</span>
                        <span style="color:#64748b;font-size:0.75em;">⏱️ {step.get('duration', 'N/A')}</span>
                    </div>
                    <div style="color:#e2e8f0;margin:4px 0;">{step.get('action', '')}</div>
                    <div style="color:#94a3b8;font-size:0.85em;">Expected: {step.get('expected_result', 'N/A')}</div>
            """
            if step.get("command"):
                html += f'<div class="step-command"><code>{step["command"]}</code></div>'
            if step.get("on_failure"):
                html += f'<div class="step-on-failure">⚠️ If fails: {step["on_failure"]}</div>'
            html += "</div>"
        
        html += """
                <h4>🔄 Rollback Steps</h4>
                <ul class="rollback-list">
        """
        for rollback in runbook.get("rollback_steps", []):
            html += f"<li>{rollback}</li>"
        
        html += """
                </ul>
                
                <h4>✅ Validation Checks</h4>
                <ul class="verify-list">
        """
        for check in runbook.get("validation_checks", []):
            html += f"<li>{check}</li>"
        
        html += f"""
                </ul>
                
                <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.08);color:#64748b;font-size:0.8em;">
                    📝 Lessons Learned: {runbook.get('lessons_learned', 'N/A')}<br>
                    🕐 Last Updated: {runbook.get('last_updated', 'N/A')}
                </div>
            </div>
        </div>
        """
        return html