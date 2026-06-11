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