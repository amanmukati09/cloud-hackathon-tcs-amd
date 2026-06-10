import gradio as gr
import requests
import pandas as pd
from datetime import datetime
import re

BACKEND_URL = "http://localhost:8000"

custom_css = """
body, .gradio-container { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', system-ui, sans-serif !important; }
footer { display: none !important; }
.nav-container { display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: space-between !important; background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; padding: 10px 25px !important; margin-bottom: 15px !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important; border-radius: 8px !important; }
.nav-logo h1 { margin: 0 !important; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900 !important; font-size: 1.6rem !important; letter-spacing: 1px; }
button.profile-btn { background: transparent !important; border: 1px solid #38bdf8 !important; color: #38bdf8 !important; border-radius: 20px !important; padding: 4px 16px !important; font-weight: 600 !important; font-size: 0.9rem !important; transition: all 0.2s !important; max-width: 140px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; display: inline-block !important; }
.profile-dropdown { position: absolute !important; right: 30px !important; top: 75px !important; z-index: 9999 !important; background: #1e293b !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; padding: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important; width: 260px !important; }
.profile-text { color: #94a3b8 !important; font-size: 0.9rem !important; line-height: 1.6 !important; word-wrap: break-word !important; }
button.logout-btn { background: rgba(239, 68, 68, 0.1) !important; border: 1px solid #ef4444 !important; color: #ef4444 !important; border-radius: 6px !important; padding: 6px 16px !important; margin-top: 15px !important; }
.card-row { align-items: stretch !important; }
.result-card { display: flex !important; flex-direction: column !important; height: 100% !important; min-height: 380px !important; border-radius: 8px !important; padding: 20px !important; background: rgba(30, 41, 59, 0.5) !important; }
.anomaly-card { border-top: 4px solid #ef4444 !important; }
.rc-card { border-top: 4px solid #f59e0b !important; }
.remed-card { border-top: 4px solid #10b981 !important; }
.table-wrap { max-height: 500px !important; overflow-y: auto !important; }
.show-pass-check { margin-top: -10px !important; margin-bottom: 10px !important; }
"""

def is_valid_email(email): 
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)

def get_chat_sessions(token):
    if not token: return []
    try:
        res = requests.get(f"{BACKEND_URL}/chat/sessions", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            return [title for session_id, title in res.json().items()]
    except: pass
    return []

def load_chat_session(session_str, token):
    if not session_str or not token: return [], None
    try:
        session_id = session_str.split("ID: ")[1].split(" |")[0]
        res = requests.get(f"{BACKEND_URL}/chat/sessions/{session_id}", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            formatted_history = []
            for user_msg, ai_msg in res.json():
                if user_msg: formatted_history.append({"role": "user", "content": user_msg})
                if ai_msg: formatted_history.append({"role": "assistant", "content": ai_msg})
            return formatted_history, session_id
    except: pass
    return [], None

def send_chat_msg(message, session_id, history, token):
    if not message.strip(): 
        yield "", history, session_id, gr.update()
        return
    if history is None: history = []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "⏳ Thinking..."})
    yield "", history, session_id, gr.update()
    try:
        payload = {"message": message, "session_id": int(session_id) if session_id else None}
        res = requests.post(f"{BACKEND_URL}/chat/message", json=payload, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            new_session_id = str(data.get("session_id"))
            formatted_history = []
            for u_msg, a_msg in data.get("history", []):
                if u_msg: formatted_history.append({"role": "user", "content": u_msg})
                if a_msg: formatted_history.append({"role": "assistant", "content": a_msg})
            choices = get_chat_sessions(token)
            selected_choice = next((c for c in choices if f"ID: {new_session_id} |" in c), None)
            yield "", formatted_history, new_session_id, gr.update(choices=choices, value=selected_choice)
        else:
            history[-1]["content"] = f"❌ Error: {res.text}"
            yield message, history, session_id, gr.update()
    except Exception as e:
        history[-1]["content"] = f"❌ Connection Error: {str(e)}"
        yield message, history, session_id, gr.update()

def api_login(email, password):
    if not email.strip() or not password.strip() or not is_valid_email(email):
        gr.Warning("⚠️ Invalid parameters.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False), gr.update()
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = email.split('@')[0].capitalize()
            disp = (raw_name[:10] + '..') if len(raw_name) > 10 else raw_name
            html = f"<div class='profile-text'><b>User:</b> {raw_name}<br><b>Email:</b> {email}</div>"
            gr.Info(f"✅ Welcome back, {disp}!")
            return token, gr.update(visible=False), gr.update(visible=True), gr.update(value=f"👤 {disp}"), gr.update(value=html), False, gr.update(visible=False), gr.update(choices=get_chat_sessions(token))
        else:
            # FIX: Reveal exact error if login is rejected!
            gr.Warning(f"❌ Login Denied: {res.json().get('detail', 'Unknown Error')}")
    except Exception as e: 
        gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False), gr.update()

def api_register(email, password, name):
    if not name.strip() or not is_valid_email(email) or len(password) < 6:
        gr.Warning("⚠️ Criteria unfulfilled. Password must be 6+ characters.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False), gr.update()
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            html = f"<div class='profile-text'><b>User:</b> {name}<br><b>Email:</b> {email}</div>"
            gr.Info("✅ Account setup complete!")
            return token, gr.update(visible=False), gr.update(visible=True), gr.update(value=f"👤 {name[:10]}"), gr.update(value=html), False, gr.update(visible=False), gr.update(choices=[])
        else:
            # FIX: Reveal exact error if email is already taken!
            gr.Warning(f"❌ Registration Failed: {res.json().get('detail', 'Email might exist')}")
    except Exception as e: 
        gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False), gr.update()

def fetch_history(token):
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={"id":"ID","timestamp":"Date","raw_logs":"Searched Logs","anomaly":"Anomaly Found","root_cause":"Root Cause","remediation":"Remediation","status":"Status"})
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            return df[["ID", "Date", "Searched Logs", "Anomaly Found", "Root Cause", "Remediation", "Status"]]
    except: pass
    return pd.DataFrame()

def diagnose_logs(logs_text, token):
    if not token or not logs_text.strip(): return gr.update(), gr.update(), gr.update(), gr.update()
    try:
        lines = [line.strip() for line in logs_text.split('\n') if line.strip()]
        res = requests.post(f"{BACKEND_URL}/diagnose", json={"logs": lines}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if not data.get("anomaly_detected", True): return gr.update(value="✅ System Normal"), gr.update(value="N/A"), gr.update(value="N/A"), fetch_history(token)
            out_anom = f"**Type:** `{data.get('anomaly',{}).get('anomaly_type','N/A')}`\n\n**Severity:** `{data.get('anomaly',{}).get('severity','N/A')}`\n\n**Description:** {data.get('anomaly',{}).get('description','N/A')}"
            out_rc = f"**Cause:** {data.get('root_cause',{}).get('root_cause','N/A')}\n\n**Confidence:** {data.get('root_cause',{}).get('confidence',0):.1%}"
            out_rem = f"**Immediate Actions:** {', '.join(data.get('remediation',{}).get('immediate_actions',[]))}\n\n**Recovery Time:** {data.get('remediation',{}).get('estimated_recovery_time','N/A')}"
            gr.Info("⚡ Analysis Complete!")
            return gr.update(value=out_anom), gr.update(value=out_rc), gr.update(value=out_rem), fetch_history(token)
        else:
            # FIX: If models.py is broken, this throws the error immediately to your UI!
            gr.Warning(f"❌ Backend Diagnosis Error: {res.text}")
    except Exception as e: 
        gr.Warning(f"❌ Connection Error: {e}")
    return gr.update(value="Error"), gr.update(value="Error"), gr.update(value="Error"), gr.update()

def bridge_to_chat(logs, anomaly):
    if not logs.strip(): return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    prompt = "I am dealing with an anomaly.\n\nLogs:\n" + logs + "\n\nDiagnosis:\n" + anomaly + "\n\nCan you guide me through resolving this step by step?"
    return gr.update(value=prompt), [], None, gr.update(value=None), gr.update(selected="tab_chat")

def logout():
    gr.Info("🔒 Logged out safely.")
    return ("", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False))

# --- UI Layout ---
with gr.Blocks(title="AegisAI") as demo:
    session_token, current_chat_id, dropdown_visible = gr.State(""), gr.State(None), gr.State(False)
    
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<br><br><center><h2>🔐 AegisAI Portal</h2></center>")
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                with gr.Tab("Login"):
                    log_email, log_pass = gr.Textbox(label="Email"), gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="👁️ Show Password", elem_classes="show-pass-check")
                    login_btn = gr.Button("Login 🚀", variant="primary")
                with gr.Tab("Register"):
                    reg_name, reg_email, reg_pass = gr.Textbox(label="Full Name"), gr.Textbox(label="Email"), gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
                    reg_show_pass = gr.Checkbox(label="👁️ Show Password", elem_classes="show-pass-check")
                    register_btn = gr.Button("Sign Up 📝", variant="primary")
            with gr.Column(scale=1): pass

    with gr.Column(visible=False) as app_view:
        with gr.Row(elem_classes="nav-container"):
            gr.Markdown("<h1>🛡️ AegisAI</h1>", elem_classes="nav-logo")
            nav_profile_btn = gr.Button("👤 Profile", elem_classes="profile-btn")
        with gr.Column(visible=False, elem_classes="profile-dropdown") as profile_panel:
            profile_info = gr.HTML("")
            logout_btn = gr.Button("Logout", elem_classes="logout-btn")
            
        with gr.Tabs(elem_id="main_tabs") as tabs_manager:
            
            with gr.Tab("Live Diagnosis", id="tab_diag"):
                # FIX: Restored titles, examples, and the clear form button!
                gr.Markdown("### 📡 System Telemetry Input")
                logs_input = gr.Textbox(label="System Logs", lines=6, placeholder="Paste your system logs here...")
                with gr.Row():
                    diagnose_btn = gr.Button("Analyze Incident ⚡", variant="primary")
                    discuss_btn = gr.Button("Discuss with AI Copilot 💬", variant="secondary")
                    clear_btn = gr.Button("Clear Form 🗑️")
                    
                gr.Examples(examples=[
                    "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
                    "[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"
                ], inputs=logs_input)
                
                gr.Markdown("<br>### 📊 Diagnostics Report")
                with gr.Row(elem_classes="card-row"):
                    with gr.Column(elem_classes="result-card anomaly-card"):
                        gr.Markdown("### 🔴 ANOMALY DETECTED")
                        anomaly_out = gr.Markdown("Waiting...")
                    with gr.Column(elem_classes="result-card rc-card"):
                        gr.Markdown("### 🔍 ROOT CAUSE")
                        rc_out = gr.Markdown("Waiting...")
                    with gr.Column(elem_classes="result-card remed-card"):
                        gr.Markdown("### ⚙️ REMEDIATION")
                        remed_out = gr.Markdown("Waiting...")
                        
            with gr.Tab("💬 AI Copilot", id="tab_chat"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Chat History")
                        # FIX: Make the button visually clear
                        new_chat_btn = gr.Button("➕ New / Clear Chat", variant="primary", size="sm")
                        chat_session_dropdown = gr.Dropdown(label="Past Chats", choices=[], interactive=True, allow_custom_value=True)
                        refresh_chat_btn = gr.Button("🔄 Refresh List", size="sm")
                    with gr.Column(scale=3):
                        chatbot_ui = gr.Chatbot(label="Aegis AI Copilot", height=450)
                        with gr.Row():
                            chat_input = gr.Textbox(show_label=False, placeholder="Ask something...", scale=4)
                            chat_send_btn = gr.Button("Send 🚀", scale=1)
                            
            with gr.Tab("My Incident History"):
                refresh_btn = gr.Button("Refresh 🔄", size="sm")
                history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-wrap")

    # --- WIRING ---
    log_show_pass.change(fn=None, inputs=[log_show_pass], js="(s) => { const el = document.querySelector('#log_pass_input input'); if(el) el.type = s ? 'text' : 'password'; }")
    reg_show_pass.change(fn=None, inputs=[reg_show_pass], js="(s) => { const el = document.querySelector('#reg_pass_input input'); if(el) el.type = s ? 'text' : 'password'; }")
    nav_profile_btn.click(fn=lambda s: (not s, gr.update(visible=not s)), inputs=[dropdown_visible], outputs=[dropdown_visible, profile_panel], queue=False)
    clear_btn.click(fn=lambda: ("", "Waiting...", "Waiting...", "Waiting..."), outputs=[logs_input, anomaly_out, rc_out, remed_out], queue=False)

    login_btn.click(fn=api_login, inputs=[log_email, log_pass], outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, chat_session_dropdown]).then(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    register_btn.click(fn=api_register, inputs=[reg_email, reg_pass, reg_name], outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, chat_session_dropdown]).then(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    logout_btn.click(fn=logout, outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel], queue=False)

    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    discuss_btn.click(fn=bridge_to_chat, inputs=[logs_input, anomaly_out], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager], queue=False)
    chat_send_btn.click(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    chat_input.submit(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    
    new_chat_btn.click(fn=lambda: ("", [], None, gr.update(value=None)), outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown], queue=False)
    chat_session_dropdown.change(fn=load_chat_session, inputs=[chat_session_dropdown, session_token], outputs=[chatbot_ui, current_chat_id])
    refresh_chat_btn.click(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860, css=custom_css)