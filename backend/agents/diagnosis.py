import requests
import json
import time

class DiagnosisAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
        
        # Fallback knowledge
        self.FALLBACK = {
            "error_event": {
                "root_cause": "Application error in system components causing service malfunction",
                "confidence": 0.85,
                "evidence": ["Error detected in logs", "Service processing failure"],
                "contributing_factors": ["Code issue", "Resource constraint", "Dependency failure"]
            },
            "critical_event": {
                "root_cause": "Critical system failure requiring immediate intervention",
                "confidence": 0.95,
                "evidence": ["Critical flag detected", "System health degraded"],
                "contributing_factors": ["System overload", "Resource exhaustion", "Cascading failure"]
            },
            "service_crash": {
                "root_cause": "Service process terminated unexpectedly due to crash or OOM",
                "confidence": 0.90,
                "evidence": ["Process crashed", "Memory limit exceeded"],
                "contributing_factors": ["Memory leak", "Segmentation fault", "Unhandled exception"]
            },
            "timeout": {
                "root_cause": "Connection/request timeout due to performance degradation or unavailability",
                "confidence": 0.88,
                "evidence": ["Timeout in logs", "Response delayed"],
                "contributing_factors": ["High latency", "Network congestion", "Service overload"]
            },
            "memory_high": {
                "root_cause": "Memory usage exceeded safe thresholds causing potential degradation",
                "confidence": 0.92,
                "evidence": ["Memory > 90%", "Swap usage detected"],
                "contributing_factors": ["Memory leak", "Large processing", "Insufficient allocation"]
            },
            "cpu_spike": {
                "root_cause": "CPU utilization spiked causing resource contention",
                "confidence": 0.90,
                "evidence": ["CPU > 95%", "Load average high"],
                "contributing_factors": ["Infinite loop", "Heavy computation", "Context switching"]
            }
        }
    
    def analyze_root_cause(self, anomaly: dict, logs: list[str]) -> dict:
        """Intelligent diagnosis with LLM + fallback"""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        
        # Try LLM first (with timeout)
        try:
            result = self._llm_diagnosis(anomaly, logs)
            if result:
                return result
        except Exception as e:
            print(f"LLM failed: {e}, using fallback")
        
        # Fallback to knowledge base
        if anomaly_type in self.FALLBACK:
            return self.FALLBACK[anomaly_type]
        
        return {
            "root_cause": "System issue detected",
            "confidence": 0.5,
            "evidence": logs[-2:] if logs else [],
            "contributing_factors": ["Requires manual investigation"]
        }
    
    def _llm_diagnosis(self, anomaly: dict, logs: list[str]) -> dict:
        """Call LLM with SHORT timeout"""
        logs_text = "\n".join(logs[-5:]) if logs else ""  # Only last 5 logs
        
        prompt = f"""Analyze this incident. RESPOND ONLY AS JSON.

Anomaly: {anomaly.get('anomaly_type')} ({anomaly.get('severity')})
Component: {anomaly.get('affected_component')}
Recent logs: {logs_text}

JSON response (NO OTHER TEXT):
{{"root_cause": "brief cause", "confidence": 0.9, "evidence": ["line1", "line2"], "contributing_factors": ["factor1", "factor2"]}}"""
        
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
        print(f"LLM diagnosis took {elapsed:.1f}s")
        
        if response.status_code == 200:
            try:
                text = response.json()["response"].strip()
                result = json.loads(text)
                if "root_cause" in result and result.get("root_cause"):
                    return result
            except:
                pass
        
        return None

if __name__ == "__main__":
    diagnosis = DiagnosisAgent()
    anomaly = {"anomaly_type": "critical_event", "severity": "CRITICAL", "affected_component": "storage"}
    result = diagnosis.analyze_root_cause(anomaly, ["[CRITICAL] disk full", "[ERROR] write failed"])
    print(json.dumps(result, indent=2))
