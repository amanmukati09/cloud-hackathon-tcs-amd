import re
import time
import gradio as gr
import pandas as pd
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def is_valid_email(email): 
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

def is_strong_password(password):
    return re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password)

def clear_status():
    time.sleep(4)
    return gr.update(value="")

def clean_markdown(text):
    text = re.sub(r'(?<!<[^>]*)\*\*(?!>)', '', text)
    return text

def format_diagnosis(data):
    anomaly = data.get("anomaly", {})
    if isinstance(anomaly, dict):
        anomaly_type = anomaly.get("anomaly_type", "Unknown")
        severity = anomaly.get("severity", "UNKNOWN").upper()
        affected = anomaly.get("affected_component", "Unknown")
        description = anomaly.get("description", "No description provided.")
    else:
        anomaly_type, severity, affected = "Unknown", "HIGH", "Unknown"
        description = str(anomaly) if anomaly else "No description provided."

    severity_colors = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981", "UNKNOWN": "#6b7280"}
    severity_color = severity_colors.get(severity, "#6b7280")

    anomaly_html = f"""
<div style="margin-bottom: 8px;">
    <span style="color: {severity_color}; font-weight: bold; font-size: 1.1em;">● {severity}</span>
    <span style="margin-left: 8px; font-weight: 600;">Type:</span> <code>{anomaly_type}</code>
</div>
<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Component:</span> {affected}</div>
<div><span style="font-weight: 600;">Details:</span> {description}</div>
"""
    root_cause = data.get("root_cause", {})
    if isinstance(root_cause, dict):
        cause_text = root_cause.get("root_cause", "Not determined")
        confidence = root_cause.get("confidence", 0.0)
        evidence = root_cause.get("evidence", [])
        factors = root_cause.get("contributing_factors", [])
    else:
        cause_text, confidence = str(root_cause) if root_cause else "Not determined", 0.0
        evidence, factors = [], []

    conf_color = "#10b981" if confidence >= 0.7 else "#f59e0b" if confidence >= 0.4 else "#ef4444"
    conf_label = "High" if confidence >= 0.7 else "Medium" if confidence >= 0.4 else "Low"

    rc_html = f"""
<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Cause:</span> {cause_text}</div>
<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Confidence:</span> <span style="color: {conf_color}; font-weight: bold;">{confidence:.0%} ({conf_label})</span></div>
"""
    if evidence:
        rc_html += '<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Evidence:</span><ul style="margin: 4px 0; padding-left: 20px;">'
        for e in evidence: rc_html += f"<li>{e}</li>"
        rc_html += "</ul></div>"
    if factors:
        rc_html += '<div><span style="font-weight: 600;">Contributing Factors:</span><ul style="margin: 4px 0; padding-left: 20px;">'
        for f in factors: rc_html += f"<li>{f}</li>"
        rc_html += "</ul></div>"

    remediation = data.get("remediation", {})
    if isinstance(remediation, dict):
        immediate = remediation.get("immediate_actions", [])
        automated = remediation.get("automated_actions", [])
        escalation = remediation.get("escalation_needed", False)
        recovery = remediation.get("estimated_recovery_time", "Unknown")
        prevention = remediation.get("prevention_measures", [])
    else:
        immediate, automated = [str(remediation)] if remediation else [], []
        escalation, recovery, prevention = True, "Unknown", []

    rem_html = ""
    if immediate:
        rem_html += '<div style="margin-bottom: 8px;"><span style="font-weight: 600;">⚡ Immediate Actions:</span><ul style="margin: 4px 0; padding-left: 20px;">'
        for a in immediate: rem_html += f"<li>{a}</li>"
        rem_html += "</ul></div>"
    if automated:
        rem_html += '<div style="margin-bottom: 8px;"><span style="font-weight: 600;">🤖 Automated Actions:</span><ul style="margin: 4px 0; padding-left: 20px;">'
        for a in automated:
            if isinstance(a, dict):
                action = a.get('action', str(a))
                risk = a.get('risk_level', 'UNKNOWN')
                risk_color = "#ef4444" if risk == "HIGH" else "#f59e0b" if risk == "MEDIUM" else "#10b981"
                rem_html += f'<li>{action} <span style="color: {risk_color}; font-size: 0.85em;">[Risk: {risk}]</span></li>'
            else: rem_html += f"<li>{a}</li>"
        rem_html += "</ul></div>"
    esc_color = "#ef4444" if escalation else "#10b981"
    esc_text = "⚠️ YES" if escalation else "✅ NO"
    rem_html += f"""
<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Escalation Needed:</span> <span style="color: {esc_color}; font-weight: bold;">{esc_text}</span></div>
<div style="margin-bottom: 8px;"><span style="font-weight: 600;">Estimated Recovery:</span> {recovery}</div>
"""
    if prevention:
        rem_html += '<div><span style="font-weight: 600;">🛡️ Prevention:</span><ul style="margin: 4px 0; padding-left: 20px;">'
        for p in prevention: rem_html += f"<li>{p}</li>"
        rem_html += "</ul></div>"

    return anomaly_html, rc_html, rem_html