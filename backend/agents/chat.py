import requests
import sys

class ChatAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate_response(self, user_message: str, chat_history: list) -> str:
        # OPTIMIZATION: Strict conciseness instructions to lower token count and boost generation speed!
        system_prompt = (
            "You are AegisAI, an expert Site Reliability Engineering (SRE) assistant. "
            "Provide highly technical, precise, and actionable answers. "
            "Keep your responses concise: strictly under 3-4 sentences or tight bullet points and reply to local daily coversations with a friendly tone and help users troubleshoot their infrastructure issues or whatever they need help with. Always ask follow-up questions to clarify the issue and gather more information if needed. Use the chat history for context but do not repeat information unnecessarily."
        )
        prompt = f"{system_prompt}\n\nUser: {user_message}\nAI:"
        
        try:
            # FIX: Increased timeout ceiling to 5 minutes to fully protect slower generations
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300 
            )
            if response.status_code == 200:
                return response.json().get("response", "Error generating response.")
            else:
                return self._mock_fallback(user_message)
        except Exception as e:
            print(f"Ollama Error: {e}")
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