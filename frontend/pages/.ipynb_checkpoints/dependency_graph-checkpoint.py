"""
Incident Dependency Graph Page
Interactive force-directed graph showing service dependencies,
blast radius analysis, and critical paths.
"""

import gradio as gr
import requests
import json
from utils import BACKEND_URL


def build_dependency_tab(session_token):
    """Build the dependency graph tab UI."""
    comp = {}
    
    with gr.Column():
        gr.Markdown("### 🗺️ Incident Dependency Graph")
        gr.Markdown("Visualize how services depend on each other. Click nodes to see blast radius.")
        
        # Status bar
        with gr.Row():
            comp["graph_status"] = gr.Markdown("📊 Click **Refresh Graph** to build the dependency map")
            comp["refresh_btn"] = gr.Button("🔄 Refresh Graph", variant="primary", size="sm")
        
        gr.Markdown("---")
        
        # Main graph + blast radius panel
        with gr.Row(equal_height=True):
            # Left: Graph visualization
            with gr.Column(scale=3, min_width=500):
                comp["graph_output"] = gr.HTML(
                    value='<div class="graph-placeholder">Click Refresh Graph to visualize dependencies</div>',
                    elem_classes="graph-container-wrap"
                )
            
            # Right: Blast radius + info
            with gr.Column(scale=1, min_width=280):
                with gr.Column(elem_classes="glass-card premium-card"):
                    gr.Markdown("#### 💥 Blast Radius Analysis")
                    comp["blast_output"] = gr.HTML(
                        value="<p style='color:#94a3b8;text-align:center;padding:20px;'>Click a node in the graph to see blast radius</p>"
                    )
                
                with gr.Column(elem_classes="glass-card premium-card"):
                    gr.Markdown("#### ⚠️ Critical Paths")
                    comp["critical_output"] = gr.HTML(
                        value="<p style='color:#94a3b8;text-align:center;'>Loading critical paths...</p>"
                    )
        
        # Node click handler (hidden)
        comp["selected_node"] = gr.Textbox(visible=False)
        comp["node_click_btn"] = gr.Button("Node Clicked", visible=False)
        
        # Legend
        with gr.Row():
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("""
                <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:0.8rem;color:#94a3b8;">
                    <span>🟦 Web Server</span>
                    <span>🟨 Database</span>
                    <span>🟥 Cache</span>
                    <span>🟪 Gateway</span>
                    <span>🟢 Security</span>
                    <span>🩷 Business</span>
                    <span>⬛ Infrastructure</span>
                </div>
                """)
    
    return comp


def fetch_dependency_graph(token):
    """Fetch dependency graph data from backend."""
    if not token:
        return (
            '<div class="graph-placeholder">Please login first</div>',
            '<p style="color:#94a3b8;text-align:center;">Login to view graph</p>',
            '<p style="color:#94a3b8;text-align:center;">Login to view</p>',
            "📊 Please login to build the graph"
        )
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/dependency/graph",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if res.status_code == 200:
            data = res.json()
            
            if not data.get("has_data"):
                return (
                    '<div class="graph-placeholder">No incidents found to build dependency graph. Create some incidents first.</div>',
                    '<p style="color:#94a3b8;text-align:center;">No data available</p>',
                    '<p style="color:#94a3b8;text-align:center;">No data</p>',
                    f"📊 {data.get('message', 'No data')}"
                )
            
            graph_html = data.get("graph_html", "")
            graph_data = data.get("graph", {})
            
            # Fetch critical paths
            crit_res = requests.get(
                f"{BACKEND_URL}/dependency/critical-paths",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            
            critical_html = "<p style='color:#94a3b8;'>No critical paths found</p>"
            if crit_res.status_code == 200:
                crit_data = crit_res.json()
                paths = crit_data.get("critical_paths", [])
                if paths:
                    critical_html = "<div style='max-height:200px;overflow-y:auto;'>"
                    for path in paths:
                        risk_color = "#ef4444" if path.get("risk") == "High" else "#f59e0b"
                        critical_html += f"""
                        <div style="padding:8px;margin:4px 0;background:rgba(0,0,0,0.2);border-radius:6px;border-left:3px solid {risk_color};">
                            <span style="font-size:1.2rem;">{graph_engine.nodes.get(path['node'], {}).get('icon', '🔧') if 'graph_engine' in dir() else '🔧'}</span>
                            <b style="color:#f8fafc;">{path.get('name', path['node'])}</b>
                            <br><small style="color:#64748b;">{path.get('connections', 0)} connections · Risk: <span style="color:{risk_color};">{path.get('risk', 'Medium')}</span></small>
                        </div>
                        """
                    critical_html += "</div>"
            
            status_msg = f"📊 {data.get('message', 'Graph built')} · {graph_data.get('total_nodes', 0)} nodes · {graph_data.get('total_edges', 0)} edges"
            
            return (
                graph_html,
                '<p style="color:#94a3b8;text-align:center;padding:20px;">Click a node in the graph to see blast radius</p>',
                critical_html,
                status_msg
            )
        else:
            return (
                f'<div class="graph-placeholder">Error: {res.status_code}</div>',
                '<p style="color:#ef4444;">Failed to load</p>',
                '<p style="color:#ef4444;">Failed to load</p>',
                "❌ Failed to build graph"
            )
    except Exception as e:
        return (
            f'<div class="graph-placeholder">Connection error: {str(e)[:100]}</div>',
            '<p style="color:#ef4444;">Error</p>',
            '<p style="color:#ef4444;">Error</p>',
            f"❌ Error: {str(e)[:50]}"
        )


def handle_node_click(node_id, token):
    """Handle when a node is clicked in the graph."""
    if not node_id or not token:
        return '<p style="color:#94a3b8;text-align:center;">Click a node to see blast radius</p>'
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/dependency/blast-radius/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if res.status_code == 200:
            data = res.json()
            return data.get("blast_html", "<p>No blast radius data</p>")
    except:
        pass
    
    return '<p style="color:#ef4444;">Failed to load blast radius</p>'