import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL, is_valid_email, is_strong_password
from notifications import fetch_notifications

def api_login(email, password):
    if not email.strip() or not password.strip():
        gr.Warning("⚠️ Enter email and password.")
        return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            is_admin = bool(data.get("is_admin", False))
            raw_name = email.split('@')[0].capitalize()

            if is_admin:
                role_display = "🛡️ Root Admin"
                role_color = "#f59e0b"
                bg_color = "rgba(245,158,11,0.15)"
            else:
                role_display = "👤 Standard User"
                role_color = "#38bdf8"
                bg_color = "rgba(56,189,248,0.15)"

            welcome_str = (
                f"### 👋 Hello, {raw_name} "
                f"<span style='color:{role_color}; background:{bg_color}; "
                f"padding:2px 10px; border-radius:12px; font-size:0.65em; "
                f"margin-left:8px; vertical-align:middle;'>{role_display}</span>"
            )

            role_str = "🛡️ Root Admin" if is_admin else "👤 Standard User"
            gr.Info(f"✅ Welcome back, {raw_name}!")
            notif_df, notif_count = fetch_notifications(token)
            return (token, gr.update(visible=False), gr.update(visible=True), welcome_str, role_str, gr.update(visible=is_admin), notif_count, notif_df, is_admin)
        else:
            gr.Warning(f"❌ Login Denied: {res.json().get('detail')}")
    except Exception as e:
        gr.Warning(f"❌ Connection Error: {e}")
    return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False)

def api_register(email, password, name):
    name, email = name.strip(), email.strip()
    if not name or not is_valid_email(email) or not is_strong_password(password):
        gr.Warning("⚠️ Please fix validation errors.")
        return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False)
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = name.split(' ')[0].capitalize()

            role_display = "👤 Standard User"
            role_color = "#38bdf8"
            bg_color = "rgba(56,189,248,0.15)"

            welcome_str = (
                f"### 👋 Hello, {raw_name} "
                f"<span style='color:{role_color}; background:{bg_color}; "
                f"padding:2px 10px; border-radius:12px; font-size:0.65em; "
                f"margin-left:8px; vertical-align:middle;'>{role_display}</span>"
            )

            role_str = "👤 Standard User"
            gr.Info("✅ Registration Successful!")
            notif_df, notif_count = fetch_notifications(token)
            return (token, gr.update(visible=False), gr.update(visible=True), welcome_str, role_str, gr.update(visible=False), notif_count, notif_df, False)
        else:
            gr.Warning(f"❌ Registration Failed: {res.json().get('detail')}")
    except Exception as e:
        gr.Warning(f"❌ Connection Error: {e}")
    return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False)

def logout():
    import pandas as pd
    gr.Info("🔒 Logged out safely.")
    return (
        "",                                    # token
        gr.update(visible=True),               # auth_view
        gr.update(visible=False),              # app_view
        "",                                    # welcome_text
        "",                                    # role_text
        gr.update(choices=[]),                 # chat_session_dropdown
        gr.update(visible=False),              # admin_dashboard_view
        gr.update(value=""),                   # log_email
        gr.update(value=""),                   # log_pass
        gr.update(value=False),                # log_show_pass
        gr.update(value=""),                   # reg_name
        gr.update(value=""),                   # reg_email
        gr.update(value=""),                   # reg_pass
        gr.update(value=False),                # reg_show_pass
        gr.update(value=None),                 # inspect_user_input
        pd.DataFrame(),                        # inspect_incidents_table
        pd.DataFrame(),                        # inspect_chats_table
        gr.update(value=""),                   # inspect_status_msg
        gr.update(value=""),                   # ticket_question_input
        pd.DataFrame(),                        # my_tickets_table
        gr.update(value=None),                 # answer_ticket_id_input
        gr.update(value=""),                   # answer_ticket_input
        pd.DataFrame(),                        # admin_tickets_table
        0, 0, 0, 0, 0, 0,                     # metric_users, metric_incidents, metric_chats, metric_resolved, gr.State(), gr.State()
        pd.DataFrame(),                        # dashboard_timeline
        pd.DataFrame(),                        # dashboard_severity_chart
        pd.DataFrame(),                        # dashboard_status_chart
        pd.DataFrame(),                        # similar_incidents_table
        gr.update(visible=False),              # similar_incidents_row
        gr.update(value=""),                   # similar_incidents_status
        pd.DataFrame(),                        # history_table
        gr.update(visible=False),              # resolve_incident_row
        gr.update(value=None),                 # resolve_incident_id
        gr.update(value=""),                   # resolve_notes_input
        gr.update(value="*Select an incident to view details*"),  # incident_details_md
        gr.update(visible=False),              # download_row
        "0",                                   # notification_count
        pd.DataFrame(),                        # notifications_table
        pd.DataFrame(),                        # community_posts_table
        pd.DataFrame(),                        # community_comments_table
        None,                                  # selected_post_id
        None,                                  # selected_comment_id
        gr.update(selected="tab_diag"),        # tabs_manager (reset to first tab)
        False,                                 # is_admin_state
    )

def oauth_login_url(provider):
    """Get OAuth login URL for a provider."""
    return f"{BACKEND_URL}/auth/{provider}"

def handle_oauth_token(token):
    """Process OAuth token from URL parameter."""
    if not token:
        return "", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False
    try:
        from jose import jwt
        payload = jwt.decode(token, "super-secret-hackathon-key", algorithms=["HS256"])
        user_id = payload.get("sub")
        return token, gr.update(visible=False), gr.update(visible=True), "### 👋 Welcome!", "👤 User", gr.update(visible=False), "0", pd.DataFrame(), False
    except:
        return "", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame(), False