"""
Fine-Tuned Model Explorer & Interactive Shell
Query your trained AegisAI models directly from Python/Jupyter.

Usage:
    python fine_tuned_model_checker.py
    
    Then in the interactive shell:
    >>> models                              # List all models
    >>> use "aegis-sre-llama3-user_5"       # Select model A
    >>> ask "What causes database timeouts?" # Query model A
    >>> compare "nginx crashes"             # Compare all models
    >>> compare "memory leaks" --top 3      # Compare top 3 models
    >>> history                             # Show query history
    >>> save "my_session"                   # Save session
    >>> help                                # Show all commands
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from typing import Optional

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

OLLAMA_URL = "http://localhost:11434"
MODEL_DIR = "./fine_tuned_models"
BASE_MODELS = ["llama3", "mistral:7b", "deepseek-r1:7b"]


# ═══════════════════════════════════════════════════
# Model Discovery
# ═══════════════════════════════════════════════════

class ModelExplorer:
    """Discover and manage fine-tuned models."""
    
    def __init__(self):
        self.models = {}
        self.active_model = None
        self.query_history = []
        self._discover_models()
    
    def _discover_models(self):
        """Find all available models (Ollama + local files)."""
        self.models = {}
        
        # Method 1: Query Ollama
        try:
            result = subprocess.run(
                ["ollama", "list", "--format", "json"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                ollama_models = json.loads(result.stdout)
                for i, m in enumerate(ollama_models):
                    name = m.get("name", f"unknown_{i}")
                    self.models[name] = {
                        "name": name,
                        "source": "ollama",
                        "size": m.get("size", "Unknown"),
                        "modified": m.get("modified_at", "Unknown"),
                        "is_finetuned": name.startswith("aegis-sre-"),
                        "index": i + 1
                    }
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
        
        # Method 2: Check local fine-tuned model directories
        if os.path.exists(MODEL_DIR):
            for folder in os.listdir(MODEL_DIR):
                folder_path = os.path.join(MODEL_DIR, folder)
                if os.path.isdir(folder_path):
                    modelfile = os.path.join(folder_path, "Modelfile")
                    if os.path.exists(modelfile):
                        model_name = folder
                        if model_name not in self.models:
                            self.models[model_name] = {
                                "name": model_name,
                                "source": "local",
                                "size": self._get_folder_size(folder_path),
                                "modified": datetime.fromtimestamp(
                                    os.path.getmtime(modelfile)
                                ).strftime("%Y-%m-%d %H:%M"),
                                "is_finetuned": True,
                                "index": len(self.models) + 1
                            }
        
        # Method 3: Add base models
        for i, base in enumerate(BASE_MODELS):
            if base not in self.models:
                self.models[base] = {
                    "name": base,
                    "source": "ollama",
                    "size": "Base model",
                    "modified": "N/A",
                    "is_finetuned": False,
                    "index": len(self.models) + 1
                }
    
    def _get_folder_size(self, path: str) -> str:
        """Get human-readable folder size."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        
        if total > 1024 * 1024 * 1024:
            return f"{total / (1024*1024*1024):.1f} GB"
        elif total > 1024 * 1024:
            return f"{total / (1024*1024):.1f} MB"
        else:
            return f"{total / 1024:.1f} KB"
    
    def list_models(self, finetuned_only: bool = False):
        """Display all discovered models."""
        print("\n" + "="*80)
        print("📦 DISCOVERED MODELS")
        print("="*80)
        
        filtered = {k: v for k, v in self.models.items() 
                   if not finetuned_only or v["is_finetuned"]}
        
        if not filtered:
            print("No models found. Train a model first or ensure Ollama is running.")
            return
        
        for name, info in sorted(filtered.items(), 
                                key=lambda x: (not x[1]["is_finetuned"], x[0])):
            badge = "🎯" if info["is_finetuned"] else "📦"
            active = " ✅ ACTIVE" if name == self.active_model else ""
            print(f"\n  [{info['index']}] {badge} {name}{active}")
            print(f"      Source: {info['source']} | Size: {info['size']}")
            print(f"      Modified: {info['modified']}")
        
        print("\n" + "-"*80)
        if self.active_model:
            print(f"🎯 Active model: {self.active_model}")
        else:
            print("💡 Use: model[X] or use(\"model_name\") to select a model")
        print("="*80 + "\n")
    
    def select_model(self, identifier):
        """Select a model by name or index."""
        # Try by index
        if isinstance(identifier, int):
            for name, info in self.models.items():
                if info["index"] == identifier:
                    self.active_model = name
                    print(f"✅ Selected: {name}")
                    return
        
        # Try by exact name
        if identifier in self.models:
            self.active_model = identifier
            print(f"✅ Selected: {identifier}")
            return
        
        # Try partial match
        matches = [n for n in self.models if identifier.lower() in n.lower()]
        if len(matches) == 1:
            self.active_model = matches[0]
            print(f"✅ Selected: {matches[0]}")
            return
        elif len(matches) > 1:
            print(f"⚠️  Multiple matches: {matches}")
            print("💡 Use exact name or index number")
            return
        
        print(f"❌ Model '{identifier}' not found")
    
    def query_model(self, prompt: str, model: Optional[str] = None) -> str:
        """Send a query to a model and get response."""
        target_model = model or self.active_model
        
        if not target_model:
            return "❌ No model selected. Use: use(\"model_name\")"
        
        if target_model not in self.models:
            return f"❌ Model '{target_model}' not found"
        
        print(f"\n🤔 Querying {target_model}...")
        print(f"📝 Prompt: {prompt}\n")
        print("-" * 60)
        
        try:
            # Format as SRE prompt
            system_prompt = (
                "You are an expert SRE assistant. Provide concise, "
                "technical answers with actionable recommendations."
            )
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": target_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "No response")
                
                # Record history
                self.query_history.append({
                    "model": target_model,
                    "prompt": prompt,
                    "response": result,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                print(result)
                print("-" * 60)
                return result
            else:
                error = f"❌ API Error: {response.status_code}"
                print(error)
                return error
                
        except requests.exceptions.ConnectionError:
            error = "❌ Cannot connect to Ollama. Is it running?"
            print(error)
            return error
        except Exception as e:
            error = f"❌ Error: {str(e)}"
            print(error)
            return error
    
    def compare_models(self, prompt: str, top_n: int = 3):
        """Run the same query across multiple models and compare."""
        finetuned = {k: v for k, v in self.models.items() if v["is_finetuned"]}
        
        if not finetuned:
            print("❌ No fine-tuned models found for comparison")
            return
        
        models_to_test = list(finetuned.keys())[:top_n]
        
        # Add base llama3 for baseline
        if "llama3" in self.models:
            models_to_test.append("llama3")
        
        print(f"\n🏟️  MODEL COMPARISON ARENA")
        print(f"📝 Prompt: {prompt}")
        print("=" * 80)
        
        results = {}
        for model in models_to_test:
            print(f"\n{'─'*60}")
            print(f"🤖 Model: {model}")
            print(f"{'─'*60}")
            result = self.query_model(prompt, model)
            results[model] = result
        
        # Summary
        print(f"\n{'='*80}")
        print("📊 COMPARISON SUMMARY")
        print(f"{'='*80}")
        for model, result in results.items():
            word_count = len(result.split())
            print(f"  {model}: {word_count} words")
        print()
    
    def show_history(self):
        """Display query history."""
        if not self.query_history:
            print("No queries yet.")
            return
        
        print("\n📜 QUERY HISTORY")
        print("=" * 80)
        for i, entry in enumerate(self.query_history[-10:], 1):
            print(f"\n[{i}] {entry['timestamp']} | Model: {entry['model']}")
            print(f"    Q: {entry['prompt'][:100]}...")
            print(f"    A: {entry['response'][:150]}...")
        print()
    
    def save_session(self, filename: str = None):
        """Save query history to file."""
        if not filename:
            filename = f"model_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "active_model": self.active_model,
                "history": self.query_history,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"✅ Session saved to: {filename}")
    
    def show_help(self):
        """Display help."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🧠 MODEL EXPLORER COMMANDS                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  models              - List all available models             ║
║  models(True)        - List only fine-tuned models           ║
║                                                              ║
║  model[1]            - Select model by index                 ║
║  use("name")         - Select model by name                  ║
║  active              - Show currently selected model         ║
║                                                              ║
║  ask("prompt")       - Query active model                    ║
║  ask("prompt", "X")  - Query specific model                  ║
║                                                              ║
║  compare("prompt")   - Compare all fine-tuned models         ║
║  compare("prompt", 5)- Compare top 5 models                  ║
║                                                              ║
║  history             - Show query history                    ║
║  save("file.json")   - Save session to file                  ║
║  help                - Show this help                        ║
║                                                              ║
║  Shortcuts:                                                  ║
║  a = ask, m = models, u = use, c = compare, h = history     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)


# ═══════════════════════════════════════════════════
# Interactive Shell
# ═══════════════════════════════════════════════════

def main():
    explorer = ModelExplorer()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🧠 AEGIS AI - MODEL EXPLORER SHELL                  ║
║                                                              ║
║  Type 'help' for commands, 'models' to see all models        ║
║  Type 'quit' to exit                                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    explorer.list_models()
    
    # Expose shortcuts
    models = lambda ft=False: explorer.list_models(ft)
    use = lambda x: explorer.select_model(x)
    ask = lambda p, m=None: explorer.query_model(p, m)
    compare = lambda p, n=3: explorer.compare_models(p, n)
    history = lambda: explorer.show_history()
    save = lambda f=None: explorer.save_session(f)
    help = lambda: explorer.show_help()
    
    # Short aliases
    a = ask
    m = models
    u = use
    c = compare
    h = history
    
    # Model access by index
    class ModelIndexer:
        def __getitem__(self, index):
            explorer.select_model(index)
    model = ModelIndexer()
    
    @property
    def active():
        if explorer.active_model:
            print(f"🎯 Active: {explorer.active_model}")
        else:
            print("No model selected. Use: model[1] or use('name')")
    
    # Welcome message
    print("\n💡 Quick start:")
    if explorer.models:
        first_model = list(explorer.models.keys())[0]
        print(f"   use(\"{first_model}\")     # Select first model")
        print(f"   ask(\"What causes server crashes?\")  # Query it")
    print()
    
    # Interactive loop
    try:
        while True:
            try:
                cmd = input(">>> ").strip()
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif cmd == 'active':
                    if explorer.active_model:
                        print(f"🎯 Active: {explorer.active_model}")
                    else:
                        print("No model selected")
                elif cmd:
                    try:
                        result = eval(cmd)
                        if result is not None:
                            print(result)
                    except SyntaxError:
                        exec(cmd)
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()