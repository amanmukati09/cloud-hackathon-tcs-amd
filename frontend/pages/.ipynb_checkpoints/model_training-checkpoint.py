"""
Model Training Page
UI for fine-tuning AI models on incident data.
"""

import gradio as gr
import requests
import time
from utils import BACKEND_URL

def build_training_tab(session_token, is_admin_state):
    comp = {}
    with gr.Column():
        gr.Markdown("### 🧠 Train Custom SRE Model")
        gr.Markdown("Fine-tune an AI model on your incident history for personalised responses.")
        comp["gpu_badge"] = gr.HTML('<span class="gpu-badge gpu-inactive">Checking GPU...</span>')
        gr.Markdown("---")
        with gr.Row(equal_height=True):
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("#### Configuration")
                comp["base_model"] = gr.Dropdown(
                    choices=["llama3", "mistral", "deepseek-r1:7b"],
                    value="llama3", label="Base Model", interactive=False
                )
                comp["num_epochs"] = gr.Slider(
                    minimum=1, maximum=5, value=3, step=1,
                    label="Number of Epochs", interactive=False
                )
                comp["use_all"] = gr.Checkbox(
                    label="Train on all incidents (admin only)" if is_admin_state else "Train on my incidents",
                    value=True, interactive=is_admin_state
                )
                comp["admin_warning"] = gr.Markdown("")
                with gr.Row():
                    comp["start_btn"] = gr.Button("🚀 Start Training", variant="primary", size="lg")
                    comp["refresh_btn"] = gr.Button("🔄 Refresh Status", variant="secondary")
                    comp["reset_btn"] = gr.Button("🧹 Reset", variant="stop", size="sm")
            with gr.Column(scale=2, min_width=400):
                gr.Markdown("#### Progress")
                comp["status_msg"] = gr.Markdown("Click **Start Training** to begin.")
                comp["progress_bar"] = gr.HTML(value=progress_bar_html(0, "Waiting..."))
                comp["loss_chart"] = gr.Markdown("")
        
        # ── Mini Chat (visible after training) ──
        with gr.Row(visible=False) as comp["chat_row"]:
            with gr.Column(elem_classes="glass-card premium-card"):
                comp["chat_header"] = gr.Markdown("### 🎯 Test Your Model")
                comp["finetuned_chatbot"] = gr.Chatbot(label="Chat with your fine-tuned model", height=300)
                with gr.Row():
                    comp["finetuned_input"] = gr.Textbox(
                        placeholder="Ask about incidents, root causes, or remediation...",
                        show_label=False, scale=4
                    )
                    comp["finetuned_send"] = gr.Button("Send", variant="primary", scale=1)
                comp["finetuned_model_name"] = gr.State("")
                gr.Markdown("*Quick tests:*")
                gr.Examples(
                    examples=[
                        ["What are the most common root causes in my incidents?"],
                        ["How should I handle a database connection timeout?"],
                        ["What remediation steps do you recommend for memory leaks?"]
                    ],
                    inputs=comp["finetuned_input"]
                )
        
        gr.Markdown("---")
        comp["log_output"] = gr.Markdown("")
    return comp


    
def progress_bar_html(pct: float, message: str = "", loss: float = None) -> str:
    color = "#38bdf8"
    if pct > 0.8:
        color = "#10b981"
    elif pct > 0.5:
        color = "#f59e0b"
    loss_text = f" | Loss: {loss:.4f}" if loss is not None else ""
    return f"""
    <div class="progress-container">
        <div class="progress-header">
            <span class="progress-label">{message}{loss_text}</span>
            <span class="progress-pct" style="color:{color};">{pct*100:.0f}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{pct*100}%;background:{color};"></div>
        </div>
    </div>
    """

def update_training_ui(is_admin):
    if is_admin:
        return (
            gr.update(interactive=True),   # base_model
            gr.update(interactive=True),   # num_epochs
            gr.update(label="Use all incidents (admin only)", interactive=True, value=True),
            gr.update(interactive=True),   # start_btn
            gr.update(interactive=True),   # reset_btn
            gr.update(value="")
        )
    else:
        return (
            gr.update(interactive=True),   # base_model (user can still change)
            gr.update(interactive=True),   # num_epochs
            gr.update(label="Train on my incidents", interactive=False, value=True),
            gr.update(interactive=True),   # start_btn (user can train)
            gr.update(interactive=True),   # reset_btn
            gr.update(value="You can train a model on your own incidents.")
        )

def check_gpu_for_training(token):
    """Check GPU status for training."""
    if not token:
        return '<span class="gpu-badge gpu-inactive">💻 Login required</span>'
    try:
        res = requests.get(f"{BACKEND_URL}/train/gpu-info", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("gpu_available"):
                return f'<span class="gpu-badge gpu-active">⚡ {data.get("gpu_name", "GPU")} ({data.get("gpu_memory_gb", 0):.0f}GB) - Training: {data.get("estimated_training_time", "10-15 min")}</span>'
            else:
                return f'<span class="gpu-badge gpu-inactive">💻 CPU Mode - {data.get("estimated_training_time", "slow")}</span>'
    except:
        pass
    return '<span class="gpu-badge gpu-inactive">⚠️ Backend offline</span>'


def start_training(base_model, num_epochs, use_all, token):
    """Start the training process."""
    if not token:
        return gr.update(value="❌ Please login first"), gr.update(), gr.update(), gr.update()
    
    try:
        res = requests.post(
            f"{BACKEND_URL}/train/start",
            json={"base_model": base_model, "num_epochs": int(num_epochs), "use_all_incidents": use_all},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            return (
                gr.update(value=f"✅ {data.get('message', 'Training started!')}"),
                gr.update(),
                gr.update(),
                gr.update(value="Training initiated. Refreshing status...")
            )
        else:
            return (
                gr.update(value=f"❌ {res.json().get('detail', 'Failed to start')}"),
                gr.update(),
                gr.update(),
                gr.update()
            )
    except Exception as e:
        return (
            gr.update(value=f"❌ Error: {str(e)}"),
            gr.update(),
            gr.update(),
            gr.update()
        )

def refresh_training_status(token):
    """Refresh training status display."""
    if not token:
        return (
            gr.update(value="Ready to train."),
            gr.update(value=progress_bar_html(0, "Waiting...")),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(visible=False),  # chat_row
            gr.update(),               # chat_header
            gr.update(),               # finetuned_model_name
        )
    
    try:
        res = requests.get(f"{BACKEND_URL}/train/status", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            running = data.get("running", False)
            progress = data.get("progress", 0)
            message = data.get("message", "")
            loss = data.get("loss")
            error = data.get("error")
            output_model = data.get("output_model", "")
            
            if error:
                status = f"❌ Training failed: {error}"
                chat_visible = False
            elif running:
                status = f"🔄 Training in progress..."
                chat_visible = False
            elif progress >= 1.0:
                model_name = data.get('output_model', 'N/A')
                status = (
                    f"✅ Training complete!\n\n"
                    f"**Model:** `{model_name}`\n\n"
                    f"👇 Use the chat below to test your model immediately."
                )
                chat_visible = True
            else:
                status = "Ready to train."
                chat_visible = False
            
            return (
                gr.update(value=status),
                gr.update(value=progress_bar_html(progress, message, loss)),
                gr.update(value=f"Step: {data.get('current_step', 0)}/{data.get('total_steps', '?')}" if running else ""),
                gr.update(value=f"Started: {data.get('started_at', 'N/A')}\nFinished: {data.get('finished_at', 'N/A')}"),
                gr.update(visible=chat_visible),  # chat_row
                gr.update(value=f"### 🎯 Test Your Model: `{output_model}`" if chat_visible else ""),  # chat_header
                gr.update(value=output_model),  # finetuned_model_name
            )
        elif res.status_code == 403:
            return (
                gr.update(value="🔒 Admin access required"),
                gr.update(value=progress_bar_html(0, "Restricted")),
                gr.update(value=""), gr.update(value=""),
                gr.update(visible=False), gr.update(), gr.update()
            )
    except:
        pass
    
    return (
        gr.update(value="⚠️ Could not fetch status"),
        gr.update(), gr.update(), gr.update(),
        gr.update(visible=False), gr.update(), gr.update()
    )

def reset_training_status(token):
    """Reset training status (admin only)."""
    if not token:
        return (
            gr.update(value="❌ Please login first"),
            gr.update(value=progress_bar_html(0, "Waiting...")),
            gr.update(value=""), gr.update(value=""),
            gr.update(visible=False), gr.update(), gr.update()
        )
    try:
        res = requests.post(f"{BACKEND_URL}/train/reset", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            return (
                gr.update(value="✅ Status reset to idle"),
                gr.update(value=progress_bar_html(0, "Idle")),
                gr.update(value=""), gr.update(value=""),
                gr.update(visible=False), gr.update(), gr.update()
            )
    except:
        pass
    return (
        gr.update(value="❌ Error"),
        gr.update(), gr.update(), gr.update(),
        gr.update(visible=False), gr.update(), gr.update()
    )

    


def chat_with_finetuned(message, history, model_name, token):
    """Send message to the fine-tuned model and get response."""
    if not message.strip() or not model_name:
        yield history, ""
        return
    
    history = history or []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "⏳ Thinking..."})
    yield history, ""
    
    try:
        # Switch to fine-tuned model first
        requests.post(
            f"{BACKEND_URL}/chat/model/switch",
            json={"model": model_name},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        # Send message
        res = requests.post(
            f"{BACKEND_URL}/chat/message",
            json={"message": message, "session_id": None},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if res.status_code == 200:
            data = res.json()
            history = []
            for item in data.get("history", []):
                if isinstance(item, list) and len(item) == 2:
                    history.append({"role": "user", "content": item[0]})
                    history.append({"role": "assistant", "content": item[1]})
            yield history, ""
        else:
            history[-1]["content"] = f"❌ Error: {res.text[:200]}"
            yield history, ""
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {str(e)}"
        yield history, ""


def get_model_chat_visible(progress, output_model):
    """Determine if the mini-chat should be visible."""
    # Show only when training complete (progress >= 1.0) AND we have a model name
    if progress >= 1.0 and output_model and output_model != "N/A":
        return gr.update(visible=True), gr.update(value=f"### 🎯 Test Your Model: `{output_model}`")
    return gr.update(visible=False), gr.update(value="")