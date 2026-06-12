import gradio as gr
import requests
import pandas as pd
import re
from utils import BACKEND_URL

def load_admin_data(token):
    if not token: return 0, 0, 0, pd.DataFrame()
    try:
        m_res = requests.get(f"{BACKEND_URL}/admin/metrics", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        u_res = requests.get(f"{BACKEND_URL}/admin/users?limit=50", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        # ... rest unchanged
    except requests.exceptions.Timeout:
        print("Admin data timeout")
        return 0, 0, 0, pd.DataFrame()
    except: return 0, 0, 0, pd.DataFrame()

        

def fetch_analytics(token):
    if not token: 
        return pd.DataFrame(columns=["date", "Incidents"]), pd.DataFrame(columns=["Severity", "Count"]), pd.DataFrame(columns=["status", "Count"])
    try:
        res = requests.get(f"{BACKEND_URL}/admin/analytics/data", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code != 200: 
            return pd.DataFrame(columns=["date", "Incidents"]), pd.DataFrame(columns=["Severity", "Count"]), pd.DataFrame(columns=["status", "Count"])
        
        df = pd.DataFrame(res.json())
        if df.empty: 
            return pd.DataFrame(columns=["date", "Incidents"]), pd.DataFrame(columns=["Severity", "Count"]), pd.DataFrame(columns=["status", "Count"])
        
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
        return pd.DataFrame(columns=["date", "Incidents"]), pd.DataFrame(columns=["Severity", "Count"]), pd.DataFrame(columns=["status", "Count"])

def fetch_enhanced_analytics(token):
    """Fetch enhanced analytics for the dashboard."""
    if not token: 
        return (
            pd.DataFrame(columns=["date", "rolling_avg"]),
            pd.DataFrame(columns=["Severity", "Avg Hours", "Resolved Count"]),
            pd.DataFrame(columns=["component", "incidents"]),
            pd.DataFrame(columns=["weekday", "hour", "incidents"])
        )
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/analytics/enhanced",
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            
            # 1. Trend Data
            trend_list = data.get("trend", [])
            if trend_list:
                trend_df = pd.DataFrame(trend_list)
                trend_df['date'] = pd.to_datetime(trend_df['date'])
            else:
                trend_df = pd.DataFrame(columns=["date", "count", "rolling_avg"])
            
            # 2. Components Data
            comp_list = data.get("components", [])
            if comp_list:
                comp_df = pd.DataFrame(comp_list)
            else:
                comp_df = pd.DataFrame(columns=["component", "incidents"])
            
            # 3. MTTR Data
            mttr_list = data.get("mttr_by_severity", [])
            if mttr_list:
                mttr_df = pd.DataFrame(mttr_list)
                mttr_df = mttr_df.rename(columns={
                    "severity": "Severity", 
                    "avg_hours": "Avg Hours", 
                    "count": "Resolved Count"
                })
            else:
                mttr_df = pd.DataFrame(columns=["Severity", "Avg Hours", "Resolved Count"])
            
            # 4. Heatmap Data
            heatmap_list = data.get("heatmap", [])
            if heatmap_list:
                heatmap_df = pd.DataFrame(heatmap_list)
            else:
                heatmap_df = pd.DataFrame(columns=["weekday", "hour", "incidents"])
            
            return trend_df, comp_df, mttr_df, heatmap_df
            
    except Exception as e:
        print(f"Enhanced Analytics Error: {e}")
    
    return (
        pd.DataFrame(columns=["date", "rolling_avg"]),
        pd.DataFrame(columns=["Severity", "Avg Hours", "Resolved Count"]),
        pd.DataFrame(columns=["component", "incidents"]),
        pd.DataFrame(columns=["weekday", "hour", "incidents"])
    )

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
    if not target_id:
        return pd.DataFrame(), pd.DataFrame(), gr.update(value="⚠️ Please enter a User ID.")
    try:
        # First check if user exists
        res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/exists",
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        if res.status_code == 200:
            if not res.json().get("exists", False):
                return pd.DataFrame(), pd.DataFrame(), gr.update(value=f"❌ User ID {int(target_id)} does not exist.")
        else:
            return pd.DataFrame(), pd.DataFrame(), gr.update(value="❌ Access Denied.")
        
        # Fetch incidents and chats
        inc_res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/incidents",
            headers={"Authorization": f"Bearer {token}"}
        )
        chat_res = requests.get(
            f"{BACKEND_URL}/admin/users/{int(target_id)}/chats",
            headers={"Authorization": f"Bearer {token}"}
        )
        df_inc = pd.DataFrame(inc_res.json()) if inc_res.status_code == 200 else pd.DataFrame()
        df_chat = pd.DataFrame(chat_res.json()) if chat_res.status_code == 200 else pd.DataFrame()
        return df_inc, df_chat, gr.update(value=f"✅ Loaded activity for User ID: {int(target_id)}")
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), gr.update(value=f"❌ Error: {e}")

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