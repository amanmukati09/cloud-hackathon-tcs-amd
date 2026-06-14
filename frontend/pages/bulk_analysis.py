"""
Bulk Log Analysis Page
Premium SaaS page for uploading log files and generating PDF reports.
Designed for seamless integration into main app.py via add_page() pattern.
"""

import gradio as gr
import requests
import os
import time
from datetime import datetime
from utils import BACKEND_URL

from components.cards import card, stat_card
from components.progress import progress_bar, step_progress
from components.headers import section_header, page_title
from styles.bulk_analysis import BULK_ANALYSIS_CSS


class BulkAnalysisPage:
    """
    Bulk Log Analysis & PDF Report Generation Page.
    
    Usage in app.py:
        bulk_page = BulkAnalysisPage()
        components = bulk_page.build()  # Returns dict of all components
        # Then wire events using components dict
    """
    
    def __init__(self):
        self.css = BULK_ANALYSIS_CSS
        
    def build(self) -> dict:
        """
        Build all UI components and return references for event wiring.
        
        Returns:
            dict: {
                'file_upload': gr.File,
                'analyze_btn': gr.Button,
                'pdf_btn': gr.Button,
                'clear_btn': gr.Button,
                'gpu_badge': gr.HTML,
                'stat_lines': gr.Column,
                'stat_anomalies': gr.Column,
                'stat_incidents': gr.Column,
                'stat_risk': gr.Column,
                'progress': gr.HTML,
                'step_progress': gr.HTML,
                'summary_output': gr.HTML,
                'anomalies_output': gr.HTML,
                'incidents_output': gr.HTML,
                'remediation_output': gr.HTML,
                'download_file': gr.File,
                'download_row': gr.Row,
                'file_info': gr.HTML,
                'sys_info': gr.HTML,
            }
        """
        comp = {}  # Components dictionary
        
        # ── GPU STATUS BADGE ───────────────────────────
        comp["gpu_badge"] = gr.HTML(
            value='<span class="gpu-badge gpu-inactive">💻 Checking GPU...</span>',
            elem_classes="gpu-badge-wrap"
        )
        
        # ── MAIN CONTENT: 2-COLUMN LAYOUT ──────────────
        with gr.Row(equal_height=True, elem_classes="bulk-main-row"):
            
            # ── LEFT COLUMN: UPLOAD & ACTIONS ──────────
            with gr.Column(scale=1, min_width=320):
                # Upload card
                with gr.Column(elem_classes="glass-card premium-card"):
                    gr.Markdown("### 📤 Upload Log File", elem_classes="card-title")
                    gr.Markdown("Supported: .log, .txt, .out (max 50MB, 50K lines)", elem_classes="card-subtitle")
                    
                    # Upload zone with visual feedback
                    gr.HTML("""
                        <div class="upload-zone" id="bulk-upload-zone">
                            <div class="upload-icon">📁</div>
                            <div class="upload-text">Drop log file here</div>
                            <div class="upload-hint">or click Browse button below</div>
                        </div>
                    """, elem_classes="upload-zone-wrap")
                    
                    comp["file_upload"] = gr.File(
                        file_count="single",
                        label="Select Log File",
                        file_types=[".log", ".txt", ".out"],
                        elem_classes="file-upload-input"
                    )
                    
                    comp["file_info"] = gr.HTML(
                        value='<div class="file-info-placeholder">📄 No file selected</div>'
                    )
                    
                    # Action buttons - equal height row
                    with gr.Row(elem_classes="button-row"):
                        comp["analyze_btn"] = gr.Button(
                            "🔍 Analyze Logs", 
                            variant="primary",
                            size="lg",
                            elem_classes="action-btn primary-btn"
                        )
                        comp["pdf_btn"] = gr.Button(
                            "📄 PDF Report",
                            variant="secondary", 
                            size="lg",
                            elem_classes="action-btn secondary-btn"
                        )
                        comp["clear_btn"] = gr.Button(
                            "🗑️",
                            variant="stop",
                            size="lg",
                            elem_classes="action-btn danger-btn"
                        )
                
                # Processing pipeline card
                with gr.Column(elem_classes="glass-card premium-card"):
                    gr.Markdown("### ⚙️ Processing Pipeline", elem_classes="card-title")
                    comp["step_progress"] = step_progress([
                        "Upload", "Pre-scan", "AI Analysis", "PDF", "Done"
                    ], current=0)
                    
                    comp["progress"] = progress_bar("Ready", 0)
                
                # System info card
                with gr.Column(elem_classes="glass-card premium-card"):
                    gr.Markdown("### 🖥️ System", elem_classes="card-title")
                    comp["sys_info"] = gr.HTML(value="""
                        <div class="sys-info-text">
                            <p>🧠 <b>AI:</b> Llama3 · Mistral · DeepSeek</p>
                            <p>💾 <b>Vector DB:</b> ChromaDB</p>
                            <p>📊 <b>PDF Engine:</b> ReportLab Pro</p>
                            <p>⚡ <b>Mode:</b> Auto-detect GPU/CPU</p>
                        </div>
                    """)
            
            # ── RIGHT COLUMN: RESULTS ──────────────────
            with gr.Column(scale=2, min_width=500):
                # Quick stats row - 4 equal stat cards
                with gr.Row(elem_classes="stats-grid"):
                    comp["stat_lines"] = gr.Markdown(
                        value='<div class="stat-card-inner" style="border-left: 3px solid #38bdf8;">'
                              '<div class="stat-icon">📝</div>'
                              '<div class="stat-value" style="color:#38bdf8;">0</div>'
                              '<div class="stat-label">Lines</div></div>',
                        elem_classes="stat-card"
                    )
                    comp["stat_anomalies"] = gr.Markdown(
                        value='<div class="stat-card-inner" style="border-left: 3px solid #ef4444;">'
                              '<div class="stat-icon">🔴</div>'
                              '<div class="stat-value" style="color:#ef4444;">0</div>'
                              '<div class="stat-label">Anomalies</div></div>',
                        elem_classes="stat-card"
                    )
                    comp["stat_incidents"] = gr.Markdown(
                        value='<div class="stat-card-inner" style="border-left: 3px solid #f59e0b;">'
                              '<div class="stat-icon">🚨</div>'
                              '<div class="stat-value" style="color:#f59e0b;">0</div>'
                              '<div class="stat-label">Incidents</div></div>',
                        elem_classes="stat-card"
                    )
                    comp["stat_risk"] = gr.Markdown(
                        value='<div class="stat-card-inner" style="border-left: 3px solid #10b981;">'
                              '<div class="stat-icon">⚠️</div>'
                              '<div class="stat-value" style="color:#10b981;">N/A</div>'
                              '<div class="stat-label">Risk</div></div>',
                        elem_classes="stat-card"
                    )
                                
                
                # Results in tabs
                with gr.Tabs(elem_classes="results-tabs"):
                    with gr.Tab("📊 Summary", id="bulk_summary"):
                        comp["summary_output"] = gr.HTML(
                            value='<div class="placeholder-text">Upload a log file and click <b>Analyze Logs</b></div>',
                            elem_classes="results-panel"
                        )
                    
                    with gr.Tab("🔴 Anomalies", id="bulk_anomalies"):
                        comp["anomalies_output"] = gr.HTML(
                            value='<div class="placeholder-text">Anomaly details appear here</div>',
                            elem_classes="results-panel"
                        )
                    
                    with gr.Tab("🚨 Incidents", id="bulk_incidents"):
                        comp["incidents_output"] = gr.HTML(
                            value='<div class="placeholder-text">Incident reports appear here</div>',
                            elem_classes="results-panel"
                        )
                    
                    with gr.Tab("🔧 Remediation", id="bulk_remediation"):
                        comp["remediation_output"] = gr.HTML(
                            value='<div class="placeholder-text">Remediation plan appears here</div>',
                            elem_classes="results-panel"
                        )
                
                # Download row (hidden until PDF generated)
                comp["download_row"] = gr.Row(visible=False)
                with comp["download_row"]:
                    with gr.Column(elem_classes="glass-card premium-card"):
                        gr.Markdown("### 📥 Download Ready", elem_classes="card-title")
                        comp["download_file"] = gr.File(
                            label="PDF Report",
                            visible=True,
                            elem_classes="download-file"
                        )
        
        return comp


# ── EVENT HANDLER FUNCTIONS (used by app.py wiring) ──

def check_gpu_status(token: str):
    """Check GPU status from backend and return badge HTML."""
    if not token:
        return gr.update(value='<span class="gpu-badge gpu-inactive">💻 Login to check</span>')
    try:
        res = requests.get(
            f"{BACKEND_URL}/bulk/gpu-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("gpu_available"):
                name = data.get("gpu_name", "GPU")
                mem = data.get("gpu_memory_gb", 0)
                return gr.update(value=f'<span class="gpu-badge gpu-active">⚡ {name} ({mem:.0f}GB)</span>')
    except:
        pass
    return gr.update(value='<span class="gpu-badge gpu-inactive">💻 CPU Mode</span>')


def handle_file_upload(file, token: str):
    """Handle file selection - update file info display."""
    if file is None:
        return (
            gr.update(value='<div class="file-info-placeholder">📄 No file selected</div>'),
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        )
    
    try:
        filename = file.name.split('/')[-1] if hasattr(file, 'name') else str(file)
        file_size = os.path.getsize(file.name) if hasattr(file, 'name') else 0
        
        if file_size > 1024 * 1024:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        else:
            size_str = f"{file_size/1024:.1f} KB"
        
        # Count lines for preview
        try:
            with open(file.name, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
        except:
            line_count = "?"
        
        info_html = f"""
        <div class="file-info-active">
            <span class="file-icon">📄</span>
            <div class="file-details">
                <span class="file-name">{filename}</span>
                <span class="file-meta">{size_str} · {line_count} lines</span>
            </div>
        </div>
        """
        return (
            gr.update(value=info_html),
            *[gr.update()] * 5
        )
    except:
        return (
            gr.update(value='<div class="file-info-active">📄 File selected</div>'),
            *[gr.update()] * 5
        )

def analyze_logs(file, token: str):
    """
    Analyze uploaded log file with progress tracking.
    This is a generator function that yields updates for streaming progress.
    """
    if file is None or not token:
        yield (
            gr.update(), gr.update(), gr.update(), gr.update(),  # stats
            gr.update(), gr.update(),  # progress, steps
            gr.update(), gr.update(), gr.update(), gr.update(),  # outputs
            gr.update(visible=False), gr.update(value=None)  # download
        )
        return
    
    # Initial progress
    yield (
        gr.update(), gr.update(), gr.update(), gr.update(),
        progress_bar("📤 Uploading file...", 10),
        step_progress(["Upload", "Pre-scan", "AI Analysis", "PDF", "Done"], 0),
        '<div class="alert-info">📤 Uploading log file to server...</div>',
        *[gr.update()] * 3,
        gr.update(visible=False), gr.update(value=None)
    )
    
    try:
        with open(file.name, 'rb') as f:
            files = {'file': (file.name.split('/')[-1], f, 'application/octet-stream')}
            res = requests.post(
                f"{BACKEND_URL}/bulk/analyze-logs",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
                timeout=300
            )
        
        if res.status_code == 200:
            data = res.json()
            analysis = data.get("analysis", {})
            summary = analysis.get("summary", {})
            stats = analysis.get("statistics", {})
            severity_bd = stats.get("severity_breakdown", {})
            
            total_lines = data.get("total_lines", 0)
            anomalies_count = len(analysis.get("anomalies", []))
            incidents_count = len(analysis.get("incidents", []))
            risk = summary.get("risk_level", "N/A")
            risk_color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(risk, "#10b981")
            
            # Build stat card HTML
            stat_lines_html = f'''<div class="stat-card-inner" style="border-left: 3px solid #38bdf8;">
                <div class="stat-icon">📝</div>
                <div class="stat-value" style="color:#38bdf8;">{total_lines:,}</div>
                <div class="stat-label">Lines</div></div>'''
                
            stat_anomalies_html = f'''<div class="stat-card-inner" style="border-left: 3px solid #ef4444;">
                <div class="stat-icon">🔴</div>
                <div class="stat-value" style="color:#ef4444;">{anomalies_count}</div>
                <div class="stat-label">Anomalies</div></div>'''
                
            stat_incidents_html = f'''<div class="stat-card-inner" style="border-left: 3px solid #f59e0b;">
                <div class="stat-icon">🚨</div>
                <div class="stat-value" style="color:#f59e0b;">{incidents_count}</div>
                <div class="stat-label">Incidents</div></div>'''
                
            stat_risk_html = f'''<div class="stat-card-inner" style="border-left: 3px solid {risk_color};">
                <div class="stat-icon">⚠️</div>
                <div class="stat-value" style="color:{risk_color};">{risk}</div>
                <div class="stat-label">Risk</div></div>'''
            
            # Build summary HTML
            summary_html = f"""
            <div class="results-content">
                <div class="result-header">
                    <h3>✅ Analysis Complete</h3>
                    <span class="risk-badge" style="background:{risk_color}20;color:{risk_color};border:1px solid {risk_color}40;">
                        Risk: {risk}
                    </span>
                </div>
                <div class="result-meta">
                    <p>📄 <b>File:</b> {data.get('filename', 'Unknown')}</p>
                    <p>📝 <b>Lines processed:</b> {total_lines:,}</p>
                    <p>⚡ <b>GPU Used:</b> {'✅ Yes' if data.get('gpu_used') else '❌ No (CPU)'}</p>
                    <p>🔴 <b>Critical:</b> {severity_bd.get('CRITICAL', 0)} | 
                       🟠 <b>High:</b> {severity_bd.get('HIGH', 0)} | 
                       🟡 <b>Medium:</b> {severity_bd.get('MEDIUM', 0)} | 
                       🟢 <b>Low:</b> {severity_bd.get('LOW', 0)}</p>
                </div>
                <div class="result-recommendation">
                    <b>💡 Recommendation:</b> {summary.get('recommendation', 'Review findings')}
                </div>
                <div class="result-next-steps">
                    <b>📋 Next Steps:</b>
                    <ul>
                        {''.join(f'<li>{s}</li>' for s in summary.get('next_steps', []))}
                    </ul>
                </div>
            </div>
            """
            
            # Build anomalies HTML (same as before)
            anomalies = analysis.get("anomalies", [])
            if anomalies:
                anomalies_html = '<div class="results-content"><h3>🔴 Detected Anomalies</h3>'
                for i, a in enumerate(anomalies[:15], 1):
                    sev = a.get("severity", "MEDIUM").upper()
                    sev_color = {"CRITICAL":"#dc2626","HIGH":"#ef4444","MEDIUM":"#f59e0b","LOW":"#10b981"}.get(sev, "#6b7280")
                    anomalies_html += f"""
                    <div class="anomaly-card" style="border-left:3px solid {sev_color};">
                        <div class="anomaly-header">
                            <span class="anomaly-number">#{i}</span>
                            <span class="anomaly-severity" style="background:{sev_color}20;color:{sev_color};">{sev}</span>
                            <span class="anomaly-type">{a.get('type', 'Unknown')}</span>
                        </div>
                        <div class="anomaly-body">
                            <small>🖥️ {a.get('affected_component', 'N/A')}</small>
                            <p>{a.get('description', 'No description')[:200]}</p>
                        </div>
                    </div>
                    """
                anomalies_html += '</div>'
            else:
                anomalies_html = '<div class="results-content"><div class="alert-success">✅ No anomalies detected</div></div>'
            
            # Build incidents HTML
            incidents = analysis.get("incidents", [])
            if incidents:
                incidents_html = '<div class="results-content"><h3>🚨 Identified Incidents</h3>'
                for inc in incidents[:8]:
                    sev = inc.get("severity", "MEDIUM").upper()
                    sev_color = {"CRITICAL":"#dc2626","HIGH":"#ef4444","MEDIUM":"#f59e0b","LOW":"#10b981"}.get(sev, "#6b7280")
                    incidents_html += f"""
                    <div class="incident-card" style="border-left:3px solid {sev_color};">
                        <span style="color:{sev_color};font-weight:700;">[{sev}]</span>
                        <b>{inc.get('title', 'Untitled')}</b>
                        <p>{inc.get('description', '')[:200]}</p>
                        <div class="incident-action">
                            🔧 <b>Action:</b> {inc.get('recommended_action', 'Review manually')}
                        </div>
                    </div>
                    """
                incidents_html += '</div>'
            else:
                incidents_html = '<div class="results-content"><div class="alert-success">✅ No incidents identified</div></div>'
            
            # Build remediation HTML
            remediation_html = f"""
            <div class="results-content">
                <h3>🔧 Remediation Plan</h3>
                <div class="remediation-section">
                    <h4>⚡ Immediate ({severity_bd.get('CRITICAL', 0)} critical)</h4>
                    <ul>
                        {''.join(f'<li>{a.get("type", "Unknown")}: {a.get("description", "Investigate")[:100]}</li>' 
                        for a in anomalies if a.get("severity") == "CRITICAL") or '<li>No critical issues</li>'}
                    </ul>
                </div>
                <div class="remediation-section">
                    <h4>📋 Short-term (24-48h)</h4>
                    <ul>
                        {''.join(f'<li>{a.get("type", "Unknown")}: {a.get("description", "Review")[:100]}</li>' 
                        for a in anomalies if a.get("severity") == "HIGH") or '<li>No high-severity issues</li>'}
                    </ul>
                </div>
                <div class="remediation-section">
                    <h4>🛡️ Prevention</h4>
                    <ul>
                        <li>Configure alerts for detected patterns</li>
                        <li>Update runbooks with findings</li>
                        <li>Schedule regular log audits</li>
                    </ul>
                </div>
            </div>
            """
            
            yield (
                stat_lines_html,
                stat_anomalies_html,
                stat_incidents_html,
                stat_risk_html,
                progress_bar("✅ Complete!", 100),
                step_progress(["Upload", "Pre-scan", "AI Analysis", "PDF", "Done"], 4),
                summary_html,
                anomalies_html,
                incidents_html,
                remediation_html,
                gr.update(visible=False),
                gr.update(value=None)
            )
        else:
            error_msg = res.json().get("detail", f"Error {res.status_code}")
            yield (
                *[gr.update()] * 4,
                progress_bar("❌ Failed", 0),
                gr.update(),
                f'<div class="alert-error">❌ {error_msg}</div>',
                *[gr.update()] * 3,
                gr.update(visible=False),
                gr.update(value=None)
            )
    except Exception as e:
        yield (
            *[gr.update()] * 4,
            progress_bar(f"❌ Error", 0),
            gr.update(),
            f'<div class="alert-error">❌ Connection Error: {str(e)[:100]}</div>',
            *[gr.update()] * 3,
            gr.update(visible=False),
            gr.update(value=None)
        )



def generate_pdf(file, token: str):
    """Generate PDF report and return download file."""
    if file is None or not token:
        return gr.update(visible=False), gr.update(value=None)
    
    try:
        with open(file.name, 'rb') as f:
            files = {'file': (file.name.split('/')[-1], f, 'application/octet-stream')}
            res = requests.post(
                f"{BACKEND_URL}/bulk/generate-pdf",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
                timeout=300
            )
        
        if res.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AegisAI_Report_{timestamp}.pdf"
            
            with open(filename, 'wb') as f:
                f.write(res.content)
            
            return gr.update(visible=True), gr.update(value=filename, visible=True)
        
    except Exception as e:
        print(f"PDF error: {e}")
    
    return gr.update(visible=False), gr.update(value=None)



def clear_all():
    """Clear all inputs and outputs."""
    empty_stat = '<div class="stat-card-inner" style="border-left: 3px solid #38bdf8;"><div class="stat-icon">📝</div><div class="stat-value" style="color:#38bdf8;">0</div><div class="stat-label">Lines</div></div>'
    empty_anomaly = '<div class="stat-card-inner" style="border-left: 3px solid #ef4444;"><div class="stat-icon">🔴</div><div class="stat-value" style="color:#ef4444;">0</div><div class="stat-label">Anomalies</div></div>'
    empty_incident = '<div class="stat-card-inner" style="border-left: 3px solid #f59e0b;"><div class="stat-icon">🚨</div><div class="stat-value" style="color:#f59e0b;">0</div><div class="stat-label">Incidents</div></div>'
    empty_risk = '<div class="stat-card-inner" style="border-left: 3px solid #10b981;"><div class="stat-icon">⚠️</div><div class="stat-value" style="color:#10b981;">N/A</div><div class="stat-label">Risk</div></div>'
    
    return (
        gr.update(value=None),  # file_upload
        gr.update(value='<div class="file-info-placeholder">📄 No file selected</div>'),  # file_info
        empty_stat, empty_anomaly, empty_incident, empty_risk,  # stats
        progress_bar("Ready", 0),  # progress
        step_progress(["Upload", "Pre-scan", "AI Analysis", "PDF", "Done"], 0),  # step_progress
        '<div class="placeholder-text">Upload a log file and click <b>Analyze Logs</b></div>',  # summary
        '<div class="placeholder-text">Anomaly details appear here</div>',  # anomalies
        '<div class="placeholder-text">Incident reports appear here</div>',  # incidents
        '<div class="placeholder-text">Remediation plan appears here</div>',  # remediation
        gr.update(visible=False),  # download_row
        gr.update(value=None)    # download_file
    )