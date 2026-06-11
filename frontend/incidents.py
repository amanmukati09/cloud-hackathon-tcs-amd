import gradio as gr
import requests
import pandas as pd
from datetime import datetime
from utils import BACKEND_URL
from diagnosis import fetch_history

def resolve_incident(incident_id, resolution_notes, token):
    if not incident_id or not token:
        return gr.update(), fetch_history(token)
    try:
        res = requests.post(
            f"{BACKEND_URL}/incidents/{int(incident_id)}/resolve",
            json={"resolution_notes": resolution_notes},
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            gr.Info(f"✅ Incident #{int(incident_id)} resolved! (MTTR: {data.get('resolution_time_hours', 0)} hours)")
        else:
            gr.Warning(f"❌ Error: {res.json().get('detail', 'Unknown error')}")
    except Exception as e:
        gr.Warning(f"❌ Connection Error: {e}")
    return gr.update(value=""), fetch_history(token)

def get_incident_details(incident_id, token):
    if not incident_id or not token:
        return gr.update(value="*Select an incident to view details*")
    try:
        res = requests.get(
            f"{BACKEND_URL}/incidents/{int(incident_id)}/details",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            status_color = "#10b981" if data['status'] == 'resolved' else "#f59e0b"
            html = f"""
<div style="padding: 10px;">
<h3 style="color: {status_color};">Incident #{data['id']}</h3>
<p><strong>Date:</strong> {data['timestamp']}</p>
<p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{data['status'].upper()}</span></p>
<hr>
<h4>📋 Raw Logs:</h4>
<pre style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; max-height: 150px; overflow-y: auto;">{data['raw_logs']}</pre>
<h4>🔴 Anomaly:</h4><p>{data['anomaly']}</p>
<h4>🔍 Root Cause:</h4><p>{data['root_cause']}</p>
<h4>⚙️ Remediation:</h4><p>{data['remediation']}</p>
"""
            if data.get('resolution_notes'):
                html += f"<h4>📝 Resolution Notes:</h4><p>{data['resolution_notes']}</p>"
            if data.get('resolved_at'):
                html += f"<h4>✅ Resolved At:</h4><p>{data['resolved_at']}</p>"
            html += "</div>"
            return gr.update(value=html)
    except: pass
    return gr.update(value="*Error loading incident details*")

def export_csv(token):
    if not token: return gr.update(visible=False)
    try:
        res = requests.get(f"{BACKEND_URL}/incidents/export/csv", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            filename = f"aegis_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'wb') as f: f.write(res.content)
            return gr.update(value=filename, visible=True)
        else: gr.Warning("❌ Failed to export CSV")
    except Exception as e: gr.Warning(f"❌ Export Error: {e}")
    return gr.update(visible=False)

def export_incident_pdf(incident_id, token):
    if not incident_id or not token: return gr.update(visible=False)
    try:
        res = requests.get(f"{BACKEND_URL}/incidents/{int(incident_id)}/export/pdf", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            filename = f"aegis_incident_{int(incident_id)}_report.pdf"
            with open(filename, 'wb') as f: f.write(res.content)
            return gr.update(value=filename, visible=True)
        else: gr.Warning("❌ Failed to export PDF")
    except Exception as e: gr.Warning(f"❌ Export Error: {e}")
    return gr.update(visible=False)