import gradio as gr
import requests
import pandas as pd
import re
from utils import BACKEND_URL

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

def fetch_analytics(token):
    if not token: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/admin/analytics/data", headers={"Authorization": f"Bearer {token}"})
        if res.status_code != 200: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        df = pd.DataFrame(res.json())
        if df.empty: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
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
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def purge_user(token, target_id):
    if not target_id: 
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value="⚠️ **Notice:** Please enter a valid User ID to delete.")
    try:
        res = requests.delete(f"{BACKEND_URL}/admin/users/{int(target_id)}", headers={"Authorization": f"Bearer {token}"})
        data = load_admin_data(token) 
        if res.status_code == 200: return data[0], data[1], data[2], data[3], gr.update(value=f"✅ **Success:** User ID {int(target_id)} permanently deleted.")
        else: return data[0], data[1], data[2], data[3], gr.update(value=f"❌ **Action Rejected:** {res.json().get('detail', 'Unknown')}")
    except Exception as e: 
        data = load_admin_data(token)
        return data[0], data[1], data[2], data[3], gr.update(value=f"❌ **Connection Error:** {e}")

def inspect_user_data(token, target_id):
    if not target_id: return pd.DataFrame(), pd.DataFrame(), gr.update(value="⚠️ **Notice:** Enter a valid User ID to inspect.")
    try:
        inc_res = requests.get(f"{BACKEND_URL}/admin/users/{int(target_id)}/incidents", headers={"Authorization": f"Bearer {token}"})
        chat_res = requests.get(f"{BACKEND_URL}/admin/users/{int(target_id)}/chats", headers={"Authorization": f"Bearer {token}"})
        if inc_res.status_code == 403 or chat_res.status_code == 403: return pd.DataFrame(), pd.DataFrame(), gr.update(value="❌ **Access Denied.**")
        df_inc = pd.DataFrame(inc_res.json()) if inc_res.status_code == 200 else pd.DataFrame()
        df_chat = pd.DataFrame(chat_res.json()) if chat_res.status_code == 200 else pd.DataFrame()
        return df_inc, df_chat, gr.update(value=f"✅ **Loaded Activity Log for User ID: {int(target_id)}**")
    except Exception as e: return pd.DataFrame(), pd.DataFrame(), gr.update(value=f"❌ **Connection Error:** {e}")