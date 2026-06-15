"""
Multi-Source Live Monitor Engine
"""

import os, json, time, threading, requests
from datetime import datetime
from collections import deque
from models import Incident, get_db

class LiveMonitorEngine:
    def __init__(self, ollama_url="http://localhost:11434", model="llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.sources = {}
        self._lock = threading.Lock()
        self._init_default_sources()

    def _init_default_sources(self):
        base = os.getcwd()
        defaults = {
            "default": os.path.join(base, "logs", "live_stream.log"),
            "ecommerce": os.path.join(base, "logs", "ecommerce_stream.log"),
            "apigateway": os.path.join(base, "logs", "apigateway_stream.log"),
            "database": os.path.join(base, "logs", "database_stream.log"),
        }
        for name, path in defaults.items():
            self.add_source(name, path)

    def add_source(self, name, path):
        with self._lock:
            if name in self.sources:
                return False
            self.sources[name] = {
                "path": path, "running": False, "thread": None,
                "last_position": os.path.getsize(path) if os.path.exists(path) else 0,
                "log_buffer": deque(maxlen=200), "active_incidents": [],
                "pipeline_steps": [],
                "metrics": {"lines_processed": 0, "anomalies_found": 0, "last_analysis": None},
                "session_start": None, "monitoring_user_id": None
            }
            return True

    def get_sources(self):
        with self._lock:
            return [{"name": k, "running": v["running"], "lines": v["metrics"]["lines_processed"], "anomalies": v["metrics"]["anomalies_found"]} for k, v in self.sources.items()]

    def start_monitor(self, source, user_id=None):
        with self._lock:
            src = self.sources.get(source)
            if not src or src["running"]:
                return False
            src["running"] = True
            src["session_start"] = datetime.now()
            src["monitoring_user_id"] = user_id
            if os.path.exists(src["path"]):
                src["last_position"] = os.path.getsize(src["path"])
            src["thread"] = threading.Thread(target=self._loop, args=(source,), daemon=True)
            src["thread"].start()
            return True

    def stop_monitor(self, source):
        with self._lock:
            src = self.sources.get(source)
            if src:
                src["running"] = False
                if src["thread"]:
                    src["thread"].join(timeout=3)
        return self._get_session_report(source)

    def get_state(self, source):
        with self._lock:
            src = self.sources.get(source, {})
            return {"running": src.get("running", False), "log_buffer": list(src.get("log_buffer", [])), "active_incidents": src.get("active_incidents", []), "pipeline_steps": src.get("pipeline_steps", []), "metrics": src.get("metrics", {}), "session_start": str(src.get("session_start", "")) if src.get("session_start") else None}

    def _loop(self, source):
        while True:
            with self._lock:
                src = self.sources.get(source)
                if not src or not src["running"]:
                    break
            lines = self._read_new_lines(source)
            if lines:
                with self._lock:
                    src["log_buffer"].extend(lines)
                    src["metrics"]["lines_processed"] += len(lines)
                self._analyze(source, lines)
            time.sleep(3)

    def _read_new_lines(self, source):
        src = self.sources[source]
        if not os.path.exists(src["path"]):
            return []
        with open(src["path"], "r") as f:
            f.seek(src["last_position"])
            data = f.read()
            src["last_position"] = f.tell()
        return [l.strip() for l in data.split("\n") if l.strip()]

    def _analyze(self, source, lines):
        src = self.sources[source]
        combined = "\n".join(lines[-20:])
        sev = self._quick_scan(lines)
        steps = [{"step": 1, "name": "Pre-scan", "status": "done", "detail": f"Severity: {sev}"}]
        anomaly = self._ask_ai(combined, "detect")
        steps.append({"step": 2, "name": "Anomaly", "status": "done", "detail": anomaly.get("anomaly_type", "None")[:40]})
        if anomaly.get("anomaly_detected"):
            rca = self._ask_ai(combined, "rca", anomaly)
            steps.append({"step": 3, "name": "Root Cause", "status": "done", "detail": rca.get("root_cause", "")[:80]})
            rem = self._ask_ai(combined, "remediation", anomaly, rca)
            steps.append({"step": 4, "name": "Remediation", "status": "done", "detail": str(rem.get("immediate_actions", []))[:100]})
            if anomaly.get("severity") in ["CRITICAL", "HIGH"]:
                self._create_incident(source, anomaly, rca, rem, lines)
                if anomaly.get("severity") == "CRITICAL":
                    self._send_email_alert(source, anomaly, rca)
        else:
            steps += [{"step": 3, "name": "Root Cause", "status": "skipped", "detail": "No anomaly"}, {"step": 4, "name": "Remediation", "status": "skipped", "detail": "No action"}]
        steps.append({"step": 5, "name": "Auto-Fix", "status": "skipped", "detail": "Manual review"})
        with self._lock:
            src["pipeline_steps"] = steps
            src["metrics"]["last_analysis"] = datetime.now().strftime("%H:%M:%S")
            if anomaly.get("anomaly_detected"):
                src["metrics"]["anomalies_found"] += 1

    def _quick_scan(self, lines):
        c = " ".join(lines).lower()
        if any(w in c for w in ["critical", "fatal", "panic"]): return "CRITICAL"
        if any(w in c for w in ["error", "fail", "crash", "timeout"]): return "HIGH"
        if any(w in c for w in ["warning", "warn"]): return "MEDIUM"
        return "LOW"

    def _ask_ai(self, log_text, task, anomaly=None, rca=None):
        prompts = {
            "detect": 'Analyze logs. Return ONLY JSON: {"anomaly_detected":bool,"anomaly_type":"str","severity":"LOW/MEDIUM/HIGH/CRITICAL","affected_component":"str","description":"str"}\nLogs:\n',
            "rca": f'Find root cause. Return JSON: {{"root_cause":"str","confidence":0.5}}\nAnomaly:{json.dumps(anomaly)}\nLogs:\n',
            "remediation": f'Suggest fix. Return JSON: {{"immediate_actions":["str"]}}\nAnomaly:{json.dumps(anomaly)}\nRootCause:{json.dumps(rca)}\nLogs:\n'
        }
        try:
            r = requests.post(f"{self.ollama_url}/api/generate", json={"model": self.model, "prompt": prompts[task] + log_text[:1500], "stream": False, "format": "json", "options": {"temperature": 0.3, "num_predict": 256}}, timeout=15)
            if r.status_code == 200:
                return json.loads(r.json().get("response", "{}"))
        except:
            pass
        return {}

    def _create_incident(self, source, anomaly, rca, rem, lines):
        try:
            db = next(get_db())
            src = self.sources[source]
            user_id = src.get("monitoring_user_id") or 1
            inc = Incident(user_id=user_id, raw_logs=f"[Source: {source}]\n" + "\n".join(lines[-20:]), status="open", anomaly_description=f"Source:{source}|Type:{anomaly.get('anomaly_type')}|Severity:{anomaly.get('severity')}", root_cause=rca.get("root_cause", ""), remediation_action=",".join(rem.get("immediate_actions", [])))
            db.add(inc); db.commit(); db.refresh(inc)
            src["active_incidents"].insert(0, {"id": inc.id, "timestamp": datetime.now().strftime("%H:%M:%S"), "type": anomaly.get("anomaly_type", "Unknown"), "severity": anomaly.get("severity", "MEDIUM"), "component": anomaly.get("affected_component", "Unknown"), "source": source, "status": "open"})
            try:
                from routers.notifications import create_notification
                create_notification(db, user_id, "new_incident", f"🚨 Live Incident #{inc.id}", f"Source: {source} | {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}")
            except:
                pass
        except Exception as e:
            print(f"Incident error: {e}")

    def _send_email_alert(self, source, anomaly, rca):
        try:
            from agents.alerting import AlertManager
            AlertManager().send_incident_alert({"id": f"LIVE-{source}", "anomaly_type": anomaly.get("anomaly_type"), "severity": anomaly.get("severity"), "affected_component": f"{source} - {anomaly.get('affected_component')}", "description": anomaly.get("description", ""), "root_cause": rca.get("root_cause", ""), "remediation": "Check Live Monitor", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")})
        except Exception as e:
            print(f"Alert error: {e}")

    def _get_session_report(self, source):
        src = self.sources.get(source, {})
        return {"source": source, "lines_processed": src.get("metrics", {}).get("lines_processed", 0), "anomalies_found": src.get("metrics", {}).get("anomalies_found", 0), "incident_ids": [i["id"] for i in src.get("active_incidents", [])]}

    def chat_about_stream(self, source, msg):
        src = self.sources.get(source, {})
        recent = "\n".join(list(src.get("log_buffer", []))[-30:])
        try:
            r = requests.post(f"{self.ollama_url}/api/generate", json={"model": self.model, "prompt": f"SRE monitoring logs:\n{recent}\n\nUser:{msg}\nAssistant:", "stream": False, "options": {"temperature": 0.7, "num_predict": 300}}, timeout=20)
            return r.json().get("response", "") if r.status_code == 200 else "AI unavailable"
        except:
            return "AI unavailable"


monitor = LiveMonitorEngine()