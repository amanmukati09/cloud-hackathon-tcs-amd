import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL, format_diagnosis

def fetch_history(token):
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={"id":"ID","timestamp":"Date","raw_logs":"Logs","anomaly":"Anomaly Found","root_cause":"Root Cause","remediation":"Remediation","status":"Status"})
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            if "Status" in df.columns:
                df["Status"] = df["Status"].apply(lambda x: "✅ RESOLVED" if x == "resolved" else "🟢 OPEN" if x == "open" else x)
            return df[["ID", "Date", "Logs", "Anomaly Found", "Root Cause", "Remediation", "Status"]]
    except: pass
    return pd.DataFrame()

def diagnose_logs(logs_text, token):
    if not token or not logs_text.strip(): 
        return gr.update(), gr.update(), gr.update(), gr.update()
    try:
        res = requests.post(
            f"{BACKEND_URL}/diagnose", 
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]}, 
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            if not data.get("anomaly_detected", True):
                return (
                    gr.update(value="### ✅ System Normal\n\nNo anomalies detected in the provided logs."),
                    gr.update(value="*N/A*"), gr.update(value="*N/A*"), fetch_history(token)
                )
            gr.Info("⚡ Analysis Complete!")
            anomaly, root_cause, remediation = format_diagnosis(data)
            return gr.update(value=anomaly), gr.update(value=root_cause), gr.update(value=remediation), fetch_history(token)
        else:
            error_msg = f"❌ Backend error: {res.status_code}"
            return gr.update(value=error_msg), gr.update(value=error_msg), gr.update(value=error_msg), gr.update()
    except Exception as e:
        error_msg = f"❌ Connection Error: {str(e)}"
        return gr.update(value=error_msg), gr.update(value=error_msg), gr.update(value=error_msg), gr.update()

def search_similar_incidents(logs_text, token):
    if not token or not logs_text.strip():
        return pd.DataFrame(), gr.update(visible=False), gr.update(value="")
    try:
        res = requests.post(
            f"{BACKEND_URL}/incidents/similar",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            incidents = data.get("similar_incidents", [])
            if incidents:
                df = pd.DataFrame(incidents)
                df = df.rename(columns={
                    "incident_id": "Incident ID", "similarity": "Similarity %",
                    "date": "Date", "anomaly": "Anomaly", "root_cause": "Root Cause", "status": "Status"
                })
                df["Status"] = df["Status"].apply(lambda x: "🟢 OPEN" if x == "open" else "✅ RESOLVED" if x == "resolved" else x)
                return df, gr.update(visible=True), gr.update(value=f"✅ Found **{len(df)}** similar incident(s)!")
            else:
                return pd.DataFrame(), gr.update(visible=True), gr.update(value="🔍 No similar incidents found.")
    except Exception as e:
        print(f"Similarity search error: {e}")
    return pd.DataFrame(), gr.update(visible=False), gr.update(value="")

def upload_log_files(file_paths, token):
    """Handle file upload and return parsed contents."""
    if not file_paths or not token:
        return gr.update(value=""), gr.update(value="")
    
    try:
        all_lines = []
        file_names = []
        
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        file_paths = [f for f in file_paths if f and str(f).strip()]
        
        if not file_paths:
            return gr.update(value=""), gr.update(value="")
        
        for file_path in file_paths:
            fname = str(file_path).split('/')[-1]
            file_names.append(fname)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    all_lines.extend(lines)
            except:
                continue
        
        if not all_lines:
            return gr.update(value=""), gr.update(value="❌ No readable content found")
        
        log_text = "\n".join(all_lines[:5000])
        info = f"✅ {len(file_names)} file(s), {len(all_lines)} lines"
        
        return gr.update(value=log_text), gr.update(value=info)
        
    except Exception as e:
        return gr.update(value=""), gr.update(value=f"❌ Error: {str(e)[:80]}")

def auto_remediate(logs_text, auto_execute, token):
    if not token or not logs_text.strip():
        return gr.update(), gr.update(), gr.update(), gr.update(), pd.DataFrame()
    try:
        res = requests.post(
            f"{BACKEND_URL}/workflow/auto-remediate",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()], "auto_execute": auto_execute},
            headers={"Authorization": f"Bearer {token}"}, timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            steps_html = "### 🤖 Autonomous Workflow\n\n"
            for step in data.get("workflow_steps", []):
                icon = "✅" if step["status"] == "completed" else "⏳" if step["status"] == "running" else "❌"
                steps_html += f"{icon} **Step {step['step']}:** {step['name']}\n"
                if "commands" in step:
                    for cmd in step["commands"]:
                        status = "✅" if cmd["success"] else "❌"
                        steps_html += f"  {status} `{cmd['command']}` → {cmd['output'][:100]}\n"
                if "results" in step:
                    for res in step["results"]:
                        status = "✅" if res["success"] else "❌"
                        steps_html += f"  {status} `{res['command']}` → {res['output'][:100]}\n"
                steps_html += "\n"
            
            anomaly = format_diagnosis(data) if data.get("anomaly_detected") else ("### ✅ System Normal", "*N/A*", "*N/A*")
            return (
                gr.update(value=anomaly[0]), gr.update(value=anomaly[1]), gr.update(value=anomaly[2]),
                gr.update(value=steps_html), fetch_history(token)
            )
    except Exception as e:
        return gr.update(), gr.update(), gr.update(), gr.update(value=f"❌ Error: {e}"), gr.update()
    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def generate_rca_tree(logs_text, token):
    if not token or not logs_text.strip():
        return gr.update(value="*Paste logs and click 'RCA Tree' to analyze*")
    try:
        res = requests.post(
            f"{BACKEND_URL}/diagnose/rca-tree",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"}, timeout=120
        )
        if res.status_code == 200:
            return gr.update(value=data.get("html", "*No tree generated*"))
    except Exception as e:
        return gr.update(value=f"*Error: {str(e)}*")

def generate_code_fix(logs_text, token):
    if not token or not logs_text.strip():
        return "<p style='color:#94a3b8;text-align:center;'>Paste logs and click 'Code Fix' to generate patches</p>"
    try:
        res = requests.post(
            f"{BACKEND_URL}/diagnose/code-fix",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"}, timeout=120
        )
        if res.status_code == 200:
            return data.get("html", "*No fixes generated*")
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"

def async_diagnose(logs_text, token):
    if not token or not logs_text.strip():
        return "Paste logs and click 'Async Analyze'"
    try:
        res = requests.post(
            f"{BACKEND_URL}/async/diagnose",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        if res.status_code == 200:
            return f"✅ Task #{res.json()['task_id']} queued! Processing in background..."
    except:
        pass
    return "❌ Failed to queue task"

def check_async_task(task_id, token):
    if not task_id or not token:
        return "No task to check"
    try:
        res = requests.get(f"{BACKEND_URL}/async/task/{int(task_id)}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            status = data.get("status", "unknown")
            result = data.get("result", "")
            if status == "completed": return f"✅ **Task #{task_id} Complete!**\n\n```json\n{result[:500]}\n```"
            elif status == "failed": return f"❌ **Task #{task_id} Failed:** {result}"
            elif status == "running": return f"⏳ **Task #{task_id} Running...**"
            else: return f"📋 **Task #{task_id} Pending...**"
    except: pass
    return "Failed to check task status"

def analyze_image(file, token):
    if not file or not token:
        return "<p style='color:#94a3b8;text-align:center;'>Upload a screenshot to analyze</p>", ""
    try:
        with open(file.name, "rb") as f:
            files = {"file": (file.name.split("/")[-1], f, "image/png")}
            res = requests.post(f"{BACKEND_URL}/diagnose/image", files=files, headers={"Authorization": f"Bearer {token}"}, timeout=120)
        if res.status_code == 200:
            data = res.json()
            sev = data.get("severity", "UNKNOWN")
            sev_color = {"CRITICAL":"#ef4444","HIGH":"#f59e0b","MEDIUM":"#3b82f6","LOW":"#10b981"}.get(sev,"#6b7280")
            logs = "\n".join(data.get("extracted_logs", []))
            html = f"""
            <div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:12px;">
                <h3>📸 AI Vision Analysis</h3>
                <p><strong>Severity:</strong> <span style="color:{sev_color};font-weight:bold;">{sev}</span></p>
                <p><strong>Affected:</strong> {data.get('affected_system','Unknown')}</p>
                <p><strong>Action:</strong> {data.get('recommended_action','N/A')}</p>
                <details><summary style="color:#38bdf8;cursor:pointer;">📝 Detailed Description</summary>
                <p style="color:#94a3b8;font-size:0.9em;">{data.get('description','')}</p></details>
            </div>"""
            return html, logs
        return f"<p style='color:#ef4444;'>Error: {res.status_code}</p>", ""
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>", ""