import gradio as gr
import requests
import json
import sqlite3
import pandas as pd

BACKEND_URL = "http://localhost:8000"

def get_stats():
    try:
        conn = sqlite3.connect("data/incidents.db")
        c = conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        resolved = c.execute("SELECT COUNT(*) FROM incidents WHERE status='resolved'").fetchone()[0]
        critical = c.execute("SELECT COUNT(*) FROM incidents WHERE anomaly_description LIKE '%CRITICAL%'").fetchone()[0]
        conn.close()
        return total, resolved, critical
    except:
        return 0, 0, 0

def get_incident_history():
    try:
        conn = sqlite3.connect("data/incidents.db")
        c = conn.cursor()
        incidents = c.execute("""
            SELECT id, timestamp, status, anomaly_description 
            FROM incidents 
            ORDER BY id DESC 
            LIMIT 15
        """).fetchall()
        conn.close()
        
        data = []
        for inc in incidents:
            try:
                anomaly = json.loads(inc[3])
                data.append({
                    "ID": inc[0],
                    "Time": inc[1][:19] if inc[1] else "N/A",
                    "Status": inc[2],
                    "Type": anomaly.get("anomaly_type", "N/A"),
                    "Severity": anomaly.get("severity", "N/A"),
                    "Component": anomaly.get("affected_component", "N/A")
                })
            except:
                pass
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    except:
        return pd.DataFrame()

def diagnose_logs(logs_text):
    if not logs_text.strip():
        return "", "", "", gr.update(value=get_incident_history())
    
    logs = [line.strip() for line in logs_text.split("\n") if line.strip()]
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/diagnose",
            json={"logs": logs},
            timeout=300
        )
        
        if response.status_code != 200:
            return f'<div style="color: red; padding: 20px; background: #f8d7da; border-radius: 4px;">❌ Backend error: {response.status_code}</div>', "", "", gr.update(value=get_incident_history())
        
        result = response.json()
        print(f"DEBUG: Response = {result}")  # Debug print
        
        # Check if anomaly detected
        anomaly = result.get("anomaly", {})
        anomaly_detected = anomaly.get("anomaly_detected", False)
        
        print(f"DEBUG: anomaly_detected = {anomaly_detected}")  # Debug
        
        if not anomaly_detected:
            return (
                '<div style="padding: 20px; background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px;"><h3 style="color: #155724;">✅ System Healthy</h3><p>No anomalies detected in the provided logs.</p></div>',
                "",
                "",
                gr.update(value=get_incident_history())
            )
        
        # ANOMALY
        anomaly_html = f'''<div style="padding: 20px; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; border-radius: 8px; box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);">
<h3 style="margin-top: 0;">🔴 ANOMALY DETECTED</h3>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
    <div><strong>Type:</strong> <code>{anomaly.get('anomaly_type', 'N/A')}</code></div>
    <div><strong>Severity:</strong> <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-weight: bold;">{anomaly.get('severity', 'N/A')}</span></div>
    <div><strong>Component:</strong> <code>{anomaly.get('affected_component', 'N/A')}</code></div>
    <div><strong>Description:</strong> {anomaly.get('description', 'N/A')}</div>
</div>
</div>'''
        
        # ROOT CAUSE
        root_cause = result.get("root_cause", {})
        root_cause_html = f'''<div style="padding: 20px; background: linear-gradient(135deg, #ffa502 0%, #ff8c00 100%); color: white; border-radius: 8px; box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);">
<h3 style="margin-top: 0;">🔍 ROOT CAUSE ANALYSIS</h3>
<div style="margin-top: 15px;">
    <div style="margin-bottom: 12px;"><strong>🎯 Root Cause:</strong><br>{root_cause.get('root_cause', 'N/A')}</div>
    <div style="margin-bottom: 12px;"><strong>📊 Confidence:</strong> <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">{root_cause.get('confidence', 0):.1%}</span></div>
    <div style="margin-bottom: 12px;"><strong>📝 Evidence:</strong><br><code style="background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px; display: block; margin-top: 5px;">{chr(10).join(root_cause.get('evidence', [])[:2])}</code></div>
    <div><strong>⚠️ Contributing Factors:</strong><br>{', '.join(root_cause.get('contributing_factors', []))}</div>
</div>
</div>'''
        
        # REMEDIATION
        remediation = result.get("remediation", {})
        escalation_badge = '⚠️ YES' if remediation.get('escalation_needed') else '✅ NO'
        remediation_html = f'''<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
<h3 style="margin-top: 0;">⚙️ REMEDIATION PLAN</h3>
<div style="margin-top: 15px;">
    <div style="margin-bottom: 12px;"><strong>🚀 Immediate Actions:</strong><br>{', '.join(remediation.get('immediate_actions', [])[:2])}</div>
    <div style="margin-bottom: 12px;"><strong>🔧 Automated Actions:</strong><br>{', '.join([a.get('action', '') for a in remediation.get('automated_actions', [])[:2]])}</div>
    <div style="margin-bottom: 12px;"><strong>⏱️ Recovery Time:</strong> <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-weight: bold;">{remediation.get('estimated_recovery_time', 'N/A')}</span></div>
    <div style="margin-bottom: 12px;"><strong>🚨 Escalation Needed:</strong> {escalation_badge}</div>
    <div><strong>🛡️ Prevention Measures:</strong><br>{', '.join(remediation.get('prevention_measures', [])[:2])}</div>
</div>
</div>'''
        
        return anomaly_html, root_cause_html, remediation_html, gr.update(value=get_incident_history())
        
    except Exception as e:
        print(f"ERROR: {e}")  # Debug
        return f'<div style="color: red; padding: 20px; background: #f8d7da; border-radius: 4px;">❌ Error: {str(e)}</div>', "", "", gr.update(value=get_incident_history())

total, resolved, critical = get_stats()

with gr.Blocks(title="AGENTS_026") as demo:
    gr.Markdown("""
    # 🔧 AGENTS_026: Autonomous Incident Diagnosis & Resolution
    **Real-time AI-powered incident detection, root cause analysis, and remediation recommendations**
    """)
    
    with gr.Row():
        with gr.Column(scale=1, min_width=150):
            gr.Markdown(f"<div style='text-align: center; padding: 20px; background: rgba(255, 107, 107, 0.1); border-radius: 8px; border-left: 4px solid #ff6b6b;'><h2 style='margin: 0;'>{total}</h2><p style='margin: 0; opacity: 0.8;'>Total Incidents</p></div>")
        with gr.Column(scale=1, min_width=150):
            gr.Markdown(f"<div style='text-align: center; padding: 20px; background: rgba(40, 167, 69, 0.1); border-radius: 8px; border-left: 4px solid #28a745;'><h2 style='margin: 0;'>{resolved}</h2><p style='margin: 0; opacity: 0.8;'>Resolved</p></div>")
        with gr.Column(scale=1, min_width=150):
            gr.Markdown(f"<div style='text-align: center; padding: 20px; background: rgba(255, 193, 7, 0.1); border-radius: 8px; border-left: 4px solid #ffc107;'><h2 style='margin: 0;'>{critical}</h2><p style='margin: 0; opacity: 0.8;'>Critical</p></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Submit System Logs")
            logs_input = gr.Textbox(
                label="System Logs",
                placeholder="[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%\n[CRITICAL] service unavailable",
                lines=12
            )
            diagnose_btn = gr.Button("🚀 Analyze Incident", size="lg", variant="primary", scale=1)
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Recent Incidents")
            history_table = gr.Dataframe(
                value=get_incident_history(),
                interactive=False
            )
    
    with gr.Row():
        with gr.Column():
            anomaly_output = gr.HTML("<p style='color: #999;'>Results will appear here...</p>")
        with gr.Column():
            root_cause_output = gr.HTML("<p style='color: #999;'>Results will appear here...</p>")
        with gr.Column():
            remediation_output = gr.HTML("<p style='color: #999;'>Results will appear here...</p>")
    
    diagnose_btn.click(
        diagnose_logs,
        inputs=logs_input,
        outputs=[anomaly_output, root_cause_output, remediation_output, history_table]
    )
    
    gr.Examples(
        [
            "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
            "[CRITICAL] database connection timeout\n[ERROR] query failed\n[WARNING] 10 failed queries",
            "[CRITICAL] service unavailable\n[ERROR] api down\n[WARNING] high latency detected",
            "[ERROR] disk usage: 98%\n[CRITICAL] no space left\n[WARNING] eviction in progress",
        ],
        inputs=logs_input,
        label="📌 Example Incidents - Click to Load"
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
