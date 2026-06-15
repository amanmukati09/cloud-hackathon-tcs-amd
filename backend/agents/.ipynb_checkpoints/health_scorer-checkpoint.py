from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Incident

class HealthScorer:
    def calculate(self, db: Session) -> dict:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_1h = now - timedelta(hours=1)

        total = db.query(Incident).count()
        open_count = db.query(Incident).filter(Incident.status == "open").count()
        resolved_count = db.query(Incident).filter(Incident.status == "resolved").count()
        
        # Auto-resolve incidents older than 1 hour
        old_open = db.query(Incident).filter(
            Incident.status == "open",
            Incident.timestamp < last_1h
        ).all()
        for inc in old_open:
            inc.status = "resolved"
            inc.resolved_at = now
        if old_open:
            db.commit()
            open_count = db.query(Incident).filter(Incident.status == "open").count()
            resolved_count = db.query(Incident).filter(Incident.status == "resolved").count()
            total = open_count + resolved_count

        critical_1h = db.query(Incident).filter(
            Incident.timestamp >= last_1h,
            Incident.anomaly_description.ilike("%CRITICAL%")
        ).count()

        # SIMPLE SCORE: Start at 100, deduct only for active issues
        score = 100
        score -= critical_1h * 8           # -8 per active critical
        score -= max(0, open_count * 2)    # -2 per open incident

        score = max(10, min(100, int(score)))

        if score >= 85:
            status, color, icon = "Excellent", "#10b981", "✅"
        elif score >= 70:
            status, color, icon = "Healthy", "#10b981", "✅"
        elif score >= 50:
            status, color, icon = "Degraded", "#f59e0b", "⚠️"
        else:
            status, color, icon = "Critical", "#ef4444", "🚨"

        # Top risk component (last 1 hour)
        from collections import Counter
        components = Counter()
        recent = db.query(Incident).filter(Incident.timestamp >= last_1h).all()
        for inc in recent:
            desc = (inc.anomaly_description or "").lower()
            if "nginx" in desc: components["Nginx"] += 1
            elif "database" in desc or "sql" in desc: components["Database"] += 1
            elif "redis" in desc or "cache" in desc: components["Redis"] += 1
            elif "api" in desc or "gateway" in desc: components["API Gateway"] += 1

        top_risk = components.most_common(1)[0][0] if components else "None"

        return {
            "score": score,
            "status": status,
            "color": color,
            "icon": icon,
            "total_incidents": total,
            "open_incidents": open_count,
            "resolved_incidents": resolved_count,
            "critical_1h": critical_1h,
            "incident_velocity": critical_1h,
            "top_risk_component": top_risk,
            "resolution_rate": round(resolved_count / max(total, 1) * 100, 1)
        }


health_scorer = HealthScorer()