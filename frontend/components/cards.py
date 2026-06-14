"""
Consistent Card Components
All cards have matching heights, padding, and border styles.
"""

import gradio as gr

# Shared card styling - ensures consistency across all pages
CARD_ELEM_CLASSES = "glass-card premium-card"

def card(children: list = None, title: str = None, subtitle: str = None, 
         min_height: int = 200) -> gr.Column:
    """
    Creates a premium glass-morphism card with consistent styling.
    
    Args:
        children: List of gradio components to put inside
        title: Optional card title
        subtitle: Optional card subtitle
        min_height: Minimum height in pixels
    
    Returns:
        gr.Column with card styling
    """
    with gr.Column(elem_classes=CARD_ELEM_CLASSES, 
                   min_width=320, scale=1) as col:
        if title:
            gr.Markdown(f"### {title}", elem_classes="card-title")
        if subtitle:
            gr.Markdown(subtitle, elem_classes="card-subtitle")
        if title or subtitle:
            gr.Markdown("---", elem_classes="card-divider")
        if children:
            for child in children:
                child.render()
    return col


def stat_card(label: str, value: str = "0", color: str = "#38bdf8",
              icon: str = "📊") -> gr.Column:
    """
    Creates a statistics/metric card.
    
    Args:
        label: Metric label (e.g., "Lines Processed")
        value: Metric value
        color: Accent color for the value
        icon: Emoji icon
    """
    with gr.Column(elem_classes=f"stat-card", min_width=140):
        gr.Markdown(
            f"""
            <div class="stat-card-inner" style="border-left: 3px solid {color};">
                <div class="stat-icon">{icon}</div>
                <div class="stat-value" style="color: {color};">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """,
            elem_classes="stat-card-content"
        )
    return gr.Column()


def detail_card(title: str, content: str = "", badge: str = None, 
                badge_color: str = "#38bdf8") -> gr.Column:
    """
    Creates a detail/info card with optional badge.
    
    Args:
        title: Card title
        content: Card content (HTML supported)
        badge: Optional badge text
        badge_color: Badge color
    """
    with gr.Column(elem_classes="detail-card", min_width=300):
        header_html = f'<div class="detail-card-header">'
        header_html += f'<span class="detail-card-title">{title}</span>'
        if badge:
            header_html += f'<span class="detail-card-badge" style="background:{badge_color}20;color:{badge_color};">{badge}</span>'
        header_html += '</div>'
        gr.Markdown(header_html, elem_classes="detail-card-header-wrap")
        if content:
            gr.Markdown(content, elem_classes="detail-card-body")
    return gr.Column()