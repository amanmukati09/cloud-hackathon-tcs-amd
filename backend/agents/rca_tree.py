import requests
import json

class RCATreeAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate_rca_tree(self, anomaly: dict, root_cause: dict, logs: list) -> dict:
        """Generate a structured RCA tree from incident data."""
        context = json.dumps({
            "anomaly": anomaly,
            "root_cause": root_cause,
            "logs": logs[:10]  # Limit log lines
        })
        
        system_prompt = (
            "You are an expert SRE root cause analysis specialist. "
            "Based on the incident data, generate a hierarchical RCA tree. "
            "Return ONLY valid JSON with this exact structure:\n"
            '{\n'
            '  "incident_summary": "one-line summary",\n'
            '  "tree": {\n'
            '    "name": "Root Cause",\n'
            '    "children": [\n'
            '      {"name": "Primary Cause", "detail": "explanation", "children": [\n'
            '        {"name": "Evidence 1", "detail": "specific evidence"},\n'
            '        {"name": "Evidence 2", "detail": "specific evidence"}\n'
            '      ]},\n'
            '      {"name": "Contributing Factor 1", "detail": "explanation"},\n'
            '      {"name": "Contributing Factor 2", "detail": "explanation"}\n'
            '    ]\n'
            '  },\n'
            '  "remediation_path": [\n'
            '    {"step": 1, "action": "immediate action", "expected_effect": "what it fixes"},\n'
            '    {"step": 2, "action": "long-term fix", "expected_effect": "what it prevents"}\n'
            '  ],\n'
            '  "affected_systems": ["system1", "system2"],\n'
            '  "severity_assessment": "LOW/MEDIUM/HIGH/CRITICAL",\n'
            '  "estimated_impact": "description of business impact"\n'
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
            print(f"RCA Tree Error: {e}")
        
        return {
            "incident_summary": "AI analysis unavailable",
            "tree": {"name": "Unknown", "children": []},
            "remediation_path": [],
            "affected_systems": [],
            "severity_assessment": "UNKNOWN",
            "estimated_impact": "Could not determine"
        }

    def render_tree_html(self, tree_data: dict) -> str:
        """Convert RCA tree data to beautiful HTML visualization."""
        html = """
        <style>
            .rca-tree { font-family: 'Inter', sans-serif; padding: 10px; }
            .rca-node { 
                background: rgba(30,41,59,0.8); border:1px solid rgba(255,255,255,0.1);
                border-radius:8px; padding:10px; margin:4px 0; 
            }
            .rca-node.root { border-left:3px solid #ef4444; }
            .rca-node.cause { border-left:3px solid #f59e0b; margin-left:20px; }
            .rca-node.evidence { border-left:3px solid #38bdf8; margin-left:40px; font-size:0.9em; }
            .rca-step { 
                background: rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3);
                border-radius:6px; padding:8px; margin:4px 0; 
            }
            .rca-badge {
                display:inline-block; padding:2px 8px; border-radius:12px;
                font-size:0.75em; font-weight:bold; margin-right:6px;
            }
            .severity-CRITICAL { background:#ef4444; color:white; }
            .severity-HIGH { background:#f59e0b; color:black; }
            .severity-MEDIUM { background:#3b82f6; color:white; }
            .severity-LOW { background:#10b981; color:white; }
        </style>
        <div class="rca-tree">
        """
        
        # Header
        sev = tree_data.get("severity_assessment", "UNKNOWN").upper()
        html += f"""
            <h3>🌳 Root Cause Analysis Tree</h3>
            <p><span class="rca-badge severity-{sev}">{sev}</span> {tree_data.get('incident_summary', '')}</p>
            <p><strong>Impact:</strong> {tree_data.get('estimated_impact', 'N/A')}</p>
        """
        
        # Tree
        tree = tree_data.get("tree", {})
        if tree:
            html += f'<div class="rca-node root"><strong>🔴 Root: {tree.get("name", "Unknown")}</strong></div>'
            for child in tree.get("children", []):
                html += f'<div class="rca-node cause"><strong>🟡 {child.get("name", "")}</strong>'
                if child.get("detail"):
                    html += f'<br><small>{child["detail"]}</small>'
                html += '</div>'
                for evidence in child.get("children", []):
                    html += f'<div class="rca-node evidence"><strong>🔵 {evidence.get("name", "")}</strong>'
                    if evidence.get("detail"):
                        html += f'<br><small>{evidence["detail"]}</small>'
                    html += '</div>'
        
        # Remediation path
        html += '<h4>🔧 Remediation Path</h4>'
        for step in tree_data.get("remediation_path", []):
            html += f"""
                <div class="rca-step">
                    <strong>Step {step.get('step', '?')}:</strong> {step.get('action', '')}
                    <br><small>➜ {step.get('expected_effect', '')}</small>
                </div>
            """
        
        # Affected systems
        systems = tree_data.get("affected_systems", [])
        if systems:
            html += f'<p><strong>🖥️ Affected Systems:</strong> {", ".join(systems)}</p>'
        
        html += '</div>'
        return html