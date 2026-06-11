import gradio as gr
import pandas as pd
from css import custom_css, saas_theme
from utils import clear_status
from auth import api_login, api_register, logout
from diagnosis import diagnose_logs, fetch_history, search_similar_incidents
from chat import get_chat_sessions, load_chat_session, send_chat_msg
from incidents import resolve_incident, get_incident_details, export_csv, export_incident_pdf
from tickets import submit_escalation, fetch_my_tickets, load_admin_tickets, answer_escalation
from notifications import fetch_notifications, mark_notifications_read
from admin import load_admin_data, fetch_analytics, purge_user, inspect_user_data

# --- UI LAYOUT ---
with gr.Blocks(title="AegisAI") as demo:
    session_token, current_chat_id = gr.State(""), gr.State(None)
    
    # --- AUTH VIEW ---
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<center><h1 style='font-size: 2.5rem; margin-bottom: 20px; color: #38bdf8;'>🛡️ AegisAI Portal</h1></center>")
        with gr.Row():
            with gr.Column(elem_classes="auth-box glass-card"):
                with gr.Tab("Login"):
                    log_email = gr.Textbox(label="Email Address", placeholder="admin@example.com")
                    log_pass = gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="👁️ Show Password")
                    login_btn = gr.Button("Login to Dashboard 🚀", variant="primary", elem_classes="push-bottom")
                with gr.Tab("Register New Account"):
                    reg_name = gr.Textbox(label="Full Name", placeholder="Jane Doe")
                    reg_email = gr.Textbox(label="Email Address", placeholder="user@example.com")
                    reg_pass = gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
                    reg_show_pass = gr.Checkbox(label="👁️ Show Password")
                    register_btn = gr.Button("Secure Sign Up 📝", variant="primary", elem_classes="push-bottom")

    # --- APP VIEW ---
    with gr.Column(visible=False) as app_view:
        
        # 🎨 FIXED NAVBAR
        with gr.Row(elem_classes="nav-container"):
            with gr.Column(scale=1, elem_classes="nav-left"):
                welcome_text = gr.Markdown("", elem_classes="welcome-text")
            with gr.Column(scale=0, min_width=200, elem_classes="nav-right"):
                notification_count = gr.Textbox(value="0", visible=False)
                logout_btn = gr.Button("🔒 Logout", variant="stop", elem_classes="logout-btn")
            
        # Admin Dashboard
        with gr.Column(visible=False) as admin_dashboard_view:
            gr.Markdown("## 🎛️ Root Administrator Dashboard")
            with gr.Tabs():
                with gr.Tab("📈 Global Analytics"):
                    with gr.Row():
                        metric_users = gr.Number(label="Total Registered Users", interactive=False)
                        metric_incidents = gr.Number(label="Incidents Analyzed", interactive=False)
                        metric_chats = gr.Number(label="Active AI Sessions", interactive=False)
                    gr.HTML("<hr style='border-color: rgba(255,255,255,0.1); margin: 15px 0;'>")
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=2, elem_classes="glass-card"):
                            gr.Markdown("### 📅 Incident Volume Over Time (30 Days)")
                            plot_timeline = gr.LinePlot(x="date", y="Incidents", tooltip=["date", "Incidents"], height=300)
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### ⚠️ Incidents by Severity")
                            plot_severity = gr.BarPlot(x="Severity", y="Count", color="Severity", tooltip=["Severity", "Count"], height=300)
                    with gr.Row():
                        with gr.Column(elem_classes="glass-card"):
                            gr.Markdown("### 🔄 Current Resolution Status")
                            plot_status = gr.BarPlot(x="status", y="Count", color="status", tooltip=["status", "Count"], height=250)
                
                with gr.Tab("👥 User Directory & Deep Dive"):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### 👥 User Directory")
                            admin_users_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### ⚙️ Account Controls")
                            refresh_admin_btn = gr.Button("🔄 Sync Directory", variant="secondary")
                            delete_user_input = gr.Number(label="Target User ID", precision=0)
                            delete_user_btn = gr.Button("🚨 Terminate Account", variant="stop", elem_classes="push-bottom")
                            admin_status_msg = gr.Markdown("")
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### 🔍 Deep-Dive User Inspection")
                            inspect_incidents_table = gr.Dataframe(label="Raw Incident Submissions", interactive=False, wrap=True, elem_classes="short-table")
                            inspect_chats_table = gr.Dataframe(label="Copilot Chat Transcripts", interactive=False, wrap=True, elem_classes="short-table")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### ⚙️ Fetch Telemetry")
                            inspect_user_input = gr.Number(label="User ID to Inspect", precision=0)
                            inspect_btn = gr.Button("Fetch User History", variant="primary", elem_classes="push-bottom")
                            inspect_status_msg = gr.Markdown("")
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.Markdown("### 🎟️ Escalation & QA Tickets")
                            admin_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                        with gr.Column(scale=1, elem_classes="glass-card"):
                            gr.Markdown("### ⚙️ Resolve Tickets")
                            refresh_admin_tickets_btn = gr.Button("🔄 Sync Tickets", variant="secondary")
                            answer_ticket_id_input = gr.Number(label="Ticket ID", precision=0)
                            answer_ticket_input = gr.Textbox(label="Your Answer", lines=2)
                            answer_ticket_btn = gr.Button("Submit Answer ✅", variant="primary", elem_classes="push-bottom")

        # MAIN TABS
        with gr.Tabs(elem_id="main_tabs") as tabs_manager:
            with gr.Tab("Live Diagnosis", id="tab_diag"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📡 System Telemetry Input")
                        logs_input = gr.Textbox(label="System Logs", lines=7, placeholder="Paste your server or application logs here...")
                        with gr.Row():
                            diagnose_btn = gr.Button("Analyze ⚡", variant="primary")
                            discuss_btn = gr.Button("Discuss 💬", variant="secondary")
                            clear_btn = gr.Button("Clear 🗑️", variant="stop")
                        with gr.Row():
                            search_similar_btn = gr.Button("🔍 Find Similar Incidents", variant="secondary", size="sm")
                        gr.Examples(examples=[
                            ["[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%"],
                            ["[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"]
                        ], inputs=logs_input)
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### 📊 Diagnostics Report")
                        anomaly_out = gr.Markdown(value="*Waiting for log analysis...*", label="🔴 ANOMALY DETECTED", elem_classes="scrollable-output")
                        rc_out = gr.Markdown(value="*Waiting for log analysis...*", label="🔍 ROOT CAUSE", elem_classes="scrollable-output")
                        remed_out = gr.Markdown(value="*Waiting for log analysis...*", label="⚙️ REMEDIATION", elem_classes="scrollable-output")
                with gr.Row(visible=False) as similar_incidents_row:
                    with gr.Column(elem_classes="glass-card"):
                        gr.Markdown("### 🔗 Similar Past Incidents (ChromaDB)")
                        similar_incidents_status = gr.Markdown("")
                        similar_incidents_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                        
            with gr.Tab("💬 AI Copilot", id="tab_chat"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Session Management")
                        chat_session_dropdown = gr.Dropdown(label="Load Past Chat", choices=[], interactive=True, allow_custom_value=True)
                        refresh_chat_btn = gr.Button("🔄 Refresh List", variant="secondary")
                        new_chat_btn = gr.Button("➕ Start New Chat", variant="primary", elem_classes="push-bottom")
                    with gr.Column(scale=3, elem_classes="glass-card"):
                        chatbot_ui = gr.Chatbot(label="Aegis AI Copilot", height=400)
                        with gr.Row():
                            chat_input = gr.Textbox(show_label=False, placeholder="Ask the Copilot a question...", scale=4)
                            chat_send_btn = gr.Button("Send 🚀", variant="primary", scale=1)
                            
            with gr.Tab("My Incident History"):
                with gr.Column(elem_classes="glass-card"):
                    with gr.Row():
                        gr.Markdown("### Your Processed Incidents", scale=2)
                        refresh_btn = gr.Button("Refresh Data 🔄", variant="secondary", scale=1)
                        export_csv_btn = gr.Button("📥 Export CSV", variant="secondary", scale=1)
                    history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")
                with gr.Row(visible=False) as download_row:
                    download_file = gr.File(label="Download", visible=True)
                with gr.Row(visible=False) as resolve_incident_row:
                    with gr.Column(elem_classes="glass-card"):
                        gr.Markdown("### 🔍 Incident Details")
                        incident_details_md = gr.Markdown(value="*Select an incident to view details*")
                    with gr.Column(elem_classes="glass-card"):
                        gr.Markdown("### ✅ Resolve Incident")
                        resolve_incident_id = gr.Number(label="Incident ID", precision=0)
                        resolve_notes_input = gr.Textbox(label="Resolution Notes", lines=3, placeholder="Describe how this incident was resolved...")
                        with gr.Row():
                            resolve_btn = gr.Button("Mark as Resolved ✅", variant="primary")
                            export_selected_pdf_btn = gr.Button("📄 Download PDF Report", variant="secondary")

            with gr.Tab("🆘 Support Tickets", id="tab_support"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("### Ask an Admin / QA")
                        gr.Markdown("If the Copilot cannot resolve your issue, escalate it directly to our Root Admin team.")
                        ticket_question_input = gr.Textbox(label="Your Question or Issue", placeholder="Describe your issue clearly...", lines=6)
                        submit_ticket_btn = gr.Button("Submit Ticket 📨", variant="primary", elem_classes="push-bottom")
                    with gr.Column(scale=2, elem_classes="glass-card"):
                        with gr.Row():
                            gr.Markdown("### Your Escalation History", scale=4) 
                            refresh_my_tickets_btn = gr.Button("🔄 Sync Status", variant="secondary", scale=1)
                        my_tickets_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

            # 🔔 Notifications Tab
            with gr.Tab("🔔 Notifications"):
                with gr.Column(elem_classes="glass-card"):
                    with gr.Row():
                        gr.Markdown("### Your Recent Notifications", scale=4)
                        mark_read_btn = gr.Button("✅ Mark All Read", variant="secondary", scale=1)
                        refresh_notif_btn = gr.Button("🔄 Refresh", variant="secondary", scale=1)
                    notifications_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-scroll")

        # Footer
        with gr.Row(elem_classes="footer-container"):
            with gr.Column(scale=1):
                gr.Markdown("🛡️ **Aegis AI**", elem_classes="footer-logo")
            with gr.Column(scale=1):
                role_text = gr.Markdown("", elem_classes="footer-role")

    # --- EVENT WIRING ---
    log_show_pass.change(fn=None, inputs=[log_show_pass], js="(s) => { const el = document.querySelector('#log_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")
    reg_show_pass.change(fn=None, inputs=[reg_show_pass], js="(s) => { const el = document.querySelector('#reg_pass_input input'); if(el) el.type = s ? 'text' : 'password'; return []; }")

    clear_btn.click(
        fn=lambda: ("", "*Waiting for log analysis...*", "*Waiting for log analysis...*", "*Waiting for log analysis...*",
                    pd.DataFrame(), gr.update(visible=False), gr.update(value="")), 
        outputs=[logs_input, anomaly_out, rc_out, remed_out, similar_incidents_table, similar_incidents_row, similar_incidents_status], 
        queue=False
    )

    login_btn.click(
        fn=api_login, inputs=[log_email, log_pass], 
        outputs=[session_token, auth_view, app_view, welcome_text, role_text, admin_dashboard_view, notification_count, notifications_table]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table]
    ).then(fn=fetch_analytics, inputs=[session_token], outputs=[plot_timeline, plot_severity, plot_status]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table]
    ).then(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table]
    ).then(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])
    
    register_btn.click(
        fn=api_register, inputs=[reg_email, reg_pass, reg_name], 
        outputs=[session_token, auth_view, app_view, welcome_text, role_text, admin_dashboard_view, notification_count, notifications_table]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table]
    ).then(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])
    
    logout_btn.click(fn=logout, outputs=[
        session_token, auth_view, app_view, welcome_text, role_text, chat_session_dropdown, admin_dashboard_view,
        log_email, log_pass, log_show_pass, reg_name, reg_email, reg_pass, reg_show_pass,
        inspect_user_input, inspect_incidents_table, inspect_chats_table, inspect_status_msg,
        ticket_question_input, my_tickets_table, answer_ticket_id_input, answer_ticket_input, admin_tickets_table,
        metric_users, metric_incidents, metric_chats, plot_timeline, plot_severity, plot_status,
        similar_incidents_table, similar_incidents_row, similar_incidents_status,
        history_table, resolve_incident_row, resolve_incident_id, resolve_notes_input, incident_details_md,
        download_row, notification_count, notifications_table
    ], queue=False)

    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    discuss_btn.click(
        fn=lambda l, a: (gr.update(value=f"Anomaly:\n{l}\n\nDiagnosis:\n{a}"), [], None, gr.update(value=None), gr.update(selected="tab_chat")) if l.strip() else (gr.update(), gr.update(), gr.update(), gr.update(), gr.update()), 
        inputs=[logs_input, anomaly_out], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown, tabs_manager], queue=False
    )
    chat_send_btn.click(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    chat_input.submit(fn=send_chat_msg, inputs=[chat_input, current_chat_id, chatbot_ui, session_token], outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown])
    new_chat_btn.click(fn=lambda: ("", [], None, gr.update(value=None)), outputs=[chat_input, chatbot_ui, current_chat_id, chat_session_dropdown], queue=False)
    chat_session_dropdown.change(fn=load_chat_session, inputs=[chat_session_dropdown, session_token], outputs=[chatbot_ui, current_chat_id])
    refresh_chat_btn.click(fn=get_chat_sessions, inputs=[session_token], outputs=[chat_session_dropdown])

    refresh_admin_btn.click(fn=load_admin_data, inputs=[session_token], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table]
    ).then(fn=fetch_analytics, inputs=[session_token], outputs=[plot_timeline, plot_severity, plot_status])
        
    delete_user_btn.click(fn=purge_user, inputs=[session_token, delete_user_input], outputs=[metric_users, metric_incidents, metric_chats, admin_users_table, admin_status_msg]
    ).then(fn=clear_status, outputs=[admin_status_msg])
    inspect_btn.click(fn=inspect_user_data, inputs=[session_token, inspect_user_input], outputs=[inspect_incidents_table, inspect_chats_table, inspect_status_msg]
    ).then(fn=clear_status, outputs=[inspect_status_msg])
    refresh_admin_tickets_btn.click(fn=load_admin_tickets, inputs=[session_token], outputs=[admin_tickets_table])
    submit_ticket_btn.click(fn=submit_escalation, inputs=[ticket_question_input, session_token], outputs=[ticket_question_input, my_tickets_table])
    refresh_my_tickets_btn.click(fn=fetch_my_tickets, inputs=[session_token], outputs=[my_tickets_table])
    answer_ticket_btn.click(fn=answer_escalation, inputs=[answer_ticket_id_input, answer_ticket_input, session_token], outputs=[answer_ticket_id_input, answer_ticket_input, admin_tickets_table])

    search_similar_btn.click(fn=search_similar_incidents, inputs=[logs_input, session_token], outputs=[similar_incidents_table, similar_incidents_row, similar_incidents_status])

    def on_history_select(evt: gr.SelectData, token):
        if evt.row_value and len(evt.row_value) > 0:
            incident_id = evt.row_value[0]
            details = get_incident_details(incident_id, token)
            return details, gr.update(visible=True), gr.update(value=incident_id)
        return gr.update(), gr.update(visible=False), gr.update(value=None)
    
    history_table.select(fn=on_history_select, inputs=[session_token], outputs=[incident_details_md, resolve_incident_row, resolve_incident_id])
    
    resolve_btn.click(fn=resolve_incident, inputs=[resolve_incident_id, resolve_notes_input, session_token], outputs=[resolve_notes_input, history_table]
    ).then(fn=lambda: (gr.update(visible=False), gr.update(value=None), gr.update(value="*Incident resolved successfully!*")),
        outputs=[resolve_incident_row, resolve_incident_id, incident_details_md])

    export_csv_btn.click(fn=export_csv, inputs=[session_token], outputs=[download_file]
    ).then(fn=lambda: gr.update(visible=True), outputs=[download_row])
    
    export_selected_pdf_btn.click(fn=export_incident_pdf, inputs=[resolve_incident_id, session_token], outputs=[download_file]
    ).then(fn=lambda: gr.update(visible=True), outputs=[download_row])

    mark_read_btn.click(fn=mark_notifications_read, inputs=[session_token], outputs=[notification_count, notifications_table])
    refresh_notif_btn.click(fn=fetch_notifications, inputs=[session_token], outputs=[notifications_table, notification_count])

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=10, max_size=100).launch(share=True, server_name="0.0.0.0", server_port=7860, theme=saas_theme, css=custom_css)