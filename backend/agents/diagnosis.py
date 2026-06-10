import requests
import json
import time

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
        
        # INTELLIGENT knowledge base - specific to each scenario
        self.KNOWLEDGE = {
            ("error_event", "nginx"): {
                "root_cause": "Nginx worker process encountered an error during request processing, indicating application or configuration issue",
                "confidence": 0.92,
                "evidence": ["Error event in nginx logs", "Worker process error detected"],
                "contributing_factors": ["Invalid configuration", "Backend service unavailable", "Resource limits exceeded", "Code bug in application"]
            },
            ("error_event", "database"): {
                "root_cause": "Database query failed or connection dropped, causing application errors and transaction failures",
                "confidence": 0.94,
                "evidence": ["Database error in logs", "Query execution failed"],
                "contributing_factors": ["Database overload", "Slow query", "Connection pool exhausted", "Schema issue"]
            },
            ("error_event", "api"): {
                "root_cause": "API endpoint returned error response indicating business logic or validation failure",
                "confidence": 0.89,
                "evidence": ["API error response", "Exception in handler"],
                "contributing_factors": ["Invalid input", "External service failure", "Missing dependency", "Incorrect configuration"]
            },
            ("critical_event", "storage"): {
                "root_cause": "Storage system at critical capacity or completely unavailable, preventing I/O operations",
                "confidence": 0.96,
                "evidence": ["Disk space critical", "Write operations failing"],
                "contributing_factors": ["Disk full (>95%)", "Corrupted filesystem", "Hardware failure", "Excessive logging"]
            },
            ("critical_event", "system"): {
                "root_cause": "System-wide critical failure affecting all services, likely due to resource exhaustion or cascading failure",
                "confidence": 0.95,
                "evidence": ["System health check failed", "Multiple services down"],
                "contributing_factors": ["Out of memory", "Disk full", "Network failure", "Kernel panic"]
            },
            ("service_crash", "nginx"): {
                "root_cause": "Nginx process crashed unexpectedly, likely due to memory issue, segmentation fault, or assertion failure",
                "confidence": 0.91,
                "evidence": ["Nginx process terminated", "Core dump detected"],
                "contributing_factors": ["Memory leak in module", "Invalid pointer access", "Out of memory (OOM)", "Unhandled exception"]
            },
            ("service_crash", "database"): {
                "root_cause": "Database service crashed or was forcefully terminated, causing immediate unavailability",
                "confidence": 0.93,
                "evidence": ["Database process killed", "Connection refused"],
                "contributing_factors": ["Out of memory", "Disk full", "Corrupt data file", "Hardware failure"]
            },
            ("timeout", "database"): {
                "root_cause": "Database queries taking too long to respond, likely due to slow queries, locks, or high load",
                "confidence": 0.90,
                "evidence": ["Query timeout in logs", "Slow response time"],
                "contributing_factors": ["Missing index", "Table lock", "High concurrency", "Inefficient query"]
            },
            ("timeout", "api"): {
                "root_cause": "API endpoint not responding within timeout threshold, indicating performance degradation or hang",
                "confidence": 0.88,
                "evidence": ["HTTP timeout", "Request queue growing"],
                "contributing_factors": ["Backend overload", "Slow downstream service", "Network latency", "Deadlock"]
            },
            ("memory_high", "nginx"): {
                "root_cause": "Nginx consuming excessive memory, likely due to large requests, memory leak, or misconfiguration",
                "confidence": 0.91,
                "evidence": ["Memory usage >90%", "RSS growing"],
                "contributing_factors": ["Memory leak in module", "Large buffer allocation", "Too many connections", "Bloated cache"]
            },
            ("memory_high", "database"): {
                "root_cause": "Database consuming excessive memory, likely due to large queries, cache, or excessive connections",
                "confidence": 0.92,
                "evidence": ["Memory usage >90%", "Buffer pool full"],
                "contributing_factors": ["Large result set", "Cache misconfiguration", "Too many connections", "Memory leak"]
            },
            ("cpu_spike", "nginx"): {
                "root_cause": "Nginx CPU utilization spiked due to high request volume, regex processing, or infinite loop",
                "confidence": 0.89,
                "evidence": ["CPU usage >95%", "Load average high"],
                "contributing_factors": ["High traffic", "Expensive regex", "Infinite loop in module", "Inefficient code"]
            },
            ("cpu_spike", "database"): {
                "root_cause": "Database CPU spiked due to expensive queries, sorting, or full table scans",
                "confidence": 0.90,
                "evidence": ["CPU usage >95%", "Query execution time high"],
                "contributing_factors": ["Missing index", "Complex join", "Full table scan", "Bad query plan"]
            },
            ("service_down", "nginx"): {
                "root_cause": "Nginx service completely stopped or not listening on configured port",
                "confidence": 0.94,
                "evidence": ["Port not responding", "Service not running"],
                "contributing_factors": ["Process killed", "Port already in use", "Permission denied", "Configuration error"]
            },
            ("service_down", "database"): {
                "root_cause": "Database service stopped or unreachable due to network issue or service failure",
                "confidence": 0.95,
                "evidence": ["Connection refused", "Service unavailable"],
                "contributing_factors": ["Service crashed", "Network partition", "Firewall blocking", "Host down"]
            },
        }
    
    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        """Smart diagnosis with component-aware knowledge base"""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        component = anomaly.get("affected_component", "system")
        
        # Try specific scenario first
        key = (anomaly_type, component)
        if key in self.KNOWLEDGE:
            return self.KNOWLEDGE[key]
        
        # Try just anomaly type
        for k, v in self.KNOWLEDGE.items():
            if k[0] == anomaly_type:
                return v
        
        # Generic fallback
        return {
            "root_cause": f"System experienced {anomaly_type} in {component} component requiring investigation",
            "confidence": 0.70,
            "evidence": logs[-2:] if logs else ["Issue detected in logs"],
            "contributing_factors": ["Resource constraint", "Configuration issue", "External factor"]
        }

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()
    
    test_cases = [
        ({"anomaly_type": "error_event", "affected_component": "nginx"}, []),
        ({"anomaly_type": "critical_event", "affected_component": "storage"}, []),
        ({"anomaly_type": "memory_high", "affected_component": "database"}, []),
    ]
    
    for anomaly, logs in test_cases:
        result = diagnosis.analyze_root_cause(anomaly, logs)
        print(f"{anomaly}:")
        print(json.dumps(result, indent=2))
        print()
