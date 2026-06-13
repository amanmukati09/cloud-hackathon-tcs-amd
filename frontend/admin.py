import gradio as gr
import requests
import pandas as pd
import re
from utils import BACKEND_URL
from datetime import datetime


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

def fetch_analytics(token, days=30, severity="ALL"):
    if not token:
        return (
            pd.DataFrame({"date": [], "Incidents": []}),
            pd.DataFrame({"Severity": [], "Count": []}),
            pd.DataFrame({"status": [], "Count": []})
        )
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/analytics/data?days={days}&severity={severity}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code != 200:
            return (
                pd.DataFrame({"date": [], "Incidents": []}),
                pd.DataFrame({"Severity": [], "Count": []}),
                pd.DataFrame({"status": [], "Count": []})
            )
        
        df = pd.DataFrame(res.json())
        if df.empty:
            return (
                pd.DataFrame({"date": [], "Incidents": []}),
                pd.DataFrame({"Severity": [], "Count": []}),
                pd.DataFrame({"status": [], "Count": []})
            )
        
        # Extract severity from description
        df['Severity'] = df['description'].apply(
            lambda x: re.search(r'Severity:\s*([A-Z]+)', str(x)).group(1)
            if re.search(r'Severity:\s*([A-Z]+)', str(x)) else 'UNKNOWN'
        )
        
        # Timeline chart
        timeline_df = df.groupby('date').size().reset_index(name='Incidents')
        timeline_df['date'] = pd.to_datetime(timeline_df['date'])
        timeline_df = timeline_df.sort_values('date')
        
        # If empty, create dummy row so chart renders
        if timeline_df.empty:
            timeline_df = pd.DataFrame({"date": [datetime.now()], "Incidents": [0]})
        
        # Severity chart - ensure all categories exist
        all_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        sev_df = df.groupby('Severity').size().reset_index(name='Count')
        
        # Fill missing severities with 0
        for sev in all_severities:
            if sev not in sev_df['Severity'].values:
                sev_df = pd.concat([sev_df, pd.DataFrame({"Severity": [sev], "Count": [0]})], ignore_index=True)
        
        sev_df = sev_df[sev_df['Severity'].isin(all_severities)]
        
        # Status chart - ensure both statuses exist
        status_df = df.groupby('status').size().reset_index(name='Count')
        status_df['status'] = status_df['status'].str.upper()
        
        for status in ["OPEN", "RESOLVED"]:
            if status not in status_df['status'].values:
                status_df = pd.concat([status_df, pd.DataFrame({"status": [status], "Count": [0]})], ignore_index=True)
        
        return timeline_df, sev_df, status_df
        
    except Exception as e:
        print(f"Analytics Error: {e}")
        return (
            pd.DataFrame({"date": [datetime.now()], "Incidents": [0]}),
            pd.DataFrame({"Severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"], "Count": [0, 0, 0, 0, 0]}),
            pd.DataFrame({"status": ["OPEN", "RESOLVED"], "Count": [0, 0]})
        )

        
        

def load_admin_data(token, days=30, severity="ALL"):
    """Load admin metrics with filtering."""
    if not token:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    try:
        m_res = requests.get(
            f"{BACKEND_URL}/admin/metrics?days={days}&severity={severity}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        u_res = requests.get(
            f"{BACKEND_URL}/admin/users?limit=50",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        users, incidents, chats, resolved, open_count, critical = 0, 0, 0, 0, 0, 0
        df = pd.DataFrame()
        
        if m_res.status_code == 200:
            m = m_res.json()
            users = m.get("users", 0)
            incidents = m.get("incidents", 0)
            chats = m.get("chats", 0)
            resolved = m.get("resolved", 0)
            open_count = m.get("open", 0)
            critical = m.get("critical", 0)
        
        if u_res.status_code == 200:
            data = u_res.json()
            if data:
                df = pd.DataFrame(data)
        
        return users, incidents, chats, resolved, open_count, critical, df
    except Exception as e:
        print(f"Admin data error: {e}")
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()

        

        
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

def get_rate_limit_status(token):
    """Check current rate limit status."""
    if not token:
        return "Not authenticated"
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/rate-limit-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            return f"Requests: {data['current']}/{data['limit']} per minute"
    except:
        pass
    return "Rate limit: 60 req/min"

def fetch_audit_logs(token):
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/admin/audit-logs?limit=50", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except:
        pass
    return pd.DataFrame()

def fetch_workspaces(token):
    if not token: return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/workspaces", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data:
                return pd.DataFrame(data)
    except: pass
    return pd.DataFrame()

def create_workspace(name, description, token):
    if not name.strip() or not token: return pd.DataFrame()
    try:
        res = requests.post(f"{BACKEND_URL}/workspaces", json={"name": name, "description": description}, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            gr.Info(f"Workspace '{name}' created!")
    except: pass
    return fetch_workspaces(token)

def fetch_workspaces(token):
    """Fetch all workspaces for the current user."""
    if not token:
        return pd.DataFrame(), []
    try:
        res = requests.get(
            f"{BACKEND_URL}/workspaces",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df = df[["id", "name", "description", "role", "member_count", "created_at"]]
                df.columns = ["ID", "Name", "Description", "Role", "Members", "Created"]
                choices = [f"{row['ID']} - {row['Name']}" for _, row in df.iterrows()]
                return df, choices
    except:
        pass
    return pd.DataFrame(), []

def create_workspace(name, description, token):
    """Create a new workspace."""
    if not name or not name.strip() or not token:
        return fetch_workspaces(token)
    try:
        res = requests.post(
            f"{BACKEND_URL}/workspaces",
            json={"name": name.strip(), "description": description.strip() if description else ""},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            gr.Info(f"✅ Workspace '{name.strip()}' created!")
        else:
            gr.Warning(f"❌ {res.json().get('detail', 'Failed')}")
    except Exception as e:
        gr.Warning(f"❌ Error: {e}")
    return fetch_workspaces(token)

def delete_workspace(workspace_id, token):
    """Delete a workspace (owner only)."""
    if not workspace_id or not token:
        return fetch_workspaces(token)
    try:
        res = requests.delete(
            f"{BACKEND_URL}/workspaces/{int(workspace_id)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            gr.Info("✅ Workspace deleted!")
        else:
            gr.Warning("❌ Failed to delete workspace")
    except:
        pass
    return fetch_workspaces(token)

def fetch_workspace_members(workspace_id, token):
    """Fetch members of a workspace."""
    if not workspace_id or not token:
        return pd.DataFrame()
    try:
        res = requests.get(
            f"{BACKEND_URL}/workspaces/{int(workspace_id)}/members",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df = df[["user_id", "name", "email", "role", "joined_at"]]
                df.columns = ["User ID", "Name", "Email", "Role", "Joined"]
                return df
    except:
        pass
    return pd.DataFrame()

def add_workspace_member(workspace_id, user_id, token):
    """Add a member to a workspace."""
    if not workspace_id or not user_id or not token:
        return fetch_workspace_members(workspace_id, token), ""
    try:
        res = requests.post(
            f"{BACKEND_URL}/workspaces/{int(workspace_id)}/members",
            json={"user_id": int(user_id), "role": "member"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            return fetch_workspace_members(workspace_id, token), f"✅ User {user_id} added!"
        else:
            return fetch_workspace_members(workspace_id, token), f"❌ {res.json().get('detail', 'Failed')}"
    except Exception as e:
        return fetch_workspace_members(workspace_id, token), f"❌ Error: {e}"

def fetch_api_keys(token):
    """Fetch user's API keys."""
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(
            f"{BACKEND_URL}/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                return df
    except:
        pass
    return pd.DataFrame()

def create_api_key(name, expires_days, token):
    """Create a new API key."""
    if not name.strip() or not token:
        return pd.DataFrame(), ""
    try:
        payload = {"name": name.strip()}
        if expires_days and int(expires_days) > 0:
            payload["expires_in_days"] = int(expires_days)
        
        res = requests.post(
            f"{BACKEND_URL}/api-keys",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            key = data.get("key", "")
            df = fetch_api_keys(token)
            return df, f"🔑 Your API Key (copy now - shown only once!):\n\n`{key}`"
        else:
            return fetch_api_keys(token), f"❌ Failed: {res.json().get('detail', 'Error')}"
    except Exception as e:
        return fetch_api_keys(token), f"❌ Error: {e}"

def revoke_api_key(key_id, token):
    """Revoke an API key."""
    if not key_id or not token:
        return fetch_api_keys(token)
    try:
        res = requests.delete(
            f"{BACKEND_URL}/api-keys/{int(key_id)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            gr.Info("✅ API key revoked!")
        else:
            gr.Warning("❌ Failed to revoke")
    except:
        pass
    return fetch_api_keys(token)

def fetch_dashboard_summary(token, days=30, severity="ALL"):
    if not token:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        res = requests.get(
            f"{BACKEND_URL}/dashboard/summary?days={days}&severity={severity}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            metrics = data.get("metrics", {})
            timeline = data.get("timeline", {})
            
            # Create metrics table
            metrics_df = pd.DataFrame([{
                "Metric": "Total Incidents", "Value": metrics.get("total_incidents", 0)
            }, {
                "Metric": "Resolved", "Value": f"{metrics.get('resolved', 0)} ({metrics.get('resolution_rate', 0)}%)"
            }, {
                "Metric": "Open", "Value": metrics.get("open", 0)
            }, {
                "Metric": "Critical", "Value": metrics.get("critical", 0)
            }, {
                "Metric": "MTTR", "Value": f"{metrics.get('mttr_hours', 0)} hours"
            }])
            
            # Create timeline dataframe
            timeline_df = pd.DataFrame({
                "date": timeline.get("dates", []),
                "incidents": timeline.get("counts", [])
            })
            
            return metrics_df, timeline_df, data.get("period", "")
    except:
        pass
    return pd.DataFrame(), pd.DataFrame(), ""

def fetch_recent_activity(token):
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(
            f"{BACKEND_URL}/dashboard/recent-activity",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data:
                return pd.DataFrame(data)
    except:
        pass
    return pd.DataFrame()

def generate_knowledge_base(token):
    """Generate knowledge base articles."""
    if not token:
        return "<p style='color:#94a3b8;text-align:center;'>Login as admin to generate</p>", pd.DataFrame()
    try:
        res = requests.post(
            f"{BACKEND_URL}/admin/knowledge-base/generate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            articles = data.get("articles", [])
            if articles:
                df = pd.DataFrame(articles)
                df = df[["title", "category", "difficulty", "estimated_time", "source_incident_id"]]
                df.columns = ["Title", "Category", "Difficulty", "Est. Time", "Source ID"]
                return f"✅ Generated {len(articles)} articles from resolved incidents!", df
            return "No resolved incidents found to generate articles.", pd.DataFrame()
    except Exception as e:
        return f"❌ Error: {str(e)}", pd.DataFrame()

        
def search_knowledge_base(query, token):
    """Search knowledge base."""
    if not query or not query.strip() or not token:
        return "<p style='color:#94a3b8;text-align:center;'>Type a query and click Search</p>"
    try:
        res = requests.get(
            f"{BACKEND_URL}/admin/knowledge-base/search?query={query.strip()}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            articles = data.get("articles", [])
            if articles:
                html = f"<h3>🔍 Found {len(articles)} results for '{query}'</h3>"
                for a in articles:
                    diff_color = {"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"}.get(
                        a.get("difficulty", "Intermediate"), "#f59e0b"
                    )
                    tags_html = " ".join([
                        f'<span style="background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 8px;border-radius:10px;font-size:0.75em;">{tag}</span>' 
                        for tag in a.get("tags", [])
                    ])
                    
                    html += f"""
                    <div style="background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:16px;margin:8px 0;">
                        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                            <h3 style="color:#f8fafc;margin:0;">📄 {a.get('title', 'Untitled')}</h3>
                            <span style="color:{diff_color};background:{diff_color}15;padding:3px 10px;border-radius:12px;font-size:0.75em;font-weight:600;">{a.get('difficulty', 'N/A')}</span>
                        </div>
                        <div style="margin:8px 0;">{tags_html}</div>
                        <div style="color:#94a3b8;font-size:0.85em;">📂 Category: {a.get('category', 'General')}</div>
                        <hr style="border-color:rgba(255,255,255,0.05);">
                        <h4 style="color:#ef4444;">🔴 Symptoms</h4>
                        <p style="color:#94a3b8;">{a.get('symptoms', 'N/A')}</p>
                        <h4 style="color:#f59e0b;">🔍 Root Cause</h4>
                        <p style="color:#94a3b8;">{a.get('root_cause', 'N/A')}</p>
                        <h4 style="color:#10b981;">✅ Solution</h4>
                        <p style="color:#94a3b8;">{a.get('solution', 'N/A')}</p>
                        <h4 style="color:#38bdf8;">🛡️ Prevention</h4>
                        <p style="color:#94a3b8;">{a.get('prevention', 'N/A')}</p>
                        <div style="color:#64748b;font-size:0.75em;margin-top:8px;">⏱️ Est. time: {a.get('estimated_time', 'N/A')} | Source: Incident #{a.get('source_incident_id', '?')}</div>
                    </div>
                    """
                return html
            return f"<p style='color:#94a3b8;text-align:center;'>No articles found for '{query}'. Try different keywords.</p>"
        else:
            return f"<p style='color:#ef4444;'>Backend error: {res.status_code}</p>"
    except Exception as e:
        return f"<p style='color:#ef4444;'>Search failed: {str(e)}</p>"

def fetch_recent_activity(token, limit=10):
    """Get recent incident activity."""
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(
            f"{BACKEND_URL}/dashboard/recent-activity?limit={limit}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                # Keep relevant columns
                cols = [c for c in ["title", "action", "severity", "time_ago", "timestamp"] if c in df.columns]
                return df[cols]
    except:
        pass
    return pd.DataFrame()