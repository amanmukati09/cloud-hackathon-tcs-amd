import json
import re

class MonitorAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass
    
    def detect_anomaly(self, logs: list[str]) -> dict:
        """PURE PATTERN-BASED DETECTION - Fast & Reliable"""
        logs_text = "\n".join(logs)
        logs_upper = logs_text.upper()
        
        # AGGRESSIVE PATTERNS
        critical_patterns = [
            (r"CRITICAL", "critical_event", "CRITICAL"),
            (r"DOWN|UNAVAILABLE|FAILED|FATAL", "service_down", "CRITICAL"),
            (r"99|100(?=%)", "cpu_spike", "CRITICAL"),
        ]
        
        high_patterns = [
            (r"ERROR", "error_event", "HIGH"),
            (r"CRASH|EXCEPTION", "crash", "HIGH"),
            (r"TIMEOUT|CONNECTION.*FAIL", "timeout", "HIGH"),
            (r"9[0-8](?=%)", "memory_high", "HIGH"),
        ]
        
        medium_patterns = [
            (r"WARNING", "warning", "MEDIUM"),
            (r"LATENCY|SLOW", "latency", "MEDIUM"),
        ]
        
        # Check CRITICAL first
        for pattern, anomaly_type, severity in critical_patterns:
            if re.search(pattern, logs_upper):
                return {
                    "anomaly_detected": True,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "affected_component": self._get_component(logs),
                    "description": f"Pattern detected: {anomaly_type.replace('_', ' ').title()}"
                }
        
        # Check HIGH
        for pattern, anomaly_type, severity in high_patterns:
            if re.search(pattern, logs_upper):
                return {
                    "anomaly_detected": True,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "affected_component": self._get_component(logs),
                    "description": f"Pattern detected: {anomaly_type.replace('_', ' ').title()}"
                }
        
        # Check MEDIUM
        for pattern, anomaly_type, severity in medium_patterns:
            if re.search(pattern, logs_upper):
                return {
                    "anomaly_detected": True,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "affected_component": self._get_component(logs),
                    "description": f"Pattern detected: {anomaly_type.replace('_', ' ').title()}"
                }
        
        return {"anomaly_detected": False}
    
    def _get_component(self, logs: list[str]) -> str:
        """Extract component from logs"""
        logs_text = "\n".join(logs).lower()
        components = {
            "nginx": "nginx",
            "postgres": "database",
            "mysql": "database",
            "mongodb": "database",
            "db": "database",
            "api": "api",
            "redis": "cache",
            "cache": "cache",
            "disk": "storage",
            "cpu": "cpu",
            "memory": "memory",
        }
        
        for keyword, component in components.items():
            if keyword in logs_text:
                return component
        
        return "system"

if __name__ == "__main__":
    monitor = MonitorAgent()
    
    # Test cases
    tests = [
        ["[ERROR] nginx worker crashed", "[WARNING] memory: 90%", "[ERROR] cpu: 95%"],
        ["[CRITICAL] database connection timeout", "[ERROR] query failed"],
        ["[INFO] system running normally"],
        ["[WARNING] disk usage high", "[WARNING] api latency 5000ms"],
    ]
    
    for test_logs in tests:
        result = monitor.detect_anomaly(test_logs)
        print(f"Logs: {test_logs[0]}")
        print(f"Result: {json.dumps(result, indent=2)}\n")
