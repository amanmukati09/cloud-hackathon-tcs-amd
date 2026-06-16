from fastapi import APIRouter, Depends
from pydantic import BaseModel
from agents.live_monitor import monitor
from auth import get_current_user
from models import User

router = APIRouter(prefix="/live", tags=["Live Monitor"])

class ChatMessage(BaseModel):
    message: str

@router.get("/sources")
async def get_sources(current_user=Depends(get_current_user)):
    return {"sources": monitor.get_sources()}

@router.get("/state")
async def get_state(source: str = "default", current_user=Depends(get_current_user)):
    return monitor.get_state(source)

@router.post("/start")
async def start_monitoring(source: str = "default", current_user: User = Depends(get_current_user)):
    ok = monitor.start_monitor(source, user_id=current_user.id)
    return {"status": "started" if ok else "already_running"}

@router.post("/stop")
async def stop_monitoring(source: str = "default", current_user=Depends(get_current_user)):
    report = monitor.stop_monitor(source)
    return {"status": "stopped", "report": report}

@router.post("/chat")
async def live_chat(msg: ChatMessage, source: str = "default", current_user=Depends(get_current_user)):
    reply = monitor.chat_about_stream(source, msg.message)
    return {"reply": reply}