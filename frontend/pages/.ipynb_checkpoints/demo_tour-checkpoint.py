"""
Demo Tour - Shows feature overview in a compact overlay.
"""

import gradio as gr

DEMO_STEPS = [
    {"icon": "🔍", "title": "Live Diagnosis", "desc": "AI analyzes logs, detects anomalies, finds root causes, suggests fixes."},
    {"icon": "📂", "title": "Bulk Analysis & PDF", "desc": "Upload 1,000+ logs. GPU-accelerated. Professional PDF reports."},
    {"icon": "📊", "title": "Smart Analytics", "desc": "Ask English questions. AI converts to SQL, returns formatted results."},
    {"icon": "🗺️", "title": "Dependency Graph", "desc": "Visual service map. Click nodes to see blast radius analysis."},
    {"icon": "🛰️", "title": "Live Monitor", "desc": "Real-time log streaming. Auto-incident detection and alerts."},
    {"icon": "🧠", "title": "Train Model", "desc": "Fine-tune Llama3 on your incidents. Custom SRE AI assistant."},
]


def get_demo_html():
    features_html = ""
    for step in DEMO_STEPS:
        features_html += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
            <span style="font-size:1.3rem;min-width:32px;text-align:center;">{step['icon']}</span>
            <div style="flex:1;min-width:0;">
                <b style="color:#f8fafc;font-size:0.8rem;">{step['title']}</b>
                <p style="color:#94a3b8;font-size:0.7rem;margin:1px 0 0 0;line-height:1.3;">{step['desc']}</p>
            </div>
        </div>"""

    return f"""
    <div style="background:rgba(15,23,42,0.98);border:1px solid rgba(56,189,248,0.25);border-radius:14px;padding:14px 18px;max-width:380px;margin:0 auto;box-shadow:0 6px 24px rgba(0,0,0,0.5);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <h3 style="color:#38bdf8;font-size:1rem;margin:0;">🛡️ AegisAI Features</h3>
            <span style="color:#64748b;font-size:0.65rem;">45+ AI Features</span>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">
            <span style="background:rgba(56,189,248,0.12);color:#38bdf8;padding:3px 8px;border-radius:10px;font-size:0.65rem;">GPU</span>
            <span style="background:rgba(16,185,129,0.12);color:#10b981;padding:3px 8px;border-radius:10px;font-size:0.65rem;">Multi-AI</span>
            <span style="background:rgba(245,158,11,0.12);color:#f59e0b;padding:3px 8px;border-radius:10px;font-size:0.65rem;">Real-Time</span>
            <span style="background:rgba(139,92,246,0.12);color:#8b5cf6;padding:3px 8px;border-radius:10px;font-size:0.65rem;">Auto-Fix</span>
        </div>
        {features_html}
    </div>
    """


def start_demo():
    return (
        get_demo_html(),
        gr.update(visible=True),
        gr.update(interactive=False),
        gr.update(visible=True),
    )


def skip_demo():
    return (
        gr.update(visible=False),
        gr.update(interactive=True),
        gr.update(visible=False),
    )