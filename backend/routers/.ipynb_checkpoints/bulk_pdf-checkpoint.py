"""
Bulk Log Processing & PDF Generation API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import get_db, User, Incident
from auth import get_current_user
from gpu_utils import gpu_detector
from agents.pdf_generator import IncidentPDFGenerator

router = APIRouter(prefix="/bulk", tags=["Bulk Processing"])


@router.get("/gpu-status")
async def get_gpu_status(current_user: User = Depends(get_current_user)):
    """Get GPU/CPU status."""
    return gpu_detector.get_config()


@router.post("/analyze-logs")
async def analyze_log_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a log file and get AI analysis."""
    
    # Validate
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['.log', '.txt', '.out']:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {ext}")
    
    # Read file
    try:
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 50:
            raise HTTPException(status_code=400, detail="Max 50MB")
        
        # Decode
        text = None
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = content.decode(enc)
                break
            except:
                continue
        if text is None:
            text = content.decode('utf-8', errors='ignore')
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Parse lines
    log_lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not log_lines:
        raise HTTPException(status_code=400, detail="File is empty")
    
    total_lines = len(log_lines)
    if total_lines > 50000:
        log_lines = log_lines[:50000]
    
    gpu_config = gpu_detector.get_config()
    
    # Step 1: Pre-scan for errors
    error_lines = _prescan_logs(log_lines)
    
    # Step 2: Chunk and analyze with AI
    chunk_size = 50 if gpu_config["gpu_available"] else 20
    chunks = [log_lines[i:i+chunk_size] for i in range(0, len(log_lines), chunk_size)]
    chunks = chunks[:50]
    
    all_anomalies = []
    all_incidents = []
    
    max_workers = 4 if gpu_config["gpu_available"] else 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_analyze_chunk, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=120)
                
                # ─── FIX: Handle anomalies safely ───
                anomalies = result.get("anomalies", [])
                if isinstance(anomalies, list):
                    for a in anomalies:
                        if isinstance(a, dict):
                            all_anomalies.append(a)
                        elif isinstance(a, str):
                            # If Ollama returned a string instead of dict
                            all_anomalies.append({
                                "type": "Unknown",
                                "severity": "MEDIUM",
                                "description": str(a)[:200],
                                "affected_component": "Unknown"
                            })
                
                # ─── FIX: Handle incidents safely ───
                incidents = result.get("incidents", [])
                if isinstance(incidents, list):
                    for inc in incidents:
                        if isinstance(inc, dict):
                            all_incidents.append(inc)
                        elif isinstance(inc, str):
                            all_incidents.append({
                                "title": "Unknown Incident",
                                "severity": "MEDIUM",
                                "description": str(inc)[:200],
                                "recommended_action": "Review manually"
                            })
                            
            except Exception as e:
                print(f"Chunk error: {e}")
    
    # Deduplicate safely
    seen_types = set()
    unique_anomalies = []
    for a in all_anomalies:
        try:
            a_type = str(a.get("type", "")) if isinstance(a, dict) else ""
            a_desc = str(a.get("description", "")) if isinstance(a, dict) else str(a)
            key = a_type + a_desc[:50]
            if key not in seen_types:
                seen_types.add(key)
                unique_anomalies.append(a if isinstance(a, dict) else {"description": str(a), "severity": "MEDIUM"})
        except Exception as e:
            print(f"Dedup error: {e}")
    
    # Severity breakdown
    severity_bd = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in unique_anomalies:
        try:
            sev = str(a.get("severity", "MEDIUM")).upper() if isinstance(a, dict) else "MEDIUM"
            if sev in severity_bd:
                severity_bd[sev] += 1
        except:
            severity_bd["MEDIUM"] += 1
    
    # Risk level
    if severity_bd["CRITICAL"] > 3:
        risk = "CRITICAL"
    elif severity_bd["CRITICAL"] > 0 or severity_bd["HIGH"] > 5:
        risk = "HIGH"
    elif severity_bd["HIGH"] > 0:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    
    # Build summary
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
    
    # Store sample incidents in DB
    for inc in all_incidents[:3]:
        try:
            if isinstance(inc, dict):
                new_inc = Incident(
                    user_id=current_user.id,
                    raw_logs=f"Bulk: {file.filename} ({total_lines} lines)",
                    status="open",
                    anomaly_description=f"{inc.get('title', 'Unknown')} | Severity: {inc.get('severity', 'MEDIUM')}",
                    root_cause=inc.get('description', 'See report'),
                    remediation_action=inc.get('recommended_action', 'Review'),
                    remediation_status="pending"
                )
                db.add(new_inc)
        except Exception as e:
            print(f"DB store error: {e}")
    db.commit()
    
    return {
        "status": "success",
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "total_lines": total_lines,
        "gpu_used": gpu_config["gpu_available"],
        "gpu_type": gpu_config["gpu_type"],
        "analysis": {
            "summary": summary,
            "anomalies": unique_anomalies[:20],
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


@router.post("/generate-pdf")
async def generate_pdf_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate PDF report from log file."""
    
    # Run analysis first
    analysis_result = await analyze_log_file(file, current_user, db)
    analysis_data = analysis_result.get("analysis", {})
    
    if not analysis_data:
        raise HTTPException(status_code=500, detail="Analysis produced no results")
    
    # Generate PDF
    try:
        pdf_gen = IncidentPDFGenerator()
        pdf_bytes = pdf_gen.generate_report(analysis_data, file.filename)
        
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        
        filename = f"AegisAI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ── Helper Functions ──────────────────────────────────

def _prescan_logs(log_lines):
    """Fast keyword scan for errors."""
    keywords = ['error', 'critical', 'fatal', 'fail', 'crash', 'exception',
                'timeout', 'denied', 'killed', 'oom', 'panic']
    errors = []
    for i, line in enumerate(log_lines):
        ll = line.lower()
        for kw in keywords:
            if kw in ll:
                errors.append({"line": i+1, "keyword": kw, "text": line[:150]})
                break
    return errors


def _analyze_chunk(chunk):
    """Send chunk to Ollama for AI analysis."""
    import requests as req
    
    log_text = "\n".join(chunk[:30])
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
        res = req.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3, "num_predict": 1024}
            },
            timeout=120
        )
        if res.status_code == 200:
            response_text = res.json().get("response", "{}")
            # Clean response - remove markdown code blocks if any
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Ensure expected structure
            if "anomalies" not in result:
                result["anomalies"] = []
            if "incidents" not in result:
                result["incidents"] = []
            
            return result
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response_text[:200] if 'response_text' in dir() else 'N/A'}")
    except Exception as e:
        print(f"Ollama error: {e}")
    
    return {"anomalies": [], "incidents": []}


def _top_components(anomalies):
    """Count top affected components."""
    from collections import Counter
    comps = Counter()
    for a in anomalies:
        try:
            comp = str(a.get("affected_component", "Unknown")) if isinstance(a, dict) else "Unknown"
            comps[comp] += 1
        except:
            comps["Unknown"] += 1
    return [{"component": c, "count": n} for c, n in comps.most_common(5)]


def _generate_next_steps(risk, anomalies):
    """Generate next steps based on risk level."""
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