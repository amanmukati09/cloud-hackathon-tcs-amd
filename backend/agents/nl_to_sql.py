"""
Natural Language to SQL Analytics Engine
Converts plain English questions into SQL queries,
executes them against the incident database, and returns formatted results.
Uses pre-defined SQL for common queries (100% reliable) with LLM fallback for novel questions.
"""

import requests
import json
import sqlite3
import re
from datetime import datetime, timedelta


class NLtoSQLEngine:
    """Converts natural language questions to SQL using pre-defined queries + LLM fallback."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.db_path = "aegis_core.db"

        # ── Pre-defined queries that ALWAYS work (100% reliable) ──
        self.query_cache = {
            "total incidents": {
                "sql": "SELECT COUNT(*) as total_incidents FROM incidents",
                "explanation": "Counts all incidents in the database",
                "chart_type": "number"
            },
            "by severity": {
                "sql": """
                    SELECT 
                        CASE 
                            WHEN anomaly_description LIKE '%Severity: CRITICAL%' THEN 'CRITICAL'
                            WHEN anomaly_description LIKE '%Severity: HIGH%' THEN 'HIGH'
                            WHEN anomaly_description LIKE '%Severity: MEDIUM%' THEN 'MEDIUM'
                            WHEN anomaly_description LIKE '%Severity: LOW%' THEN 'LOW'
                            ELSE 'UNKNOWN'
                        END as severity,
                        COUNT(*) as count
                    FROM incidents
                    GROUP BY severity
                    ORDER BY count DESC
                """,
                "explanation": "Groups incidents by severity level",
                "chart_type": "bar"
            },
            "root cause": {
                "sql": """SELECT root_cause, COUNT(*) as count 
                         FROM incidents 
                         WHERE root_cause IS NOT NULL AND root_cause != '' 
                         GROUP BY root_cause ORDER BY count DESC LIMIT 10""",
                "explanation": "Shows the most frequent root causes",
                "chart_type": "table"
            },
            "resolved vs open": {
                "sql": "SELECT UPPER(status) as status, COUNT(*) as count FROM incidents GROUP BY status",
                "explanation": "Counts open vs resolved incidents",
                "chart_type": "pie"
            },
            "critical": {
                "sql": """SELECT id, anomaly_description, date(timestamp) as date, status 
                         FROM incidents 
                         WHERE anomaly_description LIKE '%Severity: CRITICAL%' 
                         AND timestamp >= datetime('now', '-30 days') 
                         ORDER BY timestamp DESC LIMIT 20""",
                "explanation": "Shows critical incidents from the last 30 days",
                "chart_type": "table"
            },
            "average resolution": {
                "sql": """SELECT 
                            ROUND(AVG(CAST(julianday(resolved_at) - julianday(timestamp) AS REAL) * 24), 1) as avg_hours,
                            ROUND(AVG(CAST(julianday(resolved_at) - julianday(timestamp) AS REAL)), 1) as avg_days,
                            COUNT(*) as resolved_count
                         FROM incidents 
                         WHERE status = 'resolved' 
                         AND resolved_at IS NOT NULL 
                         AND timestamp IS NOT NULL""",
                "explanation": "Average time to resolve incidents (hours and days)",
                "chart_type": "number"
            },
            "failing components": {
                "sql": """
                    SELECT 
                        CASE 
                            WHEN anomaly_description LIKE '%nginx%' THEN 'Nginx'
                            WHEN anomaly_description LIKE '%database%' OR anomaly_description LIKE '%sql%' OR anomaly_description LIKE '%db%' THEN 'Database'
                            WHEN anomaly_description LIKE '%redis%' OR anomaly_description LIKE '%cache%' THEN 'Redis/Cache'
                            WHEN anomaly_description LIKE '%memory%' OR anomaly_description LIKE '%cpu%' OR anomaly_description LIKE '%oom%' THEN 'System Resources'
                            WHEN anomaly_description LIKE '%timeout%' OR anomaly_description LIKE '%connection%' THEN 'Network/Timeout'
                            ELSE 'Other'
                        END as component,
                        COUNT(*) as failure_count
                    FROM incidents
                    GROUP BY component
                    ORDER BY failure_count DESC
                    LIMIT 5
                """,
                "explanation": "Top 5 most frequently failing components",
                "chart_type": "bar"
            },
            "trend 7": {
                "sql": """SELECT date(timestamp) as date, COUNT(*) as incidents 
                         FROM incidents WHERE timestamp >= datetime('now', '-7 days') 
                         GROUP BY date(timestamp) ORDER BY date""",
                "explanation": "Daily incident count for the last 7 days",
                "chart_type": "line"
            },
            "trend 30": {
                "sql": """SELECT date(timestamp) as date, COUNT(*) as incidents 
                         FROM incidents WHERE timestamp >= datetime('now', '-30 days') 
                         GROUP BY date(timestamp) ORDER BY date""",
                "explanation": "Daily incident count for the last 30 days",
                "chart_type": "line"
            },
            "total resolved": {
                "sql": "SELECT COUNT(*) as resolved_count FROM incidents WHERE status = 'resolved'",
                "explanation": "Total number of resolved incidents",
                "chart_type": "number"
            },
            "total open": {
                "sql": "SELECT COUNT(*) as open_count FROM incidents WHERE status = 'open'",
                "explanation": "Total number of open incidents",
                "chart_type": "number"
            },
            "recent incidents": {
                "sql": """SELECT id, date(timestamp) as date, 
                                 CASE 
                                    WHEN anomaly_description LIKE '%Severity: CRITICAL%' THEN 'CRITICAL'
                                    WHEN anomaly_description LIKE '%Severity: HIGH%' THEN 'HIGH'
                                    WHEN anomaly_description LIKE '%Severity: MEDIUM%' THEN 'MEDIUM'
                                    ELSE 'LOW'
                                 END as severity,
                                 status
                          FROM incidents 
                          ORDER BY timestamp DESC LIMIT 20""",
                "explanation": "Most recent 20 incidents with severity",
                "chart_type": "table"
            },
        }

        # Schema info for LLM fallback
        self.schema_info = """
Tables:
- incidents (id, user_id, raw_logs, timestamp, status, anomaly_description, root_cause, remediation_action, resolved_at)
Status: 'open' or 'resolved'. Severity in anomaly_description: 'Severity: CRITICAL/HIGH/MEDIUM/LOW'."""

    def _match_cached_query(self, question: str) -> dict | None:
        """Find a matching pre-defined query by keyword matching."""
        q = question.lower().strip()

        # Multi-keyword matching with scoring
        matches = []
        if any(w in q for w in ['total', 'count', 'how many', 'number of']):
            if any(w in q for w in ['resolved', 'fixed', 'closed']):
                matches.append(('total resolved', self.query_cache['total resolved']))
            elif any(w in q for w in ['open', 'active', 'pending']):
                matches.append(('total open', self.query_cache['total open']))
            else:
                matches.append(('total incidents', self.query_cache['total incidents']))

        if any(w in q for w in ['severity', 'breakdown', 'by severity', 'distribution']):
            matches.append(('by severity', self.query_cache['by severity']))

        if any(w in q for w in ['root cause', 'common cause', 'frequent cause']):
            matches.append(('root cause', self.query_cache['root cause']))

        if any(w in q for w in ['resolved vs', 'open vs', 'status breakdown', 'status distribution']):
            matches.append(('resolved vs open', self.query_cache['resolved vs open']))

        if any(w in q for w in ['critical', 'urgent']):
            matches.append(('critical', self.query_cache['critical']))

        if any(w in q for w in ['average', 'avg', 'mean', 'resolution time', 'resolve time', 'mttr']):
            matches.append(('average resolution', self.query_cache['average resolution']))

        if any(w in q for w in ['component', 'failing', 'fail most', 'top 5', 'break most']):
            matches.append(('failing components', self.query_cache['failing components']))

        if '7 day' in q or 'last week' in q or ('trend' in q and '7' in q):
            matches.append(('trend 7', self.query_cache['trend 7']))
        elif '30 day' in q or 'last month' in q or 'monthly' in q or ('trend' in q and '30' in q):
            matches.append(('trend 30', self.query_cache['trend 30']))
        elif 'trend' in q or 'timeline' in q or 'over time' in q or 'chart' in q:
            matches.append(('trend 7', self.query_cache['trend 7']))

        if any(w in q for w in ['recent', 'latest', 'last few', 'newest']):
            matches.append(('recent incidents', self.query_cache['recent incidents']))

        if matches:
            # Return the best match (first one found)
            return matches[0][1]

        return None

    def _apply_user_filter(self, sql: str, user_id: int) -> str:
        """Add user_id filter to SQL query."""
        if not user_id:
            return sql

        # Add WHERE clause before GROUP BY, ORDER BY, LIMIT, or at end
        user_clause = f"incidents.user_id = {user_id}"

        if 'WHERE' in sql.upper():
            # Add to existing WHERE
            sql = re.sub(r'WHERE\s+', f'WHERE {user_clause} AND ', sql, count=1, flags=re.IGNORECASE)
        elif 'GROUP BY' in sql.upper():
            sql = re.sub(r'GROUP\s+BY', f'WHERE {user_clause} GROUP BY', sql, count=1, flags=re.IGNORECASE)
        elif 'ORDER BY' in sql.upper():
            sql = re.sub(r'ORDER\s+BY', f'WHERE {user_clause} ORDER BY', sql, count=1, flags=re.IGNORECASE)
        else:
            sql = sql.rstrip().rstrip(';') + f' WHERE {user_clause}'

        return sql

    def generate_sql(self, question: str, user_id: int = None) -> dict:
        """Convert natural language to SQL. Uses cache first, LLM as fallback."""

        # ── Step 1: Check pre-defined cache ──
        cached = self._match_cached_query(question)
        if cached:
            sql = self._apply_user_filter(cached["sql"], user_id)
            return {
                "sql": sql.strip(),
                "explanation": cached["explanation"],
                "chart_type": cached["chart_type"],
                "error": None,
                "cached": True
            }

        # ── Step 2: LLM fallback for novel questions ──
        scope_note = ""
        if user_id:
            scope_note = f"CRITICAL: Add WHERE incidents.user_id = {user_id} to filter results."

        prompt_text = f"""You generate SQLite SQL queries. Return ONLY valid JSON.

Schema:
{self.schema_info}

{scope_note}

Question: "{question}"

Return: {{"sql": "YOUR_SQL", "explanation": "one line", "chart_type": "table"}}

RULES:
- ONLY SQLite syntax
- NO DATEDIFF → use CAST(julianday(a)-julianday(b) AS INTEGER)
- NO CONCAT → use ||
- NO IFNULL → use COALESCE
- LIMIT 50
- Return ONLY the JSON object, nothing else."""

        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt_text,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 512}
                },
                timeout=30
            )

            if res.status_code == 200:
                response_text = res.json().get("response", "{}").strip()

                # Clean markdown wrappers
                if response_text.startswith("```"):
                    parts = response_text.split("```")
                    response_text = parts[1] if len(parts) > 1 else response_text
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()

                result = json.loads(response_text)
                sql = result.get("sql", "").strip()

                # Clean SQL
                if sql.startswith("```"):
                    sql = sql.split("```")[1]
                    if sql.startswith("sql"):
                        sql = sql[3:]
                    sql = sql.strip()

                # Safety checks
                if not sql.upper().startswith("SELECT"):
                    return {"sql": "", "explanation": "Security: Only SELECT allowed",
                            "chart_type": "table", "error": "Only SELECT queries are allowed"}

                for word in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']:
                    if re.search(r'\b' + word + r'\b', sql, re.IGNORECASE):
                        return {"sql": "", "explanation": f"Security: {word} blocked",
                                "chart_type": "table", "error": f"Dangerous keyword blocked: {word}"}

                # Apply user filter
                sql = self._apply_user_filter(sql, user_id)

                return {
                    "sql": sql.strip(),
                    "explanation": result.get("explanation", ""),
                    "chart_type": result.get("chart_type", "table"),
                    "error": None,
                    "cached": False
                }

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
        except Exception as e:
            print(f"LLM fallback error: {e}")

        return {
            "sql": "",
            "explanation": "Could not generate SQL for this question",
            "chart_type": "table",
            "error": "Try rephrasing your question or using a preset query",
            "cached": False
        }

    def _fix_sqlite_sql(self, sql: str) -> str:
        """Fix common non-SQLite SQL syntax."""
        # DATEDIFF(day, a, b) → julian day difference
        sql = re.sub(
            r"DATEDIFF\s*\(\s*['\"]?day['\"]?\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            r"CAST(julianday(\2) - julianday(\1) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"DATEDIFF\s*\(\s*['\"]?hour['\"]?\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            r"CAST((julianday(\2) - julianday(\1)) * 24 AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"DATEDIFF\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            r"CAST(julianday(\2) - julianday(\1) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        # NOW() / CURDATE()
        sql = re.sub(r'\bNOW\s*\(\s*\)', "datetime('now')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bCURDATE\s*\(\s*\)', "date('now')", sql, flags=re.IGNORECASE)
        # CONCAT(a,b) → a || b
        sql = re.sub(
            r'CONCAT\s*\(([^)]+)\)',
            lambda m: ' || '.join([x.strip() for x in m.group(1).split(',')]),
            sql, flags=re.IGNORECASE
        )
        # IFNULL → COALESCE
        sql = re.sub(r'\bIFNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
        # DATEADD(day, N, col) → datetime(col, '+N days')
        sql = re.sub(
            r"DATEADD\s*\(\s*(\w+)\s*,\s*(-?\d+)\s*,\s*([^)]+)\s*\)",
            r"datetime(\3, '\2 \1')",
            sql, flags=re.IGNORECASE
        )
        return sql

    def execute_query(self, sql: str) -> dict:
        """Execute SQL query with auto-fix for SQLite compatibility."""
        if not sql:
            return {"columns": [], "rows": [], "row_count": 0, "error": "No SQL provided"}

        sql = self._fix_sqlite_sql(sql)

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()

            if rows:
                columns = [desc[0] for desc in cursor.description]
                result_rows = [dict(row) for row in rows]
            else:
                columns = []
                result_rows = []

            conn.close()
            return {"columns": columns, "rows": result_rows, "row_count": len(result_rows), "error": None}

        except Exception as e:
            print(f"SQL Error: {e}\nSQL: {sql}")
            return {"columns": [], "rows": [], "row_count": 0, "error": f"SQL Error: {str(e)}"}

    def format_results_html(self, question: str, sql: str, explanation: str,
                            chart_type: str, result: dict) -> str:
        """Format query results as beautiful HTML."""
        if result.get("error"):
            return f"""
            <div style="padding:16px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;">
                <p style="color:#ef4444;font-weight:600;">❌ Query Error</p>
                <p style="color:#fca5a5;font-size:0.85rem;">{result['error']}</p>
                <details><summary style="color:#94a3b8;cursor:pointer;">🔍 SQL</summary>
                <pre style="background:#0d1117;color:#e6edf3;padding:10px;border-radius:6px;font-size:0.7rem;overflow-x:auto;">{sql}</pre></details>
            </div>"""

        rows = result.get("rows", [])
        columns = result.get("columns", [])
        row_count = result.get("row_count", 0)

        if not rows:
            return f"""
            <div style="padding:20px;text-align:center;background:rgba(30,41,59,0.8);border-radius:8px;">
                <p style="color:#94a3b8;">📭 No results for: <b>"{question}"</b></p>
                <details><summary style="color:#64748b;cursor:pointer;font-size:0.75rem;">🔍 SQL</summary>
                <pre style="background:#0d1117;color:#58a6ff;padding:10px;border-radius:6px;font-size:0.7rem;">{sql}</pre></details>
            </div>"""

        display_rows = rows[:20]
        total_rows = row_count

        html = f"""
        <div style="background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;">
            <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="color:#f8fafc;font-weight:600;">📊 Results</span>
                    <span style="color:#64748b;font-size:0.8rem;margin-left:8px;">({total_rows} rows)</span>
                </div>
                <span style="color:#10b981;font-size:0.75rem;">✅ Success</span>
            </div>
            <p style="color:#94a3b8;font-size:0.85rem;margin-bottom:12px;">{explanation}</p>
            <div style="overflow-x:auto;max-height:400px;overflow-y:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
            <tr style="background:rgba(0,0,0,0.3);position:sticky;top:0;">"""

        for col in columns:
            html += f'<th style="padding:8px 12px;text-align:left;color:#38bdf8;font-size:0.75rem;font-weight:700;border-bottom:2px solid rgba(56,189,248,0.3);white-space:nowrap;">{col.upper()}</th>'
        html += '</tr>'

        for i, row in enumerate(display_rows):
            bg = 'rgba(0,0,0,0.15)' if i % 2 == 0 else 'transparent'
            html += f'<tr style="background:{bg};">'
            for col in columns:
                val = row.get(col, '')
                if val is None:
                    display_val = '<span style="color:#64748b;">-</span>'
                elif isinstance(val, float):
                    display_val = f"{val:.1f}"
                elif isinstance(val, str) and 'CRITICAL' in val.upper():
                    display_val = f'<span style="color:#ef4444;font-weight:600;">{val[:60]}</span>'
                elif isinstance(val, str) and 'HIGH' in val.upper():
                    display_val = f'<span style="color:#f59e0b;font-weight:600;">{val[:60]}</span>'
                else:
                    display_val = str(val)[:60]
                html += f'<td style="padding:6px 12px;color:#e2e8f0;border-bottom:1px solid rgba(255,255,255,0.04);white-space:nowrap;">{display_val}</td>'
            html += '</tr>'

        html += '</table></div>'

        if total_rows > 20:
            html += f"""<div style="margin-top:8px;padding:8px;background:rgba(245,158,11,0.1);border-radius:6px;text-align:center;">
                <span style="color:#f59e0b;font-size:0.8rem;">📋 Showing 20 of {total_rows} results. Narrow your query for more specific results.</span></div>"""

        html += f"""<details style="margin-top:12px;"><summary style="color:#64748b;cursor:pointer;font-size:0.75rem;">🔍 Generated SQL</summary>
            <pre style="background:#0d1117;color:#58a6ff;padding:10px;border-radius:6px;font-size:0.7rem;overflow-x:auto;line-height:1.4;">{sql}</pre></details></div>"""

        return html


# Global instance
nl_engine = NLtoSQLEngine()