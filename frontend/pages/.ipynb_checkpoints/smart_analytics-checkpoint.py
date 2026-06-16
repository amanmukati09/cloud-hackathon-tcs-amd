"""
Smart Analytics Page
Natural language querying of incident data.
"""

import gradio as gr
import requests
from utils import BACKEND_URL


def build_analytics_tab(session_token):
    """Build the smart analytics tab UI."""
    comp = {}
    
    with gr.Column():
        gr.Markdown("### 📊 Smart Analytics")
        gr.Markdown("Ask questions about your incident data in plain English.")
        
        with gr.Row():
            with gr.Column(scale=3):
                comp["query_input"] = gr.Textbox(
                    placeholder="e.g., How many critical incidents this month?",
                    label="Ask a question about your incident data",
                    lines=2
                )
        comp["ask_btn"] = gr.Button("🔍 Ask AI", variant="primary", size="lg")
        
        # Preset queries
        gr.Markdown("#### 💡 Quick Questions")
        comp["preset_btns"] = []
        preset_questions = [
            "How many total incidents?",
            "Show incidents by severity",
            "Most common root causes",
            "Resolved vs open incidents",
            "Critical incidents this month",
            "Average resolution time",
            "Top 5 failing components",
            "Incident trend last 7 days"
        ]
        
        with gr.Row():
            for i, q in enumerate(preset_questions):
                btn = gr.Button(q, variant="secondary", size="md")
                comp["preset_btns"].append(btn)
        
        gr.Markdown("---")
        
        # Results area
        comp["results_output"] = gr.HTML(
            value='<div style="text-align:center;padding:40px;color:#94a3b8;">Ask a question above to see results</div>'
        )
        
        # Query history
        with gr.Accordion("📝 Query History", open=False):
            comp["history_output"] = gr.HTML(value="<p style='color:#64748b;'>No queries yet</p>")
    
    return comp


def ask_question(question, token):
    """Send a question to the analytics engine."""
    if not question or not question.strip():
        return '<div style="text-align:center;padding:40px;color:#94a3b8;">Please enter a question</div>', ""
    
    if not token:
        return '<div style="text-align:center;padding:40px;color:#ef4444;">Please login first</div>', ""
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/analytics/ask",
            json={"question": question.strip()},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if res.status_code == 200:
            data = res.json()
            html = data.get("html", "<p>No results</p>")
            # Generate simple history
            history = f'<div style="font-size:0.8rem;color:#94a3b8;">🕐 {question} - {data.get("explanation", "")}</div>'
            return html, history
        else:
            return f'<div style="color:#ef4444;">Error: {res.status_code} - {res.text[:200]}</div>', ""
    except Exception as e:
        return f'<div style="color:#ef4444;">Connection error: {str(e)[:100]}</div>', ""


def ask_preset(question, token):
    """Handle preset button click."""
    return ask_question(question, token)


# Store history across calls
_query_history = []


def update_history(new_entry):
    if new_entry:
        _query_history.insert(0, new_entry)
        if len(_query_history) > 10:
            _query_history.pop()
    return "<br>".join(_query_history) if _query_history else "<p style='color:#64748b;'>No queries yet</p>"