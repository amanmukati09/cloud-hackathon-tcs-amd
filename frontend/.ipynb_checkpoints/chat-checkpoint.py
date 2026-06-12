import gradio as gr
import requests
import pandas as pd
import json
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


def get_available_models():
    """Fetch available AI models."""
    try:
        res = requests.get(f"{BACKEND_URL}/chat/models", timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = data.get("models", [])
            current = data.get("current", "llama3")
            choices = [m["id"] for m in models]
            return gr.update(choices=choices, value=current)
    except:
        pass
    return gr.update()

    

def switch_model(model, token):
    """Switch the AI model."""
    if not model or not token:
        return gr.update()
    try:
        res = requests.post(
            f"{BACKEND_URL}/chat/model/switch",
            json={"model": model},
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            gr.Info(f"✅ Switched to {model}")
    except:
        gr.Warning("❌ Failed to switch model")
    return gr.update()


def send_chat_msg_stream(message, session_id, history, token):
    """Stream chat response token by token with visible loading effect."""
    if not message.strip():
        yield "", history, session_id
        return
    
    history = history or []
    history.append({"role": "user", "content": message})
    # Show animated thinking indicator
    history.append({"role": "assistant", "content": "⏳ Thinking..."})
    yield "", history, session_id
    
    full_response = ""
    token_count = 0
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/chat/message/stream",
            json={"message": message, "session_id": int(session_id) if session_id else None},
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
            timeout=300
        )
        
        for line in res.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("done"):
                        break
                    token_text = data.get("token", "")
                    full_response += token_text
                    token_count += 1
                    
                    # Show progressive loading indicator
                    if token_count == 1:
                        history[-1]["content"] = full_response + " ▌"
                    elif token_count % 5 == 0:
                        # Update every 5 tokens to avoid UI lag
                        dots = "." * ((token_count // 10) % 4)
                        history[-1]["content"] = full_response + " ▌"
                    else:
                        history[-1]["content"] = full_response + " ▌"
                    
                    # Yield every few tokens for smoother animation
                    if token_count % 3 == 0:
                        yield "", history, session_id
        
        # Final response without cursor
        history[-1]["content"] = full_response
        yield "", history, session_id
        
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {str(e)}"
        yield "", history, session_id

def analyze_sentiment(message, token):
    """Analyze sentiment of a message."""
    if not message.strip() or not token:
        return gr.update(value="")
    try:
        res = requests.post(
            f"{BACKEND_URL}/chat/analyze-sentiment?message={message.strip()}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            return gr.update(value=data.get("html", ""))
    except:
        pass
    return gr.update(value="")