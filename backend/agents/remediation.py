import requests
import json
import time

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
        
        # Fallback plans
        self.FALLBACK = {
            "error_event": {
                "immediate_actions": ["Review error logs", "Check dependencies", "Restart service"],
                "automated_actions": [{"action": "Auto-restart", "risk_level": "LOW"}],
                "escalation_needed": False,
                "estimated_recovery_time": "5-10 minutes",
                "prevention_measures": ["Error monitoring", "Dependency checks", "Health alerts"]
            },
            "critical_event": {
                "immediate_actions": ["Activate incident response", "Notify team", "Enable verbose logging"],
                "automated_actions": [{"action": "Failover to backup", "risk_level": "HIGH"}],
                "escalation_needed": True,
                "estimated_recovery_time": "15-30 minutes",
                "prevention_measures": ["Disaster recovery", "Redundancy", "Load balancing"]
            },
            "service_crash": {
                "immediate_actions": ["Restart service", "Check resources", "Review logs"],
                "automated_actions": [{"action": "Auto-restart on failure", "risk_level": "LOW"}],
                "escalation_needed": False,
                "estimated_recovery_time": "2-5 minutes",
                "prevention_measures": ["Memory profiling", "Resource limits", "Health checks"]
            },
            "timeout": {
                "immediate_actions": ["Check network", "Review queries", "Increase timeout"],
                "automated_actions": [{"action": "Enable caching", "risk_level": "LOW"}],
                "escalation_needed": False,
                "estimated_recovery_time": "5-15 minutes",
                "prevention_measures": ["Query optimization", "Connection pooling", "Caching"]
            },
            "memory_high": {
                "immediate_actions": ["Free memory", "Kill non-essential", "Check leaks"],
                "automated_actions": [{"action": "Clear cache", "risk_level": "LOW"}],
                "escalation_needed": False,
                "estimated_recovery_time": "5 minutes",
                "prevention_measures": ["Memory monitoring", "GC tuning", "Resource limits"]
            },
            "cpu_spike": {
                "immediate_actions": ["Identify heavy process", "Enable throttling", "Review jobs"],
                "automated_actions": [{"action": "Load balancing", "risk_level": "MEDIUM"}],
                "escalation_needed": False,
                "estimated_recovery_time": "5-10 minutes",
                "prevention_measures": ["CPU profiling", "Load testing", "Auto-scaling"]
            }
        }
    
    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        """Intelligent remediation with LLM + fallback"""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        
        # Try LLM first
        try:
            result = self._llm_remediation(anomaly, root_cause)
            if result:
                return result
        except Exception as e:
            print(f"LLM remediation failed: {e}, using fallback")
        
        # Fallback to knowledge base
        if anomaly_type in self.FALLBACK:
            return self.FALLBACK[anomaly_type]
        
        return {
            "immediate_actions": ["Investigate", "Monitor"],
            "automated_actions": [{"action": "Monitor", "risk_level": "LOW"}],
            "escalation_needed": True,
            "estimated_recovery_time": "Unknown",
            "prevention_measures": ["Implement monitoring"]
        }
    
    def _llm_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        """Call LLM with SHORT timeout"""
        prompt = f"""Suggest remediation. RESPOND ONLY AS JSON.

Issue: {anomaly.get('anomaly_type')} - {root_cause.get('root_cause', 'Unknown')}
Severity: {anomaly.get('severity')}

JSON response (NO OTHER TEXT):
{{"immediate_actions": ["action1", "action2"], "automated_actions": [{{"action": "fix", "risk_level": "LOW"}}], "escalation_needed": false, "estimated_recovery_time": "5 minutes", "prevention_measures": ["prevent1"]}}"""
        
        start = time.time()
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=15  # SHORT timeout
        )
        elapsed = time.time() - start
        print(f"LLM remediation took {elapsed:.1f}s")
        
        if response.status_code == 200:
            try:
                text = response.json()["response"].strip()
                result = json.loads(text)
                if "immediate_actions" in result:
                    return result
            except:
                pass
        
        return None

if __name__ == "__main__":
    remediation = RemediationAgent()
    anomaly = {"anomaly_type": "critical_event", "severity": "CRITICAL"}
    root_cause = {"root_cause": "System overload"}
    result = remediation.suggest_remediation(anomaly, root_cause)
    print(json.dumps(result, indent=2))
