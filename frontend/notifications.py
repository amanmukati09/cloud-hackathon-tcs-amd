import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL

def fetch_notifications(token):
    """Fetch recent notifications for the current user"""
    if not token:
        return pd.DataFrame(), "0"
    try:
        res = requests.get(
            f"{BACKEND_URL}/notifications",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            notifications = data.get("notifications", [])
            unread_count = str(data.get("unread_count", 0))
            if notifications:
                df = pd.DataFrame(notifications)
                # Map notification type to icon
                icons = {
                    "ticket_answered": "🎫",
                    "new_incident": "🆕",
                    "incident_resolved": "✅",
                    "diagnosis_complete": "⚡",
                    "new_escalation": "📨"
                }
                df['Icon'] = df['type'].apply(lambda x: icons.get(x, "📢"))
                df = df[['Icon', 'title', 'message', 'created_at', 'is_read']]
                df.columns = ['', 'Title', 'Message', 'Date', 'Status']
                df['Status'] = df['Status'].apply(lambda x: "🔵 New" if not x else "✓ Read")
                return df, unread_count
            return pd.DataFrame(), "0"
    except Exception as e:
        print(f"Notification error: {e}")
    return pd.DataFrame(), "0"

def mark_notifications_read(token):
    """Mark all notifications as read"""
    if not token:
        return "0", pd.DataFrame()
    try:
        res = requests.post(
            f"{BACKEND_URL}/notifications/mark-read",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            gr.Info("✅ All notifications marked as read!")
            return "0", pd.DataFrame()
    except:
        pass
    return "0", pd.DataFrame()