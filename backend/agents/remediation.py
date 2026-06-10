import json

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass

    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        severity = anomaly.get("severity", "LOW")
        
        if severity == "CRITICAL":
            return {
                "immediate_actions": ["Activate incident response", "Notify on-call engineering team"],
                "automated_actions": [{"action": "Failover to backup system", "risk_level": "HIGH"}],
                "escalation_needed": True,
                "estimated_recovery_time": "15-30 minutes",
                "prevention_measures": ["Review Disaster Recovery plan", "Enhance load balancing"]
            }
        elif severity == "HIGH":
            return {
                "immediate_actions": ["Check system status: systemctl status", "Verify port bindings"],
                "automated_actions": [{"action": "Force restart affected worker/service", "risk_level": "MEDIUM"}],
                "escalation_needed": False,
                "estimated_recovery_time": "5-10 minutes",
                "prevention_measures": ["Enable automatic service restart", "Set up watchdog monitoring"]
            }
        else:
            return {
                "immediate_actions": ["Monitor system metrics closely"],
                "automated_actions": [{"action": "Clear cache", "risk_level": "LOW"}],
                "escalation_needed": False,
                "estimated_recovery_time": "1-2 minutes",
                "prevention_measures": ["Implement request validation", "Adjust resource limits"]
            }

if __name__ == "__main__":
    remediation = RemediationAgent()