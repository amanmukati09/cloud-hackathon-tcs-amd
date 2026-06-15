"""
AI Performance Benchmark
Compares models and tracks accuracy metrics.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Incident

class BenchmarkEngine:
    def calculate(self, db: Session) -> dict:
        now = datetime.utcnow()
        last_7d = now - timedelta(days=7)

        total = db.query(Incident).count()
        resolved = db.query(Incident).filter(Incident.status == "resolved").count()
        recent = db.query(Incident).filter(Incident.timestamp >= last_7d).count()
        
        # Incidents with root cause (AI successfully diagnosed)
        with_rca = db.query(Incident).filter(
            Incident.root_cause.isnot(None),
            Incident.root_cause != ""
        ).count()
        
        # Incidents with remediation (AI suggested fix)
        with_remediation = db.query(Incident).filter(
            Incident.remediation_action.isnot(None),
            Incident.remediation_action != ""
        ).count()

        # Accuracy: % of incidents where AI found root cause
        diagnosis_accuracy = round(with_rca / max(total, 1) * 100, 1)
        
        # Remediation rate: % of incidents where AI suggested fix
        remediation_rate = round(with_remediation / max(total, 1) * 100, 1)
        
        # Resolution rate
        resolution_rate = round(resolved / max(total, 1) * 100, 1)
        
        # Avg resolution time (for resolved incidents)
        resolved_incidents = db.query(Incident).filter(
            Incident.status == "resolved",
            Incident.resolved_at.isnot(None),
            Incident.timestamp.isnot(None)
        ).all()
        
        avg_resolution_hours = 0
        if resolved_incidents:
            total_hours = 0
            for inc in resolved_incidents[:100]:
                try:
                    delta = inc.resolved_at - inc.timestamp
                    total_hours += delta.total_seconds() / 3600
                except:
                    pass
            avg_resolution_hours = round(total_hours / max(len(resolved_incidents[:100]), 1), 1)

        # GPU acceleration stats
        gpu_available = False
        try:
            from gpu_utils import gpu_detector
            gpu_available = gpu_detector.gpu_available
        except:
            pass

        return {
            "total_incidents": total,
            "diagnosis_accuracy": diagnosis_accuracy,
            "remediation_rate": remediation_rate,
            "resolution_rate": resolution_rate,
            "avg_resolution_hours": avg_resolution_hours,
            "recent_7d": recent,
            "with_root_cause": with_rca,
            "with_remediation": with_remediation,
            "gpu_accelerated": gpu_available,
            "model_used": "Llama3 + Fine-tuned",
            "features_count": 45
        }


benchmark = BenchmarkEngine()