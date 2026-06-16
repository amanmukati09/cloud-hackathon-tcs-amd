#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🧠  A E G I S   A I  —  U L T R A   E X P L O R E R              ║
║                                                                              ║
║     Premium AI Model Workbench • Testing • Comparison • Analytics            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess, json, requests, re, os, sys, time, textwrap, random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import hashlib

# ═══════════════════════════════════════════════════════════════════════════
# THEME SYSTEM — DARK / LIGHT / CUSTOM
# ═══════════════════════════════════════════════════════════════════════════

class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    CYBERPUNK = "cyberpunk"
    OCEAN = "ocean"
    FOREST = "forest"
    SUNSET = "sunset"

@dataclass
class Theme:
    """Complete theme definition."""
    name: str
    bg: str
    surface: str
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    text: str
    text_dim: str
    text_bright: str
    border: str
    gradient_start: str
    gradient_end: str

THEMES = {
    ThemeMode.DARK: Theme(
        name="Dark Mode", bg="#0a0a0f", surface="#141420", primary="#6366f1",
        secondary="#818cf8", accent="#22d3ee", success="#10b981", warning="#f59e0b",
        error="#ef4444", text="#e2e8f0", text_dim="#64748b", text_bright="#f8fafc",
        border="#1e293b", gradient_start="#6366f1", gradient_end="#a855f7"
    ),
    ThemeMode.LIGHT: Theme(
        name="Light Mode", bg="#f8fafc", surface="#ffffff", primary="#4f46e5",
        secondary="#6366f1", accent="#0891b2", success="#059669", warning="#d97706",
        error="#dc2626", text="#1e293b", text_dim="#94a3b8", text_bright="#0f172a",
        border="#e2e8f0", gradient_start="#4f46e5", gradient_end="#7c3aed"
    ),
    ThemeMode.CYBERPUNK: Theme(
        name="CyberPunk", bg="#0d0221", surface="#150533", primary="#ff00ff",
        secondary="#00ffff", accent="#ffff00", success="#00ff41", warning="#ff6600",
        error="#ff0000", text="#c0c0c0", text_dim="#555555", text_bright="#ffffff",
        border="#330066", gradient_start="#ff00ff", gradient_end="#00ffff"
    ),
    ThemeMode.OCEAN: Theme(
        name="Ocean Depths", bg="#0c1929", surface="#122738", primary="#0077b6",
        secondary="#00b4d8", accent="#90e0ef", success="#06d6a0", warning="#ffd166",
        error="#ef476f", text="#caf0f8", text_dim="#6c8ea0", text_bright="#ffffff",
        border="#1a3a4a", gradient_start="#0077b6", gradient_end="#00b4d8"
    ),
    ThemeMode.FOREST: Theme(
        name="Forest", bg="#0a1a0f", surface="#132a18", primary="#2d6a4f",
        secondary="#40916c", accent="#95d5b2", success="#52b788", warning="#ffb703",
        error="#e63946", text="#d8f3dc", text_dim="#6b9080", text_bright="#ffffff",
        border="#1b3a24", gradient_start="#2d6a4f", gradient_end="#40916c"
    ),
    ThemeMode.SUNSET: Theme(
        name="Sunset", bg="#1a0a0a", surface="#2a1515", primary="#ff6b35",
        secondary="#f7c59f", accent="#ffd700", success="#2ecc71", warning="#f39c12",
        error="#c0392b", text="#fdebd0", text_dim="#8b7355", text_bright="#ffffff",
        border="#3d2020", gradient_start="#ff6b35", gradient_end="#f7c59f"
    ),
}

# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED COLOR / ANSI RENDERER
# ═══════════════════════════════════════════════════════════════════════════

class Ansi:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKE = '\033[9m'

    FG = lambda n: f'\033[38;5;{n}m'
    BG = lambda n: f'\033[48;5;{n}m'
    RGB_FG = lambda r, g, b: f'\033[38;2;{r};{g};{b}m'
    RGB_BG = lambda r, g, b: f'\033[48;2;{r};{g};{b}m'
    GRADIENT_START = '\033[38;5;'
    TRUE_RESET = '\033[0m'

def rgb_to_ansi(r, g, b):
    """Approximate RGB to 256 ANSI."""
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return int(round((r - 8) / 10)) + 232
    return 16 + (36 * int(round(r / 255 * 5))) + (6 * int(round(g / 255 * 5))) + int(round(b / 255 * 5))

def gradient_text(text: str, start_hex: str, end_hex: str) -> str:
    """Apply color gradient to each character of text."""
    sr, sg, sb = int(start_hex[1:3], 16), int(start_hex[3:5], 16), int(start_hex[5:7], 16)
    er, eg, eb = int(end_hex[1:3], 16), int(end_hex[3:5], 16), int(end_hex[5:7], 16)
    result = ""
    n = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        r = int(sr + (er - sr) * i / n)
        g = int(sg + (eg - sg) * i / n)
        b = int(sb + (eb - sb) * i / n)
        result += Ansi.RGB_FG(r, g, b) + ch
    return result + Ansi.RESET

# ═══════════════════════════════════════════════════════════════════════════
# UI WIDGETS
# ═══════════════════════════════════════════════════════════════════════════

class Widgets:
    @staticmethod
    def box(content: str, title: str = "", width: int = 70, border_color: str = "#6366f1"):
        print(f"{Ansi.RGB_FG(*Widgets._hex(border_color))}{Ansi.BOLD}╭{'─' * (width-2)}╮{Ansi.RESET}")
        if title:
            print(f"{Ansi.RGB_FG(*Widgets._hex(border_color))}│{Ansi.RESET} {Ansi.BOLD}{title}{Ansi.RESET}" + " " * (width - len(title) - 4) + f"{Ansi.RGB_FG(*Widgets._hex(border_color))}│{Ansi.RESET}")
            print(f"{Ansi.RGB_FG(*Widgets._hex(border_color))}├{'─' * (width-2)}┤{Ansi.RESET}")
        for line in content.split('\n'):
            print(f"{Ansi.RGB_FG(*Widgets._hex(border_color))}│{Ansi.RESET} {line}" + " " * max(0, width - len(line) - 3) + f"{Ansi.RGB_FG(*Widgets._hex(border_color))}│{Ansi.RESET}")
        print(f"{Ansi.RGB_FG(*Widgets._hex(border_color))}╰{'─' * (width-2)}╯{Ansi.RESET}")

    @staticmethod
    def panel(content: str, variant: str = "info"):
        colors = {"info": "#6366f1", "success": "#10b981", "warning": "#f59e0b", "error": "#ef4444"}
        c = Widgets._hex(colors.get(variant, "#6366f1"))
        print(f"{Ansi.RGB_BG(*c)}{Ansi.RGB_FG(255,255,255)} {content} {Ansi.RESET}")

    @staticmethod
    def spinner(message: str = "Processing", duration: float = 2.0):
        frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        end = time.time() + duration
        i = 0
        while time.time() < end:
            sys.stdout.write(f'\r{Ansi.RGB_FG(99,102,241)}{frames[i%10]}{Ansi.RESET} {message}...')
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write('\r' + ' '*60 + '\r')

    @staticmethod
    def progress(current, total, width=50, label="", color="#6366f1"):
        pct = min(current / max(total, 1), 1.0)
        filled = int(width * pct)
        c = Widgets._hex(color)
        bar = f"{Ansi.RGB_BG(*c)}{' ' * filled}{Ansi.RESET}{Ansi.DIM}{'░' * (width - filled)}{Ansi.RESET}"
        sys.stdout.write(f'\r{label} {bar} {pct*100:.0f}%')
        sys.stdout.flush()
        if current >= total:
            sys.stdout.write('\n')

    @staticmethod
    def divider(char: str = "─", color: str = "#6366f1"):
        print(f"{Ansi.RGB_FG(*Widgets._hex(color))}{Ansi.DIM}{char * 70}{Ansi.RESET}")

    @staticmethod
    def table(headers: list, rows: list, col_widths: list = None):
        if not col_widths:
            col_widths = [max(len(str(r[i])) if i < len(r) else 0 for r in [headers] + rows) + 2 for i in range(len(headers))]
        sep = f"{Ansi.DIM}├{'┼'.join('─'*w for w in col_widths)}┤{Ansi.RESET}"
        top = f"{Ansi.DIM}╭{'┬'.join('─'*w for w in col_widths)}╮{Ansi.RESET}"
        bot = f"{Ansi.DIM}╰{'┴'.join('─'*w for w in col_widths)}╯{Ansi.RESET}"
        print(top)
        print(f"{Ansi.DIM}│{Ansi.RESET}{Ansi.BOLD}", end="")
        for i, h in enumerate(headers):
            print(f"{h:<{col_widths[i]}}", end="")
        print(f"{Ansi.RESET}{Ansi.DIM}│{Ansi.RESET}")
        print(sep)
        for row in rows:
            print(f"{Ansi.DIM}│{Ansi.RESET}", end="")
            for i, cell in enumerate(row):
                print(f"{str(cell):<{col_widths[i]}}", end="")
            print(f"{Ansi.DIM}│{Ansi.RESET}")
        print(bot)

    @staticmethod
    def _hex(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

w = Widgets

# ═══════════════════════════════════════════════════════════════════════════
# CORE ENGINE — ULTRA MODEL CHECKER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ModelInfo:
    name: str
    index: int
    is_finetuned: bool
    size: str
    modified: str
    response_times: List[float] = field(default_factory=list)
    quality_scores: List[float] = field(default_factory=list)
    times_used: int = 0

@dataclass
class QueryResult:
    model: str
    prompt: str
    response: str
    elapsed: float
    timestamp: str
    tokens: int
    quality_score: float

class UltraModelChecker:
    def __init__(self, theme: ThemeMode = ThemeMode.DARK):
        self.theme = THEMES[theme]
        self.models: Dict[str, ModelInfo] = {}
        self.active: Optional[str] = None
        self.history: List[QueryResult] = []
        self.favorites: set = set()
        self.benchmarks: Dict[str, dict] = {}
        self.aliases: Dict[str, str] = {}
        self.session_start = datetime.now()
        self.query_count = 0
        self.total_tokens = 0
        self._discover()
        self._load_session()

    def _discover(self):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            name = parts[0].replace(':latest', '')
                            self.models[name] = ModelInfo(
                                name=name, index=len(self.models)+1,
                                is_finetuned='aegis' in name.lower() or 'finetuned' in name.lower(),
                                size=parts[2] if len(parts)>2 else "?", 
                                modified=' '.join(parts[3:]) if len(parts)>3 else "?"
                            )
        except Exception as e:
            print(f"{Ansi.RGB_FG(239,68,68)}⚠️ Ollama: {e}{Ansi.RESET}")

    def _load_session(self):
        """Resume previous session if exists."""
        try:
            if os.path.exists('.aegis_session.json'):
                with open('.aegis_session.json') as f:
                    data = json.load(f)
                    self.favorites = set(data.get('favorites', []))
                    self.aliases = data.get('aliases', {})
        except: pass

    def _save_session(self):
        with open('.aegis_session.json', 'w') as f:
            json.dump({'favorites': list(self.favorites), 'aliases': self.aliases}, f)

    # ═══════════════════════════════════════════════════════════════════
    # DISPLAY — RICH TERMINAL UI
    # ═══════════════════════════════════════════════════════════════════

    def home(self):
        os.system('clear' if os.name != 'nt' else 'cls')
        t = self.theme
        print(gradient_text("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║              █████╗ ███████╗ ██████╗ ██╗███████╗ █████╗ ██╗              ║
║             ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝██╔══██╗██║              ║
║             ███████║█████╗  ██║  ███╗██║███████╗███████║██║              ║
║             ██╔══██║██╔══╝  ██║   ██║██║╚════██║██╔══██║██║              ║
║             ██║  ██║███████╗╚██████╔╝██║███████║██║  ██║██║              ║
║             ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝              ║
║                                                                          ║
║                   🧠  U L T R A   E X P L O R E R                        ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """, t.gradient_start, t.gradient_end))
        print(f"{Ansi.DIM}  Theme: {t.name} • Models: {len(self.models)} • Session: {self.session_start.strftime('%H:%M')}{Ansi.RESET}\n")

    def dashboard(self):
        """Rich dashboard view."""
        self.home()
        t = self.theme
        ft = sum(1 for m in self.models.values() if m.is_finetuned)
        active_info = self.models.get(self.active or '', None)

        # Stats row
        print(f"  {Ansi.RGB_FG(*w._hex(t.primary))}{Ansi.BOLD}📊 DASHBOARD{Ansi.RESET}\n")
        panels = [
            ("Total Models", str(len(self.models))),
            ("Fine-Tuned", str(ft)),
            ("Queries Today", str(self.query_count)),
            ("Total Tokens", f"{self.total_tokens:,}"),
            ("Avg Response", f"{self._avg_response_time():.1f}s" if self.history else "N/A"),
            ("Active Model", self.active or "None"),
        ]
        for label, val in panels:
            print(f"  {Ansi.DIM}┌{'─'*30}┐{Ansi.RESET}")
            print(f"  {Ansi.DIM}│{Ansi.RESET} {Ansi.BOLD}{label:<15}{Ansi.RESET}{val:>14} {Ansi.DIM}│{Ansi.RESET}")
        print(f"  {Ansi.DIM}└{'─'*30}┘{Ansi.RESET}\n")

        # Quick model list
        print(f"  {Ansi.RGB_FG(*w._hex(t.secondary))}{Ansi.BOLD}🎯 MODELS{Ansi.RESET}")
        for name, info in sorted(self.models.items(), key=lambda x: (not x[1].is_finetuned, x[0])):
            badge = "🎯" if info.is_finetuned else "📦"
            active = f"{Ansi.RGB_FG(250,204,21)} ←{Ansi.RESET}" if name == self.active else ""
            fav = f"{Ansi.RGB_FG(250,204,21)}★{Ansi.RESET} " if name in self.favorites else "  "
            times = f"{Ansi.DIM}({info.times_used}x){Ansi.RESET}" if info.times_used else ""
            print(f"  {fav}[{info.index:>2}] {badge} {name:<35} {active} {times}")

    # ═══════════════════════════════════════════════════════════════════
    # MODEL SELECTION
    # ═══════════════════════════════════════════════════════════════════

    def select(self, identifier: str):
        if not identifier:
            self.dashboard()
            return
        # Resolve aliases
        identifier = self.aliases.get(identifier, identifier)
        try:
            idx = int(identifier)
            for name, info in self.models.items():
                if info.index == idx:
                    self.active = name; self._on_select(name); return
        except ValueError:
            if identifier in self.models:
                self.active = identifier; self._on_select(identifier); return
            # Fuzzy search
            matches = [(self._fuzzy_score(identifier, n), n) for n in self.models]
            matches = [(s,n) for s,n in matches if s > 0]
            matches.sort(key=lambda x: x[0], reverse=True)
            if len(matches) == 1:
                self.active = matches[0][1]; self._on_select(matches[0][1])
            elif matches:
                print(f"\n{Ansi.RGB_FG(250,204,21)}Multiple matches:{Ansi.RESET}")
                for i, (s, n) in enumerate(matches[:5], 1):
                    print(f"  {i}. {n} ({s:.0f}%)")
                try:
                    ch = input(f"\n  Select › ").strip()
                    if ch.isdigit() and 1 <= int(ch) <= len(matches):
                        self.active = matches[int(ch)-1][1]; self._on_select(matches[int(ch)-1][1])
                except: pass

    def _on_select(self, name):
        info = self.models[name]
        info.times_used += 1
        badge = "🎯 Fine-Tuned" if info.is_finetuned else "📦 Base"
        w.box(f"Model: {name}\nType: {badge}\nSize: {info.size}\nModified: {info.modified}", title="✅ ACTIVE MODEL")

    def _fuzzy_score(self, query, target):
        q, t = query.lower(), target.lower()
        if q == t: return 100
        if q in t: return 80
        if t in q: return 60
        score = sum(1 for c in q if c in t) / max(len(q),1) * 40
        score += sum(1 for i in range(min(len(q), len(t))) if q[i] == t[i]) * 5
        return score

    def alias(self, short: str, full: str):
        self.aliases[short] = full
        self._save_session()
        print(f"{Ansi.RGB_FG(16,185,129)}✅ Alias: {short} → {full}{Ansi.RESET}")

    # ═══════════════════════════════════════════════════════════════════
    # QUERY ENGINE
    # ═══════════════════════════════════════════════════════════════════

    def ask(self, prompt: str, model: str = None, verbose: bool = True):
        target = model or self.active
        if not target:
            w.panel("No model selected! Use: select <number>", "error"); return

        self.query_count += 1
        if verbose:
            w.divider()
            print(f"  {Ansi.BOLD}🤖 {target}{Ansi.RESET}  {Ansi.DIM}Query #{self.query_count}{Ansi.RESET}")
            print(f"  {Ansi.RGB_FG(*w._hex(self.theme.accent))}📝 {prompt}{Ansi.RESET}")
            w.spinner("Thinking", 0.5)

        try:
            start = time.time()
            resp = requests.post("http://localhost:11434/api/generate", json={
                "model": target, "prompt": f"[Expert SRE]\n{prompt}",
                "stream": False, "options": {"temperature": 0.7, "num_predict": 600}
            }, timeout=120)
            elapsed = time.time() - start

            if resp.status_code == 200:
                text = resp.json().get("response", "")
                tokens = len(text.split())
                self.total_tokens += tokens
                quality = self._rate_quality(text)
                result = QueryResult(target, prompt, text, elapsed, datetime.now().strftime("%H:%M:%S"), tokens, quality)
                self.history.append(result)
                self.models[target].response_times.append(elapsed)
                self.models[target].quality_scores.append(quality)
                self._render_response(text, elapsed, tokens, quality)
                return text
        except Exception as e:
            w.panel(f"Error: {e}", "error")

    def _rate_quality(self, text: str) -> float:
        """Heuristic quality scoring."""
        score = 5.0
        if len(text) < 50: score -= 2
        if len(text) > 200: score += 1
        if any(kw in text.lower() for kw in ['step', '1.', 'first', 'next']): score += 1
        if any(kw in text.lower() for kw in ['`', 'systemctl', 'docker', 'sudo']): score += 2
        if any(kw in text.lower() for kw in ['root cause', 'because', 'therefore']): score += 1
        return max(1, min(10, score))

    def _render_response(self, text, elapsed, tokens, quality):
        q_color = "#10b981" if quality >= 7 else "#f59e0b" if quality >= 4 else "#ef4444"
        print(f"\n{Ansi.RGB_FG(*w._hex(q_color))}{'─'*70}{Ansi.RESET}")
        for line in text.split('\n'):
            line = line.strip()
            if not line: print(); continue
            c = self._line_color(line)
            print(f"  {Ansi.RGB_FG(*w._hex(c))}{line}{Ansi.RESET}")
        print(f"{Ansi.RGB_FG(*w._hex(q_color))}{'─'*70}{Ansi.RESET}")
        print(f"  {Ansi.DIM}⏱️ {elapsed:.1f}s • 📝 {tokens} tokens • ⭐ {quality:.1f}/10{Ansi.RESET}\n")

    def _line_color(self, line: str) -> str:
        l = line.lower()
        if any(k in l for k in ['step', '1.', '2.', '3.', '•']): return self.theme.warning
        if any(k in l for k in ['`', 'command', 'systemctl', 'docker', 'sudo']): return self.theme.success
        if any(k in l for k in ['error', 'critical', 'fail', 'crash']): return self.theme.error
        if any(k in l for k in ['note', 'tip', 'recommend']): return self.theme.accent
        return self.theme.text

    def _avg_response_time(self):
        return sum(h.elapsed for h in self.history) / len(self.history) if self.history else 0

    # ═══════════════════════════════════════════════════════════════════
    # COMPARISON ARENA
    # ═══════════════════════════════════════════════════════════════════

    def compare(self, prompt: str, limit: int = 3):
        ft = [(k, v) for k, v in self.models.items() if v.is_finetuned][:limit]
        models = [m[0] for m in ft]
        if "llama3" in self.models and "llama3" not in models:
            models.append("llama3")
        if len(models) < 2:
            w.panel("Need at least 2 models to compare", "warning"); return

        print(f"\n{gradient_text('  🏟️  COMPARISON ARENA', self.theme.gradient_start, self.theme.gradient_end)}")
        print(f"  {Ansi.DIM}Prompt: {prompt}{Ansi.RESET}\n")
        results = {}
        for i, model in enumerate(models):
            w.progress(i, len(models), label=f"  {model:<30}", color=self.theme.primary)
            results[model] = self.ask(prompt, model, verbose=False)
        w.progress(len(models), len(models), label="  Complete", color=self.theme.success)
        print(f"\n{Ansi.BOLD}📊 RANKING{Ansi.RESET}")
        ranked = sorted(results.items(), key=lambda x: len(x[1].split()) if x[1] else 0, reverse=True)
        for rank, (model, resp) in enumerate(ranked, 1):
            words = len(resp.split()) if resp else 0
            medal = ['🥇','🥈','🥉'][rank-1] if rank <= 3 else f'{rank}.'
            ft = "🎯" if self.models[model].is_finetuned else "📦"
            print(f"  {medal} {ft} {model}: {words} words")
        print()

    # ═══════════════════════════════════════════════════════════════════
    # BENCHMARK SUITE
    # ═══════════════════════════════════════════════════════════════════

    BENCHMARK_PROMPTS = [
        ("Root Cause", "Analyze root cause of: [ERROR] Connection refused on port 5432"),
        ("Remediation", "Provide step-by-step fix for nginx 502 Bad Gateway"),
        ("Prevention", "How to prevent memory leaks in Node.js production?"),
        ("Scalability", "Database connection pool exhausted. Solutions?"),
        ("Security", "Suspicious login attempts detected. Immediate actions?"),
    ]

    def benchmark(self, models: list = None):
        models = models or [k for k, v in self.models.items() if v.is_finetuned][:2]
        if not models:
            w.panel("No fine-tuned models", "error"); return
        print(f"\n{Ansi.BOLD}⏱️  BENCHMARK SUITE ({len(self.BENCHMARK_PROMPTS)} tests){Ansi.RESET}\n")
        results = defaultdict(list)
        for cat, prompt in self.BENCHMARK_PROMPTS:
            print(f"  {Ansi.BOLD}{cat}{Ansi.RESET}")
            for model in models:
                w.spinner(f"  {model}", 0.3)
                start = time.time()
                resp = requests.post("http://localhost:11434/api/generate", json={
                    "model": model, "prompt": prompt, "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 200}
                }, timeout=60)
                elapsed = time.time() - start
                text = resp.json().get("response", "") if resp.status_code == 200 else ""
                quality = self._rate_quality(text)
                results[model].append({"category": cat, "time": elapsed, "quality": quality, "words": len(text.split())})
                print(f"    {model}: {elapsed:.1f}s • ⭐{quality:.1f} • {len(text.split())} words")
        # Summary table
        print(f"\n{Ansi.BOLD}📊 BENCHMARK SUMMARY{Ansi.RESET}")
        w.table(["Model", "Avg Time", "Avg Quality", "Avg Words", "Score"],
                [[m, f"{sum(r['time']for r in rs)/len(rs):.1f}s",
                  f"{sum(r['quality']for r in rs)/len(rs):.1f}",
                  f"{sum(r['words']for r in rs)/len(rs):.0f}",
                  f"{sum(r['quality']for r in rs)/sum(r['time']for r in rs)*10:.0f}"]
                 for m, rs in results.items()])

    # ═══════════════════════════════════════════════════════════════════
    # CHAT MODE
    # ═══════════════════════════════════════════════════════════════════

    def chat(self):
        if not self.active:
            w.panel("Select a model first", "error"); return
        print(f"\n{Ansi.BOLD}💬 CHAT — {self.active}{Ansi.RESET}  {Ansi.DIM}/exit /clear /history{Ansi.RESET}\n")
        ctx = []
        while True:
            try:
                msg = input(f"{Ansi.RGB_FG(*w._hex(self.theme.accent))}You › {Ansi.RESET}").strip()
                if not msg: continue
                if msg == '/exit': break
                if msg == '/clear': ctx = []; os.system('clear'); continue
                if msg == '/history':
                    for i, (q, a) in enumerate(ctx, 1):
                        print(f"  {Ansi.DIM}{i}. Q: {q[:50]}...{Ansi.RESET}")
                    continue
                ctx.append((msg, ""))
                full = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in ctx[-4:]])
                print(f"{Ansi.RGB_FG(*w._hex(self.theme.success))}AI › {Ansi.RESET}", end='', flush=True)
                resp = requests.post("http://localhost:11434/api/generate", json={
                    "model": self.active, "prompt": f"{full}\nUser: {msg}\nAssistant:",
                    "stream": False, "options": {"temperature": 0.7, "num_predict": 400}
                }, timeout=90)
                if resp.status_code == 200:
                    text = resp.json().get("response", "")
                    for ch in text:
                        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(0.008)
                    print()
                    ctx[-1] = (msg, text)
            except KeyboardInterrupt: break

    # ═══════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════

    def theme_switch(self, name: str):
        try:
            mode = ThemeMode[name.upper()]
            self.theme = THEMES[mode]
            self.home()
            print(f"{Ansi.RGB_FG(16,185,129)}✅ Theme: {self.theme.name}{Ansi.RESET}")
        except KeyError:
            print(f"{Ansi.RGB_FG(239,68,68)}Available: {[t.value for t in ThemeMode]}{Ansi.RESET}")

    def save(self, filename: str = None):
        filename = filename or f"aegis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {"session": self.session_start.isoformat(), "queries": self.query_count,
                "history": [{"model": h.model, "prompt": h.prompt, "response": h.response,
                             "elapsed": h.elapsed, "quality": h.quality_score} for h in self.history]}
        with open(filename, 'w') as f: json.dump(data, f, indent=2, default=str)
        w.panel(f"Saved: {filename} ({len(self.history)} queries)", "success")

    def export_prompt(self, filename: str = "prompts.md"):
        with open(filename, 'w') as f:
            f.write("# AegisAI Prompt Library\n\n")
            for i, h in enumerate(self.history, 1):
                f.write(f"## Query {i}: {h.model}\n")
                f.write(f"**Prompt:** {h.prompt}\n\n")
                f.write(f"**Response:** {h.response[:500]}\n\n---\n")
        w.panel(f"Exported to {filename}", "success")

    def show_help(self):
        w.box("""
  select <n/name>    Select model
  ask <prompt>       Query model
  compare <prompt>   Compare all models
  benchmark          Run benchmark suite
  chat               Interactive chat
  alias <a> <b>      Create alias
  theme <name>       Switch theme
  dashboard          Show dashboard
  history            Query history
  save               Save session
  export             Export prompts
  stats              Statistics
  help               This help
        """.strip(), title="📖 COMMANDS", border_color=self.theme.accent)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SHELL
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--theme', default='dark', choices=[t.value for t in ThemeMode])
    parser.add_argument('--model', type=str, help='Auto-select model')
    parser.add_argument('--ask', type=str, help='Run single query and exit')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark')
    args = parser.parse_args()

    try: theme = ThemeMode(args.theme)
    except: theme = ThemeMode.DARK

    checker = UltraModelChecker(theme)
    checker.home()

    if args.model:
        checker.select(args.model)
    elif checker.models:
        ft = [k for k,v in checker.models.items() if v.is_finetuned]
        if ft: checker.select(ft[0])
        else: checker.select(list(checker.models.keys())[0])

    if args.ask:
        checker.ask(args.ask)
        return

    if args.benchmark:
        checker.benchmark()
        return

    checker.dashboard()
    print(f"\n{Ansi.DIM}Type 'help' for commands | 'quit' to exit{Ansi.RESET}\n")

    while True:
        try:
            cmd = input(f"{Ansi.RGB_FG(99,102,241)}{Ansi.BOLD}◆{Ansi.RESET} ").strip()
            if not cmd: continue
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            args_str = parts[1] if len(parts) > 1 else ""

            if action in ['quit', 'exit', 'q']: break
            elif action in ['dashboard', 'd', 'home']: checker.dashboard()
            elif action in ['select', 's', 'use', 'u']: checker.select(args_str)
            elif action == 'alias': 
                a = args_str.split()
                if len(a) >= 2: checker.alias(a[0], ' '.join(a[1:]))
            elif action == 'ask':
                m = None
                prompt = args_str
                if ' -m ' in args_str:
                    parts2 = args_str.split(' -m ')
                    prompt = parts2[0]
                    m = parts2[1].strip()
                checker.ask(prompt, m)
            elif action == 'compare': checker.compare(args_str, limit=3)
            elif action == 'benchmark': checker.benchmark()
            elif action == 'chat': checker.chat()
            elif action == 'theme':
                checker.theme_switch(args_str.upper())
                checker.dashboard()
            elif action in ['history', 'h']:
                if checker.history:
                    w.table(["#", "Model", "Prompt", "Time", "Quality"],
                            [[i, h.model, h.prompt[:40], f"{h.elapsed:.1f}s", f"⭐{h.quality_score:.1f}"]
                             for i, h in enumerate(checker.history[-20:], 1)])
            elif action in ['save', 'export']: checker.save(args_str if args_str else None)
            elif action == 'export-prompts': checker.export_prompt()
            elif action == 'stats':
                ft = sum(1 for m in checker.models.values() if m.is_finetuned)
                w.box(f"Models: {len(checker.models)} ({ft} FT)\nQueries: {checker.query_count}\n"
                      f"Avg Response: {checker._avg_response_time():.1f}s\n"
                      f"Tokens: {checker.total_tokens:,}\n"
                      f"Favorites: {len(checker.favorites)}\n"
                      f"Active: {checker.active or 'None'}", title="📊 STATISTICS")
            elif action in ['help', '?']: checker.show_help()
            else: checker.select(cmd)  # Try as model selection
        except KeyboardInterrupt: break

    print(f"\n{Ansi.RGB_FG(16,185,129)}👋 Goodbye!{Ansi.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════
# JUPYTER MAGIC
# ═══════════════════════════════════════════════════════════════════════════

try:
    __IPYTHON__
    _checker = UltraModelChecker(ThemeMode.DARK)
    _checker.home()
    _checker.dashboard()
    # Quick functions
    models = _checker.dashboard
    select = _checker.select
    ask = _checker.ask
    compare = _checker.compare
    benchmark = _checker.benchmark
    chat = _checker.chat
    print(f"{Ansi.RGB_FG(16,185,129)}✅ Ready! Try: ask('your question'){Ansi.RESET}\n")
except NameError:
    if __name__ == "__main__":
        main()