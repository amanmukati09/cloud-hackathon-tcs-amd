"""
SQL Runner Page - Dark terminal-style SQL IDE for admins.
"""

import gradio as gr
import requests
from utils import BACKEND_URL

PRESET_QUERIES = [
    ("📊 All Incidents", "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 20"),
    ("📈 Status Count", "SELECT status, COUNT(*) as count FROM incidents GROUP BY status"),
    ("🔴 Critical", "SELECT * FROM incidents WHERE anomaly_description LIKE '%CRITICAL%' ORDER BY timestamp DESC LIMIT 20"),
    ("👤 Users", "SELECT id, email, full_name, is_admin, created_at FROM users"),
    ("💬 Chat Sessions", "SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT 20"),
    ("💬 Chat Messages", "SELECT cm.* FROM chat_messages cm JOIN chat_sessions cs ON cm.session_id=cs.id ORDER BY cm.timestamp DESC LIMIT 30"),
    ("🎫 Tickets", "SELECT * FROM escalation_tickets ORDER BY created_at DESC"),
    ("📝 Posts", "SELECT * FROM community_posts ORDER BY created_at DESC"),
    ("🔑 API Keys", "SELECT id, name, key_prefix, is_active, created_at FROM api_keys"),
    ("📋 Audit Logs", "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 30"),
    ("🔔 Notifications", "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 30"),
    ("🏢 Workspaces", "SELECT * FROM workspaces"),
    ("✅ Resolved Today", "SELECT * FROM incidents WHERE status='resolved' AND date(timestamp)=date('now')"),
    ("⏱️ Avg Resolution", "SELECT ROUND(AVG(CAST(julianday(resolved_at)-julianday(timestamp) AS REAL)*24),1) as avg_hours FROM incidents WHERE status='resolved'"),
    ("📅 Daily Count", "SELECT date(timestamp) as date, COUNT(*) as incidents FROM incidents GROUP BY date(timestamp) ORDER BY date DESC LIMIT 30"),
    ("🗄️ Schema", "SELECT name, type FROM sqlite_master WHERE type='table' ORDER BY name"),
]


def build_sql_runner_tab(session_token):
    comp = {}
    
    with gr.Column():
        gr.Markdown("### 🏃 SQL Runner")
        gr.Markdown("Execute SQL queries directly on the database. Admin only.")
        
        with gr.Row():
            with gr.Column(scale=1, min_width=200):
                gr.Markdown("#### 📋 Tables")
                comp["tables_list"] = gr.HTML(value="<p style='color:#64748b;'>Click refresh</p>")
                comp["refresh_tables_btn"] = gr.Button("🔄 Refresh", variant="secondary", size="sm")
                comp["schema_info"] = gr.HTML(value="")
            
            with gr.Column(scale=3, min_width=500):
                gr.Markdown("#### ⚡ Query Editor")
                comp["query_input"] = gr.Textbox(
                    placeholder="SELECT * FROM incidents LIMIT 10;",
                    lines=4,
                    label="SQL Query",
                    elem_classes="sql-editor"
                )
                with gr.Row():
                    comp["execute_btn"] = gr.Button("▶️ Execute (SELECT)", variant="primary")
                    comp["execute_danger_btn"] = gr.Button("⚠️ Execute (INSERT/UPDATE/DELETE)", variant="stop")
                    comp["clear_btn"] = gr.Button("🗑️ Clear", variant="secondary", size="sm")
                
                comp["confirm_checkbox"] = gr.Checkbox(label="I confirm this write operation", visible=False)
                comp["query_result"] = gr.HTML(
                    value="<div style='color:#64748b;text-align:center;padding:20px;'>Run a query to see results</div>"
                )
        
        gr.Markdown("#### 💡 Quick Queries")
        with gr.Row():
            # First row of presets
            for i in range(0, 8):
                btn = gr.Button(PRESET_QUERIES[i][0], variant="secondary", size="sm")
                btn.click(fn=lambda q=PRESET_QUERIES[i][1]: q, outputs=[comp["query_input"]])
        
        with gr.Row():
            # Second row of presets
            for i in range(8, 16):
                btn = gr.Button(PRESET_QUERIES[i][0], variant="secondary", size="sm")
                btn.click(fn=lambda q=PRESET_QUERIES[i][1]: q, outputs=[comp["query_input"]])
    
    return comp


def fetch_tables(token):
    if not token:
        return "<p style='color:#ef4444;'>Login required</p>", ""
    try:
        res = requests.get(f"{BACKEND_URL}/admin/sql/tables", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            tables = res.json().get("tables", [])
            html = "<div style='font-size:0.75rem;max-height:300px;overflow-y:auto;'>"
            for t in tables:
                html += f"<div style='padding:4px 8px;margin:2px 0;background:rgba(0,0,0,0.2);border-radius:4px;cursor:pointer;' onclick='document.querySelector(\"textarea\").value=\"SELECT * FROM {t} LIMIT 10\";document.querySelector(\"textarea\").dispatchEvent(new Event(\"input\"));'>{t}</div>"
            html += "</div>"
            return html, ""
    except:
        pass
    return "<p style='color:#ef4444;'>Failed</p>", ""


def execute_query(query, token, confirm=False):
    if not query.strip():
        return "<div style='color:#f59e0b;'>Enter a query</div>", gr.update(visible=False)
    if not token:
        return "<div style='color:#ef4444;'>Login required</div>", gr.update(visible=False)
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/admin/sql/execute",
            json={"query": query.strip(), "confirm": confirm},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if res.status_code == 200:
            data = res.json()
            
            if data.get("type") == "select":
                columns = data.get("columns", [])
                rows = data.get("rows", [])
                
                if not rows:
                    return f"<div style='color:#94a3b8;text-align:center;padding:20px;'>No rows returned.</div>", gr.update(visible=False)
                
                html = f'<div style="margin-bottom:8px;color:#10b981;font-size:0.8rem;">✅ {data["message"]}</div>'
                html += '<div style="overflow-x:auto;max-height:450px;overflow-y:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.7rem;">'
                html += '<tr style="background:rgba(0,0,0,0.3);position:sticky;top:0;">'
                for col in columns:
                    html += f'<th style="padding:5px 8px;color:#38bdf8;border-bottom:2px solid rgba(56,189,248,0.3);text-align:left;white-space:nowrap;">{col}</th>'
                html += '</tr>'
                
                for i, row in enumerate(rows[:100]):
                    bg = 'rgba(0,0,0,0.15)' if i % 2 == 0 else 'transparent'
                    html += f'<tr style="background:{bg};">'
                    for col in columns:
                        val = row.get(col, "")
                        if val is None:
                            val = '<span style="color:#64748b;">NULL</span>'
                        else:
                            val = str(val)[:100]
                        html += f'<td style="padding:3px 8px;color:#e2e8f0;border-bottom:1px solid rgba(255,255,255,0.04);white-space:nowrap;">{val}</td>'
                    html += '</tr>'
                
                html += '</table></div>'
                
                if len(rows) > 100:
                    html += f'<div style="color:#f59e0b;font-size:0.7rem;margin-top:4px;">Showing 100 of {len(rows)} rows. Use LIMIT for more.</div>'
                
                return html, gr.update(visible=False)
            else:
                return f"<div style='color:#10b981;padding:10px;'>✅ {data['message']}</div>", gr.update(visible=False)
        else:
            return f"<div style='color:#ef4444;padding:10px;'>❌ {res.json().get('detail', 'Error')}</div>", gr.update(visible=False)
    except Exception as e:
        return f"<div style='color:#ef4444;'>❌ {str(e)[:200]}</div>", gr.update(visible=False)


def execute_danger(query, token):
    """Shows confirmation checkbox for dangerous queries."""
    first = query.strip().split()[0].upper() if query.strip() else ""
    if first in ["INSERT", "UPDATE", "DELETE", "DROP"]:
        return gr.update(visible=True), gr.update()
    return execute_query(query, token, confirm=True)