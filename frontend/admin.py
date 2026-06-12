import gradio as gr
import requests
import pandas as pd
import re
from utils import BACKEND_URL

def load_admin_data(token):
    if not token: 
        return 0, 0, 0, pd.DataFrame()
    try:
        m_res = requests.get(
            f"{BACKEND_URL}/admin/metrics", 
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        u_res = requests.get(
            f"{BACKEND_URL}/admin/users?limit=50", 
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        users, incidents, chats = 0, 0, 0
        df = pd.DataFrame()
        if m_res.status_code == 200:
            m = m_res.json()
            users = m.get("users", 0)
            incidents = m.get("incidents", 0)
            chats = m.get("chats", 0)
        if u_res.status_code == 200:
            data = u_res.json()
            if data:
                df = pd.DataFrame(data)
        return users, incidents, chats, df
    except requests.exceptions.Timeout:
        print("Admin data timeout - returning empty")
        return 0, 0, 0, pd.DataFrame()
    except Exception as e:
        print(f"Admin data error: {e}")
        return 0, 0, 0, pd.DataFrame()

def fetch_analytics(token):
    if not token: 
        return (
            pd.DataFrame(columns=["date", "Incidents"]),
            pd.DataFrame(columns=["Severity", "Count"]),
            pd.DataFrame(columns=["status", "Count"])
        )
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/analytics/data",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code != 200:
            return (
                pd.DataFrame(columns=["date", "Incidents"]),
                pd.DataFrame(columns=["Severity", "Count"]),
                pd.DataFrame(columns=["status", "Count"])
            )
        
        df = pd.DataFrame(res.json())
        if df.empty:
            return (
                pd.DataFrame(columns=["date", "Incidents"]),
                pd.DataFrame(columns=["Severity", "Count"]),
                pd.DataFrame(columns=["status", "Count"])
            )
        
        df['Severity'] = df['description'].apply(
            lambda x: re.search(r'Severity:\s*([A-Z]+)', str(x)).group(1)
            if re.search(r'Severity:\s*([A-Z]+)', str(x)) else 'UNKNOWN'
        )
        
        timeline_df = df.groupby('date').size().reset_index(name='Incidents')
        timeline_df['date'] = pd.to_datetime(timeline_df['date'])
        timeline_df = timeline_df.sort_values('date')
        
        sev_df = df.groupby('Severity').size().reset_index(name='Count')
        status_df = df.groupby('status').size().reset_index(name='Count')
        status_df['status'] = status_df['status'].str.upper()
        
        return timeline_df, sev_df, status_df
    except Exception as e:
        print(f"Analytics Error: {e}")
        return (
            pd.DataFrame(columns=["date", "Incidents"]),
            pd.DataFrame(columns=["Severity", "Count"]),
            pd.DataFrame(columns=["status", "Count"])
        )

def fetch_predictions(token):
    """Fetch incident predictions."""
    if not token:
        return gr.update(value="*Login as admin to view predictions*")
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/predictions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            risk_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
            risk = data.get('risk_level', 'LOW')
            html = f"""### AI Predictions
**Risk Level:** <span style="color:{risk_color.get(risk, '#10b981')};font-weight:bold;">{risk}</span>

{data.get('summary', '')}

---
"""
            for p in data.get("predictions", []):
                conf_color = "#10b981" if p["confidence"] > 70 else "#f59e0b" if p["confidence"] > 40 else "#ef4444"
                html += f"""**{p['title']}** <span style="color:{conf_color};font-size:0.8em;">({p['confidence']:.0f}%)</span>
{p['detail']}

"""
            return gr.update(value=html)
        else:
            return gr.update(value="*Admin access required*")
    except Exception as e:
        print(f"Prediction error: {e}")
        return gr.update(value="*Failed to load predictions*")

def purge_user(token, target_id):
    if not target_id:
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value="Please enter a valid User ID.")
    try:
        res = requests.delete(
            f"{BACKEND_URL}/admin/users/{int(target_id)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        data = load_admin_data(token)
        if res.status_code == 200:
            return data[0], data[1], data[2], data[3], gr.update(value=f"User ID {int(target_id)} permanently deleted.")
        else:
            detail = res.json().get('detail', 'Unknown error')
            return data[0], data[1], data[2], data[3], gr.update(value=f"Action Rejected: {detail}")
    except Exception as e:
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value=f"Error: {e}")

def inspect_user_data(token, target_id):
    if not target_id:
        return pd.DataFrame(), pd.DataFrame(), gr.update(value="Please enter a User ID.")
    try:
        # Check if user exists
        res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/exists",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if res.status_code == 200:
            if not res.json().get("exists", False):
                return pd.DataFrame(), pd.DataFrame(), gr.update(value=f"User ID {int(target_id)} does not exist.")
        else:
            return pd.DataFrame(), pd.DataFrame(), gr.update(value="Access Denied.")

        # Fetch incidents and chats
        inc_res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/incidents",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        chat_res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/chats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        df_inc = pd.DataFrame(inc_res.json()) if inc_res.status_code == 200 else pd.DataFrame()
        df_chat = pd.DataFrame(chat_res.json()) if chat_res.status_code == 200 else pd.DataFrame()
        return df_inc, df_chat, gr.update(value=f"Loaded activity for User ID: {int(target_id)}")
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), gr.update(value=f"Error: {e}")

        

        


def fetch_predictions(token):
    """Fetch incident predictions."""
    if not token:
        return gr.update(value="*Login as admin to see predictions*")
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/predictions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            
            # Format predictions as HTML
            risk_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
            html = f"""
### 🔮 Incident Predictions

**Risk Level:** <span style="color:{risk_color.get(data.get('risk_level', 'LOW'), '#10b981')}; font-weight:bold; font-size:1.2em;">
{data.get('risk_level', 'LOW')}</span>

{data.get('summary', '')}

---
"""
            for p in data.get("predictions", []):
                conf_color = "#10b981" if p["confidence"] > 70 else "#f59e0b" if p["confidence"] > 40 else "#ef4444"
                html += f"""
**{p['title']}** <span style="color:{conf_color}; font-size:0.8em;">({p['confidence']:.0f}% confidence)</span>

{p['detail']}

"""
            return gr.update(value=html)
    except Exception as e:
        print(f"Prediction error: {e}")
    return gr.update(value="*Failed to load predictions*")

    

def fetch_clusters(token):
    """Fetch incident clusters."""
    if not token:
        return gr.update(value="*Login as admin to view clusters*")
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/clusters",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if res.status_code == 200:
            data = res.json()
            return gr.update(value=data.get("html", "*No clusters found*"))
    except Exception as e:
        print(f"Cluster error: {e}")
    return gr.update(value="*Failed to load clusters*")