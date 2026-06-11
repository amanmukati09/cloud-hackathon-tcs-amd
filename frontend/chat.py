import gradio as gr
import requests
from utils import BACKEND_URL

def get_chat_sessions(token):
    if not token: return []
    try:
        res = requests.get(f"{BACKEND_URL}/chat/sessions", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return [title for session_id, title in res.json().items()]
    except: pass
    return []

def load_chat_session(session_str, token):
    if not session_str or not token: return [], None
    try:
        session_id = session_str.split("ID: ")[1].split(" |")[0]
        res = requests.get(f"{BACKEND_URL}/chat/sessions/{session_id}", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            return [{"role": "user" if u else "assistant", "content": u or a} for u, a in res.json() for u, a in [(u, None), (None, a)] if u or a], session_id
    except: pass
    return [], None

def send_chat_msg(message, session_id, history, token):
    if not message.strip(): 
        yield "", history, session_id, gr.update()
        return
    history = history or []
    history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": "⏳ Thinking..."}])
    yield "", history, session_id, gr.update()
    try:
        res = requests.post(f"{BACKEND_URL}/chat/message", json={"message": message, "session_id": int(session_id) if session_id else None}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            new_id = str(data.get("session_id"))
            choices = get_chat_sessions(token)
            sel = next((c for c in choices if f"ID: {new_id} |" in c), None)
            yield "", [{"role": "user" if u else "assistant", "content": u or a} for u, a in data.get("history", []) for u, a in [(u, None), (None, a)] if u or a], new_id, gr.update(choices=choices, value=sel)
        else:
            history[-1]["content"] = f"❌ Error: {res.text}"
            yield message, history, session_id, gr.update()
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {e}"
        yield message, history, session_id, gr.update()