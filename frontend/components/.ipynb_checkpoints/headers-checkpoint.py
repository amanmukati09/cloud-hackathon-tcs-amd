"""
Header Components
Consistent section and page headers.
"""

import gradio as gr

def section_header(title: str, subtitle: str = None):
    """Consistent section header with optional subtitle."""
    with gr.Row():
        gr.Markdown(f"## {title}", elem_classes="section-title")
    if subtitle:
        gr.Markdown(subtitle, elem_classes="section-subtitle")

def page_title(title: str):
    """Page title with consistent styling."""
    gr.Markdown(
        f"""<div class="page-title-wrap">
            <h1 class="page-title-text">{title}</h1>
        </div>""",
        elem_classes="page-title-container"
    )