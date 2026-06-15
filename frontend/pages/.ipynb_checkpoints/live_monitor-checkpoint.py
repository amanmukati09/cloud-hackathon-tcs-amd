"""
Live Monitor Page - Production-grade minimal SRE dashboard.
"""

import gradio as gr
import requests
from utils import BACKEND_URL


def build_live_monitor_tab(session_token):
    comp = {}
    
    with gr.Column():
        gr.Markdown("### 🛰️ Live Site Monitor")
        gr.Markdown("Real-time log monitoring with AI-powered incident detection.")

        with gr.Row():
            comp["source_selector"] = gr.Dropdown(label="Source", choices=["default"], value="default", scale=3)
            comp["start_btn"] = gr.Button("▶️ Start", variant="primary", scale=1)
            comp["stop_btn"] = gr.Button("⏹️ Stop", variant="stop", scale=1)
            comp["refresh_btn"] = gr.Button("🔄 Refresh", variant="secondary", scale=1)
            comp["status_badge"] = gr.HTML('<span class="badge inactive">● Stopped</span>', scale=1)

        gr.Markdown("---")

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                gr.Markdown("#### 📜 Live Log Stream")
                comp["log_stream"] = gr.HTML(
                    '<div class="log-stream"><span style="color:#64748b;">Click Start to begin monitoring...</span></div>',
                    elem_classes="live-log"
                )
            with gr.Column(scale=1):
                gr.Markdown("#### 🚨 Active Incidents")
                comp["incidents_html"] = gr.HTML(
                    '<div style="color:#94a3b8;text-align:center;padding:10px;">No active incidents</div>'
                )
                gr.Markdown("#### 📊 Metrics")
                comp["metric_lines"] = gr.Markdown(
                    value='<div class="stat-card-inner" style="border-left:3px solid #38bdf8;"><div class="stat-icon">📝</div><div class="stat-value" style="color:#38bdf8;">0</div><div class="stat-label">Lines</div></div>'
                )
                comp["metric_anomalies"] = gr.Markdown(
                    value='<div class="stat-card-inner" style="border-left:3px solid #ef4444;"><div class="stat-icon">🔴</div><div class="stat-value" style="color:#ef4444;">0</div><div class="stat-label">Anomalies</div></div>'
                )
                comp["metric_last"] = gr.Markdown("Last: --:--:--")

        gr.Markdown("---")

        gr.Markdown("#### 💬 AI Live Chat")
        comp["chatbot"] = gr.Chatbot(label="Ask about the live stream", height=250)
        with gr.Row():
            comp["chat_input"] = gr.Textbox(placeholder="What's happening right now?", show_label=False, scale=4)
            comp["chat_send"] = gr.Button("Send", variant="primary", scale=1)

    return comp


def refresh_dashboard(token, source):
    if not token:
        return [gr.update()] * 7
    
    try:
        src_res = requests.get(f"{BACKEND_URL}/live/sources", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        source_choices = ["default"]
        if src_res.status_code == 200:
            source_choices = [s["name"] for s in src_res.json().get("sources", [])]

        res = requests.get(f"{BACKEND_URL}/live/state?source={source}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            logs = data.get("log_buffer", [])
            log_html = '<div class="log-stream">'
            if logs:
                for line in logs[-50:]:
                    c = "#ef4444" if "ERROR" in line or "CRITICAL" in line else "#f59e0b" if "WARNING" in line else "#38bdf8" if "INFO" in line else "#e2e8f0"
                    log_html += f'<span style="color:{c};">{line}</span><br/>'
            else:
                log_html += '<span style="color:#64748b;">No logs yet. Click Start to begin monitoring.</span>'
            log_html += '</div>'

            incidents = data.get("active_incidents", [])
            if incidents:
                inc_html = '<div style="max-height:250px;overflow-y:auto;">'
                for i in incidents[:8]:
                    sev = i.get("severity", "MEDIUM")
                    sc = {"CRITICAL": "#ef4444", "HIGH": "#f59e0b"}.get(sev, "#94a3b8")
                    inc_html += f'''<div style="border-left:3px solid {sc};padding:6px 8px;margin:3px 0;background:rgba(0,0,0,0.2);border-radius:4px;font-size:0.8rem;">
                        <span style="color:{sc};font-weight:700;">[{sev}]</span> <b>#{i.get('id','?')}</b> {i.get('type','')}<br>
                        <span style="color:#94a3b8;">{i.get('timestamp','')} | {i.get('component','')}</span></div>'''
                inc_html += '</div>'
            else:
                inc_html = '<div style="color:#94a3b8;text-align:center;padding:10px;font-size:0.85rem;">No active incidents</div>'

            m = data.get("metrics", {})
            running = data.get("running", False)
            badge = '<span class="badge active">● Live</span>' if running else '<span class="badge inactive">● Stopped</span>'

            return (
                gr.update(choices=source_choices, value=source),
                log_html,
                inc_html,
                f'<div class="stat-card-inner" style="border-left:3px solid #38bdf8;"><div class="stat-icon">📝</div><div class="stat-value" style="color:#38bdf8;">{m.get("lines_processed",0):,}</div><div class="stat-label">Lines</div></div>',
                f'<div class="stat-card-inner" style="border-left:3px solid #ef4444;"><div class="stat-icon">🔴</div><div class="stat-value" style="color:#ef4444;">{m.get("anomalies_found",0)}</div><div class="stat-label">Anomalies</div></div>',
                f"Last: {m.get('last_analysis','--:--:--')}",
                badge
            )
    except Exception as e:
        print(f"Refresh error: {e}")

    return [gr.update()] * 7


def send_chat(message, history, token, source):
    if not message or not message.strip() or not token:
        return history, ""
    history = history or []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "⏳"})
    try:
        res = requests.post(f"{BACKEND_URL}/live/chat?source={source}", json={"message": message.strip()}, headers={"Authorization": f"Bearer {token}"}, timeout=20)
        history[-1]["content"] = res.json().get("reply", "") if res.status_code == 200 else "AI unavailable"
    except Exception as e:
        history[-1]["content"] = f"❌ {e}"
    return history, ""