"""
Incident Dependency Graph Engine
Auto-discovers service relationships from incident patterns,
builds force-directed graph, and analyzes blast radius.
"""

import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class DependencyGraphEngine:
    """
    Builds and analyzes a dependency graph from incident data.
    
    Nodes: Services/Components (nginx, database, redis, api-gateway, etc.)
    Edges: Dependencies inferred from co-occurring incidents and error patterns
    """
    
    def __init__(self):
        self.nodes = {}          # {node_id: {name, type, health_score, incident_count}}
        self.edges = []          # [{source, target, weight, evidence, direction}]
        self.incidents = []      # [{id, component, severity, timestamp, description}]
        
    def build_from_incidents(self, incidents: list[dict]) -> dict:
        """
        Build dependency graph from list of incidents.
        
        Args:
            incidents: List of incident dicts with keys:
                id, anomaly_description, root_cause, remediation_action, 
                timestamp, severity, status
        
        Returns:
            Graph data ready for visualization
        """
        self._extract_components(incidents)
        self._infer_dependencies(incidents)
        self._calculate_health_scores()
        self._identify_critical_paths()
        
        return self.export_graph()
    
    def _extract_components(self, incidents: list[dict]):
        """Extract service/component names from incident data."""
        component_patterns = {
            'nginx': ['nginx', 'web server', 'reverse proxy', '502', '504'],
            'database': ['database', 'postgres', 'mysql', 'sql', 'db connection', 'query'],
            'redis': ['redis', 'cache', 'memory cache'],
            'api-gateway': ['api gateway', 'gateway', 'kong', 'traefik'],
            'auth-service': ['auth', 'authentication', 'oauth', 'jwt', 'sso'],
            'payment-service': ['payment', 'stripe', 'billing', 'checkout'],
            'user-service': ['user service', 'profile', 'account'],
            'notification': ['notification', 'email', 'sms', 'push', 'slack'],
            'kubernetes': ['kubernetes', 'k8s', 'pod', 'container', 'docker'],
            'load-balancer': ['load balancer', 'haproxy', 'traefik'],
            'message-queue': ['queue', 'kafka', 'rabbitmq', 'pubsub'],
            'storage': ['storage', 's3', 'disk', 'volume', 'nfs'],
            'cdn': ['cdn', 'cloudfront', 'cloudflare'],
            'monitoring': ['monitor', 'prometheus', 'grafana', 'alert'],
        }
        
        component_counter = Counter()
        
        for inc in incidents:
            text = f"{inc.get('anomaly_description', '')} {inc.get('root_cause', '')} {inc.get('remediation_action', '')}".lower()
            
            for comp_name, keywords in component_patterns.items():
                if any(kw in text for kw in keywords):
                    component_counter[comp_name] += 1
                    
                    # Add incident reference
                    self.incidents.append({
                        'id': inc.get('id', '?'),
                        'component': comp_name,
                        'severity': inc.get('severity', 'MEDIUM'),
                        'timestamp': str(inc.get('timestamp', '')),
                        'description': (inc.get('anomaly_description', '') or '')[:150]
                    })
        
        # Create nodes
        for comp_name, count in component_counter.items():
            self.nodes[comp_name] = {
                'name': comp_name.replace('-', ' ').title(),
                'type': self._get_node_type(comp_name),
                'incident_count': count,
                'health_score': 100,
                'icon': self._get_node_icon(comp_name)
            }
    
    def _get_node_type(self, component: str) -> str:
        """Determine node type for coloring."""
        types = {
            'nginx': 'web-server',
            'database': 'database',
            'redis': 'cache',
            'api-gateway': 'gateway',
            'auth-service': 'security',
            'payment-service': 'business',
            'user-service': 'business',
            'notification': 'communication',
            'kubernetes': 'infrastructure',
            'load-balancer': 'infrastructure',
            'message-queue': 'messaging',
            'storage': 'storage',
            'cdn': 'network',
            'monitoring': 'observability',
        }
        return types.get(component, 'unknown')
    
    def _get_node_icon(self, component: str) -> str:
        """Get emoji icon for component."""
        icons = {
            'nginx': '🌐', 'database': '🗄️', 'redis': '⚡',
            'api-gateway': '🚪', 'auth-service': '🔐',
            'payment-service': '💳', 'user-service': '👤',
            'notification': '🔔', 'kubernetes': '☸️',
            'load-balancer': '⚖️', 'message-queue': '📨',
            'storage': '💾', 'cdn': '📡', 'monitoring': '📊'
        }
        return icons.get(component, '🔧')
    
    def _infer_dependencies(self, incidents: list[dict]):
        """
        Infer dependencies between components from incident patterns.
        
        Rules:
        1. Components mentioned in same incident → potential dependency
        2. Time-correlated incidents → likely dependency chain
        3. Error propagation patterns → direct dependency
        """
        # Group incidents by time window (5 minute windows)
        time_windows = defaultdict(list)
        
        for inc in self.incidents:
            try:
                ts = inc.get('timestamp', '')
                if ts:
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                    window_key = dt.strftime('%Y-%m-%d %H:%M')
                    time_windows[window_key].append(inc)
            except:
                pass
        
        # Find co-occurring components
        edge_weights = defaultdict(float)
        edge_evidence = defaultdict(list)
        
        for window_key, window_incidents in time_windows.items():
            components = list(set(inc['component'] for inc in window_incidents))
            
            if len(components) >= 2:
                for i in range(len(components)):
                    for j in range(i + 1, len(components)):
                        pair = tuple(sorted([components[i], components[j]]))
                        edge_weights[pair] += 1.0
                        edge_evidence[pair].append(window_key)
        
        # Also find dependencies from error messages
        error_chains = {
            'database': ['api-gateway', 'payment-service', 'user-service'],
            'redis': ['api-gateway', 'auth-service'],
            'nginx': ['api-gateway', 'load-balancer'],
            'kubernetes': ['nginx', 'database', 'redis'],
        }
        
        for comp, dependents in error_chains.items():
            if comp in self.nodes:
                for dep in dependents:
                    if dep in self.nodes:
                        pair = tuple(sorted([comp, dep]))
                        edge_weights[pair] += 0.5
        
        # Build edges
        for (source, target), weight in edge_weights.items():
            self.edges.append({
                'source': source,
                'target': target,
                'weight': min(weight, 10.0),
                'strength': 'strong' if weight > 3 else 'medium' if weight > 1 else 'weak',
                'evidence_count': len(edge_evidence.get((source, target), [])),
                'direction': 'bidirectional'
            })
    
    def _calculate_health_scores(self):
        """Calculate health score (0-100) for each component based on incident history."""
        for node_id, node in self.nodes.items():
            # Get incidents for this component
            comp_incidents = [i for i in self.incidents if i['component'] == node_id]
            
            if not comp_incidents:
                node['health_score'] = 100
                continue
            
            total = len(comp_incidents)
            
            # Count by severity
            severity_counts = Counter(i.get('severity', 'MEDIUM') for i in comp_incidents)
            
            # Start from 100 and deduct based on severity
            score = 100
            score -= severity_counts.get('CRITICAL', 0) * 15
            score -= severity_counts.get('HIGH', 0) * 8
            score -= severity_counts.get('MEDIUM', 0) * 3
            score -= severity_counts.get('LOW', 0) * 1
            
            # Small penalty for having many incidents
            if total > 50:
                score -= 10
            elif total > 20:
                score -= 5
            
            # Check for recent incidents (more recent = lower score)
            recent_count = 0
            for inc in comp_incidents:
                try:
                    ts = inc.get('timestamp', '')
                    if ts:
                        # Try to parse the timestamp
                        from datetime import datetime, timedelta
                        dt = None
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(str(ts)[:19], fmt)
                                break
                            except:
                                continue
                        if dt and dt > datetime.now() - timedelta(days=7):
                            recent_count += 1
                except:
                    pass
            
            if recent_count > 10:
                score -= 10
            elif recent_count > 5:
                score -= 5
            
            node['health_score'] = max(5, min(100, score))
    
    def _identify_critical_paths(self):
        """Identify critical dependency paths."""
        self.critical_paths = []
        
        # Find nodes with most connections (hub nodes)
        connection_counts = Counter()
        for edge in self.edges:
            connection_counts[edge['source']] += 1
            connection_counts[edge['target']] += 1
        
        for node_id, count in connection_counts.most_common(3):
            if count >= 2:
                self.critical_paths.append({
                    'node': node_id,
                    'connections': count,
                    'name': self.nodes[node_id]['name'],
                    'risk': 'High' if count >= 4 else 'Medium'
                })
    
    def get_blast_radius(self, component: str) -> dict:
        """
        Calculate blast radius if a component fails.
        Returns list of affected components and severity.
        """
        if component not in self.nodes:
            return {'component': component, 'affected': [], 'total_impact': 0}
        
        affected = set()
        visited = set()
        queue = [component]
        
        # BFS to find all connected components
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            for edge in self.edges:
                if edge['source'] == current and edge['target'] not in visited:
                    affected.add(edge['target'])
                    queue.append(edge['target'])
                elif edge['target'] == current and edge['source'] not in visited:
                    affected.add(edge['source'])
                    queue.append(edge['source'])
        
        affected.discard(component)
        
        # Calculate impact
        total_incidents = sum(
            self.nodes.get(comp, {}).get('incident_count', 0) 
            for comp in affected
        )
        
        return {
            'component': component,
            'component_name': self.nodes[component]['name'],
            'affected_components': [
                {
                    'name': self.nodes[comp]['name'],
                    'icon': self.nodes[comp]['icon'],
                    'incident_count': self.nodes[comp]['incident_count'],
                    'health_score': self.nodes[comp]['health_score']
                }
                for comp in affected
            ],
            'total_affected': len(affected),
            'total_incident_impact': total_incidents,
            'severity': 'CRITICAL' if len(affected) > 3 else 'HIGH' if len(affected) > 1 else 'MEDIUM'
        }
    
    def export_graph(self) -> dict:
        """Export graph data for visualization."""
        return {
            'nodes': [
                {
                    'id': node_id,
                    'name': node['name'],
                    'type': node['type'],
                    'icon': node['icon'],
                    'incident_count': node['incident_count'],
                    'health_score': node['health_score'],
                    'size': max(20, min(80, node['incident_count'] * 8))
                }
                for node_id, node in self.nodes.items()
            ],
            'edges': self.edges,
            'critical_paths': self.critical_paths,
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    
    def render_blast_radius_html(self, blast_data: dict) -> str:
        """Render blast radius analysis as HTML."""
        if not blast_data or not blast_data.get('affected_components'):
            return "<p style='color:#94a3b8;text-align:center;'>Click a node to see blast radius analysis</p>"
        
        severity_color = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f59e0b',
            'MEDIUM': '#3b82f6'
        }.get(blast_data.get('severity', 'MEDIUM'), '#3b82f6')
        
        html = f"""
        <div class="blast-radius-panel">
            <h3 style="color:{severity_color};margin-bottom:12px;">
                💥 Blast Radius: {blast_data['component_name']}
            </h3>
            <p style="color:#94a3b8;margin-bottom:8px;">
                If <b style="color:#f8fafc;">{blast_data['component_name']}</b> fails, 
                <b style="color:{severity_color};">{blast_data['total_affected']}</b> components 
                would be affected, impacting 
                <b style="color:{severity_color};">{blast_data['total_incident_impact']}</b> 
                historical incidents.
            </p>
            <div style="margin:12px 0;">
                <span style="font-size:0.8rem;color:#64748b;margin-right:8px;">Affected:</span>
        """
        
        for comp in blast_data['affected_components']:
            health_color = '#10b981' if comp['health_score'] > 70 else '#f59e0b' if comp['health_score'] > 40 else '#ef4444'
            html += f"""
                <span class="affected-chip">
                    {comp['icon']} {comp['name']}
                    <span style="color:{health_color};font-size:0.7rem;">({comp['health_score']}%)</span>
                </span>
            """
        
        html += """
            </div>
            <div style="margin-top:12px;padding:10px;background:rgba(0,0,0,0.2);border-radius:8px;">
                <span style="color:#94a3b8;font-size:0.8rem;">⚠️ Severity: </span>
                <span style="color:{0};font-weight:700;">{1}</span>
            </div>
        </div>
        """.format(severity_color, blast_data.get('severity', 'MEDIUM'))
        
        return html

    def render_graph_html(self, graph_data: dict, highlight_component: str = None) -> str:
        """Render the dependency graph as interactive HTML with better layout."""
        import math
        
        type_colors = {
            'web-server': '#38bdf8',
            'database': '#f59e0b',
            'cache': '#ef4444',
            'gateway': '#8b5cf6',
            'security': '#10b981',
            'business': '#ec4899',
            'communication': '#06b6d4',
            'infrastructure': '#64748b',
            'messaging': '#f97316',
            'storage': '#6366f1',
            'network': '#14b8a6',
            'observability': '#a855f7',
            'unknown': '#94a3b8'
        }
        
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        num_nodes = len(nodes)
        num_edges = len(edges)
        
        if not nodes:
            return '<div style="text-align:center;padding:40px;color:#94a3b8;">No components detected. Create more incidents to build the graph.</div>'
        
        # Dynamic SVG dimensions based on node count
        node_count = len(nodes)
        if node_count <= 4:
            width, height = 600, 400
            node_size = 45
        elif node_count <= 8:
            width, height = 800, 500
            node_size = 40
        else:
            width, height = 1000, 600
            node_size = 35
        
        center_x = width / 2
        center_y = height / 2
        radius_x = width / 2 - 80
        radius_y = height / 2 - 80
        
        # Calculate node positions - spread out circular layout
        positions = {}
        for i, node in enumerate(nodes):
            angle = (i / node_count) * 2 * math.pi - math.pi / 2
            offset_x = (hash(node['id']) % 30) - 15 if node_count > 4 else 0
            offset_y = (hash(node['id'] + 'y') % 30) - 15 if node_count > 4 else 0
            x = center_x + radius_x * math.cos(angle) + offset_x
            y = center_y + radius_y * math.sin(angle) + offset_y
            positions[node['id']] = (x, y)
        
        # Build SVG parts
        svg_parts = []
        svg_parts.append('''<svg width="100%" height="100%" viewBox="0 0 ''' + str(width) + ' ' + str(height) + '''" 
             style="background:rgba(15,23,42,0.8);border-radius:12px;min-height:400px;">
        <defs>
            <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <filter id="shadow">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.3"/>
            </filter>
        </defs>''')
        
        # Draw edges
        for edge in edges:
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            if source_id in positions and target_id in positions:
                x1, y1 = positions[source_id]
                x2, y2 = positions[target_id]
                strength = edge.get('strength', 'medium')
                edge_colors = {'strong': '#38bdf8', 'medium': '#64748b', 'weak': '#334155'}
                edge_width = {'strong': 3, 'medium': 2, 'weak': 1}
                edge_opacity = {'strong': 0.7, 'medium': 0.4, 'weak': 0.2}
                color = edge_colors.get(strength, '#64748b')
                w = edge_width.get(strength, 2)
                op = edge_opacity.get(strength, 0.4)
                svg_parts.append(
                    '<line x1="' + str(x1) + '" y1="' + str(y1) + '" x2="' + str(x2) + '" y2="' + str(y2) + '" '
                    'stroke="' + color + '" stroke-width="' + str(w) + '" opacity="' + str(op) + '" />'
                )
        
        # Draw nodes
        for node in nodes:
            node_id = node.get('id', '')
            if node_id not in positions:
                continue
            
            x, y = positions[node_id]
            size = node.get('size', node_size)
            display_size = max(node_size, min(55, size * 0.8))
            color = type_colors.get(node.get('type', 'unknown'), '#94a3b8')
            icon = node.get('icon', '🔧')
            name = node.get('name', node_id)[:20]
            health = node.get('health_score', 100)
            incidents = node.get('incident_count', 0)
            
            health_color = '#10b981' if health > 70 else '#f59e0b' if health > 40 else '#ef4444'
            is_highlighted = highlight_component and node_id == highlight_component
            
            glow = 'filter="url(#glow)"' if is_highlighted else 'filter="url(#shadow)"'
            border_width = 4 if is_highlighted else 2
            
            safe_id = node_id.replace('-', '_')
            svg_parts.append(
                '<g onclick="window._nodeClick_' + safe_id + '()" style="cursor:pointer;">'
                '<circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(display_size/2 + 4) + '" '
                'fill="rgba(0,0,0,0.3)" ' + glow + ' stroke="' + color + '" '
                'stroke-width="' + str(border_width) + '" stroke-opacity="' + ('1' if is_highlighted else '0.6') + '"/>'
                '<circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(display_size/2) + '" '
                'fill="' + color + '25" stroke="none"/>'
                '<text x="' + str(x) + '" y="' + str(y + 4) + '" text-anchor="middle" '
                'font-size="' + str(int(display_size*0.5)) + 'px" fill="white" '
                'font-family="Arial, sans-serif">' + icon + '</text>'
                '<text x="' + str(x) + '" y="' + str(y + display_size/2 + 18) + '" text-anchor="middle" '
                'font-size="11px" fill="#f8fafc" font-weight="600" '
                'font-family="Arial, sans-serif">' + name + '</text>'
                '<text x="' + str(x) + '" y="' + str(y + display_size/2 + 32) + '" text-anchor="middle" '
                'font-size="9px" fill="' + health_color + '" font-family="Arial, sans-serif">'
                + str(incidents) + ' incidents &middot; ' + str(health) + '% health</text>'
                '</g>'
            )
        
        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)
        
        # Generate click handler scripts
        click_scripts = []
        for node in nodes:
            node_id = node.get('id', '')
            safe_id = node_id.replace('-', '_')
            click_scripts.append('''
            window._nodeClick_''' + safe_id + ''' = function() {
                var compId = "''' + node_id + '''";
                // Find all text inputs
                var allInputs = document.querySelectorAll('input, textarea');
                var found = false;
                for (var i = 0; i < allInputs.length; i++) {
                    var inp = allInputs[i];
                    // Check if this input is inside our hidden container
                    var parent = inp.parentElement;
                    while (parent) {
                        if (parent.id && parent.id.indexOf('dep-click-container') >= 0) {
                            // Set value
                            var nativeSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeSetter.call(inp, compId);
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            found = true;
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    if (found) break;
                }
                // Click the hidden button after a short delay
                setTimeout(function() {
                    var btns = document.querySelectorAll('button');
                    for (var k = 0; k < btns.length; k++) {
                        if (btns[k].textContent.trim() === 'Node Clicked') {
                            btns[k].click();
                            break;
                        }
                    }
                }, 300);
            };''')
        
        html = '''
        <div style="width:100%;min-height:420px;position:relative;">
            <div style="margin-bottom:10px;display:flex;gap:10px;flex-wrap:wrap;padding:8px;
                        background:rgba(0,0,0,0.2);border-radius:8px;">
                <span style="font-size:0.75rem;color:#64748b;">🟦 Web</span>
                <span style="font-size:0.75rem;color:#64748b;">🟨 DB</span>
                <span style="font-size:0.75rem;color:#64748b;">🟥 Cache</span>
                <span style="font-size:0.75rem;color:#64748b;">🟪 Gateway</span>
                <span style="font-size:0.75rem;color:#64748b;">🟢 Security</span>
                <span style="font-size:0.75rem;color:#64748b;">🩷 Business</span>
                <span style="font-size:0.75rem;color:#64748b;">⬛ Infra</span>
                <span style="font-size:0.75rem;color:#94a3b8;">💡 Click nodes to see blast radius</span>
            </div>
            <div style="width:100%;overflow:auto;">
        ''' + svg + '''
            </div>
        </div>
        <script>
        ''' + '\n'.join(click_scripts) + '''
        console.log("Graph loaded: ''' + str(num_nodes) + ''' nodes, ''' + str(num_edges) + ''' edges");
        </script>
        '''
        
        return html



# Global instance
graph_engine = DependencyGraphEngine()