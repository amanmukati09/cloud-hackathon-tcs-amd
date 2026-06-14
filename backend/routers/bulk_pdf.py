"""
Bulk Log Processing & PDF Generation API
Endpoints for uploading log files, analyzing them with AI (or fallback),
and generating comprehensive PDF reports.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from models import get_db, User, Incident
from auth import get_current_user
from gpu_utils import gpu_detector
from agents.pdf_generator import IncidentPDFGenerator

router = APIRouter(prefix="/bulk", tags=["Bulk Processing"])


# ═══════════════════════════════════════════════════════
# GPU Status Endpoint
# ═══════════════════════════════════════════════════════

@router.get("/gpu-status")
async def get_gpu_status(current_user: User = Depends(get_current_user)):
    """Get current GPU/CPU status and capabilities."""
    return gpu_detector.get_config()


# ═══════════════════════════════════════════════════════
# Analyze Logs Endpoint
# ═══════════════════════════════════════════════════════

@router.post("/analyze-logs")
async def analyze_log_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a log file and get comprehensive AI-powered analysis.
    
    - Accepts .log, .txt, .out files up to 50 MB
    - Pre-scans for errors, chunks large files, analyzes with Ollama (or fallback)
    - Returns anomalies, incidents, severity breakdown, and recommendations
    """
    # ── Validate file ──
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['.log', '.txt', '.out']:
        raise HTTPException(status_code=400, detail=f"Invalid file type '{ext}'. Allowed: .log, .txt, .out")

    # ── Read file ──
    try:
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 50:
            raise HTTPException(status_code=400, detail="File too large. Maximum 50 MB.")

        # Decode with fallback
        text = None
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = content.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if text is None:
            text = content.decode('utf-8', errors='ignore')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # ── Parse lines ──
    log_lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not log_lines:
        raise HTTPException(status_code=400, detail="File is empty or contains no readable log lines")

    total_lines = len(log_lines)
    if total_lines > 50000:
        log_lines = log_lines[:50000]  # Cap at 50k lines for performance

    gpu_config = gpu_detector.get_config()

    # ═══════════════════════════════════════════════════
    # Step 1: Pre-scan for errors (fast keyword match)
    # ═══════════════════════════════════════════════════
    error_lines = _prescan_logs(log_lines)

    # ═══════════════════════════════════════════════════
    # Step 2: Chunk and analyze (AI or fallback)
    # ═══════════════════════════════════════════════════
    chunk_size = 50 if gpu_config["gpu_available"] else 20
    chunks = [log_lines[i:i+chunk_size] for i in range(0, len(log_lines), chunk_size)]
    chunks = chunks[:50]  # Max 50 chunks to prevent overload

    all_anomalies = []
    all_incidents = []

    max_workers = 4 if gpu_config["gpu_available"] else 1

    print(f"🔍 Processing {len(chunks)} chunks with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_analyze_chunk, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=120)
                
                # ── Safely collect anomalies ──
                anomalies = result.get("anomalies", [])
                if isinstance(anomalies, list):
                    for a in anomalies:
                        if isinstance(a, dict):
                            all_anomalies.append(a)
                        elif isinstance(a, str):
                            all_anomalies.append({
                                "type": "Unknown",
                                "severity": "MEDIUM",
                                "description": a[:200],
                                "affected_component": "Unknown"
                            })
                
                # ── Safely collect incidents ──
                incidents = result.get("incidents", [])
                if isinstance(incidents, list):
                    for inc in incidents:
                        if isinstance(inc, dict):
                            all_incidents.append(inc)
                        elif isinstance(inc, str):
                            all_incidents.append({
                                "title": "Unknown Incident",
                                "severity": "MEDIUM",
                                "description": inc[:200],
                                "recommended_action": "Review manually"
                            })
            except Exception as e:
                print(f"⚠️ Chunk processing error: {e}")

    # ═══════════════════════════════════════════════════
    # Step 3: Deduplicate and organize
    # ═══════════════════════════════════════════════════
    seen = set()
    unique_anomalies = []
    for a in all_anomalies:
        try:
            if isinstance(a, dict):
                key = str(a.get("type", "")) + str(a.get("description", ""))[:50]
            else:
                key = str(a)[:50]
            if key not in seen:
                seen.add(key)
                if isinstance(a, dict):
                    unique_anomalies.append(a)
                else:
                    unique_anomalies.append({"description": str(a), "severity": "MEDIUM"})
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # Step 4: Severity breakdown & risk assessment
    # ═══════════════════════════════════════════════════
    severity_bd = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in unique_anomalies:
        try:
            sev = str(a.get("severity", "MEDIUM")).upper() if isinstance(a, dict) else "MEDIUM"
            if sev in severity_bd:
                severity_bd[sev] += 1
        except:
            severity_bd["MEDIUM"] += 1

    # Determine risk level
    if severity_bd["CRITICAL"] > 3:
        risk = "CRITICAL"
    elif severity_bd["CRITICAL"] > 0 or severity_bd["HIGH"] > 5:
        risk = "HIGH"
    elif severity_bd["HIGH"] > 0 or severity_bd["MEDIUM"] > 10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    # ═══════════════════════════════════════════════════
    # Step 5: Build summary
    # ═══════════════════════════════════════════════════
    summary = {
        "risk_level": risk,
        "critical_anomalies": severity_bd["CRITICAL"],
        "high_anomalies": severity_bd["HIGH"],
        "total_anomalies": len(unique_anomalies),
        "total_incidents": len(all_incidents),
        "recommendation": (
            "Immediate attention required" if risk in ["CRITICAL", "HIGH"]
            else "Schedule review within 24h" if risk == "MEDIUM"
            else "Monitor and document"
        ),
        "next_steps": _generate_next_steps(risk, unique_anomalies)
    }

    # ═══════════════════════════════════════════════════
    # Step 6: Save sample incidents to DB
    # ═══════════════════════════════════════════════════
    for inc in all_incidents[:3]:
        try:
            if isinstance(inc, dict):
                new_incident = Incident(
                    user_id=current_user.id,
                    raw_logs=f"Bulk analysis from: {file.filename} ({total_lines} lines)",
                    status="open",
                    anomaly_description=f"{inc.get('title', 'Unknown')} | Severity: {inc.get('severity', 'MEDIUM')}",
                    root_cause=inc.get('description', 'See report'),
                    remediation_action=inc.get('recommended_action', 'Review'),
                    remediation_status="pending"
                )
                db.add(new_incident)
        except Exception as e:
            print(f"DB storage error: {e}")
    db.commit()

    # ═══════════════════════════════════════════════════
    # Return analysis
    # ═══════════════════════════════════════════════════
    return {
        "status": "success",
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "total_lines": total_lines,
        "gpu_used": gpu_config["gpu_available"],
        "gpu_type": gpu_config["gpu_type"],
        "analysis": {
            "summary": summary,
            "anomalies": unique_anomalies[:20],   # Limit for response size
            "incidents": all_incidents[:10],
            "statistics": {
                "error_count": len(error_lines),
                "error_rate": round(len(error_lines) / max(total_lines, 1) * 100, 1),
                "severity_breakdown": severity_bd,
                "top_components": _top_components(unique_anomalies)
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gpu_used": gpu_config["gpu_available"]
        }
    }


# ═══════════════════════════════════════════════════════
# Generate PDF Endpoint
# ═══════════════════════════════════════════════════════

@router.post("/generate-pdf")
async def generate_pdf_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a log file and receive a professional PDF report.
    
    Includes:
    - Executive summary with risk level
    - Severity breakdown with charts
    - Detailed anomaly listing
    - Incident reports
    - Remediation plan
    - Statistics & metrics
    """
    # Reuse the analysis endpoint
    analysis_result = await analyze_log_file(file, current_user, db)
    analysis_data = analysis_result.get("analysis", {})

    if not analysis_data:
        raise HTTPException(status_code=500, detail="Analysis produced no results")

    try:
        pdf_generator = IncidentPDFGenerator()
        pdf_bytes = pdf_generator.generate_report(
            analysis_data,
            original_filename=file.filename,
            include_charts=True
        )

        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        filename = f"AegisAI_Incident_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-GPU-Used": str(analysis_data.get("gpu_used", False)),
                "X-Total-Lines": str(analysis_data.get("total_lines", 0)),
                "X-Anomalies-Found": str(len(analysis_data.get("anomalies", [])))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ═══════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════

def _prescan_logs(log_lines):
    """Fast keyword pre-scan for error/warning lines."""
    keywords = ['error', 'critical', 'fatal', 'fail', 'crash', 'exception',
                'timeout', 'denied', 'killed', 'oom', 'panic', 'refused']
    errors = []
    for i, line in enumerate(log_lines):
        line_lower = line.lower()
        for kw in keywords:
            if kw in line_lower:
                errors.append({"line": i + 1, "keyword": kw, "text": line[:150]})
                break
    return errors


def _analyze_chunk(chunk):
    """
    Analyze a chunk of logs using Ollama (with fallback).
    Returns a dict with 'anomalies' and 'incidents'.
    """
    import requests as req

    log_text = "\n".join(chunk[:30])
    error_count = sum(1 for line in chunk if any(
        kw in line.lower() for kw in ['error', 'critical', 'fatal', 'fail', 'crash', 'exception']
    ))

    prompt = (
        "Analyze these server logs for anomalies and incidents. "
        "Return ONLY valid JSON (no markdown, no extra text):\n"
        '{"anomalies":[{"severity":"LOW/MEDIUM/HIGH/CRITICAL","type":"e.g. Memory Leak",'
        '"description":"brief description","affected_component":"e.g. nginx"}],'
        '"incidents":[{"title":"brief title","severity":"LOW/MEDIUM/HIGH/CRITICAL",'
        '"description":"what happened","recommended_action":"immediate fix"}]}\n\n'
        f"Logs:\n{log_text}"
    )

    try:
        print(f"🔄 Sending chunk to Ollama ({len(chunk)} lines, {error_count} errors)...")
        res = req.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3, "num_predict": 1024}
            },
            timeout=30
        )
        if res.status_code == 200:
            response_text = res.json().get("response", "{}").strip()
            # Strip markdown code fences if present
            if response_text.startswith("```"):
                parts = response_text.split("```")
                if len(parts) > 1:
                    response_text = parts[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)
            print(f"✅ Ollama returned {len(result.get('anomalies', []))} anomalies, {len(result.get('incidents', []))} incidents")
            result.setdefault("anomalies", [])
            result.setdefault("incidents", [])
            return result
        else:
            print(f"❌ Ollama status {res.status_code}")
    except req.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama (localhost:11434)")
    except req.exceptions.Timeout:
        print("❌ Ollama request timed out")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Ollama error: {e}")

    # Fallback to rule-based analysis
    print("⚠️ Using rule-based fallback analysis")
    return _fallback_analyze_chunk(chunk)


def _fallback_analyze_chunk(chunk):
    """
    Rule-based analysis when Ollama is unavailable.
    Detects error patterns and creates anomalies/incidents from keywords.
    """
    anomalies = []
    incidents = []

    error_patterns = {
        'critical': ('CRITICAL', 'Critical Error Detected'),
        'fatal': ('CRITICAL', 'Fatal Error'),
        'panic': ('CRITICAL', 'Kernel Panic'),
        'oom': ('HIGH', 'Out of Memory'),
        'out of memory': ('HIGH', 'Memory Exhaustion'),
        'killed': ('HIGH', 'Process Killed'),
        'crash': ('HIGH', 'Application Crash'),
        'crashed': ('HIGH', 'Application Crash'),
        'timeout': ('MEDIUM', 'Connection Timeout'),
        'timed out': ('MEDIUM', 'Connection Timeout'),
        'refused': ('MEDIUM', 'Connection Refused'),
        'denied': ('MEDIUM', 'Access Denied'),
        'failed': ('MEDIUM', 'Operation Failed'),
        'fail': ('MEDIUM', 'Operation Failed'),
        'error': ('MEDIUM', 'Error Detected'),
        'exception': ('MEDIUM', 'Exception Occurred'),
        'warning': ('LOW', 'Warning'),
        'warn': ('LOW', 'Warning'),
    }

    found_keywords = set()

    for i, line in enumerate(chunk):
        line_lower = line.lower()
        for keyword, (severity, error_type) in error_patterns.items():
            if keyword in line_lower and keyword not in found_keywords:
                found_keywords.add(keyword)
                # Determine component
                component = "System"
                if 'nginx' in line_lower:
                    component = "Nginx"
                elif 'mysql' in line_lower or 'postgres' in line_lower or 'database' in line_lower:
                    component = "Database"
                elif 'redis' in line_lower:
                    component = "Redis"
                elif 'docker' in line_lower:
                    component = "Docker"
                elif 'memory' in line_lower or 'mem' in line_lower:
                    component = "Memory"
                elif 'cpu' in line_lower:
                    component = "CPU"
                elif 'disk' in line_lower:
                    component = "Disk"
                elif 'network' in line_lower:
                    component = "Network"

                anomalies.append({
                    "severity": severity,
                    "type": error_type,
                    "description": line.strip()[:200],
                    "affected_component": component,
                    "line_number": i + 1
                })
                break

    # Create incidents for clusters of high/critical anomalies
    critical_count = sum(1 for a in anomalies if a['severity'] in ['CRITICAL', 'HIGH'])
    if critical_count >= 3:
        incidents.append({
            "title": f"Multiple Critical Errors ({critical_count} occurrences)",
            "severity": "CRITICAL" if any(a['severity'] == 'CRITICAL' for a in anomalies) else "HIGH",
            "description": f"Found {critical_count} high/critical errors in log chunk. Types: {', '.join(set(a['type'] for a in anomalies if a['severity'] in ['CRITICAL','HIGH']))}",
            "recommended_action": "Investigate all critical errors immediately. Check system resources and application logs."
        })
    elif len(anomalies) >= 5:
        incidents.append({
            "title": f"Multiple Issues Detected ({len(anomalies)} anomalies)",
            "severity": "MEDIUM",
            "description": f"Multiple error patterns found across components.",
            "recommended_action": "Review anomalies and prioritize by severity."
        })

    print(f"   Fallback found: {len(anomalies)} anomalies, {len(incidents)} incidents")
    return {"anomalies": anomalies, "incidents": incidents}


def _top_components(anomalies):
    """Count top affected components from anomalies."""
    comps = Counter()
    for a in anomalies:
        try:
            comp = str(a.get("affected_component", "Unknown")) if isinstance(a, dict) else "Unknown"
            comps[comp] += 1
        except:
            comps["Unknown"] += 1
    return [{"component": c, "count": n} for c, n in comps.most_common(5)]


def _generate_next_steps(risk, anomalies):
    """Generate actionable next steps based on risk level."""
    steps = {
        "CRITICAL": [
            "🚨 Escalate to on-call team immediately",
            "🔍 Investigate critical anomalies within 15 minutes",
            "📞 Notify stakeholders about service impact",
            "📝 Start incident post-mortem document"
        ],
        "HIGH": [
            "⚠️ Schedule investigation within 1 hour",
            "📊 Monitor affected components closely",
            "📝 Document findings for review",
            "🔧 Prepare remediation scripts"
        ],
        "MEDIUM": [
            "📋 Schedule review during next maintenance window",
            "📊 Update monitoring dashboards",
            "📝 Add findings to knowledge base",
            "🔍 Review similar past incidents"
        ],
        "LOW": [
            "✅ No immediate action required",
            "📊 Continue routine monitoring",
            "📝 Document for periodic review"
        ]
    }
    return steps.get(risk, steps["LOW"])