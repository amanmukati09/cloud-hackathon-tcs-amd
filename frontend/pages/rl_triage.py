import gradio as gr
import requests
from utils import BACKEND_URL

def build_rl_tab(session_token):
    comp = {}
    with gr.Column():
        gr.Markdown("### 🧠 RL Incident Triage")
        gr.Markdown("AI agent learns to prioritize incidents using reinforcement learning.")
        
        with gr.Row():
            comp["train_btn"] = gr.Button("🎓 Train RL Agent", variant="primary")
            comp["refresh_btn"] = gr.Button("🔄 Refresh Queue", variant="secondary")
        
        gr.Markdown("---")
        gr.Markdown("#### 📋 Priority Queue (RL-Sorted)")
        comp["queue_output"] = gr.HTML(value="<p style='color:#94a3b8;'>Click Refresh to see RL-prioritized incidents</p>")
        
        with gr.Row():
            comp["stats_output"] = gr.HTML(value="")
    
    return comp

def fetch_queue(token):
    if not token: return "<p style='color:#ef4444;'>Login required</p>"
    try:
        res = requests.get(f"{BACKEND_URL}/rl/priority-queue", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            queue = data.get("queue", [])
            if not queue:
                return "<p style='color:#94a3b8;text-align:center;'>No open incidents</p>"
            html = '<div style="font-size:0.85rem;">'
            for inc in queue[:15]:
                p = inc.get("priority", 1)
                pc = {5: "#ef4444", 4: "#f59e0b", 3: "#3b82f6", 2: "#38bdf8", 1: "#10b981"}.get(p, "#94a3b8")
                html += f'''<div style="display:flex;align-items:center;gap:10px;padding:8px;margin:3px 0;background:rgba(0,0,0,0.2);border-radius:6px;border-left:4px solid {pc};">
                    <span style="font-size:1.2rem;font-weight:800;color:{pc};min-width:30px;">P{p}</span>
                    <div style="flex:1;">
                        <b style="color:#f8fafc;">#{inc['id']}</b>
                        <span style="color:{pc};margin-left:8px;">{inc.get('severity','?')}</span>
                        <br><small style="color:#94a3b8;">{inc.get('description','')[:80]}</small>
                    </div>
                    <span style="color:#64748b;font-size:0.7rem;">{inc.get('confidence',0):.0f}%</span>
                </div>'''
            html += '</div>'
            return html
    except:
        pass
    return "<p style='color:#ef4444;'>Error</p>"
    
def train_agent(token):
    if not token: return "Login required", ""
    try:
        res = requests.post(f"{BACKEND_URL}/rl/train", json={"limit": 200}, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if res.status_code == 200:
            d = res.json()
            html = f"<p style='color:#10b981;'>✅ {d['message']}</p>"
            html += f"<p style='color:#94a3b8;font-size:0.8rem;'>Q-table: {d.get('q_table_size',0)} states</p>"
            if d.get('sample_severities'):
                html += "<p style='color:#64748b;font-size:0.7rem;'>Severities: " + ", ".join(f"{k}:{v}" for k,v in d['sample_severities'].items()) + "</p>"
            if d.get('sample_components'):
                html += "<p style='color:#64748b;font-size:0.7rem;'>Components: " + ", ".join(f"{k}:{v}" for k,v in d['sample_components'].items()) + "</p>"
            return html, ""
        return f"<p style='color:#ef4444;'>Error</p>", ""
    except Exception as e:
        return f"<p style='color:#ef4444;'>{str(e)[:100]}</p>", ""