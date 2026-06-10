import gradio as gr
import requests
import json

BACKEND_URL = "http://localhost:8000"

def diagnose_logs(logs_text):
    """Send logs to backend and get diagnosis"""
    if not logs_text.strip():
        return "Please enter logs", "", ""
    
    logs = [line.strip() for line in logs_text.split("\n") if line.strip()]
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/diagnose",
            json={"logs": logs},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if not result.get("anomaly_detected"):
                return "✅ No anomalies detected", "", ""
            
            anomaly_text = json.dumps(result["anomaly"], indent=2)
            root_cause_text = json.dumps(result["root_cause"], indent=2)
            remediation_text = json.dumps(result["remediation"], indent=2)
            
            return anomaly_text, root_cause_text, remediation_text
        else:
            return "❌ Backend error", "", ""
    except Exception as e:
        return f"❌ Error: {str(e)}", "", ""

# Create Gradio interface
with gr.Blocks(title="AGENTS_026: Incident Diagnosis") as demo:
    gr.Markdown("# 🔧 Autonomous Incident Diagnosis & Resolution")
    gr.Markdown("Submit system logs to detect anomalies, analyze root causes, and get remediation suggestions.")
    
    with gr.Row():
        logs_input = gr.Textbox(
            label="📝 System Logs",
            placeholder="[INFO] nginx started\n[ERROR] worker crashed\n[WARNING] memory: 90%",
            lines=8
        )
    
    diagnose_btn = gr.Button("🚀 Diagnose Incident", size="lg")
    
    with gr.Row():
        with gr.Column():
            anomaly_output = gr.Textbox(label="🔴 Anomaly Detected", lines=6)
        with gr.Column():
            root_cause_output = gr.Textbox(label="🔍 Root Cause", lines=6)
        with gr.Column():
            remediation_output = gr.Textbox(label="⚙️ Remediation", lines=6)
    
    diagnose_btn.click(
        diagnose_logs,
        inputs=logs_input,
        outputs=[anomaly_output, root_cause_output, remediation_output]
    )
    
    # Example logs
    gr.Examples(
        [
            ["[INFO] nginx started\n[WARNING] memory: 85%\n[ERROR] worker crashed\n[ERROR] cpu: 95%"],
            ["[INFO] database pool active\n[ERROR] connection timeout\n[ERROR] query failed\n[WARNING] retry attempt"],
        ],
        inputs=logs_input
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
