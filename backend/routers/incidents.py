from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import csv, io, re
from fastapi.responses import StreamingResponse

from models import get_db, User, Incident
from auth import get_current_user

router = APIRouter()

class ResolveIncident(BaseModel):
    resolution_notes: Optional[str] = None

# ── List incidents ────────────────────────────────────
@router.get("/my-incidents")
async def get_user_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).order_by(Incident.timestamp.desc()).all()
    return [{
        "id": i.id,
        "timestamp": i.timestamp,
        "raw_logs": i.raw_logs,
        "anomaly": i.anomaly_description,
        "root_cause": i.root_cause,
        "remediation": i.remediation_action,
        "status": i.status
    } for i in incidents]

# ── Resolve incident ──────────────────────────────────
@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    payload: ResolveIncident,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    if not incident:
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status == "resolved":
        raise HTTPException(status_code=400, detail="Incident already resolved")

    incident.status = "resolved"
    incident.remediation_status = "completed"
    incident.resolved_at = datetime.now(timezone.utc)
    if payload.resolution_notes:
        incident.resolution_notes = payload.resolution_notes
    db.commit()

    from routers.notifications import create_notification
    create_notification(db, current_user.id, "incident_resolved",
                        "Incident Resolved",
                        f"Incident #{incident_id} has been marked as resolved")

    resolution_time = incident.resolved_at - incident.timestamp
    hours = resolution_time.total_seconds() / 3600
    return {
        "status": "success",
        "incident_id": incident.id,
        "resolution_time_hours": round(hours, 2)
    }

# ── Delete incident ───────────────────────────────────
@router.delete("/incidents/{incident_id}")
async def delete_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")

    db.delete(incident)
    db.commit()

    from routers.notifications import create_notification
    if incident.user_id != current_user.id:
        create_notification(db, incident.user_id, "incident_deleted",
                            "Incident deleted by admin",
                            f"Incident #{incident_id} was deleted by an admin.")
    create_notification(db, current_user.id, "incident_deleted",
                        "Incident deleted",
                        f"Incident #{incident_id} has been deleted.")
    return {"status": "success", "message": f"Incident {incident_id} deleted"}

# ── Incident details ──────────────────────────────────
@router.get("/incidents/{incident_id}/details")
async def get_incident_details(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    if not incident:
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "id": incident.id,
        "timestamp": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_logs": incident.raw_logs,
        "anomaly": incident.anomaly_description,
        "root_cause": incident.root_cause,
        "remediation": incident.remediation_action,
        "status": incident.status,
        "resolution_notes": incident.resolution_notes or "",
        "resolved_at": incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if incident.resolved_at else None
    }

# ── Export CSV ────────────────────────────────────────
@router.get("/incidents/export/csv")
async def export_incidents_csv(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Incident).filter(Incident.user_id == current_user.id)
    if status_filter and status_filter != "all":
        query = query.filter(Incident.status == status_filter)
    incidents = query.order_by(Incident.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Status", "Anomaly", "Root Cause", "Remediation", "Resolution Notes"])
    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            inc.status.upper(),
            inc.anomaly_description[:200] if inc.anomaly_description else "",
            inc.root_cause[:200] if inc.root_cause else "",
            inc.remediation_action[:200] if inc.remediation_action else "",
            inc.resolution_notes[:200] if inc.resolution_notes else ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aegis_incidents_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# ── Export PDF ────────────────────────────────────────
@router.get("/incidents/{incident_id}/export/pdf")
async def export_incident_pdf(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id
    ).first()
    if not incident:
        if current_user.is_admin:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=HexColor('#38bdf8'), spaceAfter=30)
    story.append(Paragraph("🛡️ AegisAI Incident Report", title_style))
    story.append(Paragraph(f"Incident #{incident.id}", styles['Heading2']))
    story.append(Spacer(1, 20))

    status_color = "#10b981" if incident.status == "resolved" else "#f59e0b"
    status_text = "✅ RESOLVED" if incident.status == "resolved" else "🟢 OPEN"
    story.append(Paragraph(f"Status: <font color='{status_color}'><b>{status_text}</b></font>", styles['Normal']))
    story.append(Spacer(1, 10))

    details_data = [["Field", "Details"], ["Date/Time", incident.timestamp.strftime("%Y-%m-%d %H:%M:%S")], ["Status", incident.status.upper()]]
    if incident.resolved_at:
        details_data.append(["Resolved At", incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S")])

    table = Table(details_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e293b')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#0f172a')), ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#334155')), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    sections = [
        ("📋 Raw Logs", incident.raw_logs or "No logs provided"),
        ("🔴 Anomaly Detection", incident.anomaly_description or "Not analyzed"),
        ("🔍 Root Cause Analysis", incident.root_cause or "Not determined"),
        ("⚙️ Remediation Actions", incident.remediation_action or "No actions specified"),
        ("📝 Resolution Notes", incident.resolution_notes or "No notes provided")
    ]
    for title, content in sections:
        story.append(Paragraph(title, styles['Heading3']))
        story.append(Paragraph(content.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 15))

    story.append(Spacer(1, 30))
    story.append(Paragraph("<i>Generated by AegisAI - Enterprise SRE Platform</i>", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=aegis_incident_{incident_id}_report.pdf"})

@router.get("/incidents/{incident_id}/runbook")
async def generate_runbook(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a runbook from a resolved incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    from agents.runbook import RunbookGenerator
    
    incident_data = {
        "id": incident.id,
        "anomaly_type": incident.anomaly_description or "Unknown",
        "severity": "MEDIUM",
        "root_cause": incident.root_cause or "Not determined",
        "remediation": incident.remediation_action or "No actions recorded",
        "resolution_notes": incident.resolution_notes or "",
        "status": incident.status
    }
    
    generator = RunbookGenerator()
    runbook = generator.generate_runbook(incident_data)
    html = generator.render_runbook_html(runbook)
    
    return {"runbook": runbook, "html": html}