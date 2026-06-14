#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           🧠 AEGIS AI - PREMIUM MODEL EXPLORER               ║
║     Interactive Terminal for Fine-Tuned Model Testing        ║
╚══════════════════════════════════════════════════════════════╝

A beautiful terminal UI for exploring and comparing AI models.
"""

import subprocess
import json
import requests
import re
import os
import sys
import time
import textwrap
from datetime import datetime
from typing import Optional, List, Dict

# ═══════════════════════════════════════════════════════
# COLOR SYSTEM
# ═══════════════════════════════════════════════════════

class Colors:
    """Terminal color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    
    # Backgrounds
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

C = Colors()

# ═══════════════════════════════════════════════════════
# ANIMATION HELPERS
# ═══════════════════════════════════════════════════════

def typewriter(text: str, delay: float = 0.015, color: str = C.WHITE):
    """Animated typewriter effect."""
    for char in text:
        sys.stdout.write(f"{color}{char}{C.RESET}")
        sys.stdout.flush()
        time.sleep(delay)
    print()

def spinner(seconds: float, message: str = "Processing"):
    """Show animated spinner."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + seconds
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f'\r{C.CYAN}{frames[i % len(frames)]} {message}...{C.RESET}')
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

def progress_bar(current: int, total: int, width: int = 40, label: str = ""):
    """Draw progress bar."""
    pct = current / max(total, 1)
    filled = int(width * pct)
    bar = f"{C.BG_BLUE}{' ' * filled}{C.RESET}{C.DIM}{' ' * (width - filled)}{C.RESET}"
    sys.stdout.write(f'\r{label} [{bar}] {pct*100:.0f}%')
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write('\n')

def box(text: str, color: str = C.CYAN, padding: int = 2):
    """Draw text in a box."""
    lines = text.split('\n')
    width = max(len(line) for line in lines) + padding * 2
    top = f"{color}╔{'═' * width}╗{C.RESET}"
    bottom = f"{color}╚{'═' * width}╝{C.RESET}"
    print(top)
    for line in lines:
        print(f"{color}║{C.RESET}{' ' * padding}{line}{' ' * (width - len(line) - padding)}{color}║{C.RESET}")
    print(bottom)


# ═══════════════════════════════════════════════════════
# PREMIUM MODEL CHECKER
# ═══════════════════════════════════════════════════════

class PremiumModelChecker:
    """Advanced model explorer with beautiful terminal UI."""
    
    def __init__(self):
        self.models = {}
        self.active = None
        self.history = []
        self.favorites = set()
        self.session_start = datetime.now()
        self.query_count = 0
        self._discover()
    
    def _discover(self):
        """Find all models from Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            name = parts[0].replace(':latest', '')
                            self.models[name] = {
                                "name": name,
                                "index": len(self.models) + 1,
                                "finetuned": 'aegis' in name.lower() or 'finetuned' in name.lower(),
                                "size": parts[2] if len(parts) > 2 else "?",
                                "modified": ' '.join(parts[3:]) if len(parts) > 3 else "?"
                            }
        except Exception as e:
            print(f"{C.RED}⚠️  Ollama error: {e}{C.RESET}")
    
    # ═══════════════════════════════════════════════════
    # DISPLAY METHODS
    # ═══════════════════════════════════════════════════
    
    def show_banner(self):
        """Display welcome banner."""
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"""
{C.BRIGHT_CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🧠  A E G I S   A I   E X P L O R E R           ║
║                                                              ║
║         Interactive Model Testing & Comparison Shell          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{C.RESET}
{C.DIM}Session: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')} | Models: {len(self.models)} | Press 'h' for help{C.RESET}
""")
    
    def list_models(self, finetuned_only: bool = False):
        """Display models with rich formatting."""
        print(f"\n{C.BOLD}{'='*70}{C.RESET}")
        print(f"{C.BRIGHT_CYAN}{C.BOLD}  📦 AVAILABLE MODELS{C.RESET}")
        print(f"{C.BOLD}{'='*70}{C.RESET}")
        
        items = {k:v for k,v in self.models.items() 
                if not finetuned_only or v["finetuned"]}
        
        if not items:
            print(f"\n{C.YELLOW}  No models found. Train a model or start Ollama.{C.RESET}")
            return
        
        # Sort: fine-tuned first, then alphabetically
        sorted_items = sorted(items.items(), 
                            key=lambda x: (not x[1]["finetuned"], x[0]))
        
        ft_count = sum(1 for _, v in sorted_items if v["finetuned"])
        
        print(f"\n{C.BRIGHT_GREEN}  🎯 FINE-TUNED MODELS ({ft_count}){C.RESET}")
        print(f"  {C.DIM}{'─'*60}{C.RESET}")
        
        ft_shown = 0
        for name, info in sorted_items:
            if not info["finetuned"]:
                continue
            ft_shown += 1
            active_marker = f"{C.BRIGHT_YELLOW} ← ACTIVE{C.RESET}" if name == self.active else ""
            fav_marker = f"{C.YELLOW}⭐{C.RESET} " if name in self.favorites else "  "
            
            print(f"  {fav_marker}{C.BOLD}[{info['index']}]{C.RESET} {C.GREEN}{name}{C.RESET}{active_marker}")
            print(f"     {C.DIM}Size: {info['size']} | Modified: {info['modified']}{C.RESET}")
        
        if ft_shown == 0:
            print(f"  {C.DIM}No fine-tuned models yet. Train one from the web UI!{C.RESET}")
        
        print(f"\n{C.BRIGHT_BLUE}  📦 BASE MODELS ({len(items) - ft_count}){C.RESET}")
        print(f"  {C.DIM}{'─'*60}{C.RESET}")
        
        for name, info in sorted_items:
            if info["finetuned"]:
                continue
            active_marker = f"{C.BRIGHT_YELLOW} ← ACTIVE{C.RESET}" if name == self.active else ""
            
            print(f"     {C.BOLD}[{info['index']}]{C.RESET} {C.BLUE}{name}{C.RESET}{active_marker}")
        
        print(f"\n{C.BOLD}{'='*70}{C.RESET}\n")
    
    def show_active(self):
        """Show currently active model with details."""
        if not self.active:
            print(f"\n{C.YELLOW}⚠️  No model selected. Use: {C.BOLD}use <number/name>{C.RESET}\n")
            return
        
        info = self.models.get(self.active, {})
        ft_badge = f"{C.GREEN}🎯 Fine-Tuned{C.RESET}" if info.get("finetuned") else f"{C.BLUE}📦 Base Model{C.RESET}"
        
        print(f"\n{C.BOLD}{'─'*50}{C.RESET}")
        print(f"  {C.BRIGHT_CYAN}🎯 ACTIVE MODEL{C.RESET}")
        print(f"{C.BOLD}{'─'*50}{C.RESET}")
        print(f"  Name: {C.BOLD}{self.active}{C.RESET}")
        print(f"  Type: {ft_badge}")
        print(f"  Size: {C.DIM}{info.get('size', '?')}{C.RESET}")
        print(f"  Modified: {C.DIM}{info.get('modified', '?')}{C.RESET}")
        print(f"  Queries: {C.BRIGHT_YELLOW}{self.query_count}{C.RESET}")
        print(f"{C.BOLD}{'─'*50}{C.RESET}\n")
    
    # ═══════════════════════════════════════════════════
    # MODEL SELECTION
    # ═══════════════════════════════════════════════════
    
    def select_model(self, identifier):
        """Select model by name, index, or partial match with fuzzy search."""
        # Try exact index
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            idx = int(identifier)
            for name, info in self.models.items():
                if info["index"] == idx:
                    self.active = name
                    self._on_select(name)
                    return
        
        # Try exact name
        if identifier in self.models:
            self.active = identifier
            self._on_select(identifier)
            return
        
        # Fuzzy search
        identifier_lower = identifier.lower()
        matches = []
        for name in self.models:
            score = 0
            name_lower = name.lower()
            # Exact substring gets high score
            if identifier_lower in name_lower:
                score += 10
            # Character overlap
            score += sum(1 for c in identifier_lower if c in name_lower)
            # Prefer shorter names
            score -= len(name) * 0.01
            if score > 2:
                matches.append((score, name))
        
        matches.sort(key=lambda x: x[0], reverse=True)
        
        if len(matches) == 1:
            self.active = matches[0][1]
            self._on_select(matches[0][1])
        elif matches:
            print(f"\n{C.YELLOW}Multiple matches found:{C.RESET}")
            for i, (score, name) in enumerate(matches[:5], 1):
                ft = "🎯" if self.models[name]["finetuned"] else "📦"
                print(f"  {C.BOLD}{i}.{C.RESET} {ft} {name} {C.DIM}(score: {score:.1f}){C.RESET}")
            
            try:
                choice = input(f"\n{C.CYAN}Select number (or 0 to cancel): {C.RESET}")
                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(matches):
                        self.active = matches[idx-1][1]
                        self._on_select(matches[idx-1][1])
            except (KeyboardInterrupt, EOFError):
                pass
        else:
            print(f"{C.RED}❌ No model matches '{identifier}'{C.RESET}")
    
    def _on_select(self, name):
        """Called when a model is selected."""
        info = self.models[name]
        badge = "🎯" if info["finetuned"] else "📦"
        print(f"\n{C.GREEN}✅ Selected: {badge} {C.BOLD}{name}{C.RESET}")
        
        if name in self.favorites:
            print(f"   {C.YELLOW}⭐ This is a favorite model{C.RESET}")
        
        print(f"   {C.DIM}Try: ask \"your question here\"{C.RESET}\n")
    
    def toggle_favorite(self, name: str = None):
        """Toggle favorite status for a model."""
        target = name or self.active
        if not target:
            print(f"{C.RED}No model selected{C.RESET}")
            return
        
        if target in self.favorites:
            self.favorites.discard(target)
            print(f"{C.YELLOW}💛 Removed from favorites: {target}{C.RESET}")
        else:
            self.favorites.add(target)
            print(f"{C.YELLOW}⭐ Added to favorites: {target}{C.RESET}")
    
    # ═══════════════════════════════════════════════════
    # QUERY METHODS
    # ═══════════════════════════════════════════════════
    
    def ask(self, prompt: str, model: str = None, show_thinking: bool = True):
        """Query a model with animated thinking indicator."""
        target = model or self.active
        if not target:
            print(f"{C.RED}❌ No model selected. Use: {C.BOLD}use <number>{C.RESET}")
            return None
        
        self.query_count += 1
        
        # Header
        info = self.models.get(target, {})
        badge = "🎯" if info.get("finetuned") else "📦"
        
        print(f"\n{C.BOLD}{'─'*60}{C.RESET}")
        print(f"  {badge} {C.BOLD}{target}{C.RESET}")
        print(f"  {C.DIM}Query #{self.query_count}{C.RESET}")
        print(f"  {C.CYAN}📝 {prompt}{C.RESET}")
        print(f"{C.BOLD}{'─'*60}{C.RESET}")
        
        if show_thinking:
            print(f"\n  {C.DIM}🧠 Thinking", end='')
        
        try:
            start_time = time.time()
            
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": target,
                    "prompt": (
                        f"[Role: Expert SRE Assistant]\n"
                        f"[Task: Provide concise, technical, actionable answer]\n\n"
                        f"User: {prompt}\n\nAssistant:"
                    ),
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 500}
                },
                timeout=120
            )
            
            elapsed = time.time() - start_time
            
            if show_thinking:
                sys.stdout.write(f"\r{' ' * 30}\r")
                sys.stdout.flush()
            
            if resp.status_code == 200:
                result = resp.json().get("response", "No response")
                
                # Store in history
                self.history.append({
                    "model": target, "prompt": prompt,
                    "response": result, 
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "elapsed": round(elapsed, 2)
                })
                
                # Print response with formatting
                print(f"\n{C.GREEN}{'─'*60}{C.RESET}")
                self._print_response(result)
                print(f"{C.GREEN}{'─'*60}{C.RESET}")
                print(f"  {C.DIM}⏱️  {elapsed:.1f}s | {len(result.split())} words{C.RESET}\n")
                
                return result
            else:
                print(f"\n{C.RED}❌ HTTP {resp.status_code}: {resp.text[:100]}{C.RESET}")
        except requests.exceptions.ConnectionError:
            print(f"\n{C.RED}❌ Cannot connect to Ollama. Is it running?{C.RESET}")
        except Exception as e:
            print(f"\n{C.RED}❌ Error: {e}{C.RESET}")
        
        return None
    
    def _print_response(self, text: str):
        """Print response with nice formatting."""
        # Wrap long lines
        wrapper = textwrap.TextWrapper(width=60, initial_indent='  ', subsequent_indent='  ')
        
        for line in text.split('\n'):
            if line.strip():
                # Color code prefixes
                if line.strip().startswith(('Step', '1.', '2.', '3.', '•', '-', '*')):
                    print(f"  {C.BRIGHT_YELLOW}{line.strip()}{C.RESET}")
                elif line.strip().startswith(('Error', 'Critical', 'WARNING')):
                    print(f"  {C.RED}{line.strip()}{C.RESET}")
                elif line.strip().startswith(('Note', 'Tip', 'Recommend')):
                    print(f"  {C.BRIGHT_CYAN}{line.strip()}{C.RESET}")
                elif any(kw in line.lower() for kw in ['command', '`', 'sudo', 'systemctl', 'docker']):
                    print(f"  {C.BRIGHT_GREEN}{line.strip()}{C.RESET}")
                else:
                    for wrapped in wrapper.wrap(line):
                        print(f"{C.WHITE}{wrapped}{C.RESET}")
            else:
                print()
    
    def compare(self, prompt: str, limit: int = 3):
        """Compare multiple models on the same query."""
        finetuned = [(k, v) for k, v in self.models.items() if v["finetuned"]]
        finetuned = sorted(finetuned, key=lambda x: x[1]['index'])[:limit]
        
        models_to_test = [m[0] for m in finetuned]
        if "llama3" in self.models and "llama3" not in models_to_test:
            models_to_test.append("llama3")
        
        if len(models_to_test) < 2:
            print(f"{C.YELLOW}Need at least 2 models to compare. Found: {len(models_to_test)}{C.RESET}")
            return
        
        print(f"\n{C.BOLD}{C.BRIGHT_MAGENTA}{'='*70}{C.RESET}")
        print(f"{C.BRIGHT_MAGENTA}{C.BOLD}  🏟️  MODEL COMPARISON ARENA{C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_MAGENTA}{'='*70}{C.RESET}")
        print(f"  {C.CYAN}📝 Query: {prompt}{C.RESET}")
        print(f"  {C.DIM}Models: {', '.join(models_to_test)}{C.RESET}")
        print()
        
        results = {}
        for i, model in enumerate(models_to_test, 1):
            progress_bar(i-1, len(models_to_test), label=f"  Processing")
            result = self.ask(prompt, model, show_thinking=False)
            results[model] = result
        
        progress_bar(len(models_to_test), len(models_to_test), label=f"  Processing")
        print()
        
        # Summary
        print(f"{C.BOLD}{C.BRIGHT_MAGENTA}{'='*70}{C.RESET}")
        print(f"{C.BRIGHT_MAGENTA}{C.BOLD}  📊 COMPARISON SUMMARY{C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_MAGENTA}{'='*70}{C.RESET}\n")
        
        # Sort by response length (longer = more detailed usually)
        sorted_results = sorted(results.items(), key=lambda x: len(x[1].split()) if x[1] else 0, reverse=True)
        
        for rank, (model, result) in enumerate(sorted_results, 1):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, f'  {rank}.')
            ft = "🎯" if self.models.get(model, {}).get("finetuned") else "📦"
            words = len(result.split()) if result else 0
            
            # Quality heuristics
            has_steps = any(kw in (result or '').lower() for kw in ['step', '1.', '2.', 'first'])
            has_commands = any(kw in (result or '').lower() for kw in ['`', 'systemctl', 'docker', 'sudo'])
            quality = []
            if has_steps: quality.append(f"{C.GREEN}📋 Steps{C.RESET}")
            if has_commands: quality.append(f"{C.GREEN}💻 Commands{C.RESET}")
            quality_str = ' '.join(quality) if quality else f"{C.DIM}Basic{C.RESET}"
            
            print(f"  {medal} {ft} {C.BOLD}{model}{C.RESET}")
            print(f"     {C.DIM}Words: {words} | Quality: {quality_str}{C.RESET}")
            print(f"     {C.DIM}Preview: {(result or 'N/A')[:100]}...{C.RESET}")
            print()
    
    def chat_mode(self):
        """Interactive chat mode with current model."""
        if not self.active:
            print(f"{C.RED}Select a model first: {C.BOLD}use <number>{C.RESET}")
            return
        
        print(f"\n{C.BOLD}{C.BRIGHT_GREEN}{'='*60}{C.RESET}")
        print(f"{C.BRIGHT_GREEN}  💬 CHAT MODE - {self.active}{C.RESET}")
        print(f"  {C.DIM}Type 'exit' to leave, 'clear' to reset, 'history' to see past{C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_GREEN}{'='*60}{C.RESET}\n")
        
        chat_history = []
        
        while True:
            try:
                user_input = input(f"{C.BRIGHT_CYAN}You › {C.RESET}").strip()
                
                if not user_input:
                    continue
                if user_input.lower() == 'exit':
                    print(f"{C.GREEN}👋 Exiting chat mode{C.RESET}\n")
                    break
                if user_input.lower() == 'clear':
                    os.system('clear')
                    chat_history = []
                    continue
                if user_input.lower() == 'history':
                    for i, (q, a) in enumerate(chat_history, 1):
                        print(f"\n{C.DIM}[{i}] Q: {q[:50]}...{C.RESET}")
                    continue
                
                # Build context from history
                context = ""
                for q, a in chat_history[-3:]:  # Last 3 exchanges
                    context += f"User: {q}\nAssistant: {a}\n"
                
                full_prompt = f"{context}User: {user_input}\nAssistant:"
                
                # Query
                print(f"\n{C.BRIGHT_GREEN}AI › {C.RESET}", end='')
                resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.active,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 300}
                    },
                    timeout=60
                )
                
                if resp.status_code == 200:
                    result = resp.json().get("response", "")
                    typewriter(result, delay=0.01, color=C.WHITE)
                    print()
                    chat_history.append((user_input, result))
                else:
                    print(f"{C.RED}Error: {resp.status_code}{C.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{C.GREEN}👋 Exiting chat mode{C.RESET}\n")
                break
    
    def show_history(self):
        """Display query history."""
        if not self.history:
            print(f"\n{C.DIM}No queries yet.{C.RESET}\n")
            return
        
        print(f"\n{C.BOLD}{'='*70}{C.RESET}")
        print(f"{C.BRIGHT_CYAN}  📜 QUERY HISTORY ({len(self.history)} total){C.RESET}")
        print(f"{C.BOLD}{'='*70}{C.RESET}\n")
        
        for i, entry in enumerate(self.history[-15:], 1):
            ft = "🎯" if self.models.get(entry['model'], {}).get('finetuned') else "📦"
            print(f"  {C.BOLD}[{i}]{C.RESET} {C.DIM}{entry['time']}{C.RESET} | {ft} {C.CYAN}{entry['model']}{C.RESET}")
            print(f"     {C.YELLOW}Q:{C.RESET} {entry['prompt'][:80]}")
            print(f"     {C.GREEN}A:{C.RESET} {entry['response'][:100]}...")
            print(f"     {C.DIM}⏱️ {entry.get('elapsed', '?')}s{C.RESET}")
            print()
    
    def show_help(self):
        """Display help."""
        box(f"""
{C.BOLD}AVAILABLE COMMANDS{C.RESET}

{C.BOLD}Model Selection:{C.RESET}
  {C.CYAN}models, m{C.RESET}          List all models
  {C.CYAN}models ft{C.RESET}         List fine-tuned only
  {C.CYAN}use <n>, u <n>{C.RESET}    Select model by index
  {C.CYAN}use <name>{C.RESET}        Select by name/partial
  {C.CYAN}active, a{C.RESET}         Show active model
  {C.CYAN}fav, f{C.RESET}            Toggle favorite

{C.BOLD}Querying:{C.RESET}
  {C.CYAN}ask "query"{C.RESET}       Query active model
  {C.CYAN}ask "q" model{C.RESET}     Query specific model
  {C.CYAN}compare "q"{C.RESET}       Compare all fine-tuned
  {C.CYAN}compare "q" 5{C.RESET}     Compare top 5 models
  {C.CYAN}chat{C.RESET}              Interactive chat mode

{C.BOLD}Session:{C.RESET}
  {C.CYAN}history, h{C.RESET}        Show query history
  {C.CYAN}save, s{C.RESET}           Save session to file
  {C.CYAN}stats{C.RESET}             Show session statistics
  {C.CYAN}clear{C.RESET}             Clear screen
  {C.CYAN}help{C.RESET}              Show this help
  {C.CYAN}quit, q{C.RESET}           Exit explorer
        """, color=C.CYAN)
    
    def show_stats(self):
        """Show session statistics."""
        duration = datetime.now() - self.session_start
        hours = duration.total_seconds() / 3600
        
        print(f"\n{C.BOLD}{'='*50}{C.RESET}")
        print(f"{C.BRIGHT_CYAN}  📊 SESSION STATISTICS{C.RESET}")
        print(f"{C.BOLD}{'='*50}{C.RESET}")
        print(f"  Duration: {C.BOLD}{hours:.1f} hours{C.RESET}")
        print(f"  Queries: {C.BOLD}{self.query_count}{C.RESET}")
        print(f"  Models: {C.BOLD}{len(self.models)}{C.RESET} ({sum(1 for v in self.models.values() if v['finetuned'])} fine-tuned)")
        print(f"  Favorites: {C.BOLD}{len(self.favorites)}{C.RESET}")
        print(f"  Active: {C.BOLD}{self.active or 'None'}{C.RESET}")
        
        if self.history:
            models_used = set(h['model'] for h in self.history)
            avg_words = sum(len(h['response'].split()) for h in self.history) / len(self.history)
            print(f"  Models used: {C.BOLD}{len(models_used)}{C.RESET}")
            print(f"  Avg response: {C.BOLD}{avg_words:.0f} words{C.RESET}")
        
        print(f"{C.BOLD}{'='*50}{C.RESET}\n")
    
    def save_session(self, filename: str = None):
        """Save session to JSON file."""
        if not filename:
            filename = f"aegis_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "session_start": self.session_start.isoformat(),
            "saved_at": datetime.now().isoformat(),
            "active_model": self.active,
            "query_count": self.query_count,
            "favorites": list(self.favorites),
            "history": self.history
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n{C.GREEN}✅ Session saved to: {C.BOLD}{filename}{C.RESET}")
        print(f"   {C.DIM}Queries: {len(self.history)} | Size: {os.path.getsize(filename)} bytes{C.RESET}\n")


# ═══════════════════════════════════════════════════════
# MAIN INTERACTIVE LOOP
# ═══════════════════════════════════════════════════════

def main():
    checker = PremiumModelChecker()
    checker.show_banner()
    checker.list_models()
    
    # Auto-select first fine-tuned model
    finetuned = [k for k, v in checker.models.items() if v["finetuned"]]
    if finetuned:
        checker.select_model(finetuned[0])
    
    print(f"{C.DIM}Type 'help' for commands, 'ask \"query\"' to question models{C.RESET}\n")
    
    while True:
        try:
            cmd = input(f"{C.BRIGHT_CYAN}➤ {C.RESET}").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            # Navigation
            if action in ['quit', 'exit', 'q']:
                checker.show_stats()
                print(f"{C.GREEN}👋 Goodbye!{C.RESET}\n")
                break
            
            elif action in ['models', 'm']:
                checker.list_models(finetuned_only=(args == 'ft'))
            
            elif action in ['use', 'u']:
                if args:
                    # Try as integer first
                    if args.isdigit():
                        checker.select_model(int(args))
                    else:
                        checker.select_model(args)
                else:
                    checker.show_active()
            
            elif action in ['active', 'a']:
                checker.show_active()
            
            elif action in ['fav', 'f']:
                checker.toggle_favorite(args if args else None)
            
            # Querying
            elif action == 'ask':
                if args:
                    # Check if format is: ask "query" model_name
                    if '"' in args:
                        match = re.match(r'"(.+)"\s*(.*)', args)
                        if match:
                            prompt = match.group(1)
                            model = match.group(2).strip() or None
                            checker.ask(prompt, model)
                        else:
                            checker.ask(args)
                    else:
                        checker.ask(args)
                else:
                    print(f"{C.YELLOW}Usage: ask \"your question\"{C.RESET}")
            
            elif action == 'compare':
                if args:
                    # Check if format is: compare "query" limit
                    if '"' in args:
                        match = re.match(r'"(.+)"\s*(\d*)', args)
                        if match:
                            prompt = match.group(1)
                            limit = int(match.group(2)) if match.group(2) else 3
                            checker.compare(prompt, limit)
                        else:
                            checker.compare(args)
                    else:
                        checker.compare(args)
                else:
                    print(f"{C.YELLOW}Usage: compare \"your question\"{C.RESET}")
            
            elif action == 'chat':
                checker.chat_mode()
            
            # Session
            elif action in ['history', 'h']:
                checker.show_history()
            
            elif action in ['save', 's']:
                checker.save_session(args if args else None)
            
            elif action == 'stats':
                checker.show_stats()
            
            elif action in ['help', '?']:
                checker.show_help()
            
            elif action == 'clear':
                os.system('clear' if os.name != 'nt' else 'cls')
                checker.show_banner()
            
            else:
                # Try as model selection shortcut
                if args:
                    print(f"{C.YELLOW}Unknown command. Type 'help' for commands.{C.RESET}")
                else:
                    # Single word - try as model name/index
                    if action.isdigit():
                        checker.select_model(int(action))
                    else:
                        checker.select_model(action)
                    
        except KeyboardInterrupt:
            print(f"\n{C.GREEN}👋 Goodbye!{C.RESET}\n")
            break
        except EOFError:
            break


# ═══════════════════════════════════════════════════════
# JUPYTER-FRIENDLY EXPORT
# ═══════════════════════════════════════════════════════

# If in Jupyter, create a quick-access instance
try:
    __IPYTHON__
    checker = PremiumModelChecker()
    checker.show_banner()
    checker.list_models()
    
    # Aliases for Jupyter
    models = checker.list_models
    use = checker.select_model
    ask = checker.ask
    compare = checker.compare
    chat = checker.chat_mode
    history = checker.show_history
    
    print(f"{C.GREEN}✅ Premium Model Checker ready!{C.RESET}")
    print(f"{C.DIM}Try: ask(\"What causes nginx crashes?\"){C.RESET}\n")
except NameError:
    # Running as script
    if __name__ == "__main__":
        main()