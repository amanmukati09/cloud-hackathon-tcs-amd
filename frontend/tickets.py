import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL

def submit_escalation(question, token):
    if not question.strip(): return gr.update(), fetch_my_tickets(token)
    try:
        res = requests.post(f"{BACKEND_URL}/escalations", json={"question": question}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("✅ Ticket submitted securely to the Admin team!")
            return gr.update(value=""), fetch_my_tickets(token)
    except Exception as e: gr.Warning(f"Error: {e}")
    return gr.update(), fetch_my_tickets(token)

def fetch_my_tickets(token):
    if not token: return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/escalations/my", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame()

def load_admin_tickets(token):
    if not token: return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/admin/escalations", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200: return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame()

def answer_escalation(ticket_id, answer, token):
    if not ticket_id or not answer.strip():
        return gr.update(), gr.update(), load_admin_tickets(token)
    try:
        res = requests.post(f"{BACKEND_URL}/admin/escalations/{int(ticket_id)}/answer", json={"answer": answer}, headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("✅ Answer posted successfully!")
            return gr.update(value=None), gr.update(value=""), load_admin_tickets(token)
        else: gr.Warning(f"❌ Error: {res.json().get('detail')}")
    except Exception as e: gr.Warning(f"❌ Error: {e}")
    return gr.update(), gr.update(), load_admin_tickets(token)