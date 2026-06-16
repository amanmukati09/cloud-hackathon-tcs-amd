"""
SQL Runner API - Admin only SQL execution with extended capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from models import get_db, User
from auth import get_current_user

router = APIRouter(prefix="/admin/sql", tags=["SQL Runner"])


class SQLRequest(BaseModel):
    query: str
    confirm: bool = False  # Required for non-SELECT queries


ALLOWED_COMMANDS = ["SELECT", "PRAGMA", "EXPLAIN", "WITH", "INSERT", "UPDATE", "DELETE", 
                    "CREATE", "ALTER", "DROP", "VACUUM", "REINDEX"]


@router.post("/execute")
async def execute_sql(
    req: SQLRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty query")
    
    first_word = query.split()[0].upper()
    
    if first_word not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=400, detail=f"Command blocked")
    
    # Require confirmation for dangerous commands
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
    if first_word in dangerous and not req.confirm:
        raise HTTPException(status_code=400, detail=f"Confirm required for {first_word}. Set confirm=true")
    
    # Block multiple statements
    cleaned = query.rstrip(";")
    if ";" in cleaned:
        raise HTTPException(status_code=400, detail="Only single query allowed")
    
    try:
        result = db.execute(text(query))
        
        if query.upper().startswith(("SELECT", "WITH", "PRAGMA", "EXPLAIN")):
            rows = result.fetchall()
            if rows:
                columns = list(result.keys())
                data = [dict(zip(columns, row)) for row in rows]
                return {
                    "type": "select",
                    "columns": columns,
                    "rows": data,
                    "row_count": len(data),
                    "message": f"Returned {len(data)} rows"
                }
            return {"type": "select", "columns": [], "rows": [], "row_count": 0, "message": "No rows"}
        else:
            db.commit()
            rowcount = result.rowcount if hasattr(result, 'rowcount') else 0
            return {"type": "dml", "message": f"Query OK. {rowcount} rows affected."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
async def get_tables(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    tables = [row[0] for row in result.fetchall()]
    return {"tables": tables}


@router.get("/schema/{table}")
async def get_schema(table: str, current_user: User = Depends(get_current_user), db = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
    result = db.execute(text(f"PRAGMA table_info({table})"))
    columns = [{"name": row[1], "type": row[2], "nullable": not row[3], "pk": bool(row[5])} for row in result.fetchall()]
    row_count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
    return {"table": table, "columns": columns, "row_count": row_count}