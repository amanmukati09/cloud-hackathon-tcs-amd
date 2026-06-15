"""
Dependency Graph API
Endpoints for building and querying the incident dependency graph.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import re

from models import get_db, User, Incident
from auth import get_current_user
from agents.dependency_graph import graph_engine

router = APIRouter(prefix="/dependency", tags=["Dependency Graph"])


def _extract_severity(anomaly_desc: str) -> str:
    """Extract severity from anomaly description."""
    if not anomaly_desc:
        return "MEDIUM"
    # Try to find "Severity: X" pattern
    match = re.search(r'Severity:\s*([A-Z]+)', str(anomaly_desc))
    if match:
        return match.group(1)
    # Fallback: check if description contains severity keywords
    desc_upper = str(anomaly_desc).upper()
    if 'CRITICAL' in desc_upper:
        return 'CRITICAL'
    if 'HIGH' in desc_upper:
        return 'HIGH'
    if 'MEDIUM' in desc_upper:
        return 'MEDIUM'
    if 'LOW' in desc_upper:
        return 'LOW'
    return "MEDIUM"
    

@router.get("/graph")
async def get_dependency_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Build and return the incident dependency graph.
    Uses all incidents for admin, user's own incidents for regular users.
    """
    query = db.query(Incident)
    if not current_user.is_admin:
        query = query.filter(Incident.user_id == current_user.id)
    
    incidents = query.order_by(Incident.timestamp.desc()).limit(500).all()
    
    if not incidents:
        return {
            "graph": graph_engine.export_graph(),
            "message": "No incidents found to build dependency graph",
            "has_data": False
        }
    
    # Format incidents for graph engine
    incident_data = []
    for inc in incidents:
        
        incident_data.append({
            
            "id": inc.id,
            "anomaly_description": inc.anomaly_description or "",
            "root_cause": inc.root_cause or "",
            "remediation_action": inc.remediation_action or "",
            "timestamp": str(inc.timestamp) if inc.timestamp else "",
            "severity": _extract_severity(inc.anomaly_description),
            "status": inc.status or "open"  # <-- This should already be there
        })
    
    # Build graph
    graph_data = graph_engine.build_from_incidents(incident_data)
    graph_html = graph_engine.render_graph_html(graph_data)
    
    return {
        "graph": graph_data,
        "graph_html": graph_html,
        "message": f"Graph built from {len(incident_data)} incidents",
        "has_data": True
    }


@router.get("/blast-radius/{component}")
async def get_blast_radius(
    component: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate blast radius for a specific component.
    Shows which other components would be affected if this one fails.
    """
    blast_data = graph_engine.get_blast_radius(component)
    blast_html = graph_engine.render_blast_radius_html(blast_data)
    
    return {
        "blast_data": blast_data,
        "blast_html": blast_html
    }


@router.get("/critical-paths")
async def get_critical_paths(
    current_user: User = Depends(get_current_user)
):
    """Get the most critical dependency paths (hub nodes)."""
    return {
        "critical_paths": graph_engine.critical_paths,
        "total_nodes": len(graph_engine.nodes),
        "total_edges": len(graph_engine.edges)
    }