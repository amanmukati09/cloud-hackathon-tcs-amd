import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

class IncidentPredictor:
    def __init__(self):
        self.patterns = {}
    
    def analyze_patterns(self, incidents: list) -> dict:
        """Analyze incident patterns and predict future risks."""
        if not incidents:
            return {"predictions": [], "risk_level": "LOW", "summary": "No historical data available"}
        
        df = pd.DataFrame(incidents)
        
        predictions = []
        
        # 1. Time-based patterns
        if 'hour' in df.columns:
            hour_counts = df['hour'].value_counts()
            peak_hour = hour_counts.index[0] if len(hour_counts) > 0 else 0
            predictions.append({
                "type": "time_pattern",
                "title": f"⚠️ Peak incident hour: {peak_hour}:00",
                "detail": f"Most incidents occur around {peak_hour}:00. Schedule monitoring for this time.",
                "confidence": min(90, hour_counts.iloc[0] / len(df) * 100)
            })
        
        # 2. Day of week patterns
        if 'weekday' in df.columns:
            day_counts = df['weekday'].value_counts()
            peak_day = day_counts.index[0] if len(day_counts) > 0 else "Unknown"
            predictions.append({
                "type": "day_pattern",
                "title": f"📅 Highest incident day: {peak_day}",
                "detail": f"{peak_day}s have historically had the most incidents. Consider increased staffing.",
                "confidence": min(90, day_counts.iloc[0] / len(df) * 100)
            })
        
        # 3. Component risk analysis
        if 'component' in df.columns:
            comp_counts = df['component'].value_counts()
            for comp in comp_counts.head(3).index:
                comp_df = df[df['component'] == comp]
                recent_count = len(comp_df[comp_df['date'] >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')]) if 'date' in df.columns else 0
                predictions.append({
                    "type": "component_risk",
                    "title": f"🔧 High-risk component: {comp}",
                    "detail": f"'{comp}' has {len(comp_df)} total incidents. {'Recently active.' if recent_count > 0 else 'Monitor for recurrence.'}",
                    "confidence": min(85, len(comp_df) / len(df) * 100)
                })
        
        # 4. Severity trend
        if 'severity' in df.columns:
            sev_counts = df['severity'].value_counts()
            high_sev = sev_counts.get('HIGH', 0) + sev_counts.get('CRITICAL', 0)
            predictions.append({
                "type": "severity_trend",
                "title": f"🚨 Severity trend: {high_sev} high/critical incidents",
                "detail": f"{round(high_sev/len(df)*100)}% of incidents are HIGH or CRITICAL severity.",
                "confidence": 80
            })
        
        # 5. Recurrence prediction
        if 'anomaly_type' in df.columns:
            type_counts = df['anomaly_type'].value_counts()
            top_type = type_counts.index[0] if len(type_counts) > 0 else "Unknown"
            predictions.append({
                "type": "recurrence",
                "title": f"🔄 Most recurring: {top_type}",
                "detail": f"'{top_type}' has occurred {type_counts.iloc[0]} times. High chance of recurrence.",
                "confidence": min(95, type_counts.iloc[0] / len(df) * 100)
            })
        
        # Calculate overall risk
        avg_confidence = np.mean([p['confidence'] for p in predictions]) if predictions else 0
        risk_level = "HIGH" if avg_confidence > 70 else "MEDIUM" if avg_confidence > 40 else "LOW"
        
        return {
            "predictions": predictions,
            "risk_level": risk_level,
            "total_incidents": len(df),
            "summary": f"Based on {len(df)} historical incidents, overall risk is **{risk_level}** with {len(predictions)} active predictions.",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }