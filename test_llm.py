import requests
import json

print("Testing LLM connection with Ollama...")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "Classify this log: '[ERROR] nginx: worker crashed'. Is this CRITICAL or WARNING?",
        "stream": False
    },
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print("\n✅ LLM Response:")
    print(result["response"])
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
