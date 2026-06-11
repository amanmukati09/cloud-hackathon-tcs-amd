import gradio as gr
import requests
import pandas as pd
from datetime import datetime
import re
import asyncio
import time

BACKEND_URL = "http://localhost:8000"

# --- 🎨 FULLY FIXED SAAS CSS: Strict equal heights + balanced margins ---
custom_css = """
/* Base styling */
body { font-family: 'Inter', -apple-system, sans-serif !important; background-color: #0f172a !important; }
footer { display: none !important; }

/* Navigation */
.nav-container { 
    display: flex !important; 
    align-items: center !important; 
    justify-content: space-between !important; 
    background: transparent !important;
    padding: 10px 15px !important; 
    margin-bottom: 20px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}
.welcome-text h3 { margin: 0 !important; color: #f8fafc !important; font-weight: 600 !important; font-size: 1.3rem !important; }
.logout-btn { height: 38px !important; padding: 0 20px !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s !important; }

/* Footer – tighter padding */
.footer-container {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 12px 20px !important;
    margin-top: 40px !important;
    border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    background: rgba(15, 23, 42, 0.4) !important;
    border-radius: 12px 12px 0 0 !important;
}
.footer-logo { text-align: left !important; color: #94a3b8 !important; font-size: 0.95rem !important; font-weight: 600 !important; letter-spacing: 0.5px !important; }
.footer-role p { text-align: right !important; margin: 0 !important; color: #38bdf8 !important; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 1px !important; text-transform: uppercase !important; }

/* Auth box – centered with margin */
.auth-box { 
    max-width: 480px !important; 
    margin: 60px auto 0 auto !important; 
    float: none !important; 
}

/* Glass cards – flex-1 to fill parent column height */
.glass-card { 
    background: rgba(30, 41, 59, 0.5) !important; 
    border: 1px solid rgba(255, 255, 255, 0.08) !important; 
    padding: 16px !important; 
    border-radius: 12px !important; 
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    display: flex !important; 
    flex-direction: column !important;
    height: auto !important;
    min-height: 0 !important;
}
.push-bottom { margin-top: auto !important; }

/* ========== THE REAL FIX: Force equal-height columns to stretch cards ========== */
.equal-height > .gr-column {
    display: flex !important;
    flex-direction: column !important;
}
.equal-height > .gr-column > *:first-child {
    flex: 1 1 auto !important;
    height: auto !important;
}

/* Internal spacing */
.glass-card > * { margin-top: 0 !important; margin-bottom: 0.5rem !important; }
.glass-card > *:last-child { margin-bottom: 0 !important; }

/* Tables scrolling */
.table-scroll { max-height: 300px !important; overflow-y: auto !important; display: block !important; width: 100% !important; border-radius: 8px; }
.short-table { max-height: 180px !important; overflow-y: auto !important; display: block !important; width: 100% !important; border-radius: 8px; }

/* Admin panel highlight */
.admin-panel { border: 2px solid rgba(245, 158, 11, 0.3) !important; background: rgba(245, 158, 11, 0.02) !important; border-radius: 16px !important; padding: 25px !important; margin-bottom: 25px !important; }
"""

saas_theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    spacing_size="lg",
    radius_size="lg"
)

# --- UTILITY & AUTO-CLEAR ---
def is_valid_email(email): 
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

def is_strong_password(password):
    return re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password)

async def clear_status():
    await asyncio.sleep(4)
    return ""

def _safe_join(val):
    """Safely converts whatever the AI agent returns (string, list, or dict) into a readable string to prevent sequence crashes."""
    if not val: return "None"
    if isinstance(val, list):
        return ", ".join([str(item) for item in val])
    return str(val)

# --- APIs ---
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

def submit_escalation(question, token):
    if not question.strip(): return gr.skip(), fetch_my_tickets(token)
    try:
        res = requests.post(f"{BACKEND_URL}/escalations", json={"question": question}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("✅ Ticket submitted securely to the Admin team!")
            return "", fetch_my_tickets(token)
    except Exception as e: gr.Warning(f"Error: {e}")
    return gr.skip(), fetch_my_tickets(token)

def fetch_my_tickets(token):
    if not token: return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/escalations/my", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame()

def load_admin_tickets(token):
    if not token: return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/admin/escalations", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame()

def answer_escalation(ticket_id, answer, token):
    if not ticket_id or not answer.strip():
        return gr.skip(), gr.skip(), load_admin_tickets(token)
    try:
        res = requests.post(f"{BACKEND_URL}/admin/escalations/{int(ticket_id)}/answer", json={"answer": answer}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("✅ Answer posted successfully!")
            return None, "", load_admin_tickets(token)
        else: gr.Warning(f"❌ Error: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Error: {e}")
    return gr.skip(), gr.skip(), load_admin_tickets(token)

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
        return data[0], data[1], data[2], data[3], "⚠️ **Notice:** Please enter a valid User ID to delete."
    try:
        res = requests.delete(f"{BACKEND_URL}/admin/users/{int(target_id)}", headers={"Authorization": f"Bearer {token}"})
        data = load_admin_data(token) 
        if res.status_code == 200: return data[0], data[1], data[2], data[3], f"✅ **Success:** User ID {int(target_id)} permanently deleted."
        else: return data[0], data[1], data[2], data[3], f"❌ **Action Rejected:** {res.json().get('detail', 'Unknown')}"
    except Exception as e: 
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], f"❌ **Connection Error:** {e}"

def inspect_user_data(token, target_id):
    if not target_id: return pd.DataFrame(), pd.DataFrame(), "⚠️ **Notice:** Enter a valid User ID to inspect."
    try:
        inc_res = requests.get(f"{BACKEND_URL}/admin/users/{int(target_id)}/incidents", headers={"Authorization": f"Bearer {token}"})
        chat_res = requests.get(f"{BACKEND_URL}/admin/users/{int(target_id)}/chats", headers={"Authorization": f"Bearer {token}"})
        if inc_res.status_code == 403 or chat_res.status_code == 403: return pd.DataFrame(), pd.DataFrame(), "❌ **Access Denied.**"
        df_inc = pd.DataFrame(inc_res.json()) if inc_res.status_code == 200 else pd.DataFrame()
        df_chat = pd.DataFrame(chat_res.json()) if chat_res.status_code == 200 else pd.DataFrame()
        return df_inc, df_chat, f"✅ **Loaded Activity Log for User ID: {int(target_id)}**"
    except Exception as e: return pd.DataFrame(), pd.DataFrame(), f"❌ **Connection Error:** {e}"

def api_login(email, password):
    if not email.strip() or not password.strip():
        gr.Warning("⚠️ Enter email and password.")
        return "", gr.Column(visible=True), gr.Column(visible=False), "", "", gr.Column(visible=False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            is_admin = bool(data.get("is_admin", False)) 
            raw_name = email.split('@')[0].capitalize()
            welcome_str = f"### 👋 Hello, {raw_name}"
            role_str = "🛡️ Root Admin" if is_admin else "👤 Standard User"
            gr.Info(f"✅ Welcome back, {raw_name}!")
            return token, gr.Column(visible=False), gr.Column(visible=True), welcome_str, role_str, gr.Column(visible=is_admin)
        else: gr.Warning(f"❌ Login Denied: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.Column(visible=True), gr.Column(visible=False), "", "", gr.Column(visible=False)

def api_register(email, password, name):
    name, email = name.strip(), email.strip()
    if not name or not is_valid_email(email) or not is_strong_password(password):
        gr.Warning("⚠️ Please fix validation errors.")
        return "", gr.Column(visible=True), gr.Column(visible=False), "", "", gr.Column(visible=False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = name.split(' ')[0].capitalize()
            welcome_str = f"### 👋 Hello, {raw_name}"
            role_str = "👤 Standard User"
            gr.Info("✅ Registration Successful!")
            return token, gr.Column(visible=False), gr.Column(visible=True), welcome_str, role_str, gr.Column(visible=False)
        else: gr.Warning(f"❌ Registration Failed: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Connection Error: {e}")
    return "", gr.Column(visible=True), gr.Column(visible=False), "", "", gr.Column(visible=False)

def fetch_history(token):
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={"id":"ID","timestamp":"Date","raw_logs":"Logs","anomaly":"Anomaly Found","root_cause":"Root Cause","remediation":"Remediation","status":"Status"})
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            return df[["ID", "Date", "Logs", "Anomaly Found", "Root Cause", "Remediation", "Status"]]
    except: pass
    return pd.DataFrame()

# 🚀 BULLETPROOF AI JSON PARSER
def diagnose_logs(logs_text, token):
    if not token or not logs_text.strip(): return gr.skip(), gr.skip(), gr.skip(), gr.skip()
    try:
        res = requests.post(f"{BACKEND_URL}/diagnose", json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if not data.get("anomaly_detected", True): 
                return "✅ System Normal", "N/A", "N/A", fetch_history(token)
            
            gr.Info("⚡ Analysis Complete!")
            
            # --- Safely Parse Anomaly Section ---
            a_type = data.get("anomaly_type") or (data.get("anomaly", {}).get("anomaly_type", "Unknown") if isinstance(data.get("anomaly"), dict) else "Unknown")
            a_sev = data.get("severity") or (data.get("anomaly", {}).get("severity", "N/A") if isinstance(data.get("anomaly"), dict) else "N/A")
            a_comp = data.get("affected_component") or (data.get("anomaly", {}).get("affected_component", "N/A") if isinstance(data.get("anomaly"), dict) else "N/A")
            a_desc = data.get("description") or (data.get("anomaly", {}).get("description", "No description provided.") if isinstance(data.get("anomaly"), dict) else "No description provided.")
            out_anomaly = f"Type: {a_type}\nSeverity: {a_sev}\nComponent: {a_comp}\nDescription: {a_desc}"
            
            # --- Safely Parse Root Cause Section ---
            rc_val = data.get("root_cause")
            if isinstance(rc_val, dict):
                c_cause = rc_val.get("root_cause", "Unknown")
                c_conf = rc_val.get("confidence", "N/A")
                c_ev = _safe_join(rc_val.get("evidence", []))
                c_cf = _safe_join(rc_val.get("contributing_factors", []))
                out_rc = f"Cause: {c_cause}\nConfidence: {c_conf}\nEvidence: {c_ev}\nFactors: {c_cf}"
            else:
                c_conf = data.get("confidence", "N/A")
                c_ev = _safe_join(data.get("evidence", []))
                c_cf = _safe_join(data.get("contributing_factors", []))
                out_rc = f"Cause: {rc_val or 'Unknown'}\nConfidence: {c_conf}\nEvidence: {c_ev}\nFactors: {c_cf}"

            # --- Safely Parse Remediation Section ---
            rem_val = data.get("remediation")
            if isinstance(rem_val, dict):
                r_imm = _safe_join(rem_val.get("immediate_actions", []))
                r_auto = _safe_join(rem_val.get("automated_actions", []))
                r_esc = rem_val.get("escalation_needed", False)
                r_ert = rem_val.get("estimated_recovery_time", "Unknown")
                r_prev = _safe_join(rem_val.get("prevention_measures", []))
                out_rem = f"Immediate: {r_imm}\nAutomated: {r_auto}\nEscalate: {r_esc}\nRecovery: {r_ert}\nPrevention: {r_prev}"
            else:
                r_imm = _safe_join(data.get("immediate_actions", []))
                r_auto = _safe_join(data.get("automated_actions", []))
                r_esc = data.get("escalation_needed", False)
                r_ert = data.get("estimated_recovery_time", "Unknown")
                r_prev = _safe_join(data.get("prevention_measures", []))
                out_rem = f"Immediate: {r_imm}\nAutomated: {r_auto}\nEscalate: {r_esc}\nRecovery: {r_ert}\nPrevention: {r_prev}"

            return out_anomaly, out_rc, out_rem, fetch_history(token)
    except Exception as e: 
        print(f"Diagnostics Parsing Error: {e}")
        return f"Error processing diagnosis: {e}", "Error", "Error", gr.skip()
    
    return "Error", "Error", "Error", gr.skip()

def logout():
    gr.Info("🔒 Logged out safely.")
    return (
        "", gr.Column(visible=True), gr.Column(visible=False), "", "", gr.Dropdown(choices=[], value=None), gr.Column(visible=False),
        "", "", False, "", "", "", False,
        None, pd.DataFrame(), pd.DataFrame(), "",
        "", pd.DataFrame(), None, "", pd.DataFrame()
    )

# --- UI LAYOUT ---
# 🚀 FIX: Removed theme/css from here to silence the deprecation warning
with gr.Blocks(title="AegisAI") as demo:
    session_token, current_chat_id = gr.State(""), gr.State(None)
    
    # --- AUTH VIEW ---
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<center><h1 style='font-size: 2.5rem; margin-bottom: 20px; color: #38bdf8;'>🛡️ AegisAI Portal</h1></center>")
        with gr.Row():
            with gr.Column(elem_classes="auth-box glass-card"):
                with gr.Tab("Login"):
                    log_email = gr.Textbox(label="Email Address", placeholder="admin@example.com")
                    log_pass = gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="👁️ Show Password")
                    login_btn = gr.Button("Login to Dashboard 🚀", variant="primary", elem_classes="push-bottom")
                with gr.Tab("Register New Account"):
                    reg_name = gr.Textbox(label="Full Name", placeholder="Jane Doe")
                    reg_email = gr.Textbox(label="Email Address", placeholder="user@example.com")
                    reg_pass = gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
                    reg_show_pass = gr.Checkbox(label="👁️ Show Password")
                    register_btn = gr.Button("Secure Sign Up 📝", variant="primary", elem_classes="push-bottom")

    # --- APP VIEW ---
    with gr.Column(visible=False) as app_view:
        
        with gr.Row(elem_classes="nav-container"):
            with gr.Column(scale=1):
                welcome_text = gr.Markdown("", elem_classes="welcome-text")
            with gr.Column(scale=0, min_width=120):
                logout_btn = gr.Button("Logout 🔒", variant="stop", elem_classes="logout-btn")
            
        # Admin Dashboard
        with gr.Column(visible=False) as admin_dashboard_view:
            with gr.Column(elem_classes="admin-panel"):
                gr.Markdown("## 🎛️ Root Administrator Dashboard")
                with gr.Row():
                    metric_users = gr.Number(label="Total Registered Users", interactive=False)
                    metric_incidents = gr.Number(label="Incidents Analyzed", interactive=False)
                    metric_chats = gr.Number(label="Active AI Sessions", interactive=False)
                
                gr.HTML("<hr style='border-color: rgba(255,255,255,0.1); margin: 15px 0;'>")
                
                with gr.Row(equal_height=True):
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        gr.Markdown("### 👥 User Directory")
                        admin_users_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### ⚙️ Account Controls")
                        refresh_admin_btn = gr.Button("🔄 Sync Directory", variant="secondary")
                        delete_user_input = gr.Number(label="Target User ID", precision=0)
                        delete_user_btn = gr.Button("🚨 Terminate Account", variant="stop", elem_classes="push-bottom")
                        admin_status_msg = gr.Markdown("")

                with gr.Row(equal_height=True):
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        gr.Markdown("### 🔍 Deep-Dive User Inspection")
                        inspect_incidents_table = gr.Dataframe(label="Raw Incident Submissions", interactive=False, wrap=True, elem_classes="short-table")
                        inspect_chats_table = gr.Dataframe(label="Copilot Chat Transcripts", interactive=False, wrap=True, elem_classes="short-table")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### ⚙️ Fetch Telemetry")
                        inspect_user_input = gr.Number(label="User ID to Inspect", precision=0)
                        inspect_btn = gr.Button("Fetch User History", variant="primary", elem_classes="push-bottom")
                        inspect_status_msg = gr.Markdown("")

                with gr.Row(equal_height=True):
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        gr.Markdown("### 🎟️ Escalation & QA Tickets")
                        admin_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### ⚙️ Resolve Tickets")
                        refresh_admin_tickets_btn = gr.Button("🔄 Sync Tickets", variant="secondary")
                        answer_ticket_id_input = gr.Number(label="Ticket ID", precision=0)
                        answer_ticket_input = gr.Textbox(label="Your Answer", lines=2)
                        answer_ticket_btn = gr.Button("Submit Answer ✅", variant="primary", elem_classes="push-bottom")

        # MAIN TABS
        with gr.Tabs(elem_id="main_tabs") as tabs_manager:
            with gr.Tab("Live Diagnosis", id="tab_diag"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📡 System Telemetry Input")
                        logs_input = gr.Textbox(label="System Logs", lines=9, placeholder="Paste your server or application logs here...")
                        with gr.Row():
                            diagnose_btn = gr.Button("Analyze ⚡", variant="primary")
                            discuss_btn = gr.Button("Discuss 💬", variant="secondary")
                            clear_btn = gr.Button("Clear 🗑️", variant="stop")
                        gr.Examples(examples=[
                            ["[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%"],
                            ["[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"]
                        ], inputs=logs_input)
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📊 Diagnostics Report")
                        anomaly_out = gr.Textbox(label="🔴 ANOMALY DETECTED", interactive=False, lines=3)
                        rc_out = gr.Textbox(label="🔍 ROOT CAUSE", interactive=False, lines=3)
                        remed_out = gr.Textbox(label="⚙️ REMEDIATION", interactive=False, lines=3)
                        
            with gr.Tab("💬 AI Copilot", id="tab_chat"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Session Management")
                        chat_session_dropdown = gr.Dropdown(label="Load Past Chat", choices=[], interactive=True, allow_custom_value=True)
                        refresh_chat_btn = gr.Button("🔄 Refresh List", variant="secondary")
                        new_chat_btn = gr.Button("➕ Start New Chat", variant="primary", elem_classes="push-bottom")
                        
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        chatbot_ui = gr.Chatbot(label="Aegis AI Copilot", height=400)
                        with gr.Row():
                            chat_input = gr.Textbox(show_label=False, placeholder="Ask the Copilot a question...", scale=4)
                            chat_send_btn = gr.Button("Send 🚀", variant="primary", scale=1)
                            
            with gr.Tab("My Incident History"):
                with gr.Column(elem_classes="glass-card"):
                    with gr.Row():
                        gr.Markdown("### Your Processed Incidents", scale=4)
                        refresh_btn = gr.Button("Refresh Data 🔄", variant="secondary", scale=1)
                    history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

            with gr.Tab("🆘 Support Tickets", id="tab_support"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Ask an Admin / QA")
                        gr.Markdown("If the Copilot cannot resolve your issue, escalate it directly to our Root Admin team.")
                        ticket_question_input = gr.Textbox(label="Your Question or Issue", placeholder="Describe your issue clearly...", lines=6)
                        submit_ticket_btn = gr.Button("Submit Ticket 📨", variant="primary", elem_classes="push-bottom")
                    
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Your Escalation History", scale=4) 
                            refresh_my_tickets_btn = gr.Button("🔄 Sync Status", variant="secondary", scale=1)
                        my_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

        # Footer
        with gr.Row(elem_classes="footer-container"):
            with gr.Column(scale=1):
                gr.Markdown("🛡️ **Aegis AI**", elem_classes="footer-logo")
            with gr.Column(scale=1):
                role_text = gr.Markdown("", elem_classes="footer-role")

    # --- EVENT WIRING ---
    log_show_pass.change(fn=None, inputs=[log_show_pass], js="(s) => { const el = document.querySelector('#log_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")
    reg_show_pass.change(fn=None, inputs=[reg_show_pass], js="(s) => { const el = document.querySelector('#reg_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")
    
    clear_btn.click(fn=lambda: ("", "", "", ""), outputs=[logs_input, anomaly_out, rc_out, remed_out], queue=False)

    login_btn.click(
        fn=api_login, inputs=[log_email, log_pass], outputs=[session_token, auth_view, app_view, welcome_text, role_text, admin_dashboard_view]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table]
    ).then(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table]
    ).then(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])
    
    register_btn.click(
        fn=api_register, inputs=[reg_email, reg_pass, reg_name], outputs=[session_token, auth_view, app_view, welcome_text, role_text, admin_dashboard_view]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])
    
    logout_btn.click(fn=logout, outputs=[
        session_token, auth_view, app_view, welcome_text, role_text, chat_session_dropdown, admin_dashboard_view,
        log_email, log_pass, log_show_pass, reg_name, reg_email, reg_pass, reg_show_pass,
        inspect_user_input, inspect_incidents_table, inspect_chats_table, inspect_status_msg,
        ticket_question_input, my_tickets_table, answer_ticket_id_input, answer_ticket_input, admin_tickets_table
    ], queue=False)

    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    
    discuss_btn.click(fn=lambda l, a: (f"Anomaly:\n{l}\n\nDiagnosis:\n{a}", [], None, None, gr.Tabs(selected="tab_chat")) if l.strip() else (gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()), inputs=[logs_input, anomaly_out], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager], queue=False)
    
    chat_send_btn.click(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    chat_input.submit(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    new_chat_btn.click(fn=lambda: ("", [], None, None), outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown], queue=False)
    chat_session_dropdown.change(fn=load_chat_session, inputs=[chat_session_dropdown, session_token], outputs=[chatbot_ui, current_chat_id])
    refresh_chat_btn.click(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])

    refresh_admin_btn.click(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table])
    delete_user_btn.click(
        fn=purge_user, inputs=[session_token, delete_user_input], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table, admin_status_msg]
    ).then(fn=clear_status, outputs=[admin_status_msg])
    
    inspect_btn.click(
        fn=inspect_user_data, inputs=[session_token, inspect_user_input], outputs=[inspect_incidents_table, inspect_chats_table, inspect_status_msg]
    ).then(fn=clear_status, outputs=[inspect_status_msg])
    
    refresh_admin_tickets_btn.click(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table])
    submit_ticket_btn.click(fn=submit_escalation, inputs=[ticket_question_input, session_token], outputs=[ticket_question_input, my_tickets_table])
    refresh_my_tickets_btn.click(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])
    answer_ticket_btn.click(fn=answer_escalation, inputs=[answer_ticket_id_input, answer_ticket_input, session_token], outputs=[answer_ticket_id_input, answer_ticket_input, admin_tickets_table])

if __name__ == "__main__":
    # 🚀 FIX: Passed theme and css directly to launch() so the terminal warning goes away!
    demo.queue().launch(share=True, server_name="0.0.0.0", server_port=7860, theme=saas_theme, css=custom_css)