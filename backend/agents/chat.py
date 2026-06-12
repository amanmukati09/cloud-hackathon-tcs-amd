import requests
import sys
import json
import time

class ChatAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        # 🆕 Model-specific system prompts
        self.model_configs = {
            "llama3": {
                "max_tokens": 2048,
                "temperature": 0.7,
                "system_prompt": (
                    "You are AegisAI, an expert Site Reliability Engineering (SRE) assistant. "
                    "Provide highly technical, precise, and actionable answers. "
                    "Keep responses concise: under 3-4 sentences or tight bullet points. "
                    "Use the chat history for context. "
                    "If [RELEVANT PAST INCIDENTS] is provided, use that data to give "
                    "company-specific answers. Reference incident IDs when applicable."
                )
            },
            "deepseek-r1:7b": {
                "max_tokens": 4096,
                "temperature": 0.3,
                "system_prompt": (
                    "You are AegisAI, powered by DeepSeek-R1 – an expert SRE reasoning engine. "
                    "Think step-by-step through the incident analysis. "
                    "First, analyze the logs and past incidents systematically. "
                    "Then, provide a structured response with: "
                    "1) Root Cause Analysis 2) Evidence from past incidents "
                    "3) Recommended Actions 4) Prevention measures. "
                    "Be thorough but concise. Reference specific incident IDs."
                )
            },
            "mistral:7b": {
                "max_tokens": 2048,
                "temperature": 0.5,
                "system_prompt": (
                    "You are AegisAI, an efficient SRE assistant powered by Mistral. "
                    "Provide quick, actionable answers. "
                    "Focus on the most critical information first. "
                    "Use bullet points for clarity. "
                    "Reference past incidents when available."
                )
            }
        }

    def set_model(self, model: str):
        """Switch the active model."""
        if model in self.model_configs:
            self.model = model
            return True
        return False

    def get_available_models(self) -> list:
        """Return list of available model names."""
        return list(self.model_configs.keys())

    def generate_response(self, user_message: str, chat_history: list) -> str:
        config = self.model_configs.get(self.model, self.model_configs["llama3"])
        system_prompt = config["system_prompt"]

        # Build conversation string
        conversation = system_prompt + "\n\n"
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "AI"
            conversation += f"{role}: {msg['content']}\n"
        conversation += f"User: {user_message}\nAI:"

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": conversation,
                    "stream": False,
                    "options": {
                        "temperature": config["temperature"],
                        "num_predict": config["max_tokens"]
                    }
                },
                timeout=300
            )
            if response.status_code == 200:
                result = response.json().get("response", "")
                # DeepSeek sometimes includes thinking in response
                if "deepseek" in self.model and " " in result.lower():
                    # Extract just the final answer
                    parts = result.split(" final answer ", 1)
                    if len(parts) > 1:
                        result = parts[1].strip()
                return result
            else:
                return self._mock_fallback(user_message)
        except Exception as e:
            print(f"Ollama Error with {self.model}: {e}")
            return self._mock_fallback(user_message)

    def _mock_fallback(self, msg: str) -> str:
        msg = msg.lower()
        if "hello" in msg or "hi " in msg or msg.strip() == "hi":
            return "Hello! 👋 I am AegisAI, your intelligent SRE Copilot. How can I help you investigate your infrastructure today?"
        elif "version" in msg or "python" in msg:
            return f"I can certainly help with that! The backend is currently running on **Python {sys.version.split(' ')[0]}**."
        elif "log" in msg or "error" in msg or "anomaly" in msg:
            return "I am analyzing the logs. This signature typically indicates resource exhaustion or a sudden crash. Would you like me to generate a bash script to restart the service?"
        else:
            return "I am operating in fallback mode (Ollama is currently unreachable). However, I'm still recording this session! What else would you like to discuss?"

    import time
    
    def generate_response_stream(self, user_message: str, chat_history: list):
        
        """Generate streaming response with subtle pacing."""
        config = self.model_configs.get(self.model, self.model_configs["llama3"])
        system_prompt = config["system_prompt"]
    
        conversation = system_prompt + "\n\n"
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "AI"
            conversation += f"{role}: {msg['content']}\n"
        conversation += f"User: {user_message}\nAI:"
    
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": conversation,
                    "stream": True,
                    "options": {
                        "temperature": config["temperature"],
                        "num_predict": config["max_tokens"]
                    }
                },
                timeout=300,
                stream=True
            )
            if response.status_code == 200:
                token_buffer = []
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                token_buffer.append(token)
                                # Send in small groups for smoother animation
                                if len(token_buffer) >= 2:
                                    combined = "".join(token_buffer)
                                    yield combined
                                    token_buffer = []
                            if data.get("done", False):
                                if token_buffer:
                                    yield "".join(token_buffer)
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                yield self._mock_fallback(user_message)
        except Exception as e:
            print(f"Streaming error: {e}")
            yield self._mock_fallback(user_message)
    
    
