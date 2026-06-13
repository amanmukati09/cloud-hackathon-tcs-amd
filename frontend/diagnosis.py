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
        return "", "📂 Upload .log or .txt files to auto-fill the text area"
    
    try:
        all_lines = []
        file_names = []
        
        # file_paths can be a single string or list
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        for file_path in file_paths:
            if not file_path:
                continue
                
            file_names.append(file_path.split('/')[-1])
            
            # Read the file locally (Gradio saves uploaded files to temp location)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                all_lines.extend(lines)
        
        if not all_lines:
            return "", "❌ No valid log lines found in uploaded files"
        
        log_text = "\n".join(all_lines[:5000])  # Limit to 5000 lines
        info = f"✅ Loaded {len(file_names)} file(s): {', '.join(file_names[:3])} | {len(all_lines)} lines total"
        
        return log_text, info
        
    except Exception as e:
        return "", f"❌ Error reading file: {str(e)}"

def auto_remediate(logs_text, auto_execute, token):
    """Run the full agentic workflow."""
    if not token or not logs_text.strip():
        return gr.update(), gr.update(), gr.update(), gr.update(), pd.DataFrame()
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/workflow/auto-remediate",
            json={
                "logs": [line.strip() for line in logs_text.split('\n') if line.strip()],
                "auto_execute": auto_execute
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            
            # Format workflow steps for display
            steps_html = "### 🤖 Autonomous Workflow\n\n"
            for step in data.get("workflow_steps", []):
                icon = "✅" if step["status"] == "completed" else "⏳" if step["status"] == "running" else "❌"
                steps_html += f"{icon} **Step {step['step']}:** {step['name']}\n"
                
                # Show command results
                if "commands" in step:
                    for cmd in step["commands"]:
                        status = "✅" if cmd["success"] else "❌"
                        steps_html += f"  {status} `{cmd['command']}` → {cmd['output'][:100]}\n"
                
                # Show execution results
                if "results" in step:
                    for res in step["results"]:
                        status = "✅" if res["success"] else "❌"
                        steps_html += f"  {status} `{res['command']}` → {res['output'][:100]}\n"
                
                steps_html += "\n"
            
            # Get diagnosis results
            anomaly = format_diagnosis(data) if data.get("anomaly_detected") else (
                "### ✅ System Normal", "*N/A*", "*N/A*"
            )
            
            return (
                gr.update(value=anomaly[0]),
                gr.update(value=anomaly[1]),
                gr.update(value=anomaly[2]),
                gr.update(value=steps_html),
                fetch_history(token)
            )
    except Exception as e:
        return gr.update(), gr.update(), gr.update(), gr.update(value=f"❌ Error: {e}"), gr.update()
    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()


def generate_rca_tree(logs_text, token):
    """Generate and display RCA tree."""
    if not token or not logs_text.strip():
        return gr.update(value="*Paste logs and click 'RCA Tree' to analyze*")
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/diagnose/rca-tree",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            return gr.update(value=data.get("html", "*No tree generated*"))
        else:
            return gr.update(value="*Failed to generate RCA tree*")
    except Exception as e:
        return gr.update(value=f"*Error: {str(e)}*")

def generate_code_fix(logs_text, token):
    """Generate code fixes for an incident."""
    if not token or not logs_text.strip():
        return "<p style='color:#94a3b8;text-align:center;'>Paste logs and click 'Code Fix' to generate patches</p>"
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/diagnose/code-fix",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if res.status_code == 200:
            data = res.json()
            return data.get("html", "*No fixes generated*")
        else:
            return "<p style='color:#ef4444;'>Failed to generate code fixes</p>"
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"

def async_diagnose(logs_text, token):
    """Submit diagnosis to background worker."""
    if not token or not logs_text.strip():
        return "Paste logs and click 'Async Analyze'"
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/async/diagnose",
            json={"logs": [line.strip() for line in logs_text.split('\n') if line.strip()]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            task_id = data['task_id']
            return f"✅ Task #{task_id} queued! Processing in background..."
    except:
        pass
    return "❌ Failed to queue task"

def check_async_task(task_id, token):
    """Check status of a background task."""
    if not task_id or not token:
        return "No task to check"
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/async/task/{int(task_id)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            status = data.get("status", "unknown")
            result = data.get("result", "")
            
            if status == "completed":
                return f"✅ **Task #{task_id} Complete!**\n\n```json\n{result[:500]}\n```"
            elif status == "failed":
                return f"❌ **Task #{task_id} Failed:** {result}"
            elif status == "running":
                return f"⏳ **Task #{task_id} Running...**"
            else:
                return f"📋 **Task #{task_id} Pending...**"
    except:
        pass
    return "Failed to check task status"
def analyze_image(file, token):
    """Upload and analyze an image for incidents. Returns (html, extracted_text)."""
    if not file or not token:
        return "<p style='color:#94a3b8;text-align:center;'>Upload a screenshot to analyze</p>", ""
    
    try:
        with open(file.name, "rb") as f:
            files = {"file": (file.name.split("/")[-1], f, "image/png")}
            res = requests.post(
                f"{BACKEND_URL}/diagnose/image",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
                timeout=60
            )
        
        if res.status_code == 200:
            data = res.json()
            if not data.get("text_found"):
                return "<p style='color:#f59e0b;text-align:center;'>⚠️ No text found in image</p>", ""
            
            sev_colors = {"CRITICAL": "#ef4444", "HIGH": "#f59e0b", "MEDIUM": "#3b82f6", "LOW": "#10b981", "UNKNOWN": "#6b7280"}
            sev = data.get("severity", "UNKNOWN")
            sev_color = sev_colors.get(sev, "#6b7280")
            
            extracted = data.get("extracted_text", "")
            html = f"""
            <div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:16px;">
                <h3>📸 Image Analysis</h3>
                <p><strong>Severity:</strong> <span style="color:{sev_color};font-weight:bold;">{sev}</span></p>
                <p><strong>Summary:</strong> {data.get('summary', 'N/A')}</p>
                <p><strong>Affected System:</strong> {data.get('affected_system', 'N/A')}</p>
                <p><strong>Recommended:</strong> {data.get('recommended_action', 'N/A')}</p>
                <p style="font-size:0.85em;color:#94a3b8;">📋 Extracted text has been placed in the logs area below. Click <b>Analyze Logs</b> to diagnose.</p>
            </div>
            """
            return html, extracted
        else:
            return f"<p style='color:#ef4444;'>Error: {res.status_code}</p>", ""
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>", ""