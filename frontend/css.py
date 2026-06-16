# frontend/css.py

import gradio as gr

custom_css = """
/* ========== BASE ========== */
body { font-family: 'Inter', -apple-system, sans-serif !important; background-color: #0f172a !important; }
footer { display: none !important; }

/* ========== NAVBAR ========== */
.nav-container { 
    display: flex !important; 
    align-items: center !important; 
    justify-content: space-between !important; 
    background: transparent !important;
    padding: 6px 12px !important; 
    margin-bottom: 12px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    min-height: 42px !important;
}
.nav-left { display: flex !important; align-items: center !important; gap: 8px !important; }
.nav-right { display: flex !important; align-items: center !important; gap: 6px !important; }
.welcome-text h3 { margin: 0 !important; color: #f8fafc !important; font-weight: 600 !important; font-size: 1.1rem !important; }
.logout-btn { 
    height: 30px !important; 
    border-radius: 6px !important; 
    font-weight: 600 !important; 
    padding: 0 10px !important;
    font-size: 0.8rem !important;
    white-space: nowrap !important;
}

.demo-overlay {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    z-index: 1000 !important;
    max-width: 400px !important;
}

.sql-editor textarea {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    background: #0d1117 !important;
    color: #e6edf3 !important;
    font-size: 0.8rem !important;
}


/* ========== UPLOAD BOX ========== */
.upload-box {
    background: rgba(0,0,0,0.15) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    padding: 10px !important;
    min-height: 80px !important;
    display: flex !important;
    flex-direction: column !important;
}
.upload-box p { margin: 0 0 4px 0 !important; font-size: 0.85em !important; }
.upload-area { flex: 1 !important; min-height: 50px !important; }

.upload-status {
    font-size: 0.75em !important;
    min-height: 18px !important;
    max-height: 36px !important;  /* 🆕 allow 2 lines */
    overflow-y: auto !important;  /* 🆕 scroll if needed */
    margin-top: 4px !important;
    color: #94a3b8 !important;
    word-break: break-word !important;
}
.upload-status p {
    margin: 0 !important;
    font-size: 0.75em !important;
}

/* ========== IMAGE UPLOAD BOX (TALLER) ========== */
.image-upload-box {
    background: rgba(0,0,0,0.15) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    padding: 12px !important;
    min-height: 180px !important;   /* 🆕 taller */
    display: flex !important;
    flex-direction: column !important;
}
.image-upload-box p { margin: 0 0 6px 0 !important; font-size: 0.9em !important; }
.image-upload-area { flex: 1 !important; min-height: 120px !important; }
.image-upload-area .gr-file {
    min-height: 120px !important;
}

/* ========== MATCHED BUTTON HEIGHTS ========== */
.image-action-row .gr-button {
    height: 40px !important;
}

/* ========== FOOTER ========== */
.footer-container {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 8px 16px !important;
    margin-top: 20px !important;
    border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    background: rgba(15, 23, 42, 0.4) !important;
    border-radius: 12px 12px 0 0 !important;
}
.footer-logo { text-align: left !important; color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 600 !important; }
.footer-role p { text-align: right !important; margin: 0 !important; color: #38bdf8 !important; font-weight: 700 !important; font-size: 0.75rem !important; }

/* ========== AUTH ========== */
.auth-box { max-width: 440px !important; margin: 40px auto 0 auto !important; float: none !important; }

/* ========== CARDS ========== */
.glass-card { 
    background: rgba(30, 41, 59, 0.5) !important; 
    border: 1px solid rgba(255, 255, 255, 0.06) !important; 
    padding: 12px !important; 
    border-radius: 10px !important; 
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    display: flex !important; 
    flex-direction: column !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: hidden !important;
    max-height: 100% !important;
}
.push-bottom { margin-top: auto !important; }

/* ========== EQUAL HEIGHT ========== */
.equal-height > .gr-column {
    display: flex !important;
    flex-direction: column !important;
}
.equal-height > .gr-column > *:first-child {
    flex: 1 1 auto !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: 100% !important;
}

/* ========== CARD SPACING ========== */
.glass-card > * {
    margin-top: 0 !important;
    margin-bottom: 6px !important;
    flex-shrink: 0 !important;
}
.glass-card > *:first-child { margin-top: 0 !important; }
.glass-card > *:last-child { margin-bottom: 0 !important; }

/* ========== SCROLLABLE OUTPUTS ========== */
.scrollable-output {
    flex: 1 1 auto !important;
    min-height: 60px !important;
    max-height: none !important;
    overflow-y: auto !important;
    padding: 6px 8px !important;
    border: 1px solid rgba(255,255,255,0.04) !important;
    border-radius: 6px !important;
    background: rgba(0,0,0,0.12) !important;
    margin-bottom: 4px !important;
}
.scrollable-output label { flex-shrink: 0 !important; }
.scrollable-output > div { flex: 1 1 auto !important; min-height: 0 !important; overflow-y: auto !important; }

/* ========== PREDICTIONS PANEL ========== */
.predictions-panel {
    max-height: 250px !important;
    overflow-y: auto !important;
    padding: 8px !important;
}

/* ========== TAB SPACING ========== */
.gr-tab-item { padding: 6px 12px !important; }
.gr-tabs { gap: 0 !important; }
.tabs > .tab-nav { margin-bottom: 8px !important; }

/* ========== TABLES ========== */
.table-scroll { 
    max-height: 220px !important; 
    overflow-y: auto !important; 
    display: block !important; 
    width: 100% !important; 
    border-radius: 6px; 
}
.short-table { 
    max-height: 140px !important; 
    overflow-y: auto !important; 
    display: block !important; 
    width: 100% !important; 
    border-radius: 6px; 
}

/* ========== CHAT AREA ========== */
.gr-chatbot {
    min-height: 350px !important;
    max-height: 400px !important;
}

/* ========== ADMIN ========== */
.admin-panel { 
    border: 1px solid rgba(245, 158, 11, 0.2) !important; 
    background: rgba(245, 158, 11, 0.01) !important; 
    border-radius: 12px !important; 
    padding: 16px !important; 
    margin-bottom: 16px !important; 
}

/* ========== COMMUNITY ========== */
.community-feed table {
    border-collapse: separate !important;
    border-spacing: 0 4px !important;
}
.community-feed tr {
    background: rgba(30, 41, 59, 0.6) !important;
    border-radius: 6px !important;
}
.community-feed td { padding: 6px 8px !important; border: none !important; }
.community-comments table {
    border-collapse: separate !important;
    border-spacing: 0 3px !important;
}
.community-comments tr { background: rgba(15, 23, 42, 0.5) !important; border-radius: 4px !important; }
.community-comments td { padding: 4px 6px !important; border: none !important; }

/* ========== STREAMING CURSOR ========== */
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
.streaming-cursor { animation: blink 0.8s infinite; color: #38bdf8; font-weight: bold; }

/* ========== COMPACT FORMS ========== */
.gr-textbox textarea { min-height: 60px !important; }
.gr-textbox label { margin-bottom: 2px !important; font-size: 0.8rem !important; }
.gr-button { margin-top: 2px !important; margin-bottom: 2px !important; }
.gr-dropdown { margin-bottom: 4px !important; }

/* ========== RESPONSIVE ROW GAPS ========== */
.gr-row { gap: 8px !important; }
.gr-box { gap: 6px !important; }

/* ========== SYSTEM HEALTH CARD ========== */
.health-card {
    padding: 12px !important;
    text-align: center !important;
}
.health-card h2 { font-size: 1.5rem !important; margin: 4px 0 !important; }
.health-card p { margin: 2px 0 !important; font-size: 0.8rem !important; }

/* ========== KNOWLEDGE BASE SCROLL ========== */
.kb-results-scroll {
    max-height: 500px !important;
    overflow-y: auto !important;
    padding-right: 8px !important;
    margin-top: 8px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    background: rgba(0,0,0,0.1) !important;
}
.kb-results-scroll::-webkit-scrollbar { width: 6px; }
.kb-results-scroll::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); border-radius: 3px; }
.kb-results-scroll::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.3); border-radius: 3px; }
.kb-results-scroll::-webkit-scrollbar-thumb:hover { background: rgba(56,189,248,0.5); }
.kb-results-scroll > div { padding-right: 4px; }

/* ========== BUTTON CONSISTENCY ========== */
.gr-button {
    height: 36px !important;
    min-height: 36px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    font-size: 0.82rem !important;
    padding: 0 14px !important;
}
.gr-button[variant="primary"] {
    font-weight: 600 !important;
}
.gr-button[variant="stop"] {
    font-weight: 600 !important;
}
.gr-button[size="sm"] {
    height: 30px !important;
    min-height: 30px !important;
    font-size: 0.75rem !important;
    padding: 0 10px !important;
}
.gr-button[size="lg"] {
    height: 44px !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
    padding: 0 20px !important;
}

/* ========== DEMO BUTTON ========== */
.demo-btn {
    background: linear-gradient(135deg, #38bdf8, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    animation: demo-pulse 2s infinite;
}
@keyframes demo-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(56,189,248,0.4); }
    50% { box-shadow: 0 0 0 8px rgba(56,189,248,0); }
}

/* ========== LIVE MONITOR BADGES ========== */
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

/* ========== LIVE LOG STREAM ========== */
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
.live-log span { display: block; white-space: pre-wrap; word-break: break-all; }
.live-log::-webkit-scrollbar { width: 4px; }
.live-log::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

/* ========== STAT CARD ========== */
.stat-card-inner {
    padding: 12px !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 10px !important;
    text-align: center !important;
}
.stat-icon { font-size: 1.3rem !important; margin-bottom: 2px !important; }
.stat-value { font-size: 1.6rem !important; font-weight: 800 !important; line-height: 1.2 !important; }
.stat-label { font-size: 0.7rem !important; color: #64748b !important; font-weight: 500 !important; text-transform: uppercase !important; }


"""

# At the bottom of your custom_css string, add:
from styles.bulk_analysis import BULK_ANALYSIS_CSS
from styles.live_monitor import LIVE_MONITOR_CSS


custom_css += BULK_ANALYSIS_CSS
custom_css += LIVE_MONITOR_CSS

saas_theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    spacing_size="sm",
    radius_size="md"
)