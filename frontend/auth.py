import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL, is_valid_email, is_strong_password
from notifications import fetch_notifications

def api_login(email, password):
    if not email.strip() or not password.strip():
        gr.Warning("⚠️ Enter email and password.")
        return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame())
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
            return (token, gr.update(visible=False), gr.update(visible=True), welcome_str, role_str, gr.update(visible=is_admin), notif_count, notif_df)
        else:
            gr.Warning(f"❌ Login Denied: {res.json().get('detail')}")
    except Exception as e:
        gr.Warning(f"❌ Connection Error: {e}")
    return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame())

def api_register(email, password, name):
    name, email = name.strip(), email.strip()
    if not name or not is_valid_email(email) or not is_strong_password(password):
        gr.Warning("⚠️ Please fix validation errors.")
        return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame())
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
            return (token, gr.update(visible=False), gr.update(visible=True), welcome_str, role_str, gr.update(visible=False), notif_count, notif_df)
        else:
            gr.Warning(f"❌ Registration Failed: {res.json().get('detail')}")
    except Exception as e:
        gr.Warning(f"❌ Connection Error: {e}")
    return ("", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame())

def logout():
    import pandas as pd
    gr.Info("🔒 Logged out safely.")
    return (
        "", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(choices=[]), gr.update(visible=False),
        gr.update(value=""), gr.update(value=""), gr.update(value=False), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value=False),
        gr.update(value=None), pd.DataFrame(), pd.DataFrame(), gr.update(value=""),
        gr.update(value=""), pd.DataFrame(), gr.update(value=None), gr.update(value=""), pd.DataFrame(),
        0, 0, 0, 0, 0, 0,  # 🆕 6 metrics
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),  # 3 charts
        pd.DataFrame(), gr.update(visible=False), gr.update(value=""),
        pd.DataFrame(), gr.update(visible=False), gr.update(value=None), gr.update(value=""), gr.update(value="*Select an incident to view details*"),
        gr.update(visible=False), "0", pd.DataFrame(),
        pd.DataFrame(), pd.DataFrame(), None, None
    )

def oauth_login_url(provider):
    """Get OAuth login URL for a provider."""
    return f"{BACKEND_URL}/auth/{provider}"

def handle_oauth_token(token):
    """Process OAuth token from URL parameter."""
    if not token:
        return "", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame()
    try:
        # Verify token and get user info
        from jose import jwt
        payload = jwt.decode(token, "super-secret-hackathon-key", algorithms=["HS256"])
        user_id = payload.get("sub")
        # We need to fetch user details... simplified for now
        return token, gr.update(visible=False), gr.update(visible=True), "### 👋 Welcome!", "👤 User", gr.update(visible=False), "0", pd.DataFrame()
    except:
        return "", gr.update(visible=True), gr.update(visible=False), "", "", gr.update(visible=False), "0", pd.DataFrame()