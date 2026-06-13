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

def delete_incident(incident_id, token):
    """Delete an incident by ID."""
    if not incident_id or not token:
        return fetch_history(token)
    try:
        res = requests.delete(
            f"{BACKEND_URL}/incidents/{int(incident_id)}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            gr.Info(f"✅ Incident {int(incident_id)} deleted")
        else:
            gr.Warning(f"❌ {res.json().get('detail', 'Delete failed')}")
    except Exception as e:
        gr.Warning(f"❌ Error: {e}")
    return fetch_history(token)

def generate_runbook(incident_id, token):
    """Generate a runbook from an incident."""
    if not incident_id or not token:
        return "<p style='color:#94a3b8;text-align:center;'>Select a resolved incident and click 'Generate Runbook'</p>"
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/incidents/{int(incident_id)}/runbook",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        if res.status_code == 200:
            data = res.json()
            return data.get("html", "*No runbook generated*")
        else:
            return "<p style='color:#ef4444;'>Failed to generate runbook</p>"
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"

def fetch_incident_timeline(incident_id, token):
    """Fetch and render incident timeline."""
    if not incident_id or not token:
        return "<p style='color:#94a3b8;text-align:center;'>Select an incident to view timeline</p>"
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/incidents/{int(incident_id)}/timeline",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            events = data.get("timeline", [])
            
            if not events:
                return "<p style='color:#94a3b8;text-align:center;'>No timeline data available</p>"
            
            html = '<div style="position:relative;padding-left:30px;">'
            
            for i, event in enumerate(events):
                # Connector line
                if i < len(events) - 1:
                    html += '<div style="position:absolute;left:11px;top:20px;width:2px;height:60px;background:rgba(255,255,255,0.1);"></div>'
                
                # Event dot + card
                html += f"""
                <div style="position:relative;margin-bottom:16px;">
                    <div style="position:absolute;left:-22px;top:4px;width:14px;height:14px;border-radius:50%;background:{event['color']};border:2px solid rgba(255,255,255,0.2);"></div>
                    <div style="background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px 14px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                            <span style="font-weight:600;color:#f8fafc;">{event['icon']} {event['title']}</span>
                            <span style="font-size:0.7em;color:#64748b;">{event['time']}</span>
                        </div>
                        <p style="color:#94a3b8;font-size:0.85em;margin:0;">{event.get('description', '')[:200]}</p>
                    </div>
                </div>
                """
            
            html += '</div>'
            
            # Status badge
            status = data.get("status", "open")
            status_color = "#10b981" if status == "resolved" else "#f59e0b"
            status_icon = "✅" if status == "resolved" else "🟢"
            html += f"""
            <div style="margin-top:12px;padding:8px 12px;background:rgba(30,41,59,0.6);border-radius:8px;text-align:center;">
                <span style="color:{status_color};font-weight:600;">{status_icon} Status: {status.upper()}</span>
            </div>
            """
            
            return html
        
        return f"<p style='color:#ef4444;'>Error: {res.status_code}</p>"
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"