import requests
import json
import os

class AlertManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", None)
            cls._instance.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL", None)
        return cls._instance
    
    def configure(self, slack_url: str = None, teams_url: str = None):
        """Update webhook URLs."""
        if slack_url:
            self.slack_webhook = slack_url
        if teams_url:
            self.teams_webhook = teams_url
    
    def send_slack_alert(self, title: str, message: str, severity: str) -> bool:
        """Send alert to Slack channel."""
        if not self.slack_webhook:
            print("Slack webhook not configured")
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
                "footer": "AegisAI Incident Management"
            }]
        }
        
        try:
            res = requests.post(self.slack_webhook, json=payload, timeout=10)
            print(f"Slack response: {res.status_code} - {res.text}")
            return res.status_code == 200 and res.text == "ok"
        except Exception as e:
            print(f"Slack alert failed: {e}")
            return False
    
    def send_teams_alert(self, title: str, message: str, severity: str) -> bool:
        """Send alert to Microsoft Teams."""
        if not self.teams_webhook:
            print("Teams webhook not configured")
            return False
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "#ef4444" if severity.upper() in ["CRITICAL", "HIGH"] else "#10b981",
            "summary": title,
            "sections": [{
                "activityTitle": f"🚨 {title}",
                "activitySubtitle": f"Severity: {severity.upper()}",
                "text": message,
                "facts": [
                    {"name": "Platform", "value": "AegisAI"},
                    {"name": "Severity", "value": severity.upper()}
                ]
            }]
        }
        
        try:
            res = requests.post(self.teams_webhook, json=payload, timeout=10)
            print(f"Teams response: {res.status_code}")
            return res.status_code == 200
        except Exception as e:
            print(f"Teams alert failed: {e}")
            return False
    
    def send_incident_alert(self, incident_data: dict) -> dict:
        """Send alert through all configured channels."""
        results = {}
        title = f"Incident #{incident_data.get('id', 'NEW')}: {incident_data.get('anomaly_type', 'Unknown')}"
        message = f"""
Incident Details:
• Type: {incident_data.get('anomaly_type', 'Unknown')}
• Severity: {incident_data.get('severity', 'UNKNOWN')}
• Component: {incident_data.get('affected_component', 'Unknown')}
• Description: {incident_data.get('description', 'No description')}
• Root Cause: {incident_data.get('root_cause', 'Pending')}
• Remediation: {incident_data.get('remediation', 'Pending')}
• Time: {incident_data.get('timestamp', 'Now')}
        """.strip()
        
        severity = incident_data.get('severity', 'MEDIUM')
        
        print(f"\n🔔 Alerting: {title} (Severity: {severity})")
        print(f"Slack webhook: {'Configured' if self.slack_webhook else 'Not configured'}")
        print(f"Teams webhook: {'Configured' if self.teams_webhook else 'Not configured'}")
        
        if self.slack_webhook:
            results["slack"] = self.send_slack_alert(title, message, severity)
        
        if self.teams_webhook:
            results["teams"] = self.send_teams_alert(title, message, severity)
        
        print(f"Alert results: {results}")
        return results