# frontend/app.py

import gradio as gr
import pandas as pd
import requests
import re
from css import custom_css, saas_theme
from utils import clear_status, BACKEND_URL
from auth import api_login, api_register, logout
from diagnosis import (
    diagnose_logs, fetch_history, search_similar_incidents, upload_log_files,
    auto_remediate, generate_rca_tree, generate_code_fix,
    async_diagnose, check_async_task, analyze_image
)
from chat import (
    get_chat_sessions, load_chat_session, send_chat_msg_stream, search_chats,
    load_chat_by_id, delete_chat_session, rename_chat_session,
    get_available_models, switch_model
)
from incidents import (
    resolve_incident, get_incident_details, export_csv, export_incident_pdf,
    delete_incident, generate_runbook
)
from tickets import submit_escalation, fetch_my_tickets, load_admin_tickets, answer_escalation
from notifications import fetch_notifications, mark_notifications_read
from admin import (
    load_admin_data, fetch_analytics, purge_user, inspect_user_data,
    fetch_predictions, fetch_clusters, fetch_audit_logs,
    fetch_workspaces, create_workspace, delete_workspace,
    fetch_workspace_members, add_workspace_member,
    fetch_api_keys, create_api_key, revoke_api_key,
    generate_knowledge_base, search_knowledge_base,
    fetch_recent_activity
)
from community import (
    load_posts, create_post, delete_post, like_post,
    load_comments_for_post, add_comment_to_post, delete_comment, like_comment
)

def dismiss_download():
    return gr.update(visible=False), gr.update(value=None)

def dismiss_resolve():
    return gr.update(visible=False), gr.update(value=None), gr.update(value="*Click an incident to view details*")

def dismiss_workflow():
    return gr.update(value="")

def dismiss_rca():
    return "<p style='color:#94a3b8;text-align:center;'>Click 'RCA Tree' to visualize</p>"

def dismiss_code_fix():
    return "<p style='color:#94a3b8;text-align:center;'>Click 'Code Fix' to generate</p>"

def dismiss_runbook():
    return gr.update(visible=False), "<p style='color:#94a3b8;text-align:center;'>Select resolved incident → Generate Runbook</p>"

def save_alert_config(slack, teams, pagerduty, opsgenie, smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, alert_emails, token):
    try:
        res = requests.post(
            f"{BACKEND_URL}/admin/alerts/configure",
            json={
                "slack_webhook": slack if slack else None, "teams_webhook": teams if teams else None,
                "pagerduty_key": pagerduty if pagerduty else None, "opsgenie_key": opsgenie if opsgenie else None,
                "smtp_host": smtp_host if smtp_host else None, "smtp_port": int(smtp_port) if smtp_port else None,
                "smtp_username": smtp_user if smtp_user else None, "smtp_password": smtp_pass if smtp_pass else None,
                "smtp_from": smtp_from if smtp_from else None, "alert_emails": alert_emails if alert_emails else None
            },
            headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        if res.status_code == 200: return gr.update(value="Configuration saved successfully!")
    except: pass
    return gr.update(value="Failed to save configuration")

def send_test_alert(token):
    try:
        res = requests.post(f"{BACKEND_URL}/admin/alerts/test", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200: return gr.update(value="Test alert sent! Check your channels.")
    except: pass
    return gr.update(value="Failed to send test alert")

def analyze_sentiment_ui(message, token):
    if not message.strip() or not token: return ""
    try:
        res = requests.post(f"{BACKEND_URL}/chat/analyze-sentiment?message={message.strip()}", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200: return res.json().get("html", "")
    except: pass
    return ""

def extract_task_id(status_text):
    match = re.search(r'Task #(\d+)', status_text or "")
    return int(match.group(1)) if match else None

def handle_file_change(files, token):
    """Handle file upload with auto-clear on removal."""
    # When file is removed, use gr.update to properly clear the Markdown component
    if files is None or files == "" or files == [] or (isinstance(files, list) and len(files) == 0):
        return gr.update(value=""), gr.update(value="")
    
    try:
        if isinstance(files, str):
            files = [files]
        
        valid_files = []
        invalid_names = []
        for f in files:
            if not f or not str(f).strip():
                continue
            fname = str(f).lower()
            if fname.endswith(('.log', '.txt', '.out')):
                valid_files.append(f)
            else:
                short_name = fname.split('/')[-1] if '/' in fname else fname
                invalid_names.append(short_name)
        
        if not valid_files:
            if invalid_names:
                return gr.update(value=""), gr.update(value=f"❌ Not log files: {', '.join(invalid_names[:2])}")
            return gr.update(value=""), gr.update(value="❌ Please select .log, .txt, or .out files")
        
        return upload_log_files(valid_files, token)
        
    except Exception as e:
        return gr.update(value=""), gr.update(value=f"❌ Error: {str(e)[:80]}")


        

def handle_image_change(image, token):
    """Handle image upload with auto-clear on removal."""
    if image is None:
        return gr.update(value=""), gr.update(value="*Upload an image and click 'Analyze Image' to see results*")
    return gr.update(), gr.update()

# --- UI LAYOUT ---
with gr.Blocks(title="AegisAI") as demo:
    session_token, current_chat_id = gr.State(""), gr.State(None)
    selected_post_id = gr.State(None)
    selected_comment_id = gr.State(None)
    selected_workspace_id = gr.State(None)
    selected_api_key_id = gr.State(None)
    async_task_id = gr.State(None)

    # --- AUTH VIEW ---
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<center><h1 style='font-size:2.2rem;margin-bottom:16px;color:#38bdf8;'>AegisAI</h1></center>")
        with gr.Row():
            with gr.Column(elem_classes="auth-box glass-card"):
                with gr.Tab("Login"):
                    log_email = gr.Textbox(label="Email", placeholder="admin@example.com")
                    log_pass = gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="Show Password")
                    login_btn = gr.Button("Login to Dashboard", variant="primary", elem_classes="push-bottom")
                with gr.Tab("Register"):
                    reg_name = gr.Textbox(label="Full Name", placeholder="Jane Doe")
                    reg_email = gr.Textbox(label="Email", placeholder="user@example.com")
                    reg_pass = gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
                    reg_show_pass = gr.Checkbox(label="Show Password")
                    register_btn = gr.Button("Create Account", variant="primary", elem_classes="push-bottom")

    # --- APP VIEW ---
    with gr.Column(visible=False) as app_view:
        with gr.Row(elem_classes="nav-container"):
            with gr.Column(scale=1, elem_classes="nav-left"):
                welcome_text = gr.Markdown("", elem_classes="welcome-text")
            with gr.Column(scale=0, min_width=180, elem_classes="nav-right"):
                notification_count = gr.Textbox(value="0", visible=False)
                logout_btn = gr.Button("Logout", variant="stop", elem_classes="logout-btn")

        # ADMIN DASHBOARD
        with gr.Column(visible=False) as admin_dashboard_view:
            gr.Markdown("## Admin Dashboard")
            with gr.Tabs():
                with gr.Tab("Analytics"):
                    with gr.Row():
                        metric_users = gr.Number(label="Total Users", interactive=False)
                        metric_incidents = gr.Number(label="Total Incidents", interactive=False)
                        metric_chats = gr.Number(label="Active Chats", interactive=False)
                        metric_resolved = gr.Number(label="Resolved", interactive=False, value=0)
                    with gr.Row():
                        dashboard_days = gr.Slider(minimum=1, maximum=90, value=30, step=1, label="Period (days)", scale=3, interactive=True)
                        dashboard_severity = gr.Dropdown(
                            choices=["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
                            value="ALL", label="Severity Filter", scale=1, interactive=True
                        )
                        refresh_dashboard_btn = gr.Button("Refresh Dashboard", variant="primary", scale=1)
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=2, elem_classes="glass-card"):
                            gr.Markdown("### Incident Timeline")
                            dashboard_timeline = gr.LinePlot(x="date", y="Incidents", tooltip=["date", "Incidents"], height=280)
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### By Severity")
                            dashboard_severity_chart = gr.BarPlot(x="Severity", y="Count", color="Severity", tooltip=["Severity", "Count"], height=280)
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### Status Breakdown")
                            dashboard_status_chart = gr.BarPlot(x="status", y="Count", color="status", tooltip=["status", "Count"], height=250)
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### AI Predictions")
                            predictions_output = gr.Markdown(value="*Loading predictions...*", elem_classes="predictions-panel")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### Recent Activity")
                            recent_activity_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                    with gr.Row():
                        with gr.Column(elem_classes="glass-card"):
                            gr.Markdown("### Incident Clusters")
                            clusters_output = gr.HTML(value="<p style='color:#94a3b8;text-align:center;'>Loading clusters...</p>")
                    with gr.Row():
                        with gr.Column(elem_classes="glass-card health-card"):
                            gr.Markdown("### System Health")
                            gr.Markdown("""<div style="padding:4px;text-align:center;">
                                <h2 style="color:#10b981;font-size:1.2rem;margin:2px 0;">All Systems Operational</h2>
                                <p style="color:#94a3b8;margin:1px 0;font-size:0.7rem;">API: Online | AI: Connected | DB: SQLite | ChromaDB: Active</p>
                            </div>""")

                with gr.Tab("User Management"):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### Registered Users")
                            admin_users_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### Account Controls")
                            refresh_admin_btn = gr.Button("Refresh List", variant="secondary")
                            delete_user_input = gr.Number(label="Target User ID", precision=0)
                            delete_user_btn = gr.Button("Delete Account", variant="stop", elem_classes="push-bottom")
                            admin_status_msg = gr.Markdown("")
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### User Activity Inspector")
                            inspect_incidents_table = gr.Dataframe(label="User Incidents", interactive=False, wrap=True, elem_classes="short-table")
                            inspect_chats_table = gr.Dataframe(label="User Chat History", interactive=False, wrap=True, elem_classes="short-table")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### Inspect User")
                            inspect_user_input = gr.Number(label="User ID to Inspect", precision=0)
                            inspect_btn = gr.Button("Fetch Activity", variant="primary", elem_classes="push-bottom")
                            inspect_status_msg = gr.Markdown("")

                with gr.Tab("Support Tickets"):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### All Escalation Tickets")
                            admin_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### Answer Ticket")
                            refresh_admin_tickets_btn = gr.Button("Refresh Tickets", variant="secondary")
                            answer_ticket_id_input = gr.Number(label="Ticket ID", precision=0)
                            answer_ticket_input = gr.Textbox(label="Your Answer", lines=3)
                            answer_ticket_btn = gr.Button("Send Answer", variant="primary", elem_classes="push-bottom")

                with gr.Tab("Alert Settings"):
                    with gr.Row():
                        with gr.Column(elem_classes="glass-card"):
                            gr.Markdown("### Configure Alert Channels")
                            gr.Markdown("Alerts sent for CRITICAL and HIGH severity only.")
                            slack_webhook_input = gr.Textbox(label="Slack Webhook URL", placeholder="https://hooks.slack.com/...")
                            teams_webhook_input = gr.Textbox(label="Teams Webhook URL", placeholder="https://prod-xx.logic.azure.com/...")
                            with gr.Row():
                                smtp_host_input = gr.Textbox(label="SMTP Host", value="smtp.gmail.com", scale=2)
                                smtp_port_input = gr.Number(label="Port", value=587, precision=0, scale=1)
                            with gr.Row():
                                smtp_username_input = gr.Textbox(label="Username", placeholder="your@gmail.com", scale=1)
                                smtp_password_input = gr.Textbox(label="App Password", type="password", scale=1)
                            smtp_from_input = gr.Textbox(label="From Email", value="aegisai@alerts.com")
                            alert_emails_input = gr.Textbox(label="Alert Recipients", placeholder="team@company.com")
                            pagerduty_key_input = gr.Textbox(label="PagerDuty Routing Key", placeholder="Your PagerDuty key")
                            opsgenie_key_input = gr.Textbox(label="Opsgenie API Key", placeholder="Your Opsgenie GenieKey")
                            with gr.Row():
                                save_alerts_btn = gr.Button("Save Configuration", variant="primary")
                                test_alert_btn = gr.Button("Send Test Alert", variant="secondary")
                            alert_status = gr.Markdown("")

                with gr.Tab("Audit Logs"):
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Recent Activity Logs", scale=4)
                            refresh_audit_btn = gr.Button("Refresh", variant="secondary", scale=1)
                        audit_logs_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

        # MAIN TABS
        with gr.Tabs(elem_id="main_tabs") as tabs_manager:
            # LIVE DIAGNOSIS
            with gr.Tab("Live Diagnosis", id="tab_diag"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📡 Input")
                        with gr.Row():
                            with gr.Column(scale=1, elem_classes="upload-box"):
                                gr.Markdown("**📁 Upload Log Files**")
                                log_upload = gr.File(file_count="multiple", label="Select .log/.txt files", elem_classes="upload-area")
                                upload_status = gr.Markdown("", elem_classes="upload-status")
                        gr.Markdown("**Or Paste Logs**")
                        logs_input = gr.Textbox(lines=8, placeholder="Paste your server or application logs here...", show_label=False)
                        with gr.Row():
                            diagnose_btn = gr.Button("Analyze Logs", variant="primary")
                            auto_remediate_btn = gr.Button("Auto-Remediate", variant="primary")
                            rca_tree_btn = gr.Button("RCA Tree", variant="primary")
                            code_fix_btn = gr.Button("Code Fix", variant="primary")
                            clear_btn = gr.Button("Clear", variant="stop")
                        with gr.Row():
                            discuss_btn = gr.Button("Discuss with AI", variant="secondary")
                            search_similar_btn = gr.Button("Find Similar Incidents", variant="secondary")
                            async_diagnose_btn = gr.Button("Async Analyze", variant="secondary")
                        gr.Examples(examples=[
                            ["[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%"],
                            ["[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"]
                        ], inputs=logs_input)
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📊 Diagnostics Report")
                        anomaly_out = gr.Markdown(value="*Waiting for analysis...*", label="🔴 Anomaly Detected", elem_classes="scrollable-output")
                        rc_out = gr.Markdown(value="*Waiting for analysis...*", label="🔍 Root Cause", elem_classes="scrollable-output")
                        remed_out = gr.Markdown(value="*Waiting for analysis...*", label="⚙️ Remediation", elem_classes="scrollable-output")
                
                with gr.Row():
                    with gr.Column(elem_classes="glass-card"):
                        gr.Markdown("### ⚡ Background Tasks")
                        async_status = gr.Markdown(value="*No background tasks running*")
                        with gr.Row():
                            refresh_async_btn = gr.Button("Check Status", variant="secondary", size="sm")
                            clear_async_btn = gr.Button("Clear", variant="stop", size="sm")
                
                with gr.Row(visible=False) as similar_incidents_row:
                    with gr.Column(elem_classes="glass-card"):
                        gr.Markdown("### Similar Past Incidents")
                        similar_incidents_status = gr.Markdown("")
                        similar_incidents_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                with gr.Row() as workflow_output_row:
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Auto-Remediation Results", scale=4)
                            dismiss_workflow_btn = gr.Button("Close", variant="stop", size="sm", scale=1)
                        workflow_output = gr.Markdown(value="", elem_classes="predictions-panel")
                with gr.Row() as rca_tree_row:
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### RCA Tree", scale=4)
                            dismiss_rca_btn = gr.Button("Close", variant="stop", size="sm", scale=1)
                        rca_tree_output = gr.HTML(value="<p style='color:#94a3b8;text-align:center;'>Click 'RCA Tree' to visualize</p>")
                with gr.Row() as code_fix_row:
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Code Fixes", scale=4)
                            dismiss_code_fix_btn = gr.Button("Close", variant="stop", size="sm", scale=1)
                        code_fix_output = gr.HTML(value="<p style='color:#94a3b8;text-align:center;'>Click 'Code Fix' to generate</p>")

            # IMAGE ANALYSIS TAB
            with gr.Tab("📸 Image Analysis"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📤 Upload Screenshot")
                        gr.Markdown("*Upload a screenshot of error messages, dashboards, or logs for AI analysis*")
                        with gr.Column(elem_classes="image-upload-box"):
                            
                            image_upload = gr.File(file_count="single", label="Select image file", elem_classes="image-upload-area")                        
                            with gr.Row(elem_classes="image-action-row"):
                            analyze_image_btn = gr.Button("🔍 Analyze Image", variant="primary", scale=3)
                            clear_image_btn = gr.Button("Clear", variant="stop", size="sm", scale=1)
                        image_result = gr.HTML(value="")
                    
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📊 Analysis Results")
                        image_analysis_output = gr.Markdown(value="*Upload an image and click 'Analyze Image' to see results*", elem_classes="scrollable-output")
                        gr.Markdown("---")
                        gr.Markdown("### ⚡ Actions")
                        with gr.Row():
                            send_to_chat_btn = gr.Button("💬 Discuss with Copilot", variant="secondary", size="sm")
                            extract_to_logs_btn = gr.Button("📄 Use as Log Input", variant="secondary", size="sm")
                        image_action_status = gr.Markdown("")

            # AI COPILOT
            with gr.Tab("AI Copilot", id="tab_chat"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### AI Model")
                        model_selector = gr.Dropdown(
                            choices=["llama3", "deepseek-r1:7b", "mistral:7b"],
                            value="llama3", interactive=True, label="Select Model"
                        )
                        gr.Markdown("---")
                        gr.Markdown("### Chat Sessions")
                        chat_session_dropdown = gr.Dropdown(
                            label="Load conversation", choices=[], interactive=True,
                            allow_custom_value=True, value=None
                        )
                        with gr.Row():
                            refresh_chat_btn = gr.Button("Refresh", variant="secondary", size="sm")
                            new_chat_btn = gr.Button("New Chat", variant="primary", size="sm")
                        with gr.Row():
                            rename_chat_input = gr.Textbox(label="Rename", placeholder="New title...", scale=3)
                            rename_chat_btn = gr.Button("Rename", variant="secondary", size="sm", scale=1)
                        delete_chat_btn = gr.Button("Delete Current Chat", variant="stop", size="sm")
                        gr.Markdown("---")
                        gr.Markdown("### Search Messages")
                        with gr.Row():
                            chat_search_input = gr.Textbox(placeholder="Search...", show_label=False, scale=4)
                            chat_search_btn = gr.Button("Search", variant="secondary", size="sm", scale=1)
                        chat_search_status = gr.Markdown("")
                        chat_search_results = gr.Dataframe(
                            interactive=False, wrap=True, elem_classes="short-table",
                            label="Results (click to load)"
                        )
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        chatbot_ui = gr.Chatbot(label="Aegis AI Copilot", height=400)
                        with gr.Row():
                            chat_input = gr.Textbox(show_label=False, placeholder="Ask anything...", scale=4, lines=1, max_lines=4)
                            chat_send_btn = gr.Button("Send", variant="primary", scale=1)
                        sentiment_output = gr.HTML(value="")

            # INCIDENT HISTORY
            with gr.Tab("Incident History"):
                with gr.Column(elem_classes="glass-card"):
                    with gr.Row():
                        gr.Markdown("### Your Processed Incidents", scale=3)
                        refresh_btn = gr.Button("Refresh Data", variant="secondary", scale=1)
                        export_csv_btn = gr.Button("Export CSV", variant="secondary", scale=1)
                    history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                with gr.Row(visible=False) as download_row:
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Download Ready", scale=4)
                            dismiss_download_btn = gr.Button("Close", variant="stop", size="sm", scale=1)
                        download_file = gr.File(label="Your file", visible=True)
                with gr.Row(visible=False) as resolve_incident_row:
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        gr.Markdown("### Incident Details")
                        incident_details_md = gr.Markdown(value="*Click an incident to view details*")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Actions", scale=3)
                            dismiss_resolve_btn = gr.Button("Close Panel", variant="stop", size="sm", scale=1)
                        resolve_incident_id = gr.Number(label="Incident ID", precision=0)
                        resolve_notes_input = gr.Textbox(label="Resolution Notes", lines=3, placeholder="How was this resolved?")
                        with gr.Row():
                            resolve_btn = gr.Button("Mark Resolved", variant="primary")
                            delete_incident_btn = gr.Button("Delete", variant="stop")
                            export_selected_pdf_btn = gr.Button("PDF Report", variant="secondary")
                        with gr.Row():
                            runbook_btn = gr.Button("Generate Runbook", variant="primary")
                with gr.Row(visible=False) as runbook_row:
                    with gr.Column(elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Generated Runbook", scale=4)
                            dismiss_runbook_btn = gr.Button("Close", variant="stop", size="sm", scale=1)
                        runbook_output = gr.HTML(value="<p style='color:#94a3b8;text-align:center;'>Select resolved incident → Generate Runbook</p>")

            # SUPPORT TICKETS
            with gr.Tab("Support Tickets"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Ask an Admin")
                        ticket_question_input = gr.Textbox(label="Your Question", lines=4, placeholder="Describe your issue...")
                        submit_ticket_btn = gr.Button("Submit Ticket", variant="primary", elem_classes="push-bottom")
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Ticket History", scale=4)
                            refresh_my_tickets_btn = gr.Button("Refresh", variant="secondary", scale=1)
                        my_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

            # COMMUNITY
            with gr.Tab("Community"):
                with gr.Row():
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        gr.Markdown("### Feed")
                        community_posts_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll community-feed", label="Posts")
                        with gr.Row():
                            new_post_input = gr.Textbox(label="Share", lines=2, placeholder="What's on your mind?")
                            post_btn = gr.Button("Post", variant="primary")
                        with gr.Row():
                            refresh_posts_btn = gr.Button("Refresh", variant="secondary")
                            like_post_btn = gr.Button("Like", variant="secondary")
                            delete_post_btn = gr.Button("Delete", variant="stop")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Comments")
                        community_comments_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="short-table community-comments", label="Comments")
                        with gr.Row():
                            new_comment_input = gr.Textbox(label="Reply", lines=1, placeholder="Write a reply...")
                            comment_btn = gr.Button("Reply", variant="primary")
                        with gr.Row():
                            like_comment_btn = gr.Button("Like", variant="secondary")
                            delete_comment_btn = gr.Button("Delete", variant="stop")

            # WORKSPACES
            with gr.Tab("Workspaces"):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Your Workspaces")
                        workspaces_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll", label="Workspaces")
                        with gr.Row():
                            refresh_workspaces_btn = gr.Button("Refresh", variant="secondary", size="sm")
                            delete_workspace_btn = gr.Button("Delete Selected", variant="stop", size="sm")
                        gr.Markdown("---")
                        gr.Markdown("### Create Workspace")
                        workspace_name_input = gr.Textbox(label="Name", placeholder="e.g., Team Alpha")
                        workspace_desc_input = gr.Textbox(label="Description", lines=2)
                        create_workspace_btn = gr.Button("Create", variant="primary")
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        gr.Markdown("### Members")
                        workspace_members_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll", label="Members")
                        gr.Markdown("### Add Member")
                        with gr.Row():
                            add_member_id_input = gr.Number(label="User ID", precision=0, scale=2)
                            add_member_btn = gr.Button("Add", variant="primary", scale=1)
                        add_member_status = gr.Markdown("")

            # API KEYS
            with gr.Tab("API Keys"):
                with gr.Row():
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        gr.Markdown("### Your API Keys")
                        api_keys_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll", label="Keys")
                        with gr.Row():
                            refresh_api_keys_btn = gr.Button("Refresh", variant="secondary")
                            revoke_key_btn = gr.Button("Revoke Selected", variant="stop")
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Create Key")
                        api_key_name_input = gr.Textbox(label="Key Name", placeholder="e.g., Production")
                        api_key_expiry_input = gr.Number(label="Expires (days, 0=never)", value=0, precision=0)
                        create_api_key_btn = gr.Button("Generate", variant="primary")
                        api_key_output = gr.Markdown("")

            # KNOWLEDGE BASE
            with gr.Tab("Knowledge Base"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Generate Articles")
                        generate_kb_btn = gr.Button("Generate Knowledge Base", variant="primary")
                        kb_status = gr.Markdown("")
                        gr.Markdown("---")
                        gr.Markdown("### Article List")
                        kb_articles_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll", label="Generated Articles")
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        gr.Markdown("### Search Knowledge Base")
                        with gr.Row():
                            kb_search_input = gr.Textbox(placeholder="Search for solutions...", show_label=False, scale=4)
                            kb_search_btn = gr.Button("Search", variant="primary", scale=1)
                        kb_results = gr.HTML(value="<p style='color:#94a3b8;text-align:center;padding:20px;'>Generate articles first, then search</p>", elem_classes="kb-results-scroll")

            # NOTIFICATIONS
            with gr.Tab("Notifications"):
                with gr.Column(elem_classes="glass-card"):
                    with gr.Row():
                        gr.Markdown("### Recent Notifications", scale=4)
                        mark_read_btn = gr.Button("Mark All Read", variant="secondary", scale=1)
                        refresh_notif_btn = gr.Button("Refresh", variant="secondary", scale=1)
                    notifications_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

        # FOOTER
        with gr.Row(elem_classes="footer-container"):
            with gr.Column(scale=1):
                gr.Markdown("**Aegis AI**", elem_classes="footer-logo")
            with gr.Column(scale=1):
                role_text = gr.Markdown("", elem_classes="footer-role")

    # ========== EVENT WIRING ==========
    log_show_pass.change(fn=None, inputs=[log_show_pass], js="(s)=>{const el=document.querySelector('#log_pass_input input');if(el)el.type=s?'text':'password';return[];}")
    reg_show_pass.change(fn=None, inputs=[reg_show_pass], js="(s)=>{const el=document.querySelector('#reg_pass_input input');if(el)el.type=s?'text':'password';return[];}")

    # 🆕 Log upload - auto-clear on removal
    log_upload.change(fn=handle_file_change, inputs=[log_upload, session_token], outputs=[logs_input, upload_status])

    # 🆕 Image upload - auto-clear on removal
    image_upload.change(fn=handle_image_change, inputs=[image_upload, session_token], outputs=[image_result, image_analysis_output])

    # Image Analysis wiring
    analyze_image_btn.click(fn=analyze_image, inputs=[image_upload, session_token], outputs=[image_result, image_analysis_output])
    clear_image_btn.click(
        fn=lambda: (
            gr.update(value=""),
            gr.update(value="*Upload an image and click 'Analyze Image' to see results*"),
            gr.update(value=None)
        ),
        outputs=[image_result, image_analysis_output, image_upload]
    )

    send_to_chat_btn.click(
        fn=lambda text: (text, [], None, gr.update(value=None), gr.update(selected="tab_chat")),
        inputs=[image_analysis_output],
        outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager],
        queue=False
    )

    extract_to_logs_btn.click(
        fn=lambda text: (text, "✅ Extracted text sent to logs input. Go to Live Diagnosis to analyze.", gr.update(selected="tab_diag")),
        inputs=[image_analysis_output],
        outputs=[logs_input, image_action_status, tabs_manager],
        queue=False
    )

    clear_btn.click(
        fn=lambda:("","","*Waiting for analysis...*","*Waiting for analysis...*","*Waiting for analysis...*",pd.DataFrame(),gr.update(visible=False),gr.update(value="")),
        outputs=[logs_input,upload_status,anomaly_out,rc_out,remed_out,similar_incidents_table,similar_incidents_row,similar_incidents_status], queue=False
    )

    dismiss_workflow_btn.click(fn=dismiss_workflow, outputs=[workflow_output])
    dismiss_rca_btn.click(fn=dismiss_rca, outputs=[rca_tree_output])
    dismiss_code_fix_btn.click(fn=dismiss_code_fix, outputs=[code_fix_output])

    login_btn.click(
        fn=api_login, inputs=[log_email,log_pass],
        outputs=[session_token,auth_view,app_view,welcome_text,role_text,admin_dashboard_view,notification_count,notifications_table]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=load_admin_data, inputs=[session_token, gr.State(30), gr.State("ALL")],
           outputs=[metric_users,metric_incidents,metric_chats,metric_resolved,gr.State(),gr.State(),admin_users_table]
    ).then(fn=fetch_analytics, inputs=[session_token, gr.State(30), gr.State("ALL")],
           outputs=[dashboard_timeline,dashboard_severity_chart,dashboard_status_chart]
    ).then(fn=fetch_predictions, inputs=[session_token], outputs=[predictions_output]
    ).then(fn=fetch_recent_activity, inputs=[session_token], outputs=[recent_activity_table]
    ).then(fn=fetch_clusters, inputs=[session_token], outputs=[clusters_output]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table]
    ).then(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table]
    ).then(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown]
    ).then(fn=load_posts, inputs=[session_token], outputs=[community_posts_table]
    ).then(fn=get_available_models, outputs=[model_selector]
    ).then(fn=fetch_audit_logs, inputs=[session_token], outputs=[audit_logs_table]
    ).then(fn=fetch_workspaces, inputs=[session_token], outputs=[workspaces_table, gr.State()]
    ).then(fn=fetch_api_keys, inputs=[session_token], outputs=[api_keys_table])

    register_btn.click(
        fn=api_register, inputs=[reg_email,reg_pass,reg_name],
        outputs=[session_token,auth_view,app_view,welcome_text,role_text,admin_dashboard_view,notification_count,notifications_table]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])

    logout_btn.click(fn=logout, outputs=[
        session_token,auth_view,app_view,welcome_text,role_text,chat_session_dropdown,admin_dashboard_view,
        log_email,log_pass,log_show_pass,reg_name,reg_email,reg_pass,reg_show_pass,
        inspect_user_input,inspect_incidents_table,inspect_chats_table,inspect_status_msg,
        ticket_question_input,my_tickets_table,answer_ticket_id_input,answer_ticket_input,admin_tickets_table,
        metric_users,metric_incidents,metric_chats,metric_resolved,gr.State(),gr.State(),
        dashboard_timeline,dashboard_severity_chart,dashboard_status_chart,
        similar_incidents_table,similar_incidents_row,similar_incidents_status,
        history_table,resolve_incident_row,resolve_incident_id,resolve_notes_input,incident_details_md,
        download_row,notification_count,notifications_table,
        community_posts_table,community_comments_table,selected_post_id,selected_comment_id
    ], queue=False)

    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input,session_token], outputs=[anomaly_out,rc_out,remed_out,history_table])
    auto_remediate_btn.click(fn=auto_remediate, inputs=[logs_input,gr.State(False),session_token], outputs=[anomaly_out,rc_out,remed_out,workflow_output,history_table])
    rca_tree_btn.click(fn=generate_rca_tree, inputs=[logs_input,session_token], outputs=[rca_tree_output])
    code_fix_btn.click(fn=generate_code_fix, inputs=[logs_input,session_token], outputs=[code_fix_output])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])

    discuss_btn.click(
        fn=lambda l: (f"Please analyze these logs:\n\n{l}" if l.strip() else "", [], None, gr.update(value=None), gr.update(selected="tab_chat")),
        inputs=[logs_input],
        outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager],
        queue=False
    )

    refresh_dashboard_btn.click(
        fn=fetch_analytics, inputs=[session_token, dashboard_days, dashboard_severity],
        outputs=[dashboard_timeline, dashboard_severity_chart, dashboard_status_chart]
    ).then(
        fn=lambda token, days, sev: load_admin_data(token, days, sev)[:4],
        inputs=[session_token, dashboard_days, dashboard_severity],
        outputs=[metric_users, metric_incidents, metric_chats, metric_resolved]
    ).then(fn=fetch_recent_activity, inputs=[session_token], outputs=[recent_activity_table]
    ).then(fn=fetch_predictions, inputs=[session_token], outputs=[predictions_output])

    async_diagnose_btn.click(fn=async_diagnose, inputs=[logs_input, session_token], outputs=[async_status]
    ).then(fn=extract_task_id, inputs=[async_status], outputs=[async_task_id])
    
    refresh_async_btn.click(fn=check_async_task, inputs=[async_task_id, session_token], outputs=[async_status])
    clear_async_btn.click(fn=lambda:("*No background tasks*",None), outputs=[async_status,async_task_id])

    def send_with_sentiment(message, session_id, history, token):
        gen = send_chat_msg_stream(message, session_id, history, token)
        for output in gen:
            if len(output)==3: msg,hist,sid=output; yield msg,hist,sid,gr.update()
            else:
                try: yield output[0],output[1],output[2],gr.update()
                except: yield gr.update(),gr.update(),gr.update(),gr.update()
        yield gr.update(),gr.update(),gr.update(),analyze_sentiment_ui(message,token)

    chat_send_btn.click(fn=send_with_sentiment, inputs=[chat_input,current_chat_id,chatbot_ui,session_token], outputs=[chat_input,chatbot_ui,current_chat_id,sentiment_output])
    chat_input.submit(fn=send_with_sentiment, inputs=[chat_input,current_chat_id,chatbot_ui,session_token], outputs=[chat_input,chatbot_ui,current_chat_id,sentiment_output])
    new_chat_btn.click(fn=lambda:("",[],None,""), outputs=[chat_input,chatbot_ui,current_chat_id,sentiment_output], queue=False)
    model_selector.change(fn=switch_model, inputs=[model_selector,session_token], outputs=[])
    chat_session_dropdown.change(fn=load_chat_session, inputs=[chat_session_dropdown,session_token], outputs=[chatbot_ui,current_chat_id])
    refresh_chat_btn.click(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])
    delete_chat_btn.click(fn=delete_chat_session, inputs=[current_chat_id,session_token], outputs=[chatbot_ui,chat_session_dropdown])
    rename_chat_btn.click(fn=rename_chat_session, inputs=[current_chat_id,rename_chat_input,session_token], outputs=[chat_session_dropdown,chat_session_dropdown])

    chat_search_btn.click(fn=search_chats, inputs=[chat_search_input,session_token], outputs=[chat_search_results,chat_search_status])
    def on_search_click(evt:gr.SelectData,token):
        if evt.row_value is not None and len(evt.row_value)>0:
            sid=str(evt.row_value[0]); h,id,d=load_chat_by_id(sid,token); return h,id,d
        return gr.update(),gr.update(),gr.update()
    chat_search_results.select(fn=on_search_click, inputs=[session_token], outputs=[chatbot_ui,current_chat_id,chat_session_dropdown])

    refresh_admin_btn.click(fn=load_admin_data, inputs=[session_token, dashboard_days, dashboard_severity],
                           outputs=[metric_users,metric_incidents,metric_chats,admin_users_table]
    ).then(fn=fetch_analytics, inputs=[session_token, dashboard_days, dashboard_severity],
           outputs=[dashboard_timeline,dashboard_severity_chart,dashboard_status_chart]
    ).then(fn=fetch_predictions, inputs=[session_token], outputs=[predictions_output]
    ).then(fn=fetch_recent_activity, inputs=[session_token], outputs=[recent_activity_table]
    ).then(fn=fetch_clusters, inputs=[session_token], outputs=[clusters_output])

    delete_user_btn.click(fn=purge_user, inputs=[session_token,delete_user_input],
                         outputs=[metric_users,metric_incidents,metric_chats,admin_users_table,admin_status_msg]
    ).then(fn=clear_status, outputs=[admin_status_msg])
    inspect_btn.click(fn=inspect_user_data, inputs=[session_token,inspect_user_input],
                     outputs=[inspect_incidents_table,inspect_chats_table,inspect_status_msg]
    ).then(fn=clear_status, outputs=[inspect_status_msg])
    refresh_admin_tickets_btn.click(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table])
    submit_ticket_btn.click(fn=submit_escalation, inputs=[ticket_question_input,session_token], outputs=[ticket_question_input,my_tickets_table])
    refresh_my_tickets_btn.click(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])
    answer_ticket_btn.click(fn=answer_escalation, inputs=[answer_ticket_id_input,answer_ticket_input,session_token],
                            outputs=[answer_ticket_id_input,answer_ticket_input,admin_tickets_table])

    search_similar_btn.click(fn=search_similar_incidents, inputs=[logs_input,session_token],
                            outputs=[similar_incidents_table,similar_incidents_row,similar_incidents_status])

    save_alerts_btn.click(fn=save_alert_config, inputs=[
        slack_webhook_input,teams_webhook_input,pagerduty_key_input,opsgenie_key_input,
        smtp_host_input,smtp_port_input,smtp_username_input,smtp_password_input,
        smtp_from_input,alert_emails_input,session_token
    ], outputs=[alert_status])
    test_alert_btn.click(fn=send_test_alert, inputs=[session_token], outputs=[alert_status])

    refresh_audit_btn.click(fn=fetch_audit_logs, inputs=[session_token], outputs=[audit_logs_table])

    generate_kb_btn.click(fn=generate_knowledge_base, inputs=[session_token], outputs=[kb_status, kb_articles_table])
    kb_search_btn.click(fn=search_knowledge_base, inputs=[kb_search_input, session_token], outputs=[kb_results])

    refresh_workspaces_btn.click(fn=fetch_workspaces, inputs=[session_token], outputs=[workspaces_table,gr.State()])
    create_workspace_btn.click(fn=create_workspace, inputs=[workspace_name_input,workspace_desc_input,session_token],
                              outputs=[workspaces_table,gr.State()]
    ).then(fn=lambda:(gr.update(value=""),gr.update(value="")), outputs=[workspace_name_input,workspace_desc_input])
    delete_workspace_btn.click(fn=delete_workspace, inputs=[selected_workspace_id,session_token],
                              outputs=[workspaces_table,gr.State()])
    def on_workspace_select(evt:gr.SelectData,token):
        if evt.row_value is not None and len(evt.row_value)>0:
            ws_id=evt.row_value[0]; return fetch_workspace_members(ws_id,token),ws_id
        return pd.DataFrame(),None
    workspaces_table.select(fn=on_workspace_select, inputs=[session_token],
                           outputs=[workspace_members_table,selected_workspace_id])
    add_member_btn.click(fn=add_workspace_member, inputs=[selected_workspace_id,add_member_id_input,session_token],
                        outputs=[workspace_members_table,add_member_status])

    refresh_api_keys_btn.click(fn=fetch_api_keys, inputs=[session_token], outputs=[api_keys_table])
    create_api_key_btn.click(fn=create_api_key, inputs=[api_key_name_input,api_key_expiry_input,session_token],
                            outputs=[api_keys_table,api_key_output])
    def on_key_select(evt:gr.SelectData):
        if evt.row_value is not None and len(evt.row_value)>0: return evt.row_value[0]
        return None
    api_keys_table.select(fn=on_key_select, outputs=[selected_api_key_id])
    revoke_key_btn.click(fn=revoke_api_key, inputs=[selected_api_key_id,session_token], outputs=[api_keys_table])

    def on_history_select(evt:gr.SelectData,token):
        if evt.row_value and len(evt.row_value)>0:
            iid=evt.row_value[0]; d=get_incident_details(iid,token); return d,gr.update(visible=True),gr.update(value=iid)
        return gr.update(),gr.update(visible=False),gr.update(value=None)
    history_table.select(fn=on_history_select, inputs=[session_token],
                        outputs=[incident_details_md,resolve_incident_row,resolve_incident_id])

    resolve_btn.click(fn=resolve_incident, inputs=[resolve_incident_id,resolve_notes_input,session_token],
                     outputs=[resolve_notes_input,history_table]
    ).then(fn=lambda:(gr.update(visible=False),gr.update(value=None),gr.update(value="*Resolved!*")),
            outputs=[resolve_incident_row,resolve_incident_id,incident_details_md])
    delete_incident_btn.click(fn=delete_incident, inputs=[resolve_incident_id,session_token],
                             outputs=[history_table]
    ).then(fn=lambda:(gr.update(visible=False),gr.update(value=None),gr.update(value="*Deleted*")),
            outputs=[resolve_incident_row,resolve_incident_id,incident_details_md])

    runbook_btn.click(fn=generate_runbook, inputs=[resolve_incident_id,session_token],
                     outputs=[runbook_output]
    ).then(fn=lambda:gr.update(visible=True), outputs=[runbook_row])
    dismiss_runbook_btn.click(fn=dismiss_runbook, outputs=[runbook_row,runbook_output])

    export_csv_btn.click(fn=export_csv, inputs=[session_token], outputs=[download_file]
    ).then(fn=lambda:gr.update(visible=True), outputs=[download_row])
    export_selected_pdf_btn.click(fn=export_incident_pdf, inputs=[resolve_incident_id,session_token],
                                 outputs=[download_file]
    ).then(fn=lambda:gr.update(visible=True), outputs=[download_row])

    dismiss_download_btn.click(fn=dismiss_download, outputs=[download_row,download_file])
    dismiss_resolve_btn.click(fn=dismiss_resolve, outputs=[resolve_incident_row,resolve_incident_id,incident_details_md])

    refresh_posts_btn.click(fn=load_posts, inputs=[session_token], outputs=[community_posts_table])
    post_btn.click(fn=create_post, inputs=[new_post_input,session_token], outputs=[community_posts_table])
    def on_post_select(evt:gr.SelectData,token):
        if evt.row_value is not None and len(evt.row_value)>0:
            pid=int(evt.row_value[0]); c=load_comments_for_post(pid,token); return c,pid
        return pd.DataFrame(),None
    community_posts_table.select(fn=on_post_select, inputs=[session_token],
                                outputs=[community_comments_table,selected_post_id])
    delete_post_btn.click(fn=delete_post, inputs=[selected_post_id,session_token], outputs=[community_posts_table])
    like_post_btn.click(fn=like_post, inputs=[selected_post_id,session_token], outputs=[community_posts_table])
    comment_btn.click(fn=add_comment_to_post, inputs=[selected_post_id,new_comment_input,session_token],
                     outputs=[community_comments_table])
    def on_comment_select(evt:gr.SelectData,token):
        if evt.row_value is not None and len(evt.row_value)>0: return evt.row_value[0]
        return None
    community_comments_table.select(fn=on_comment_select, inputs=[session_token],
                                  outputs=[selected_comment_id])
    delete_comment_btn.click(fn=delete_comment, inputs=[selected_comment_id,selected_post_id,session_token],
                            outputs=[community_comments_table])
    like_comment_btn.click(fn=like_comment, inputs=[selected_comment_id,selected_post_id,session_token],
                          outputs=[community_comments_table])

    mark_read_btn.click(fn=mark_notifications_read, inputs=[session_token],
                       outputs=[notification_count,notifications_table])
    refresh_notif_btn.click(fn=fetch_notifications, inputs=[session_token],
                           outputs=[notifications_table,notification_count])

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=10, max_size=100).launch(
        share=True, server_name="0.0.0.0", server_port=7860,
        theme=saas_theme, css=custom_css
    )