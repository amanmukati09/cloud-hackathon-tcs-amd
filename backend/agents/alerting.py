import requests
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class AlertManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", None)
            cls._instance.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL", None)
            cls._instance.pagerduty_key = os.getenv("PAGERDUTY_ROUTING_KEY", None)
            cls._instance.opsgenie_key = os.getenv("OPSGENIE_API_KEY", None)
            cls._instance.smtp_config = {
                "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME", None),
                "password": os.getenv("SMTP_PASSWORD", None),
                "from_email": os.getenv("SMTP_FROM", "aegisai@alerts.com"),
                "to_emails": os.getenv("ALERT_EMAILS", "").split(",") if os.getenv("ALERT_EMAILS") else []
            }
        return cls._instance
    
    def configure(self, slack_url=None, teams_url=None, pagerduty_key=None, opsgenie_key=None, smtp_config=None):
        """Update all webhook/alert configurations."""
        if slack_url:
            self.slack_webhook = slack_url
        if teams_url:
            self.teams_webhook = teams_url
        if pagerduty_key:
            self.pagerduty_key = pagerduty_key
        if opsgenie_key:
            self.opsgenie_key = opsgenie_key
        if smtp_config:
            self.smtp_config.update(smtp_config)
    
    # ── Slack ─────────────────────────────────────────
    def send_slack_alert(self, title: str, message: str, severity: str) -> bool:
        if not self.slack_webhook:
            return False
        colors = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
        color = colors.get(severity.upper(), "#6b7280")
        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 {title}",
                "text": message,
                "fields": [
                    {"title": "Severity", "value": severity.upper(), "short": True},
                    {"title": "Platform", "value": "AegisAI", "short": True}
                ],
                "footer": "AegisAI Incident Management",
                "ts": int(datetime.now().timestamp())
            }]
        }
        try:
            res = requests.post(self.slack_webhook, json=payload, timeout=10)
            return res.status_code == 200 and res.text == "ok"
        except Exception as e:
            print(f"Slack alert failed: {e}")
            return False
    
    # ── Microsoft Teams ───────────────────────────────
    def send_teams_alert(self, title: str, message: str, severity: str) -> bool:
        if not self.teams_webhook:
            return False
        theme_color = "#ef4444" if severity.upper() in ["CRITICAL", "HIGH"] else "#10b981"
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "sections": [{
                "activityTitle": f"🚨 {title}",
                "activitySubtitle": f"Severity: {severity.upper()} | Platform: AegisAI",
                "text": message
            }]
        }
        try:
            res = requests.post(self.teams_webhook, json=payload, timeout=10)
            return res.status_code == 200
        except Exception as e:
            print(f"Teams alert failed: {e}")
            return False
    

    # ── Email (SMTP) ──────────────────────────────────
    def send_email_alert(self, subject: str, body: str, severity: str, to_emails: list = None, source: str = None) -> bool:
        if not self.smtp_config.get("username") or not self.smtp_config.get("password"):
            print("⚠️ SMTP not configured - email not sent")
            return False
        
        recipients = to_emails or self.smtp_config.get("to_emails", [])
        if not recipients:
            print("⚠️ No recipients configured")
            return False
        
        colors = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
        color = colors.get(severity.upper(), "#6b7280")
        
        # Professional subject line
        site_info = f" - {source}" if source else ""
        email_subject = f"🚨 [{severity}] AegisAI Alert{site_info}: {subject}"
        
        html = f"""
        <html>
        <body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:0;margin:0;background:#0f172a;">
            <div style="max-width:600px;margin:20px auto;background:#1e293b;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.3);">
                <!-- Header -->
                <div style="background:{color};padding:20px 24px;">
                    <h2 style="margin:0;color:white;font-size:1.3rem;">🚨 {severity} Incident Detected</h2>
                    <p style="margin:4px 0 0 0;color:rgba(255,255,255,0.8);font-size:0.85rem;">{email_subject}</p>
                </div>
                
                <!-- Body -->
                <div style="padding:20px 24px;">
                    <table style="width:100%;border-collapse:collapse;">
                        <tr>
                            <td style="padding:8px 0;color:#94a3b8;font-size:0.85rem;width:120px;">Severity</td>
                            <td style="padding:8px 0;"><span style="background:{color}20;color:{color};padding:3px 10px;border-radius:12px;font-weight:700;font-size:0.8rem;">{severity.upper()}</span></td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0;color:#94a3b8;font-size:0.85rem;">Time</td>
                            <td style="padding:8px 0;color:#e2e8f0;font-size:0.85rem;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0;color:#94a3b8;font-size:0.85rem;">Platform</td>
                            <td style="padding:8px 0;color:#38bdf8;font-size:0.85rem;">AegisAI SRE Platform</td>
                        </tr>
                    </table>
                    
                    <hr style="border-color:rgba(255,255,255,0.06);margin:16px 0;">
                    
                    <div style="background:#0f172a;padding:16px;border-radius:10px;border:1px solid rgba(255,255,255,0.05);">
                        <pre style="margin:0;color:#e2e8f0;font-family:'SF Mono',monospace;font-size:0.8rem;white-space:pre-wrap;line-height:1.5;">{body}</pre>
                    </div>
                    
                    <hr style="border-color:rgba(255,255,255,0.06);margin:16px 0;">
                    
                    <div style="text-align:center;">
                        <a href="http://localhost:7860" style="display:inline-block;padding:10px 24px;background:{color};color:white;text-decoration:none;border-radius:8px;font-weight:600;font-size:0.85rem;">🔍 View in Live Monitor</a>
                    </div>
                    
                    <p style="color:#64748b;font-size:0.7rem;text-align:center;margin-top:16px;">
                        This is an automated alert from <b>AegisAI</b>. Configure notification settings in Admin Dashboard.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_subject
            msg['From'] = self.smtp_config["from_email"]
            msg['To'] = ", ".join(recipients)
            msg.attach(MIMEText(html, 'html'))
            
            server = smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"], timeout=10)
            server.starttls()
            server.login(self.smtp_config["username"], self.smtp_config["password"])
            server.send_message(msg)
            server.quit()
            print(f"✅ Email sent to {len(recipients)} recipients")
            return True
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False
    
    # ── PagerDuty ─────────────────────────────────────
    def send_pagerduty_alert(self, title: str, message: str, severity: str, incident_id: str = None) -> bool:
        if not self.pagerduty_key:
            return False
        
        pagerduty_severity = {
            "CRITICAL": "critical",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "info"
        }
        
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": title,
                "source": "AegisAI",
                "severity": pagerduty_severity.get(severity.upper(), "warning"),
                "custom_details": {
                    "message": message,
                    "incident_id": incident_id or "N/A",
                    "platform": "AegisAI"
                }
            }
        }
        
        try:
            res = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            return res.status_code == 202
        except Exception as e:
            print(f"PagerDuty alert failed: {e}")
            return False
    
    # ── Opsgenie ──────────────────────────────────────
    def send_opsgenie_alert(self, title: str, message: str, severity: str, incident_id: str = None) -> bool:
        if not self.opsgenie_key:
            return False
        
        opsgenie_priority = {
            "CRITICAL": "P1",
            "HIGH": "P2",
            "MEDIUM": "P3",
            "LOW": "P4"
        }
        
        payload = {
            "message": title,
            "description": message,
            "priority": opsgenie_priority.get(severity.upper(), "P3"),
            "source": "AegisAI",
            "tags": ["aegisai", severity.lower()],
            "details": {
                "incident_id": incident_id or "N/A",
                "platform": "AegisAI"
            }
        }
        
        try:
            res = requests.post(
                "https://api.opsgenie.com/v2/alerts",
                json=payload,
                headers={
                    "Authorization": f"GenieKey {self.opsgenie_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            return res.status_code == 202
        except Exception as e:
            print(f"Opsgenie alert failed: {e}")
            return False
    
    # ── Send to all configured channels ───────────────
    def send_incident_alert(self, incident_data: dict, source: str = None) -> dict:
        results = {}
        
        title = f"{incident_data.get('anomaly_type', 'Unknown')} - {incident_data.get('affected_component', 'Unknown')}"
        message = f"""
    Incident Details:
    • Type: {incident_data.get('anomaly_type', 'Unknown')}
    • Severity: {incident_data.get('severity', 'UNKNOWN')}
    • Component: {incident_data.get('affected_component', 'Unknown')}
    • Description: {incident_data.get('description', 'No description')}
    • Root Cause: {incident_data.get('root_cause', 'Pending')}
    • Remediation: {incident_data.get('remediation', 'Check dashboard')}
    • Time: {incident_data.get('timestamp', 'Now')}
        """.strip()
        
        severity = incident_data.get('severity', 'MEDIUM')
        
        # Email with source info
        results["email"] = self.send_email_alert(title, message, severity, source=source)
        results["slack"] = self.send_slack_alert(title, message, severity)
        results["teams"] = self.send_teams_alert(title, message, severity)
        
        print(f"📧 Alert results: {results}")
        return results