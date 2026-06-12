import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
import re

class IncidentClusterer:
    def __init__(self):
        self.clusters = {}
    
    def extract_features(self, incidents: list) -> list:
        """Extract key features from incidents for clustering."""
        features = []
        for inc in incidents:
            desc = (inc.get("anomaly_description") or "").lower()
            root = (inc.get("root_cause") or "").lower()
            combined = desc + " " + root
            
            # Extract key patterns
            features.append({
                "id": inc.get("id"),
                "has_cpu": "cpu" in combined,
                "has_memory": "memory" in combined or "mem" in combined,
                "has_disk": "disk" in combined,
                "has_network": "network" in combined or "timeout" in combined or "connection" in combined,
                "has_nginx": "nginx" in combined,
                "has_database": "database" in combined or "db" in combined or "sql" in combined,
                "has_crash": "crash" in combined or "crashed" in combined,
                "has_oom": "oom" in combined or "out of memory" in combined or "killed" in combined,
                "severity": inc.get("severity", "UNKNOWN"),
                "component": inc.get("component", "Unknown"),
                "status": inc.get("status", "open"),
                "date": inc.get("date", ""),
                "text": combined
            })
        return features
    
    def calculate_similarity(self, f1: dict, f2: dict) -> float:
        """Calculate similarity score between two incidents."""
        score = 0
        total = 0
        
        # Compare boolean features
        bool_features = ["has_cpu", "has_memory", "has_disk", "has_network", 
                        "has_nginx", "has_database", "has_crash", "has_oom"]
        for feat in bool_features:
            total += 1
            if f1[feat] == f2[feat]:
                score += 1
        
        # Compare severity
        total += 1
        if f1["severity"] == f2["severity"]:
            score += 1
        
        # Compare component
        total += 1
        if f1["component"] == f2["component"]:
            score += 1
        
        # Compare temporal proximity (incidents within 24h are more similar)
        total += 1
        try:
            d1 = datetime.strptime(f1["date"][:10], "%Y-%m-%d")
            d2 = datetime.strptime(f2["date"][:10], "%Y-%m-%d")
            if abs((d1 - d2).days) <= 1:
                score += 1
        except:
            pass
        
        return score / max(total, 1)
    
    def cluster_incidents(self, incidents: list, threshold: float = 0.6) -> dict:
        """Group similar incidents into clusters."""
        if len(incidents) < 2:
            return {"clusters": [], "unclustered": len(incidents), "summary": "Not enough incidents to cluster"}
        
        features = self.extract_features(incidents)
        
        # Simple greedy clustering
        clusters = []
        assigned = set()
        
        for i, f1 in enumerate(features):
            if i in assigned:
                continue
            
            cluster = {
                "id": len(clusters) + 1,
                "name": self._generate_cluster_name(f1),
                "incidents": [incidents[i]],
                "count": 1,
                "common_features": [],
                "severity_distribution": {f1["severity"]: 1},
                "date_range": {"start": f1["date"], "end": f1["date"]}
            }
            
            for j, f2 in enumerate(features):
                if j <= i or j in assigned:
                    continue
                
                similarity = self.calculate_similarity(f1, f2)
                if similarity >= threshold:
                    cluster["incidents"].append(incidents[j])
                    cluster["count"] += 1
                    cluster["severity_distribution"][f2["severity"]] = \
                        cluster["severity_distribution"].get(f2["severity"], 0) + 1
                    assigned.add(j)
            
            # Identify common features
            bool_features = ["has_cpu", "has_memory", "has_disk", "has_network",
                           "has_nginx", "has_database", "has_crash", "has_oom"]
            feature_labels = {
                "has_cpu": "CPU Issues", "has_memory": "Memory Issues",
                "has_disk": "Disk Issues", "has_network": "Network Issues",
                "has_nginx": "Nginx Related", "has_database": "Database Related",
                "has_crash": "Service Crashes", "has_oom": "OOM Events"
            }
            
            if cluster["count"] > 1:
                for feat in bool_features:
                    count = sum(1 for inc in cluster["incidents"] 
                              if self.extract_features([inc])[0][feat])
                    if count >= cluster["count"] * 0.5:  # Feature in >50% of cluster
                        cluster["common_features"].append(feature_labels[feat])
            
            clusters.append(cluster)
            assigned.add(i)
        
        # Calculate summary
        total_clustered = sum(c["count"] for c in clusters)
        unclustered = len(incidents) - total_clustered
        
        return {
            "clusters": clusters,
            "total_incidents": len(incidents),
            "total_clusters": len(clusters),
            "clustered_incidents": total_clustered,
            "unclustered_incidents": unclustered,
            "summary": f"Found {len(clusters)} clusters covering {total_clustered} incidents. {unclustered} unique incidents."
        }
    
    def _generate_cluster_name(self, feature: dict) -> str:
        """Generate a descriptive name for a cluster."""
        if feature["has_oom"]:
            return "Memory Exhaustion Cluster"
        elif feature["has_crash"] and feature["has_nginx"]:
            return "Nginx Crash Cluster"
        elif feature["has_network"] and feature["has_database"]:
            return "Database Connectivity Cluster"
        elif feature["has_cpu"] and feature["has_memory"]:
            return "Resource Exhaustion Cluster"
        elif feature["has_crash"]:
            return "Service Crash Cluster"
        elif feature["has_network"]:
            return "Network Issue Cluster"
        elif feature["has_database"]:
            return "Database Issue Cluster"
        elif feature["has_cpu"]:
            return "CPU Spike Cluster"
        else:
            return f"Issue Cluster ({feature.get('component', 'Unknown')})"
    
    def render_clusters_html(self, cluster_data: dict) -> str:
        """Render clusters as beautiful HTML."""
        html = """
        <style>
            .cluster-card {
                background: rgba(30,41,59,0.8);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 14px;
                margin: 8px 0;
            }
            .cluster-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            .cluster-name {
                font-size: 1.1em;
                font-weight: 600;
                color: #f8fafc;
            }
            .cluster-badge {
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
            }
            .cluster-stats {
                display: flex;
                gap: 12px;
                margin: 6px 0;
                font-size: 0.85em;
                color: #94a3b8;
            }
            .cluster-features {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin: 6px 0;
            }
            .feature-tag {
                background: rgba(56,189,248,0.15);
                color: #38bdf8;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.75em;
            }
            .cluster-incidents {
                font-size: 0.8em;
                color: #64748b;
                margin-top: 6px;
            }
            .severity-bar {
                display: flex;
                gap: 2px;
                height: 6px;
                border-radius: 3px;
                overflow: hidden;
                margin-top: 6px;
            }
            .severity-CRITICAL { background: #ef4444; }
            .severity-HIGH { background: #f59e0b; }
            .severity-MEDIUM { background: #3b82f6; }
            .severity-LOW { background: #10b981; }
        </style>
        <div>
        """
        
        html += f"""
            <h3>🔬 Incident Clusters</h3>
            <p style="color:#94a3b8;margin-bottom:12px;">{cluster_data.get('summary', '')}</p>
        """
        
        for cluster in cluster_data.get("clusters", []):
            # Severity colors
            sev_colors = {"CRITICAL": "#ef4444", "HIGH": "#f59e0b", "MEDIUM": "#3b82f6", "LOW": "#10b981"}
            top_sev = max(cluster["severity_distribution"], key=cluster["severity_distribution"].get)
            sev_color = sev_colors.get(top_sev, "#6b7280")
            
            html += f"""
            <div class="cluster-card">
                <div class="cluster-header">
                    <span class="cluster-name">📦 {cluster['name']}</span>
                    <span class="cluster-badge" style="background:{sev_color}20;color:{sev_color};">
                        {cluster['count']} incidents
                    </span>
                </div>
                <div class="cluster-stats">
                    <span>🔴 Critical: {cluster['severity_distribution'].get('CRITICAL', 0)}</span>
                    <span>🟠 High: {cluster['severity_distribution'].get('HIGH', 0)}</span>
                    <span>🔵 Medium: {cluster['severity_distribution'].get('MEDIUM', 0)}</span>
                    <span>🟢 Low: {cluster['severity_distribution'].get('LOW', 0)}</span>
                </div>
                <div class="cluster-features">
            """
            for feat in cluster.get("common_features", [])[:5]:
                html += f'<span class="feature-tag">{feat}</span>'
            
            html += f"""
                </div>
                <div class="cluster-incidents">
                    Incidents: {', '.join([f"#{i.get('id','?')}" for i in cluster['incidents'][:5]])}
                    {f'... +{cluster["count"]-5} more' if cluster['count'] > 5 else ''}
                </div>
                <div class="severity-bar">
            """
            total = sum(cluster["severity_distribution"].values())
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                count = cluster["severity_distribution"].get(sev, 0)
                pct = (count / total * 100) if total > 0 else 0
                html += f'<div class="severity-{sev}" style="width:{pct}%"></div>'
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
        return html