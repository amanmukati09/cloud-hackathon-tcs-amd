import gradio as gr

custom_css = """
/* Base styling */
body { font-family: 'Inter', -apple-system, sans-serif !important; background-color: #0f172a !important; }
footer { display: none !important; }

/* Navigation */
.nav-container { 
    display: flex !important; 
    align-items: center !important; 
    justify-content: space-between !important; 
    background: transparent !important;
    padding: 8px 15px !important; 
    margin-bottom: 20px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    min-height: 50px !important;
}
.nav-left { display: flex !important; align-items: center !important; gap: 10px !important; }
.nav-right { display: flex !important; align-items: center !important; gap: 8px !important; }
.welcome-text h3 { margin: 0 !important; color: #f8fafc !important; font-weight: 600 !important; font-size: 1.2rem !important; }

.logout-btn { 
    height: 34px !important; 
    border-radius: 8px !important; 
    font-weight: 600 !important; 
    transition: all 0.2s !important; 
    padding: 0 12px !important;
    font-size: 0.85rem !important;
    white-space: nowrap !important;
}

/* Theme Toggle Button */
.theme-toggle-btn {
    height: 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    border-radius: 8px !important;
    font-size: 1.1rem !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(255, 255, 255, 0.05) !important;
}
.theme-toggle-btn:hover {
    transform: scale(1.05);
    background: rgba(255, 255, 255, 0.1) !important;
}

/* Footer */
.footer-container {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 12px 20px !important;
    margin-top: 40px !important;
    border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    background: rgba(15, 23, 42, 0.4) !important;
    border-radius: 12px 12px 0 0 !important;
}
.footer-logo { text-align: left !important; color: #94a3b8 !important; font-size: 0.95rem !important; font-weight: 600 !important; letter-spacing: 0.5px !important; }
.footer-role p { text-align: right !important; margin: 0 !important; color: #38bdf8 !important; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 1px !important; text-transform: uppercase !important; }

/* Auth box */
.auth-box { max-width: 480px !important; margin: 60px auto 0 auto !important; float: none !important; }

/* Glass cards */
.glass-card { 
    background: rgba(30, 41, 59, 0.5) !important; 
    border: 1px solid rgba(255, 255, 255, 0.08) !important; 
    padding: 16px !important; 
    border-radius: 12px !important; 
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    display: flex !important; 
    flex-direction: column !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: hidden !important;
}
.push-bottom { margin-top: auto !important; }

/* Equal height columns */
.equal-height > .gr-column { display: flex !important; flex-direction: column !important; }
.equal-height > .gr-column > *:first-child { flex: 1 1 auto !important; height: auto !important; min-height: 0 !important; }

/* Internal spacing */
.glass-card > * { margin-top: 0 !important; margin-bottom: 0.5rem !important; flex-shrink: 0 !important; }
.glass-card > *:last-child { margin-bottom: 0 !important; }

/* Scrollable outputs */
.scrollable-output { flex: 1 1 auto !important; min-height: 0 !important; overflow-y: auto !important; max-height: 100% !important; }
.scrollable-output label { flex-shrink: 0 !important; }
.scrollable-output > div { flex: 1 1 auto !important; min-height: 0 !important; overflow-y: auto !important; }

/* Tables */
.table-scroll { max-height: 300px !important; overflow-y: auto !important; display: block !important; width: 100% !important; border-radius: 8px; }
.short-table { max-height: 180px !important; overflow-y: auto !important; display: block !important; width: 100% !important; border-radius: 8px; }

/* Admin panel */
.admin-panel { 
    border: 2px solid rgba(245, 158, 11, 0.3) !important; 
    background: rgba(245, 158, 11, 0.02) !important; 
    border-radius: 16px !important; 
    padding: 25px !important; 
    margin-bottom: 25px !important; 
}

/* Community feed styling */
.community-feed table {
    border-collapse: separate !important;
    border-spacing: 0 8px !important;
}
.community-feed tr {
    background: rgba(30, 41, 59, 0.7) !important;
    border-radius: 8px !important;
    transition: background 0.2s;
}
.community-feed tr:hover {
    background: rgba(30, 41, 59, 0.9) !important;
}
.community-feed td {
    padding: 10px 12px !important;
    border: none !important;
}
.community-comments table {
    border-collapse: separate !important;
    border-spacing: 0 4px !important;
}
.community-comments tr {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 6px !important;
}
.community-comments td {
    padding: 8px 10px !important;
    border: none !important;
}

"""



saas_theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    spacing_size="lg",
    radius_size="lg"
)