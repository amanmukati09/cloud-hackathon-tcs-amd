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
            welcome_str = f"### 👋 Hello, {raw_name}"
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
            welcome_str = f"### 👋 Hello, {raw_name}"
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
        0, 0, 0, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
        pd.DataFrame(), gr.update(visible=False), gr.update(value=""),
        pd.DataFrame(), gr.update(visible=False), gr.update(value=None), gr.update(value=""), gr.update(value="*Select an incident to view details*"),
        gr.update(visible=False),
        "0", pd.DataFrame()
    )