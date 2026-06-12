import subprocess
import shlex
import json
import requests

class RemediationAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        # 🆕 Safe commands whitelist
        self.safe_commands = [
            "systemctl status", "systemctl restart", "systemctl start", "systemctl stop",
            "nginx -t", "nginx -s reload", "df -h", "free -m", "top -bn1",
            "ps aux", "netstat -tlnp", "ss -tlnp", "journalctl", "tail", "head",
            "grep", "cat", "ls", "pwd", "uptime", "dmesg", "docker ps", "docker logs"
        ]
    
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is in the safe whitelist."""
        cmd_base = command.strip().split()[0] if command.strip() else ""
        for safe in self.safe_commands:
            if command.strip().startswith(safe):
                return True
        return False
    
    def execute_remediation(self, command: str) -> dict:
        """Execute a remediation command if it's safe."""
        if not self.is_safe_command(command):
            return {
                "success": False,
                "output": "🚨 BLOCKED: Command not in safe whitelist.",
                "command": command
            }
        
        try:
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            return {
                "success": result.returncode == 0,
                "output": result.stdout[:1000] if result.stdout else result.stderr[:1000],
                "return_code": result.returncode,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "⏰ Command timed out after 30s", "command": command}
        except Exception as e:
            return {"success": False, "output": str(e), "command": command}
    
    def suggest_remediation(self, anomaly: dict, root_cause: dict) -> dict:
        """Generate remediation plan with executable commands."""
        context_str = json.dumps({"anomaly": anomaly, "root_cause": root_cause})
        
        system_prompt = (
            "You are an expert SRE remediation agent. Based on the anomaly and root cause, "
            "generate an incident response plan with SAFE diagnostic commands. "
            "Return ONLY valid JSON: "
            '{"immediate_actions": ["string"], '
            '"diagnostic_commands": ["safe shell commands to run"], '
            '"automated_actions": [{"action": "string", "command": "safe_command", "risk_level": "LOW/MEDIUM/HIGH"}], '
            '"escalation_needed": bool, "estimated_recovery_time": "string", '
            '"prevention_measures": ["string"]}'
        )
        
        prompt = f"{system_prompt}\n\nIncident Context:\n{context_str}"
        
        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=120
            )
            if res.status_code == 200:
                return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            print(f"Remediation AI Error: {e}")
        
        return {
            "immediate_actions": ["Manual intervention required."],
            "diagnostic_commands": ["systemctl status nginx", "df -h", "free -m"],
            "automated_actions": [],
            "escalation_needed": True,
            "estimated_recovery_time": "Unknown",
            "prevention_measures": ["Investigate AI pipeline failure."]
        }