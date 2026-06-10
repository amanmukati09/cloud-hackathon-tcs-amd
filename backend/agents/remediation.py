import json

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        pass
        
        # DETAILED, ACTIONABLE remediation plans
        self.REMEDIATION = {
            ("error_event", "nginx"): {
                "immediate_actions": [
                    "Check Nginx error log: tail -f /var/log/nginx/error.log",
                    "Verify upstream services are responding",
                    "Check Nginx configuration: nginx -t",
                    "Review recent application changes"
                ],
                "automated_actions": [
                    {"action": "Reload Nginx config gracefully: nginx -s reload", "risk_level": "LOW"},
                    {"action": "Restart Nginx worker processes", "risk_level": "MEDIUM"}
                ],
                "escalation_needed": False,
                "estimated_recovery_time": "5-10 minutes",
                "prevention_measures": [
                    "Implement request validation middleware",
                    "Set up real-time error alerts via monitoring",
                    "Regular Nginx configuration review",
                    "Load testing before production deployment"
                ]
            },
            ("error_event", "database"): {
                "immediate_actions": [
                    "Check database connectivity: mysql -u user -p -h host",
                    "Review recent slow queries in logs",
                    "Check available disk space: df -h",
                    "Verify database service status: systemctl status mysql/postgres"
                ],
                "automated_actions": [
                    {"action": "Kill long-running queries", "risk_level": "MEDIUM"},
                    {"action": "Rebuild corrupted indexes", "risk_level": "HIGH"}
                ],
                "escalation_needed": False,
                "estimated_recovery_time": "10-20 minutes",
                "prevention_measures": [
                    "Regular index maintenance and optimization",
                    "Query performance monitoring (enable slow query log)",
                    "Automated backups and replication",
                    "Regular integrity checks"
                ]
            },
            ("critical_event", "storage"): {
                "immediate_actions": [
                    "Check disk usage: df -h && du -sh /*",
                    "Identify large files: find / -size +100M -type f 2>/dev/null",
                    "Clear old logs: rm /var/log/old-*.log",
                    "Remove temporary files: rm -rf /tmp/*"
                ],
                "automated_actions": [
                    {"action": "Enable log rotation immediately", "risk_level": "LOW"},
                    {"action": "Archive old data to external storage", "risk_level": "MEDIUM"}
                ],
                "escalation_needed": True,
                "estimated_recovery_time": "20-30 minutes",
                "prevention_measures": [
                    "Configure automated log rotation (logrotate)",
                    "Set up disk usage alerts (alert at 80%, critical at 90%)",
                    "Regular cleanup of temporary files",
                    "Archive old data periodically to cold storage"
                ]
            },
            ("service_crash", "nginx"): {
                "immediate_actions": [
                    "Check system logs for OOM: dmesg | grep nginx",
                    "Verify memory availability: free -h",
                    "Check for core dumps: ls -la /var/crash/",
                    "Review Nginx error log for segfault"
                ],
                "automated_actions": [
                    {"action": "Restart Nginx service: systemctl restart nginx", "risk_level": "LOW"},
                    {"action": "Increase memory limits if OOM detected", "risk_level": "MEDIUM"}
                ],
                "escalation_needed": False,
                "estimated_recovery_time": "2-5 minutes",
                "prevention_measures": [
                    "Set appropriate memory limits: ulimit -m",
                    "Update Nginx to latest stable version",
                    "Enable core dump for debugging: ulimit -c unlimited",
                    "Monitor memory usage trends"
                ]
            },
            ("memory_high", "database"): {
                "immediate_actions": [
                    "Check memory usage: free -h && ps aux | grep mysql/postgres",
                    "Identify memory-consuming queries",
                    "Reduce buffer pool size temporarily",
                    "Kill non-critical connections"
                ],
                "automated_actions": [
                    {"action": "Flush cache/buffers", "risk_level": "MEDIUM"},
                    {"action": "Restart database service to reclaim memory", "risk_level": "HIGH"}
                ],
                "escalation_needed": False,
                "estimated_recovery_time": "5-15 minutes",
                "prevention_measures": [
                    "Configure appropriate buffer pool size based on available memory",
                    "Implement connection pooling",
                    "Monitor memory usage and set alerts",
                    "Regular garbage collection tuning"
                ]
            },
            ("cpu_spike", "database"): {
                "immediate_actions": [
                    "Identify expensive queries: SHOW PROCESSLIST;",
                    "Check query execution plan: EXPLAIN <query>",
                    "Look for missing indexes",
                    "Monitor CPU usage: top -p <pid>"
                ],
                "automated_actions": [
                    {"action": "Kill long-running queries: KILL <id>", "risk_level": "MEDIUM"},
                    {"action": "Add missing indexes", "risk_level": "MEDIUM"}
                ],
                "escalation_needed": False,
                "estimated_recovery_time": "10-20 minutes",
                "prevention_measures": [
                    "Analyze and optimize slow queries",
                    "Create appropriate indexes on frequently searched columns",
                    "Implement query caching",
                    "Regular performance profiling and optimization"
                ]
            },
            ("service_down", "nginx"): {
                "immediate_actions": [
                    "Check service status: systemctl status nginx",
                    "Check if port is in use: netstat -tulnp | grep 80/443",
                    "Verify configuration: nginx -t",
                    "Check service logs: journalctl -u nginx -n 50"
                ],
                "automated_actions": [
                    {"action": "Start Nginx service: systemctl start nginx", "risk_level": "LOW"},
                    {"action": "Force kill existing processes and restart", "risk_level": "MEDIUM"}
                ],
                "escalation_needed": True,
                "estimated_recovery_time": "5-10 minutes",
                "prevention_measures": [
                    "Enable automatic service restart on failure",
                    "Monitor service health with watchdog",
                    "Set up instant alerts for service down",
                    "Implement health check endpoints"
                ]
            },
        }
    
    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        """Smart remediation with component-specific actions"""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        component = anomaly.get("affected_component", "system")
        
        # Try specific scenario
        key = (anomaly_type, component)
        if key in self.REMEDIATION:
            return self.REMEDIATION[key]
        
        # Try just anomaly type
        for k, v in self.REMEDIATION.items():
            if k[0] == anomaly_type:
                return v
        
        # Generic fallback
        return {
            "immediate_actions": [
                f"Investigate {anomaly_type} in {component}",
                "Check system logs",
                "Monitor system metrics",
                "Notify operations team"
            ],
            "automated_actions": [{"action": "Monitor and log incident", "risk_level": "LOW"}],
            "escalation_needed": True,
            "estimated_recovery_time": "15-30 minutes",
            "prevention_measures": [
                "Implement comprehensive monitoring",
                "Regular system health checks",
                "Automated alerting on critical events"
            ]
        }

if __name__ == "__main__":
    remediation = RemediationAgent()
    
    test_cases = [
        ({"anomaly_type": "error_event", "affected_component": "nginx"}, {}),
        ({"anomaly_type": "critical_event", "affected_component": "storage"}, {}),
        ({"anomaly_type": "memory_high", "affected_component": "database"}, {}),
    ]
    
    for anomaly, root_cause in test_cases:
        result = remediation.suggest_remediation(anomaly, root_cause)
        print(f"{anomaly}:")
        print(json.dumps(result, indent=2))
        print()
