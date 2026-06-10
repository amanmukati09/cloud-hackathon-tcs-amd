import json

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass
    
    # Knowledge base for root causes
    ROOT_CAUSES = {
        "error_event": {
            "root_cause": "Application error detected in system logs indicating service malfunction or failure",
            "confidence": 0.90,
            "evidence": ["Error event detected in logs", "Service processing failure"],
            "contributing_factors": ["Code bug", "Resource constraint", "Dependency failure"]
        },
        "critical_event": {
            "root_cause": "Critical system failure requiring immediate attention and remediation",
            "confidence": 0.95,
            "evidence": ["Critical event flag in logs", "System health check failed"],
            "contributing_factors": ["System overload", "Resource exhaustion", "Hardware failure"]
        },
        "service_crash": {
            "root_cause": "Service process terminated unexpectedly due to crash or memory issue",
            "confidence": 0.92,
            "evidence": ["Process terminated", "Core dump detected"],
            "contributing_factors": ["Memory leak", "Segmentation fault", "Out of memory"]
        },
        "service_down": {
            "root_cause": "Service is completely unavailable and not responding to requests",
            "confidence": 0.95,
            "evidence": ["Service not responding", "Connection refused"],
            "contributing_factors": ["Network failure", "Service stopped", "Port in use"]
        },
        "timeout": {
            "root_cause": "Connection or request timeout indicating performance degradation or unavailability",
            "confidence": 0.88,
            "evidence": ["Timeout detected", "Response time exceeded"],
            "contributing_factors": ["High latency", "Network congestion", "Service overload"]
        },
        "memory_high": {
            "root_cause": "Memory usage has reached critical levels causing potential system degradation",
            "confidence": 0.93,
            "evidence": ["Memory usage above 90%", "Swap in use"],
            "contributing_factors": ["Memory leak", "Large dataset processing", "Insufficient memory allocation"]
        },
        "cpu_spike": {
            "root_cause": "CPU usage has spiked to critical levels indicating resource contention",
            "confidence": 0.91,
            "evidence": ["CPU usage above 95%", "Load average high"],
            "contributing_factors": ["Infinite loop", "Heavy computation", "Context switching"]
        },
        "latency": {
            "root_cause": "System latency has increased indicating performance issues",
            "confidence": 0.85,
            "evidence": ["Response time increased", "Request queue growing"],
            "contributing_factors": ["Network delay", "Database slow query", "Resource contention"]
        },
        "disk_full": {
            "root_cause": "Disk space has reached critical levels preventing normal operations",
            "confidence": 0.96,
            "evidence": ["Disk usage above 95%", "Write operations failing"],
            "contributing_factors": ["Log file growth", "Large temporary files", "Insufficient cleanup"]
        }
    }
    
    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        """Instant root cause analysis using knowledge base"""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        
        if anomaly_type in self.ROOT_CAUSES:
            return self.ROOT_CAUSES[anomaly_type]
        
        # Fallback
        return {
            "root_cause": "Unknown system issue detected",
            "confidence": 0.5,
            "evidence": logs[-2:],
            "contributing_factors": ["Insufficient diagnostic data"]
        }

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()
    
    anomaly = {"anomaly_type": "critical_event", "severity": "CRITICAL"}
    result = diagnosis.analyze_root_cause(anomaly, [])
    print(json.dumps(result, indent=2))
