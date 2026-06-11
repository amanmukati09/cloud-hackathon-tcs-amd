import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL

def get_chat_sessions(token):
    if not token: return []
    try:
        res = requests.get(f"{BACKEND_URL}/chat/sessions", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: 
            sessions = res.json()
            # Build clean dropdown options
            choices = []
            for sid, title in sessions.items():
                # Clean title - remove newlines, truncate
                clean_title = title.replace('\n', ' ').replace('\\n', ' ').strip()
                if len(clean_title) > 45:
                    clean_title = clean_title[:42] + "..."
                choices.append(f"ID: {sid} | {clean_title}")
            return choices
    except Exception as e:
        print(f"Get sessions error: {e}")
    return []

def load_chat_session(session_str, token):
    if not session_str or not token: 
        return [], None
    
    # Handle case where session_str might be a list
    if isinstance(session_str, list):
        session_str = session_str[0] if session_str else ""
    
    session_str = str(session_str)
    
    try:
        # Extract session ID
        if "ID: " in session_str:
            session_id = session_str.split("ID: ")[1].split(" |")[0].strip()
        else:
            session_id = session_str.strip()
        
        res = requests.get(
            f"{BACKEND_URL}/chat/sessions/{session_id}", 
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            history = []
            for item in data:
                if isinstance(item, list) and len(item) == 2:
                    history.append({"role": "user", "content": item[0]})
                    history.append({"role": "assistant", "content": item[1]})
            return history, session_id
    except Exception as e:
        print(f"Load chat error: {e}")
    return [], None

def send_chat_msg(message, session_id, history, token):
    if not message.strip(): 
        yield "", history, session_id, gr.update()
        return
    history = history or []
    history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": "⏳ Thinking..."}])
    yield "", history, session_id, gr.update()
    try:
        res = requests.post(
            f"{BACKEND_URL}/chat/message", 
            json={"message": message, "session_id": int(session_id) if session_id else None}, 
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            new_id = str(data.get("session_id"))
            choices = get_chat_sessions(token)
            sel = next((c for c in choices if f"ID: {new_id} |" in c), None)
            yield "", [{"role": "user" if u else "assistant", "content": u or a} 
                      for u, a in data.get("history", []) 
                      for u, a in [(u, None), (None, a)] if u or a], new_id, gr.update(choices=choices, value=sel)
        else:
            history[-1]["content"] = f"❌ Error: {res.text}"
            yield message, history, session_id, gr.update()
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {e}"
        yield message, history, session_id, gr.update()

def search_chats(query, token):
    if not token or not query or len(query.strip()) < 2:
        return pd.DataFrame(), "*Enter 2+ characters to search*"
    
    try:
        res = requests.get(
            f"{BACKEND_URL}/chat/search?query={query.strip()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                df = pd.DataFrame(results)
                df = df.rename(columns={
                    "session_id": "ID",
                    "session_title": "Session",
                    "role": "Role",
                    "snippet": "Message",
                    "timestamp": "Time"
                })
                df = df[["ID", "Session", "Role", "Message", "Time"]]
                return df, f"✅ Found **{len(df)}** results"
            else:
                return pd.DataFrame(), f"🔍 No results for '{query}'"
    except Exception as e:
        print(f"Chat search error: {e}")
    return pd.DataFrame(), "❌ Search failed"

def load_chat_by_id(session_id, token):
    """Load a chat session directly by its numeric ID."""
    if not session_id or not token:
        return [], "", gr.update(choices=[])
    
    try:
        sid = int(session_id)
        res = requests.get(
            f"{BACKEND_URL}/chat/sessions/{sid}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            history = []
            for item in data:
                if isinstance(item, list) and len(item) == 2:
                    history.append({"role": "user", "content": item[0]})
                    history.append({"role": "assistant", "content": item[1]})
            
            # Get fresh dropdown choices
            choices = get_chat_sessions(token)
            sel = next((c for c in choices if c.startswith(f"ID: {sid} |")), None)
            
            return history, str(sid), gr.update(choices=choices, value=sel)
    except Exception as e:
        print(f"Load by ID error: {e}")
    
    return [], "", gr.update(choices=[])

def delete_chat_session(session_id, token):
    """Delete a chat session by ID."""
    if not session_id or not token:
        return gr.update(), gr.update(choices=[])
    try:
        res = requests.delete(
            f"{BACKEND_URL}/chat/sessions/{int(session_id)}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            gr.Info(f"✅ Chat session {session_id} deleted")
            # Refresh dropdown
            choices = get_chat_sessions(token)
            return [], gr.update(choices=choices, value=None)
        else:
            gr.Warning(f"❌ {res.json().get('detail', 'Failed to delete')}")
    except Exception as e:
        gr.Warning(f"❌ Error: {e}")
    return gr.update(), gr.update(choices=get_chat_sessions(token))

def rename_chat_session(session_id, new_title, token):
    if not session_id or not new_title.strip() or not token:
        return gr.update(), gr.update(choices=get_chat_sessions(token))
    try:
        res = requests.put(
            f"{BACKEND_URL}/chat/sessions/{int(session_id)}/rename",
            json={"new_title": new_title.strip()},
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            gr.Info(f"✅ Renamed to '{new_title.strip()}'")
            choices = get_chat_sessions(token)
            # Select the updated session
            for c in choices:
                if c.startswith(f"ID: {session_id} |"):
                    return gr.update(choices=choices, value=c), gr.update(choices=choices)
            return gr.update(choices=choices), gr.update(choices=choices)
        else:
            detail = res.json().get('detail', 'Rename failed')
            gr.Warning(f"❌ {detail}")
    except Exception as e:
        gr.Warning(f"❌ Error: {e}")
    return gr.update(), gr.update(choices=get_chat_sessions(token))