"""
Professional PDF Report Generator
Generates beautiful, multi-page incident reports from bulk log analysis.
Uses ReportLab for PDF generation with industry-standard formatting.
"""

import io
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, Color, white, black
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas


class SeverityGauge(Flowable):
    """Custom severity gauge flowable for PDF."""
    
    def __init__(self, severity: str, width: float = 200, height: float = 30):
        Flowable.__init__(self)
        self.severity = severity.upper()
        self.width = width
        self.height = height
        self._colors = {
            "CRITICAL": HexColor("#dc2626"),
            "HIGH": HexColor("#ef4444"),
            "MEDIUM": HexColor("#f59e0b"),
            "LOW": HexColor("#10b981")
        }
    
    def draw(self):
        color = self._colors.get(self.severity, HexColor("#6b7280"))
        levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        idx = levels.index(self.severity) if self.severity in levels else 0
        
        # Background bar
        self.canv.setFillColor(HexColor("#1e293b"))
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        
        # Filled portion
        fill_width = (idx + 1) / 4 * self.width
        self.canv.setFillColor(color)
        self.canv.roundRect(0, 0, fill_width, self.height, 4, fill=1, stroke=0)
        
        # Text
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", 10)
        self.canv.drawCentredString(self.width / 2, self.height / 2 - 4, f"SEVERITY: {self.severity}")


class IncidentPDFGenerator:
    """Generate professional incident analysis PDF reports."""
    
    # Brand colors
    PRIMARY = HexColor("#38bdf8")      # Sky blue
    SECONDARY = HexColor("#0f172a")    # Dark navy
    ACCENT = HexColor("#f59e0b")       # Amber
    SUCCESS = HexColor("#10b981")      # Emerald
    DANGER = HexColor("#ef4444")       # Red
    DARK_BG = HexColor("#1e293b")      # Slate dark
    LIGHT_TEXT = HexColor("#f8fafc")   # Almost white
    MUTED_TEXT = HexColor("#94a3b8")   # Slate gray
    
    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize PDF generator.
        
        Args:
            output_path: Path to save PDF. If None, returns BytesIO buffer.
        """
        self.output_path = output_path
        self.buffer = io.BytesIO()
        self.styles = self._create_styles()
        
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the report."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=28,
            leading=34,
            textColor=self.PRIMARY,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=self.MUTED_TEXT,
            spaceAfter=20,
            alignment=TA_LEFT
        ))
        
        # Section header
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=18,
            leading=22,
            textColor=self.LIGHT_TEXT,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 2, 0)
        ))
        
        # Subsection header
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            leading=18,
            textColor=self.PRIMARY,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='BodyText2',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=14,
            textColor=self.MUTED_TEXT,
            spaceAfter=8,
            fontName='Helvetica'
        ))
        
        # Code block
        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Code'],
            fontSize=7.5,
            leading=10,
            textColor=HexColor("#e2e8f0"),
            backColor=HexColor("#0d1117"),
            borderPadding=8,
            borderWidth=1,
            borderColor=HexColor("#30363d"),
            borderRadius=4,
            fontName='Courier'
        ))
        
        # Severity badge styles
        for sev, color in [("CRITICAL", "#dc2626"), ("HIGH", "#ef4444"), 
                           ("MEDIUM", "#f59e0b"), ("LOW", "#10b981")]:
            styles.add(ParagraphStyle(
                name=f'Severity_{sev}',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                textColor=white,
                backColor=HexColor(color),
                borderPadding=4,
                borderRadius=10,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ))
        
        return styles
    
    def generate_report(self, analysis_data: Dict[str, Any], 
                       original_filename: str = "log_file.log",
                       include_charts: bool = True) -> bytes:
        """
        Generate a complete incident analysis PDF report.
        
        Args:
            analysis_data: Results from BulkLogProcessor.process_log_file()
            original_filename: Name of the uploaded log file
            include_charts: Whether to include charts/graphs
            
        Returns:
            PDF as bytes
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
            title=f"AegisAI Incident Report - {original_filename}",
            author="AegisAI SRE Platform",
            subject="Incident Analysis Report"
        )
        
        story = []
        
        # ── COVER PAGE ─────────────────────────────────
        story.extend(self._build_cover_page(analysis_data, original_filename))
        story.append(PageBreak())
        
        # ── EXECUTIVE SUMMARY ──────────────────────────
        story.extend(self._build_executive_summary(analysis_data))
        
        # ── SEVERITY BREAKDOWN ─────────────────────────
        story.extend(self._build_severity_breakdown(analysis_data))
        
        # ── ANOMALY DETAILS ────────────────────────────
        story.extend(self._build_anomaly_details(analysis_data))
        
        # ── INCIDENT REPORTS ───────────────────────────
        story.extend(self._build_incident_reports(analysis_data))
        
        # ── REMEDIATION PLAN ───────────────────────────
        story.extend(self._build_remediation_plan(analysis_data))
        
        # ── STATISTICS & METRICS ───────────────────────
        story.extend(self._build_statistics(analysis_data))
        
        # ── APPENDIX ───────────────────────────────────
        story.extend(self._build_appendix(analysis_data, original_filename))
        
        # Build PDF
        doc.build(story)
        
        if self.output_path:
            with open(self.output_path, 'wb') as f:
                f.write(self.buffer.getvalue())
            return self.buffer.getvalue()
        
        return self.buffer.getvalue()
    
    def _build_cover_page(self, data: Dict, filename: str) -> List:
        """Build the cover page of the report."""
        elements = []
        
        # Spacing from top
        elements.append(Spacer(1, 30*mm))
        
        # Logo / Title
        elements.append(Paragraph("🛡️ AegisAI", self.styles['ReportTitle']))
        elements.append(Paragraph("Enterprise SRE Platform", self.styles['ReportSubtitle']))
        
        elements.append(Spacer(1, 15*mm))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 10*mm))
        
        # Report title
        elements.append(Paragraph("Incident Analysis Report", self.styles['SectionHeader']))
        elements.append(Paragraph(
            f"Comprehensive log analysis for: <b>{filename}</b>",
            self.styles['BodyText2']
        ))
        
        elements.append(Spacer(1, 8*mm))
        
        # Severity gauge
        summary = data.get("summary", {})
        risk_level = summary.get("risk_level", "MEDIUM")
        elements.append(SeverityGauge(risk_level, width=250, height=35))
        
        elements.append(Spacer(1, 8*mm))
        
        # Quick stats box
        stats = data.get("statistics", {})
        quick_stats = [
            ["📊 Total Lines", f"{data.get('total_lines', 0):,}"],
            ["🔴 Anomalies Found", str(len(data.get("anomalies", [])))],
            ["🚨 Incidents Detected", str(len(data.get("incidents", [])))],
            ["⚠️ Critical Issues", str(summary.get("critical_anomalies", 0))],
            ["🖥️ Processing Mode", "GPU Accelerated" if data.get("gpu_used") else "CPU"],
        ]
        
        stats_table = Table(quick_stats, colWidths=[120, 120])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.DARK_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), self.MUTED_TEXT),
            ('TEXTCOLOR', (1, 0), (1, -1), self.LIGHT_TEXT),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(stats_table)
        
        elements.append(Spacer(1, 15*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#334155")))
        
        # Footer info
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            f"Generated: {data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))} UTC<br/>"
            f"Confidential - For Authorized Personnel Only",
            ParagraphStyle('CoverFooter', parent=self.styles['BodyText2'], 
                          fontSize=8, textColor=HexColor("#64748b"), alignment=TA_CENTER)
        ))
        
        return elements
    
    def _build_executive_summary(self, data: Dict) -> List:
        """Build executive summary section."""
        elements = []
        elements.append(Paragraph("1. Executive Summary", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 5*mm))
        
        summary = data.get("summary", {})
        
        # Risk level badge
        risk = summary.get("risk_level", "MEDIUM")
        risk_colors = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
        
        elements.append(Paragraph(
            f"<b>Overall Risk Level:</b> "
            f'<font color="{risk_colors.get(risk, "#6b7280")}"><b>{risk}</b></font>',
            self.styles['BodyText2']
        ))
        
        elements.append(Paragraph(
            f"<b>Recommendation:</b> {summary.get('recommendation', 'Review required')}",
            self.styles['BodyText2']
        ))
        
        # Key findings
        elements.append(Paragraph("Key Findings:", self.styles['SubsectionHeader']))
        findings = [
            f"• {summary.get('critical_anomalies', 0)} critical anomalies requiring immediate attention",
            f"• {summary.get('high_anomalies', 0)} high-severity issues identified",
            f"• {summary.get('total_anomalies', 0)} total anomalies detected across all severities",
            f"• {summary.get('total_incidents', 0)} distinct incidents identified",
        ]
        for finding in findings:
            elements.append(Paragraph(finding, self.styles['BodyText2']))
        
        # Next steps
        elements.append(Paragraph("Recommended Next Steps:", self.styles['SubsectionHeader']))
        for i, step in enumerate(summary.get("next_steps", []), 1):
            elements.append(Paragraph(f"{i}. {step}", self.styles['BodyText2']))
        
        elements.append(Spacer(1, 5*mm))
        return elements
    
    def _build_severity_breakdown(self, data: Dict) -> List:
        """Build severity breakdown with chart."""
        elements = []
        elements.append(Paragraph("2. Severity Breakdown", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 5*mm))
        
        stats = data.get("statistics", {})
        breakdown = stats.get("severity_breakdown", {})
        
        # Create severity bar chart
        if breakdown:
            drawing = Drawing(400, 150)
            
            # Background
            drawing.add(Rect(0, 0, 400, 150, fillColor=HexColor("#0f172a"), strokeColor=None))
            
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 30
            bc.height = 100
            bc.width = 300
            
            severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            values = [breakdown.get(s, 0) for s in severities]
            
            bc.data = [values]
            bc.categoryAxis.categoryNames = severities
            bc.categoryAxis.labels.fontName = 'Helvetica'
            bc.categoryAxis.labels.fontSize = 8
            bc.categoryAxis.labels.fillColor = HexColor("#94a3b8")
            
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(values) + 1 if values else 5
            bc.valueAxis.labels.fontName = 'Helvetica'
            bc.valueAxis.labels.fontSize = 7
            bc.valueAxis.labels.fillColor = HexColor("#64748b")
            
            # Bar colors
            bar_colors = [HexColor("#dc2626"), HexColor("#ef4444"), 
                         HexColor("#f59e0b"), HexColor("#10b981")]
            for i, color in enumerate(bar_colors):
                bc.bars[i].fillColor = color
            
            drawing.add(bc)
            elements.append(drawing)
        
        # Severity table
        sev_data = [["Severity", "Count", "Percentage", "Action Required"]]
        total = sum(breakdown.values()) or 1
        actions = {
            "CRITICAL": "🚨 IMMEDIATE",
            "HIGH": "⚠️ Within 1 hour",
            "MEDIUM": "📋 Within 24 hours",
            "LOW": "✅ Monitor"
        }
        
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = breakdown.get(sev, 0)
            pct = round(count / total * 100, 1)
            sev_data.append([sev, str(count), f"{pct}%", actions.get(sev, "")])
        
        sev_table = Table(sev_data, colWidths=[80, 60, 70, 120])
        sev_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.DARK_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.LIGHT_TEXT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        # Color severity rows
        for i, sev in enumerate(["CRITICAL", "HIGH", "MEDIUM", "LOW"], 1):
            if sev == "CRITICAL":
                sev_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#dc262620")),
                ]))
        
        elements.append(sev_table)
        elements.append(Spacer(1, 5*mm))
        return elements
    
    def _build_anomaly_details(self, data: Dict) -> List:
        """Build detailed anomaly listing."""
        elements = []
        elements.append(Paragraph("3. Anomaly Details", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 3*mm))
        
        anomalies = data.get("anomalies", [])
        
        if not anomalies:
            elements.append(Paragraph("✅ No anomalies detected.", self.styles['BodyText2']))
            return elements
        
        elements.append(Paragraph(f"Found {len(anomalies)} anomalies:", self.styles['BodyText2']))
        elements.append(Spacer(1, 2*mm))
        
        for i, anomaly in enumerate(anomalies[:15], 1):  # Max 15 in main report
            sev = anomaly.get("severity", "MEDIUM").upper()
            sev_color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", 
                        "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(sev, "#6b7280")
            
            anomaly_html = f"""
            <b>#{i}</b> 
            <font color="{sev_color}"><b>[{sev}]</b></font> 
            <b>{anomaly.get('type', 'Unknown')}</b><br/>
            <font size="8">Component: {anomaly.get('affected_component', 'N/A')}<br/>
            {anomaly.get('description', 'No description')}</font>
            """
            elements.append(Paragraph(anomaly_html, self.styles['BodyText2']))
            elements.append(Spacer(1, 1*mm))
        
        return elements
    
    def _build_incident_reports(self, data: Dict) -> List:
        """Build incident report cards."""
        elements = []
        elements.append(Paragraph("4. Incident Reports", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 3*mm))
        
        incidents = data.get("incidents", [])
        
        if not incidents:
            elements.append(Paragraph("No incidents identified.", self.styles['BodyText2']))
            return elements
        
        for i, incident in enumerate(incidents[:8], 1):
            sev = incident.get("severity", "MEDIUM").upper()
            sev_color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", 
                        "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(sev, "#6b7280")
            
            # Incident card with border
            incident_html = f"""
            <font color="{sev_color}"><b>INCIDENT #{i}: [{sev}]</b></font><br/>
            <b>Title:</b> {incident.get('title', 'Untitled')}<br/>
            <b>Description:</b> {incident.get('description', 'N/A')}<br/>
            <b>Recommended Action:</b> {incident.get('recommended_action', 'Review manually')}<br/>
            """
            elements.append(Paragraph(incident_html, self.styles['BodyText2']))
            
            # Separator between incidents
            if i < len(incidents[:8]):
                elements.append(HRFlowable(width="80%", thickness=0.3, color=HexColor("#334155")))
                elements.append(Spacer(1, 2*mm))
        
        return elements
    
    def _build_remediation_plan(self, data: Dict) -> List:
        """Build remediation action plan."""
        elements = []
        elements.append(Paragraph("5. Remediation Plan", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 3*mm))
        
        summary = data.get("summary", {})
        
        # Immediate actions
        elements.append(Paragraph("⚡ Immediate Actions:", self.styles['SubsectionHeader']))
        
        critical_anomalies = [a for a in data.get("anomalies", []) 
                            if a.get("severity") == "CRITICAL"]
        
        if critical_anomalies:
            for a in critical_anomalies[:5]:
                elements.append(Paragraph(
                    f"• [CRITICAL] {a.get('type', 'Unknown')}: {a.get('description', 'Investigate immediately')}",
                    self.styles['BodyText2']
                ))
        else:
            elements.append(Paragraph("• No critical issues requiring immediate action", 
                                     self.styles['BodyText2']))
        
        # Short-term actions
        elements.append(Paragraph("📋 Short-term Actions (24-48 hours):", self.styles['SubsectionHeader']))
        high_anomalies = [a for a in data.get("anomalies", []) 
                         if a.get("severity") == "HIGH"]
        for a in high_anomalies[:5]:
            elements.append(Paragraph(
                f"• {a.get('type', 'Unknown')}: {a.get('description', 'Schedule investigation')}",
                self.styles['BodyText2']
            ))
        
        # Prevention measures
        elements.append(Paragraph("🛡️ Prevention Measures:", self.styles['SubsectionHeader']))
        elements.append(Paragraph("• Implement automated monitoring for detected patterns", self.styles['BodyText2']))
        elements.append(Paragraph("• Update runbooks with findings from this report", self.styles['BodyText2']))
        elements.append(Paragraph("• Schedule regular log audits to detect anomalies early", self.styles['BodyText2']))
        elements.append(Paragraph("• Configure alerts for critical severity patterns", self.styles['BodyText2']))
        
        return elements
    
    def _build_statistics(self, data: Dict) -> List:
        """Build statistics and metrics section."""
        elements = []
        elements.append(Paragraph("6. Statistics & Metrics", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 3*mm))
        
        stats = data.get("statistics", {})
        
        # Metrics table
        metrics_data = [
            ["Metric", "Value"],
            ["Total Log Lines Processed", f"{data.get('total_lines', 0):,}"],
            ["Error/Exception Lines", f"{stats.get('error_count', 0):,}"],
            ["Error Rate", f"{stats.get('error_rate', 0)}%"],
            ["Anomalies Detected", str(len(data.get('anomalies', [])))],
            ["Incidents Identified", str(len(data.get('incidents', [])))],
            ["Processing Mode", "GPU Accelerated" if data.get("gpu_used") else "CPU"],
            ["Generated At", data.get("generated_at", "N/A")],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[180, 180])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.DARK_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.LIGHT_TEXT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#0f172a"), HexColor("#1a2332")]),
        ]))
        
        elements.append(metrics_table)
        
        # Top affected components
        elements.append(Paragraph("Top Affected Components:", self.styles['SubsectionHeader']))
        for comp in stats.get("top_components", []):
            elements.append(Paragraph(
                f"• <b>{comp.get('component', 'Unknown')}</b>: {comp.get('count', 0)} incidents",
                self.styles['BodyText2']
            ))
        
        return elements
    
    def _build_appendix(self, data: Dict, filename: str) -> List:
        """Build appendix with metadata and disclaimer."""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Appendix", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        elements.append(Spacer(1, 5*mm))
        
        elements.append(Paragraph("A. Report Metadata", self.styles['SubsectionHeader']))
        metadata = [
            ["Field", "Value"],
            ["Report ID", f"AEGIS-{datetime.now().strftime('%Y%m%d%H%M%S')}"],
            ["Source File", filename],
            ["Generated", data.get("generated_at", "N/A")],
            ["Platform", "AegisAI Enterprise SRE Platform"],
            ["GPU Acceleration", "Enabled" if data.get("gpu_used") else "Disabled - CPU Mode"],
            ["Analyzed Lines", f"{data.get('total_lines', 0):,}"],
            ["Anomalies Found", str(len(data.get("anomalies", [])))],
        ]
        
        meta_table = Table(metadata, colWidths=[120, 240])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.DARK_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.LIGHT_TEXT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("B. Disclaimer", self.styles['SubsectionHeader']))
        elements.append(Paragraph(
            "This report is auto-generated by AegisAI using artificial intelligence. "
            "While every effort is made to ensure accuracy, all findings should be reviewed "
            "by qualified SRE personnel before taking action. The platform uses machine "
            "learning models that may produce occasional false positives or miss edge cases.",
            self.styles['BodyText2']
        ))
        
        elements.append(Paragraph(
            "<i>Confidential - For internal use only. Do not distribute without authorization.</i>",
            self.styles['BodyText2']
        ))
        
        return elements
    
    def get_buffer(self) -> io.BytesIO:
        """Get the PDF buffer for streaming."""
        self.buffer.seek(0)
        return self.buffer