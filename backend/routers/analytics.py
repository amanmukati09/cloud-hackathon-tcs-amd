"""
Smart Analytics API
Natural language to SQL querying endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import get_db, User
from auth import get_current_user
from agents.nl_to_sql import nl_engine

router = APIRouter(prefix="/analytics", tags=["Smart Analytics"])


class QueryRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    question = req.question.strip()
    
    if not question or len(question) < 3:
        raise HTTPException(status_code=400, detail="Question too short")
    
    # Generate SQL
    sql_result = nl_engine.generate_sql(
        question, 
        user_id=None if current_user.is_admin else current_user.id
    )
    
    sql = sql_result.get("sql", "")
    explanation = sql_result.get("explanation", "")
    chart_type = sql_result.get("chart_type", "table")
    
    if sql_result.get("error"):
        error_html = nl_engine.format_results_html(
            question, sql, explanation, chart_type,
            {"error": sql_result["error"], "columns": [], "rows": [], "row_count": 0}
        )
        return {
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "result": None,
            "html": error_html,
            "has_results": False
        }
    
    if not sql:
        error_html = nl_engine.format_results_html(
            question, "", "AI could not generate a valid SQL query", "table",
            {"error": "No SQL generated", "columns": [], "rows": [], "row_count": 0}
        )
        return {
            "question": question,
            "sql": "",
            "explanation": "Failed to generate SQL",
            "result": None,
            "html": error_html,
            "has_results": False
        }
    
    # Execute and format
    try:
        result = nl_engine.execute_query(sql)
        html = nl_engine.format_results_html(question, sql, explanation, chart_type, result)
        
        return {
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "chart_type": chart_type,
            "result": {
                "columns": result.get("columns", []),
                "rows": result.get("rows", []),
                "row_count": result.get("row_count", 0)
            },
            "html": html,
            "has_results": result.get("row_count", 0) > 0 and not result.get("error")
        }
    except Exception as e:
        error_html = nl_engine.format_results_html(
            question, sql, explanation, chart_type,
            {"error": str(e), "columns": [], "rows": [], "row_count": 0}
        )
        return {
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "result": None,
            "html": error_html,
            "has_results": False
        }
        

# Saved/common queries
PRESET_QUERIES = [
    "How many total incidents do I have?",
    "Show me incidents by severity",
    "What are the most common root causes?",
    "How many incidents were resolved this month?",
    "Show me critical incidents from last week",
    "Which components fail most often?",
    "What is the average resolution time?",
    "Show me incident trend over last 30 days",
]


@router.get("/presets")
async def get_preset_queries():
    """Get list of preset/common queries."""
    return {"queries": PRESET_QUERIES}