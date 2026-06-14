"""
Progress Components
Animated progress bars and loading indicators.
"""

import gradio as gr
import time

def progress_bar(label: str = "Processing...", value: float = 0.0) -> gr.HTML:
    """
    Creates an animated progress bar.
    
    Args:
        label: Progress label
        value: Progress value (0-100)
    """
    pct = min(max(value, 0), 100)
    
    # Determine color based on progress
    if pct < 30:
        color = "#38bdf8"
    elif pct < 70:
        color = "#f59e0b"
    else:
        color = "#10b981"
    
    html = f"""
    <div class="progress-container">
        <div class="progress-header">
            <span class="progress-label">{label}</span>
            <span class="progress-pct" style="color:{color};">{pct:.0f}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{pct}%;background:{color};"></div>
        </div>
    </div>
    """
    return gr.HTML(value=html)


def loading_spinner(message: str = "Loading...") -> gr.HTML:
    """
    Creates a CSS loading spinner.
    
    Args:
        message: Loading message
    """
    html = f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-message">{message}</p>
    </div>
    """
    return gr.HTML(value=html)


def step_progress(steps: list, current: int = 0) -> gr.HTML:
    """
    Creates a step progress indicator.
    
    Args:
        steps: List of step names
        current: Current step index (0-based)
    """
    html = '<div class="step-progress">'
    for i, step in enumerate(steps):
        if i < current:
            status_class = "completed"
            icon = "✅"
        elif i == current:
            status_class = "active"
            icon = "🔄"
        else:
            status_class = "pending"
            icon = "⏳"
        
        html += f"""
        <div class="step-item {status_class}">
            <div class="step-circle">{icon}</div>
            <div class="step-label">{step}</div>
        </div>
        """
        if i < len(steps) - 1:
            html += f'<div class="step-connector {status_class}"></div>'
    html += '</div>'
    return gr.HTML(value=html)