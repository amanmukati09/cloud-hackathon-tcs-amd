import gradio as gr
import requests
import pandas as pd
from datetime import datetime
import re

BACKEND_URL = "http://localhost:8000"

# --- Advanced Pro SaaS CSS Styling ---
custom_css = """
body, .gradio-container { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', system-ui, sans-serif !important; }
footer { display: none !important; }
.nav-container { display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: space-between !important; background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; padding: 10px 25px !important; margin-bottom: 15px !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important; border-radius: 8px !important; }
.nav-logo h1 { margin: 0 !important; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900 !important; font-size: 1.6rem !important; letter-spacing: 1px; }
button.profile-btn { background: transparent !important; border: 1px solid #38bdf8 !important; color: #38bdf8 !important; border-radius: 20px !important; padding: 4px 16px !important; font-weight: 600 !important; font-size: 0.9rem !important; transition: all 0.2s !important; max-width: 140px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; display: inline-block !important; }
.profile-dropdown { position: absolute !important; right: 30px !important; top: 75px !important; z-index: 9999 !important; background: #1e293b !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; padding: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important; width: 260px !important; }
.profile-text { color: #94a3b8 !important; font-size: 0.9rem !important; line-height: 1.6 !important; word-wrap: break-word !important; }
button.logout-btn { background: rgba(239, 68, 68, 0.1) !important; border: 1px solid #ef4444 !important; color: #ef4444 !important; border-radius: 6px !important; padding: 6px 16px !important; margin-top: 15px !important; width: 100% !important; transition: all 0.2s !important; }
.card-row { align-items: stretch !important; }
.result-card { display: flex !important; flex-direction: column !important; height: 100% !important; min-height: 380px !important; border-radius: 8px !important; padding: 20px !important; background: rgba(30, 41, 59, 0.5) !important; box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important; }
.anomaly-card { border-top: 4px solid #ef4444 !important; }
.rc-card { border-top: 4px solid #f59e0b !important; }
.remed-card { border-top: 4px solid #10b981 !important; }
.table-wrap { max-height: 500px !important; overflow-y: auto !important; }
.admin-badge { color: #f59e0b !important; font-size: 0.8em; font-weight: bold; margin-left: 5px; }
.show-pass-check { margin-top: -10px !important; margin-bottom: 10px !important; }
/* FIX 1: Applied styling strictly to inner wrapper to prevent empty box bug */
.admin-wrapper { background: rgba(245, 158, 11, 0.05) !important; border: 1px solid rgba(245, 158, 11, 0.3) !important; padding: 20px !important; border-radius: 8px !important; margin-bottom: 20px !important; }
/* FIX 4: Aligns buttons perfectly with inputs */
.align-bottom { display: flex; flex-direction: column; justify-content: flex-end; }
"""

def is_valid_email(email): 
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

def is_strong_password(password):
    return re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password)

# --- Chat APIs ---
def get_chat_sessions(token):
    if not token: return []
    try:
        res = requests.get(f"{BACKEND_URL}/chat/sessions", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return [title for session_id, title in res.json().items()]
    except: pass
    return []

def load_chat_session(session_str, token):
    if not session_str or not token: return [], None
    try:
        session_id = session_str.split("ID: ")[1].split(" |")[0]
        res = requests.get(f"{BACKEND_URL}/chat/sessions/{session_id}", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            return [{"role": "user" if u else "assistant", "content": u or a} for u, a in res.json() for u, a in [(u, None), (None, a)] if u or a], session_id
    except: pass
    return [], None

def send_chat_msg(message, session_id, history, token):
    if not message.strip(): 
        yield "", history, session_id, gr.update()
        return
    history = history or []
    history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": "⏳ Thinking..."}])
    yield "", history, session_id, gr.update()
    try:
        res = requests.post(f"{BACKEND_URL}/chat/message", json={"message": message, "session_id": int(session_id) if session_id else None}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            new_id = str(data.get("session_id"))
            choices = get_chat_sessions(token)
            sel = next((c for c in choices if f"ID: {new_id} |" in c), None)
            yield "", [{"role": "user" if u else "assistant", "content": u or a} for u, a in data.get("history", []) for u, a in [(u, None), (None, a)] if u or a], new_id, gr.update(choices=choices, value=sel)
        else:
            history[-1]["content"] = f"❌ Error: {res.text}"
            yield message, history, session_id, gr.update()
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {e}"
        yield message, history, session_id, gr.update()

# --- Admin Data Loaders ---
def load_admin_data(token):
    if not token: return 0, 0, 0, pd.DataFrame()
    try:
        m_res = requests.get(f"{BACKEND_URL}/admin/metrics", headers={"Authorization": f"Bearer {token}"})
        u_res = requests.get(f"{BACKEND_URL}/admin/users", headers={"Authorization": f"Bearer {token}"})
        users, incidents, chats = 0, 0, 0
        df = pd.DataFrame()
        if m_res.status_code == 200:
            m = m_res.json()
            users, incidents, chats = m.get("users", 0), m.get("incidents", 0), m.get("chats", 0)
        if u_res.status_code == 200: df = pd.DataFrame(u_res.json())
        return users, incidents, chats, df
    except: return 0, 0, 0, pd.DataFrame()

def purge_user(token, target_id):
    if not target_id: 
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value="⚠️ **Notice:** Please enter a valid User ID to delete.")
    
    try:
        res = requests.delete(f"{BACKEND_URL}/admin/users/{int(target_id)}", headers={"Authorization": f"Bearer {token}"})
        data = load_admin_data(token) 
        if res.status_code == 200: 
            return data[0], data[1], data[2], data[3], gr.update(value=f"✅ **Success:** User ID {int(target_id)} permanently deleted.")
        else: 
            error_msg = res.json().get('detail', 'Unknown error')
            return data[0], data[1], data[2], data[3], gr.update(value=f"❌ **Action Rejected:** {error_msg}")
    except Exception as e: 
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value=f"❌ **Connection Error:** {e}")

# --- Auth APIs ---
def api_login(email, password):
    if not email.strip() or not password.strip():
        gr.Warning("⚠️ Enter email and password.")
        return "", gr.update(visible=True), gr.update(visible=False), "👤 Profile", "", False, gr.update(visible=False), gr.update(), gr.update(visible=False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            is_admin = bool(data.get("is_admin", False)) 
            
            raw_name = email.split('@')[0].capitalize()
            disp = (raw_name[:10] + '..') if len(raw_name) > 10 else raw_name
            role_badge = "<span class='admin-badge'>[ROOT]</span>" if is_admin else ""
            html = f"<div class='profile-text'><b>User:</b> {raw_name} {role_badge}<br><b>Email:</b> {email}</div>"
            gr.Info(f"✅ Welcome back, {disp}!")
            
            return token, gr.update(visible=False), gr.update(visible=True), gr.update(value=f"👤 {disp}"), gr.update(value=html), False, gr.update(visible=False), gr.update(choices=get_chat_sessions(token)), gr.update(visible=is_admin)
        else: gr.Warning(f"❌ Login Denied: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.update(visible=True), gr.update(visible=False), "👤 Profile", "", False, gr.update(visible=False), gr.update(), gr.update(visible=False)

def api_register(email, password, name):
    name, email = name.strip(), email.strip()
    if not name or not is_valid_email(email) or not is_strong_password(password):
        gr.Warning("⚠️ Please fix validation errors (Valid Email, Strong Password).")
        return "", gr.update(visible=True), gr.update(visible=False), "👤 Profile", "", False, gr.update(visible=False), gr.update(), gr.update(visible=False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = name.split(' ')[0].capitalize()
            html = f"<div class='profile-text'><b>User:</b> {name}<br><b>Email:</b> {email}</div>"
            gr.Info("✅ Registration Successful!")
            return token, gr.update(visible=False), gr.update(visible=True), gr.update(value=f"👤 {raw_name[:10]}"), gr.update(value=html), False, gr.update(visible=False), gr.update(choices=[]), gr.update(visible=False)
        else: gr.Warning(f"❌ Registration Failed: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.update(visible=True), gr.update(visible=False), "👤 Profile", "", False, gr.update(visible=False), gr.update(), gr.update(visible=False)

def fetch_history(token):
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={"id":"ID","timestamp":"Date","raw_logs":"Logs","anomaly":"Anomaly Found","root_cause":"Root Cause","remediation":"Remediation","status":"Status"})
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            return df[["ID", "Date", "Logs", "Anomaly Found", "Root Cause", "Remediation", "Status"]]
    except: pass
    return pd.DataFrame()

def diagnose_logs(logs_text, token):
    if not token or not logs_text.strip(): return gr.update(), gr.update(), gr.update(), gr.update()
    try:
        res = requests.post(f"{BACKEND_URL}/diagnose", json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if not data.get("anomaly_detected", True): return gr.update(value="✅ System Normal"), gr.update(value="N/A"), gr.update(value="N/A"), fetch_history(token)
            gr.Info("⚡ Analysis Complete!")
            return gr.update(value=f"**Type:** `{data.get('anomaly',{}).get('anomaly_type','N/A')}`\n\n**Description:** {data.get('anomaly',{}).get('description','N/A')}"), gr.update(value=f"**Cause:** {data.get('root_cause',{}).get('root_cause','N/A')}"), gr.update(value=f"**Immediate Actions:** {', '.join(data.get('remediation',{}).get('immediate_actions',[]))}"), fetch_history(token)
    except: pass
    return gr.update(value="Error"), gr.update(value="Error"), gr.update(value="Error"), gr.update()

# FIX 2 & 3: Wiping out textboxes and unticking checkboxes explicitly on Logout
def logout():
    gr.Info("🔒 Logged out safely.")
    return (
        "", # session_token
        gr.update(visible=True), # auth_view
        gr.update(visible=False), # app_view
        "👤 Profile", # nav_profile_btn
        "", # profile_info
        False, # dropdown_visible
        gr.update(visible=False), # profile_panel
        gr.update(choices=[]), # chat_session_dropdown
        gr.update(visible=False), # admin_dashboard_view
        gr.update(value=""), # log_email
        gr.update(value=""), # log_pass
        gr.update(value=False), # log_show_pass
        gr.update(value=""), # reg_name
        gr.update(value=""), # reg_email
        gr.update(value=""), # reg_pass
        gr.update(value=False)  # reg_show_pass
    )

# --- UI Layout ---
with gr.Blocks(title="AegisAI") as demo:
    session_token, current_chat_id, dropdown_visible = gr.State(""), gr.State(None), gr.State(False)
    
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<br><br><center><h2>🔐 AegisAI Portal</h2></center>")
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                with gr.Tab("Login"):
                    log_email = gr.Textbox(label="Email")
                    log_pass = gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="👁️ Show Password", elem_classes="show-pass-check")
                    login_btn = gr.Button("Login 🚀", variant="primary")
                with gr.Tab("Register"):
                    reg_name = gr.Textbox(label="Full Name")
                    reg_email = gr.Textbox(label="Email")
                    reg_pass = gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
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
            
        with gr.Column(visible=False) as admin_dashboard_view:
            # FIX 1: The styling wrapper is inside the logic toggle
            with gr.Column(elem_classes="admin-wrapper"):
                gr.Markdown("### 🎛️ Root Administrator Dashboard")
                with gr.Row():
                    refresh_admin_btn = gr.Button("🔄 Sync Telemetry", variant="primary", size="sm")
                with gr.Row():
                    metric_users = gr.Number(label="Total Registered Users", interactive=False)
                    metric_incidents = gr.Number(label="Incidents Analyzed", interactive=False)
                    metric_chats = gr.Number(label="Active AI Sessions", interactive=False)
                
                gr.Markdown("### 👥 User Directory & Access Management")
                admin_users_table = gr.Dataframe(interactive=False, wrap=True)
                
                with gr.Row():
                    with gr.Column(scale=3):
                        delete_user_input = gr.Number(label="Target User ID", precision=0)
                    # FIX 4: Gradio structural baseline alignment
                    with gr.Column(scale=1, elem_classes="align-bottom"):
                        delete_user_btn = gr.Button("🚨 Terminate Account", variant="stop")
                
                admin_status_msg = gr.Markdown("")
            
        with gr.Tabs(elem_id="main_tabs") as tabs_manager:
            with gr.Tab("Live Diagnosis", id="tab_diag"):
                gr.Markdown("### 📡 System Telemetry Input")
                logs_input = gr.Textbox(label="System Logs", lines=6, placeholder="Paste logs...")
                with gr.Row():
                    diagnose_btn, discuss_btn, clear_btn = gr.Button("Analyze ⚡", variant="primary"), gr.Button("Discuss 💬", variant="secondary"), gr.Button("Clear 🗑️")
                
                gr.Examples(examples=[
                    "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
                    "[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"
                ], inputs=logs_input)

                gr.Markdown("<br>\n\n### 📊 Diagnostics Report")
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
                        new_chat_btn, chat_session_dropdown, refresh_chat_btn = gr.Button("➕ New Chat", variant="primary", size="sm"), gr.Dropdown(label="Past Chats", choices=[], interactive=True), gr.Button("🔄 Refresh", size="sm")
                    with gr.Column(scale=3):
                        chatbot_ui = gr.Chatbot(label="Copilot", height=450)
                        with gr.Row():
                            chat_input, chat_send_btn = gr.Textbox(show_label=False, placeholder="Ask...", scale=4), gr.Button("Send 🚀", scale=1)
                            
            with gr.Tab("My Incident History"):
                refresh_btn, history_table = gr.Button("Refresh 🔄", size="sm"), gr.Dataframe(interactive=False, wrap=True)

    # --- WIRING ---
    # FIX 3: Reset password fields properly using JS injected on Checkbox toggle
    log_show_pass.change(fn=None, inputs=[log_show_pass], js="(s) => { const el = document.querySelector('#log_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")
    reg_show_pass.change(fn=None, inputs=[reg_show_pass], js="(s) => { const el = document.querySelector('#reg_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")
    
    nav_profile_btn.click(fn=lambda s: (not s, gr.update(visible=not s)), inputs=[dropdown_visible], outputs=[dropdown_visible, profile_panel], queue=False)
    clear_btn.click(fn=lambda: ("", "Waiting...", "Waiting...", "Waiting..."), outputs=[logs_input, anomaly_out, rc_out, remed_out], queue=False)

    login_btn.click(
        fn=api_login, inputs=[log_email, log_pass], outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, chat_session_dropdown, admin_dashboard_view]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table])
    
    register_btn.click(
        fn=api_register, inputs=[reg_email, reg_pass, reg_name], outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, chat_session_dropdown, admin_dashboard_view]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    
    # Updated Logout Wiring to explicitly wipe the 7 Auth UI elements
    logout_btn.click(fn=logout, outputs=[
        session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, chat_session_dropdown, admin_dashboard_view,
        log_email, log_pass, log_show_pass, reg_name, reg_email, reg_pass, reg_show_pass
    ], queue=False)

    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    discuss_btn.click(fn=lambda l, a: (gr.update(value=f"Anomaly:\n{l}\n\nDiagnosis:\n{a}"), [], None, gr.update(value=None), gr.update(selected="tab_chat")) if l.strip() else (gr.update(), gr.update(), gr.update(), gr.update(), gr.update()), inputs=[logs_input, anomaly_out], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager], queue=False)
    chat_send_btn.click(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    chat_input.submit(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    new_chat_btn.click(fn=lambda: ("", [], None, gr.update(value=None)), outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown], queue=False)
    chat_session_dropdown.change(fn=load_chat_session, inputs=[chat_session_dropdown, session_token], outputs=[chatbot_ui, current_chat_id])
    refresh_chat_btn.click(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])

    # Admin Dashboard Wiring
    refresh_admin_btn.click(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table])
    delete_user_btn.click(fn=purge_user, inputs=[session_token, delete_user_input], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table, admin_status_msg])

if __name__ == "__main__":
    demo.queue().launch(share=True, server_name="0.0.0.0", server_port=7860, css=custom_css)