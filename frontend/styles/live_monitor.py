LIVE_MONITOR_CSS = """
/* Premium live stream log */
.live-log {
    background: #0d1117 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.8rem !important;
    line-height: 1.6 !important;
    max-height: 450px !important;
    overflow-y: auto !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
.live-log span {
    display: block;
    white-space: pre-wrap;
    word-break: break-all;
}
.live-log::-webkit-scrollbar { width: 4px; }
.live-log::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.02em;
}
.badge.active { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.badge.inactive { background: rgba(100,116,139,0.15); color: #64748b; border: 1px solid rgba(100,116,139,0.3); }

/* Incident cards */
.incident-card {
    border-left: 4px solid #ef4444;
    padding: 12px;
    margin: 8px 0;
    background: rgba(239,68,68,0.05);
    border-radius: 8px;
}
.incident-card h4 { margin: 0 0 4px 0; font-size: 0.95rem; }
.incident-card p { margin: 0; font-size: 0.8rem; color: #94a3b8; }

/* Pipeline step progression */
.pipeline-container {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    transition: all 0.3s ease;
}
.pipeline-step.done { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: #10b981; }
.pipeline-step.running { background: rgba(56,189,248,0.1); border-color: rgba(56,189,248,0.3); animation: pulse 2s infinite; }
.pipeline-step.skipped { background: rgba(100,116,139,0.1); border-color: rgba(100,116,139,0.2); color: #64748b; }
"""

