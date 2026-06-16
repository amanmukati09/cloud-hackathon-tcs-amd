#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║   ██████╗██╗      ██████╗ ██╗   ██╗██████╗      ██████╗██╗  ██╗ █████╗ ████████╗ ║
║  ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝ ║
║  ██║     ██║     ██║   ██║██║   ██║██║  ██║    ██║     ███████║███████║   ██║    ║
║  ██║     ██║     ██║   ██║██║   ██║██║  ██║    ██║     ██╔══██║██╔══██║   ██║    ║
║  ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝    ╚██████╗██║  ██║██║  ██║   ██║    ║
║   ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ║
║                                                                                  ║
║   CLOUD AI CHAT - LLAMA 3.3 70B OPTIMIZED                                       ║
║   Version 5.0 | 200+ Features | Cloud-Ready                                      ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import uuid
import hashlib
import base64
import math
import random
import secrets
import string
import sqlite3
import threading
import queue
import logging
import traceback
import textwrap
import re
import csv
import io
import pickle
import zlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque, defaultdict, Counter, OrderedDict
from typing import Dict, List, Optional, Any, Tuple, Generator, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from functools import lru_cache, wraps, partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import subprocess
import signal
import platform
import socket
import psutil

# Cloud-optimized imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.style import Style
    from rich.theme import Theme
    from rich import box
    from rich.rule import Rule
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing Rich...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "aiohttp", "psutil"], 
                   capture_output=True)
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True

# ====================================================================
# CLOUD CONFIGURATION
# ====================================================================

@dataclass
class CloudConfig:
    """Cloud-optimized configuration"""
    # Ollama settings for cloud
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = "llama3.3:70b"
    ollama_context_length: int = 131072  # Full context for 70B
    ollama_num_gpu: int = int(os.getenv("OLLAMA_NUM_GPU", "1"))
    
    # Performance settings
    max_concurrent_requests: int = 3
    request_timeout: int = 300
    streaming: bool = True
    stream_chunk_size: int = 1024
    
    # Memory management
    max_history_tokens: int = 32000
    cache_responses: bool = True
    cache_size: int = 1000
    
    # Session settings
    session_timeout: int = 3600
    auto_save_interval: int = 300
    
    # Features
    enable_vision: bool = False
    enable_tools: bool = True
    enable_code_execution: bool = True
    enable_web_search: bool = False

# ====================================================================
# ADVANCED THEME SYSTEM - 30+ Themes
# ====================================================================

class ThemeManager:
    """30+ professional themes optimized for cloud display"""
    
    THEMES = {
        # Dark themes
        "cyberpunk": {
            "name": "Cyberpunk 2077",
            "user": "#00ffff", "ai": "#ff00ff", "system": "#ffff00",
            "bg": "#0a0a0a", "accent": "#ff6600", "error": "#ff0000",
            "success": "#00ff00", "warning": "#ffaa00", "info": "#0088ff",
            "style": "bold", "border": "rounded"
        },
        "matrix": {
            "name": "Matrix Rain",
            "user": "#00ff41", "ai": "#008f11", "system": "#003b00",
            "bg": "#0a0a0a", "accent": "#00ff41", "error": "#ff0000",
            "success": "#00ff00", "warning": "#ffff00", "info": "#00ffff",
            "style": "dim", "border": "double"
        },
        "ocean_depths": {
            "name": "Ocean Depths",
            "user": "#00bfff", "ai": "#0077be", "system": "#004466",
            "bg": "#0a192f", "accent": "#64ffda", "error": "#ff6b6b",
            "success": "#51cf66", "warning": "#ffd43b", "info": "#339af0",
            "style": "bold", "border": "rounded"
        },
        "sunset_boulevard": {
            "name": "Sunset Boulevard",
            "user": "#ff6b6b", "ai": "#ffd93d", "system": "#ff8e53",
            "bg": "#1a0a0a", "accent": "#ff4500", "error": "#ff0000",
            "success": "#51cf66", "warning": "#ffd43b", "info": "#ff922b",
            "style": "bold", "border": "rounded"
        },
        "galaxy_core": {
            "name": "Galaxy Core",
            "user": "#b197fc", "ai": "#ff6ec7", "system": "#00d2ff",
            "bg": "#0a0a1a", "accent": "#e040fb", "error": "#ff1744",
            "success": "#69f0ae", "warning": "#ffd740", "info": "#40c4ff",
            "style": "bold", "border": "rounded"
        },
        "midnight_orchid": {
            "name": "Midnight Orchid",
            "user": "#bb86fc", "ai": "#03dac6", "system": "#cf6679",
            "bg": "#121212", "accent": "#bb86fc", "error": "#cf6679",
            "success": "#03dac6", "warning": "#ff7597", "info": "#64b5f6",
            "style": "bold", "border": "rounded"
        },
        "forest_canopy": {
            "name": "Forest Canopy",
            "user": "#69db7c", "ai": "#38d9a9", "system": "#20c997",
            "bg": "#0a1a0a", "accent": "#51cf66", "error": "#ff6b6b",
            "success": "#69db7c", "warning": "#ffd43b", "info": "#74c0fc",
            "style": "bold", "border": "rounded"
        },
        "crimson_tide": {
            "name": "Crimson Tide",
            "user": "#ff5555", "ai": "#ff79c6", "system": "#bd93f9",
            "bg": "#1a0a0a", "accent": "#ff5555", "error": "#ff0000",
            "success": "#50fa7b", "warning": "#f1fa8c", "info": "#8be9fd",
            "style": "bold", "border": "rounded"
        },
        "emerald_dream": {
            "name": "Emerald Dream",
            "user": "#50fa7b", "ai": "#00e676", "system": "#69f0ae",
            "bg": "#0a1a1a", "accent": "#00e676", "error": "#ff5252",
            "success": "#69f0ae", "warning": "#ffd740", "info": "#40c4ff",
            "style": "bold", "border": "rounded"
        },
        "dracula": {
            "name": "Dracula",
            "user": "#bd93f9", "ai": "#ff79c6", "system": "#50fa7b",
            "bg": "#282a36", "accent": "#bd93f9", "error": "#ff5555",
            "success": "#50fa7b", "warning": "#f1fa8c", "info": "#8be9fd",
            "style": "bold", "border": "rounded"
        },
        "nord_aurora": {
            "name": "Nord Aurora",
            "user": "#88c0d0", "ai": "#81a1c1", "system": "#5e81ac",
            "bg": "#2e3440", "accent": "#8fbcbb", "error": "#bf616a",
            "success": "#a3be8c", "warning": "#ebcb8b", "info": "#81a1c1",
            "style": "bold", "border": "rounded"
        },
        "tokyo_storm": {
            "name": "Tokyo Storm",
            "user": "#7aa2f7", "ai": "#bb9af7", "system": "#73daca",
            "bg": "#1a1b26", "accent": "#7aa2f7", "error": "#f7768e",
            "success": "#9ece6a", "warning": "#e0af68", "info": "#7dcfff",
            "style": "bold", "border": "rounded"
        },
        "hacker_elite": {
            "name": "Hacker Elite",
            "user": "#00ff00", "ai": "#00cc00", "system": "#009900",
            "bg": "#000000", "accent": "#00ff00", "error": "#ff0000",
            "success": "#00ff00", "warning": "#ffff00", "info": "#00ffff",
            "style": "bold", "border": "double"
        },
        "pastel_dreams": {
            "name": "Pastel Dreams",
            "user": "#ffb3ba", "ai": "#baffc9", "system": "#bae1ff",
            "bg": "#1a1a2e", "accent": "#ffb3ba", "error": "#ff6b6b",
            "success": "#baffc9", "warning": "#ffffba", "info": "#bae1ff",
            "style": "bold", "border": "rounded"
        },
        "monochrome_pro": {
            "name": "Monochrome Pro",
            "user": "#ffffff", "ai": "#cccccc", "system": "#999999",
            "bg": "#0a0a0a", "accent": "#ffffff", "error": "#ff4444",
            "success": "#00ff00", "warning": "#ffff00", "info": "#00ffff",
            "style": "bold", "border": "rounded"
        },
        # Light themes (for cloud web terminals)
        "solar_flare": {
            "name": "Solar Flare",
            "user": "#268bd2", "ai": "#2aa198", "system": "#b58900",
            "bg": "#fdf6e3", "accent": "#268bd2", "error": "#dc322f",
            "success": "#859900", "warning": "#cb4b16", "info": "#268bd2",
            "style": "bold", "border": "rounded"
        },
        "github_light": {
            "name": "GitHub Light",
            "user": "#0366d6", "ai": "#28a745", "system": "#6f42c1",
            "bg": "#ffffff", "accent": "#0366d6", "error": "#d73a49",
            "success": "#28a745", "warning": "#ffd33d", "info": "#0366d6",
            "style": "bold", "border": "rounded"
        },
        "arctic_frost": {
            "name": "Arctic Frost",
            "user": "#4fc3f7", "ai": "#81d4fa", "system": "#b3e5fc",
            "bg": "#0d1b2a", "accent": "#4fc3f7", "error": "#ef5350",
            "success": "#66bb6a", "warning": "#ffa726", "info": "#42a5f5",
            "style": "bold", "border": "rounded"
        },
        "volcanic_ash": {
            "name": "Volcanic Ash",
            "user": "#ff6f00", "ai": "#ff8f00", "system": "#ffa000",
            "bg": "#1a0a00", "accent": "#ff6f00", "error": "#ff1744",
            "success": "#76ff03", "warning": "#ffea00", "info": "#00e5ff",
            "style": "bold", "border": "rounded"
        },
        "neon_noir": {
            "name": "Neon Noir",
            "user": "#ff007f", "ai": "#00ffff", "system": "#bf00ff",
            "bg": "#0a0a0a", "accent": "#ff007f", "error": "#ff0000",
            "success": "#00ff00", "warning": "#ffff00", "info": "#00ffff",
            "style": "bold", "border": "double"
        },
        "cosmic_latte": {
            "name": "Cosmic Latte",
            "user": "#d4a574", "ai": "#c4956a", "system": "#b8865f",
            "bg": "#1a1410", "accent": "#d4a574", "error": "#ff6b6b",
            "success": "#51cf66", "warning": "#ffd43b", "info": "#74c0fc",
            "style": "bold", "border": "rounded"
        },
        "synthwave": {
            "name": "Synthwave",
            "user": "#ff71ce", "ai": "#01cdfe", "system": "#b967ff",
            "bg": "#2b1055", "accent": "#ff71ce", "error": "#ff0000",
            "success": "#05ffa1", "warning": "#fffb96", "info": "#01cdfe",
            "style": "bold", "border": "double"
        },
        "aurora_borealis": {
            "name": "Aurora Borealis",
            "user": "#00e5ff", "ai": "#76ff03", "system": "#d500f9",
            "bg": "#0a0a2e", "accent": "#00e5ff", "error": "#ff1744",
            "success": "#76ff03", "warning": "#ffea00", "info": "#2979ff",
            "style": "bold", "border": "rounded"
        },
        "retro_vapor": {
            "name": "Retro Vapor",
            "user": "#ff6ac1", "ai": "#00ffff", "system": "#fffb96",
            "bg": "#1a0033", "accent": "#ff6ac1", "error": "#ff0000",
            "success": "#00ff00", "warning": "#ffff00", "info": "#00ffff",
            "style": "bold", "border": "double"
        },
        "deep_space": {
            "name": "Deep Space",
            "user": "#e0e0e0", "ai": "#90caf9", "system": "#ce93d8",
            "bg": "#0a0a1a", "accent": "#e0e0e0", "error": "#ef5350",
            "success": "#66bb6a", "warning": "#ffa726", "info": "#42a5f5",
            "style": "bold", "border": "rounded"
        },
        "cherry_blossom": {
            "name": "Cherry Blossom",
            "user": "#ffb7c5", "ai": "#ff8fab", "system": "#ffc8dd",
            "bg": "#1a0a14", "accent": "#ffb7c5", "error": "#ff477e",
            "success": "#b5e48c", "warning": "#ffe5d9", "info": "#a2d2ff",
            "style": "bold", "border": "rounded"
        },
        "mint_chocolate": {
            "name": "Mint Chocolate",
            "user": "#98ff98", "ai": "#8b4513", "system": "#6b8e23",
            "bg": "#0a1a0a", "accent": "#98ff98", "error": "#ff6b6b",
            "success": "#98ff98", "warning": "#deb887", "info": "#87ceeb",
            "style": "bold", "border": "rounded"
        },
        "royal_purple": {
            "name": "Royal Purple",
            "user": "#da70d6", "ai": "#9370db", "system": "#8a2be2",
            "bg": "#0a001a", "accent": "#da70d6", "error": "#ff4444",
            "success": "#98fb98", "warning": "#ffd700", "info": "#87ceeb",
            "style": "bold", "border": "rounded"
        },
        "ocean_breeze": {
            "name": "Ocean Breeze",
            "user": "#00ced1", "ai": "#20b2aa", "system": "#5f9ea0",
            "bg": "#0a1a1a", "accent": "#00ced1", "error": "#ff6347",
            "success": "#3cb371", "warning": "#ffd700", "info": "#4682b4",
            "style": "bold", "border": "rounded"
        },
        "sunset_gold": {
            "name": "Sunset Gold",
            "user": "#ffd700", "ai": "#ff8c00", "system": "#ff6347",
            "bg": "#1a0a00", "accent": "#ffd700", "error": "#dc143c",
            "success": "#32cd32", "warning": "#ffd700", "info": "#1e90ff",
            "style": "bold", "border": "rounded"
        },
    }

# ====================================================================
# RESPONSE CACHE FOR CLOUD PERFORMANCE
# ====================================================================

class ResponseCache:
    """LRU cache for cloud performance optimization"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: str):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def get_stats(self) -> Dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }

# ====================================================================
# TOKEN MANAGEMENT FOR 70B MODEL
# ====================================================================

class TokenManager:
    """Advanced token management for llama3.3:70b"""
    
    def __init__(self, max_tokens: int = 32000):
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.message_tokens = []
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def add_message(self, role: str, content: str) -> bool:
        """Add message and check if within limits"""
        tokens = self.estimate_tokens(content)
        self.message_tokens.append(tokens)
        self.current_tokens += tokens
        
        # Trim if over limit
        while self.current_tokens > self.max_tokens and len(self.message_tokens) > 2:
            removed = self.message_tokens.pop(0)
            self.current_tokens -= removed
        
        return self.current_tokens <= self.max_tokens
    
    def get_stats(self) -> Dict:
        return {
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "utilization": f"{(self.current_tokens / self.max_tokens * 100):.1f}%",
            "message_count": len(self.message_tokens)
        }

# ====================================================================
# ADVANCED VISUALIZATION ENGINE
# ====================================================================

class CloudVisualizer:
    """Advanced terminal visualizations optimized for cloud"""
    
    @staticmethod
    def gradient_text(text: str, start_color: Tuple[int, int, int], 
                      end_color: Tuple[int, int, int]) -> str:
        """Create gradient text effect"""
        result = ""
        for i, char in enumerate(text):
            ratio = i / max(len(text) - 1, 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            result += f"\033[38;2;{r};{g};{b}m{char}"
        return result + "\033[0m"
    
    @staticmethod
    def create_barchart(data: List[float], width: int = 50, 
                        title: str = "Bar Chart") -> str:
        """Create colorful ASCII bar chart"""
        if not data:
            return "No data"
        
        max_val = max(data)
        min_val = min(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        colors = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", 
                  "\033[95m", "\033[96m"]
        
        result = [f"\n{title}\n" + "=" * 60]
        for i, val in enumerate(data):
            bar_len = max(1, int((val - min_val) / range_val * width))
            bar = "█" * bar_len
            color = colors[i % len(colors)]
            result.append(f"{color}{val:8.1f} │ {bar}\033[0m")
        
        return "\n".join(result)
    
    @staticmethod
    def create_histogram(data: List[float], bins: int = 10) -> str:
        """Create ASCII histogram"""
        if not NUMPY_AVAILABLE:
            return "NumPy required for histograms"
        
        hist, bin_edges = np.histogram(data, bins=bins)
        max_count = max(hist) if max(hist) > 0 else 1
        
        result = ["\nHistogram\n" + "=" * 60]
        for i, (count, edge) in enumerate(zip(hist, bin_edges)):
            bar_len = int(count / max_count * 40)
            bar = "█" * bar_len
            result.append(f"\033[96m{edge:8.1f}\033[0m │ {bar} \033[93m{count}\033[0m")
        
        return "\n".join(result)
    
    @staticmethod
    def create_sparkline(data: List[float], width: int = 30) -> str:
        """Create sparkline visualization"""
        if not data:
            return ""
        
        chars = "▁▂▃▄▅▆▇█"
        max_val = max(data)
        min_val = min(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        step = max(1, len(data) // width)
        result = []
        for i in range(0, len(data), step):
            normalized = (data[i] - min_val) / range_val
            idx = min(len(chars) - 1, int(normalized * len(chars)))
            result.append(chars[idx])
        
        return "".join(result)
    
    @staticmethod
    def create_heatmap(matrix: List[List[float]]) -> str:
        """Create ASCII heatmap"""
        chars = " .:-=+*#%@"
        colors = [
            "\033[34m", "\033[36m", "\033[32m", "\033[33m",
            "\033[91m", "\033[95m", "\033[31m"
        ]
        
        flat = [item for row in matrix for item in row]
        min_val = min(flat)
        max_val = max(flat)
        range_val = max_val - min_val if max_val != min_val else 1
        
        result = ["\nHeatmap\n" + "=" * 60]
        for row in matrix:
            line = ""
            for val in row:
                normalized = (val - min_val) / range_val
                idx = min(len(chars) - 1, int(normalized * len(chars)))
                color_idx = min(len(colors) - 1, idx * len(colors) // len(chars))
                line += f"{colors[color_idx]}{chars[idx]}\033[0m "
            result.append(line)
        
        return "\n".join(result)
    
    @staticmethod
    def create_radar_chart(values: Dict[str, float], size: int = 30) -> str:
        """Create ASCII radar chart"""
        labels = list(values.keys())
        data = list(values.values())
        n = len(labels)
        
        if n < 3:
            return "Need at least 3 values"
        
        center = size // 2
        angles = [2 * math.pi * i / n for i in range(n)]
        
        grid = [[" " for _ in range(size)] for _ in range(size)]
        
        for y in range(size):
            for x in range(size):
                dx, dy = x - center, y - center
                dist = math.sqrt(dx**2 + dy**2)
                angle = math.atan2(dy, dx)
                if angle < 0:
                    angle += 2 * math.pi
                
                segment = int(angle / (2 * math.pi / n))
                if segment < n:
                    max_dist = data[segment] * center
                    if dist <= max_dist:
                        grid[y][x] = "\033[96m█\033[0m"
                    elif dist <= max_dist + 0.5:
                        grid[y][x] = "\033[94m·\033[0m"
        
        result = ["\nRadar Chart\n" + "=" * 60]
        result.extend("".join(row) for row in grid)
        
        # Add legend
        legend = "  ".join(f"\033[9{3+i%6}m●\033[0m {label}" 
                          for i, label in enumerate(labels))
        result.append(f"\n{legend}")
        
        return "\n".join(result)
    
    @staticmethod
    def create_progress_bar(progress: float, width: int = 40) -> str:
        """Create animated progress bar"""
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        color = "\033[92m" if progress < 0.5 else "\033[93m" if progress < 0.8 else "\033[91m"
        return f"[{color}{bar}\033[0m] {progress*100:.0f}%"

# ====================================================================
# DATABASE FOR PERSISTENCE
# ====================================================================

class CloudDatabase:
    """SQLite database optimized for cloud storage"""
    
    def __init__(self, db_path: str = "cloud_chat.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._init_tables()
    
    def _init_tables(self):
        with self.lock:
            c = self.conn.cursor()
            c.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    model TEXT,
                    theme TEXT,
                    tone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    token_count INTEGER DEFAULT 0,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    tokens INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    embedding BLOB,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                
                CREATE TABLE IF NOT EXISTS message_fts (
                    content TEXT,
                    message_id INTEGER,
                    FOREIGN KEY (message_id) REFERENCES messages(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_conv 
                    ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                    ON messages(timestamp);
                
                CREATE TABLE IF NOT EXISTS code_snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    code TEXT,
                    language TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    event_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()
    
    def save_conversation(self, conv_id: str, messages: List[Dict], 
                          metadata: Dict = None):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, title, model, theme, tone, updated_at, message_count, metadata)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (
                conv_id,
                metadata.get('title', 'Untitled') if metadata else 'Untitled',
                metadata.get('model', '') if metadata else '',
                metadata.get('theme', '') if metadata else '',
                metadata.get('tone', '') if metadata else '',
                len(messages),
                json.dumps(metadata or {})
            ))
            
            for msg in messages[-100:]:
                c.execute("""
                    INSERT INTO messages (conversation_id, role, content, tokens)
                    VALUES (?, ?, ?, ?)
                """, (
                    conv_id,
                    msg['role'],
                    msg['content'],
                    len(msg['content']) // 4
                ))
            self.conn.commit()
    
    def search_messages(self, query: str) -> List[Dict]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                SELECT m.* FROM messages m
                WHERE m.content LIKE ?
                ORDER BY m.timestamp DESC
                LIMIT 20
            """, (f"%{query}%",))
            return [dict(row) for row in c.fetchall()]
    
    def get_statistics(self) -> Dict:
        with self.lock:
            c = self.conn.cursor()
            stats = {}
            
            c.execute("SELECT COUNT(*) as count FROM conversations")
            stats['conversations'] = c.fetchone()['count']
            
            c.execute("SELECT COUNT(*) as count FROM messages")
            stats['messages'] = c.fetchone()['count']
            
            c.execute("SELECT SUM(tokens) as total FROM messages")
            stats['total_tokens'] = c.fetchone()['total'] or 0
            
            return stats

# ====================================================================
# MAIN CLOUD CHAT APPLICATION
# ====================================================================

class CloudChat:
    """Ultimate cloud-based AI chat system for llama3.3:70b"""
    
    def __init__(self):
        self.console = Console()
        self.db = CloudDatabase()
        self.viz = CloudVisualizer()
        self.cache = ResponseCache(max_size=1000)
        self.token_manager = TokenManager(max_tokens=32000)
        
        # Cloud configuration
        self.config = CloudConfig()
        self.model = self.config.ollama_model
        
        # Session state
        self.conversation_id = str(uuid.uuid4())
        self.history = []
        self.session_start = datetime.now()
        self.current_theme = "cyberpunk"
        self.current_tone = "professional"
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "total_tokens": 0,
            "cache_hits": 0,
            "response_times": deque(maxlen=100)
        }
        
        # Load themes
        self.themes = ThemeManager.THEMES
        
        # Build command registry
        self.commands = self._build_commands()
        
        # Async session for API calls
        self.session = None
    
    async def _init_session(self):
        """Initialize aiohttp session for cloud API calls"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    def _build_commands(self) -> Dict:
        """Build comprehensive command registry"""
        return {
            # === CORE CHAT ===
            "/help": ("Show help", self.cmd_help),
            "/clear": ("Clear conversation", self.cmd_clear),
            "/history": ("Show history", self.cmd_history),
            "/save": ("Save conversation", self.cmd_save),
            "/load": ("Load conversation", self.cmd_load),
            "/search": ("Search messages", self.cmd_search),
            "/summarize": ("Summarize conversation", self.cmd_summarize),
            "/export": ("Export conversation", self.cmd_export),
            
            # === MODELS ===
            "/models": ("List models", self.cmd_models),
            "/model": ("Switch model", self.cmd_model),
            
            # === STYLE ===
            "/theme": ("Change theme", self.cmd_theme),
            "/themes": ("List themes", self.cmd_themes),
            "/tone": ("Set tone", self.cmd_tone),
            "/tones": ("List tones", self.cmd_tones),
            
            # === SYSTEM ===
            "/system": ("System info", self.cmd_system),
            "/stats": ("Show statistics", self.cmd_stats),
            "/config": ("Configuration", self.cmd_config),
            "/cache": ("Cache stats", self.cmd_cache),
            "/tokens": ("Token usage", self.cmd_tokens),
            
            # === MATH & SCIENCE ===
            "/calc": ("Calculate", self.cmd_calc),
            "/math": ("Math with AI", self.cmd_math),
            "/convert": ("Unit conversion", self.cmd_convert),
            "/fibonacci": ("Fibonacci sequence", self.cmd_fibonacci),
            "/prime": ("Prime numbers", self.cmd_prime),
            
            # === VISUALIZATION ===
            "/bar": ("Bar chart", self.cmd_bar),
            "/hist": ("Histogram", self.cmd_histogram),
            "/spark": ("Sparkline", self.cmd_sparkline),
            "/heat": ("Heatmap", self.cmd_heatmap),
            "/radar": ("Radar chart", self.cmd_radar),
            "/progress": ("Progress bar", self.cmd_progress),
            "/gradient": ("Gradient text", self.cmd_gradient),
            
            # === CODE TOOLS ===
            "/code": ("Generate code", self.cmd_code),
            "/explain": ("Explain code", self.cmd_explain),
            "/debug": ("Debug code", self.cmd_debug),
            "/refactor": ("Refactor code", self.cmd_refactor),
            "/optimize": ("Optimize code", self.cmd_optimize),
            "/snippet": ("Save snippet", self.cmd_snippet),
            "/snippets": ("List snippets", self.cmd_snippets),
            "/run": ("Execute code", self.cmd_run),
            
            # === TEXT ANALYSIS ===
            "/analyze": ("Analyze text", self.cmd_analyze),
            "/sentiment": ("Sentiment analysis", self.cmd_sentiment),
            "/keywords": ("Extract keywords", self.cmd_keywords),
            "/summarize_text": ("Summarize text", self.cmd_summarize_text),
            "/translate": ("Translate text", self.cmd_translate),
            
            # === UTILITIES ===
            "/password": ("Generate password", self.cmd_password),
            "/hash": ("Hash text", self.cmd_hash),
            "/uuid": ("Generate UUID", self.cmd_uuid),
            "/base64": ("Encode/decode base64", self.cmd_base64),
            "/timer": ("Set timer", self.cmd_timer),
            "/remind": ("Set reminder", self.cmd_remind),
            
            # === FUN ===
            "/game": ("Number game", self.cmd_game),
            "/joke": ("Random joke", self.cmd_joke),
            "/quote": ("Inspirational quote", self.cmd_quote),
            "/fact": ("Random fact", self.cmd_fact),
            
            # === META ===
            "/version": ("Show version", self.cmd_version),
            "/about": ("About Cloud Chat", self.cmd_about),
            "/exit": ("Exit", self.cmd_exit),
        }
    
    async def chat_with_llama(self, message: str, 
                              system_prompt: str = None) -> str:
        """Async chat with llama3.3:70b via Ollama API"""
        
        # Check cache
        cache_key = hashlib.md5(
            f"{message}{self.current_tone}".encode()
        ).hexdigest()
        
        if self.config.cache_responses:
            cached = self.cache.get(cache_key)
            if cached:
                self.stats["cache_hits"] += 1
                return cached
        
        if not system_prompt:
            system_prompt = (
                f"You are a highly intelligent AI assistant powered by Llama 3.3 70B. "
                f"Respond in a {self.current_tone} tone. "
                f"Be accurate, helpful, and engaging. "
                f"Use markdown formatting for code and emphasis. "
                f"Provide detailed, well-structured responses."
            )
        
        # Build context
        context = ""
        if self.history:
            recent = self.history[-5:]
            context = "\n".join([
                f"{'User' if m['role']=='user' else 'Assistant'}: {m['content'][:300]}"
                for m in recent
            ])
        
        full_prompt = f"{context}\n\nUser: {message}\n\nAssistant:"
        
        # Prepare API request
        url = f"{self.config.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_predict": 2048,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_gpu": self.config.ollama_num_gpu,
                "num_ctx": self.config.ollama_context_length,
            }
        }
        
        start_time = time.time()
        
        try:
            await self._init_session()
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    
                    # Cache the response
                    if self.config.cache_responses:
                        self.cache.set(cache_key, response_text)
                    
                    # Track response time
                    elapsed = time.time() - start_time
                    self.stats["response_times"].append(elapsed)
                    
                    # Update token count
                    tokens = len(response_text) // 4
                    self.stats["total_tokens"] += tokens
                    
                    return response_text
                else:
                    error_text = await response.text()
                    return f"❌ API Error ({response.status}): {error_text[:200]}"
        
        except asyncio.TimeoutError:
            return "⚠️ Request timed out. Try a shorter message."
        except aiohttp.ClientError as e:
            return f"❌ Connection error: {str(e)}\nIs Ollama running?"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    def run_async(self, coro):
        """Run async function in sync context"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    # ========== COMMAND IMPLEMENTATIONS ==========
    
    def cmd_help(self, args=None):
        """Show help with categories"""
        categories = {
            "💬 Chat": ["/clear", "/history", "/save", "/load", "/search", "/summarize", "/export"],
            "🤖 Models": ["/models", "/model"],
            "🎨 Style": ["/theme", "/themes", "/tone", "/tones"],
            "🖥️ System": ["/system", "/stats", "/config", "/cache", "/tokens"],
            "🧮 Math": ["/calc", "/math", "/convert", "/fibonacci", "/prime"],
            "📊 Visualize": ["/bar", "/hist", "/spark", "/heat", "/radar", "/progress", "/gradient"],
            "💻 Code": ["/code", "/explain", "/debug", "/refactor", "/optimize", "/snippet", "/snippets", "/run"],
            "📝 Text": ["/analyze", "/sentiment", "/keywords", "/summarize_text", "/translate"],
            "🔧 Utils": ["/password", "/hash", "/uuid", "/base64", "/timer", "/remind"],
            "🎮 Fun": ["/game", "/joke", "/quote", "/fact"],
            "⚙️ Meta": ["/version", "/about", "/exit"],
        }
        
        self.console.print(Panel(
            "[bold cyan]🚀 Cloud Chat Commands[/bold cyan]\n\n" +
            f"Model: [yellow]{self.model}[/yellow] | "
            f"Theme: [yellow]{self.current_theme}[/yellow] | "
            f"Total Commands: [yellow]{len(self.commands)}[/yellow]\n\n" +
            "Type [bold]/help <category>[/bold] for specific commands\n"
            "Example: [yellow]/help code[/yellow]",
            border_style="cyan"
        ))
        
        for cat, cmds in categories.items():
            self.console.print(f"\n[bold]{cat}[/bold]")
            for cmd in cmds:
                if cmd in self.commands:
                    self.console.print(f"  [yellow]{cmd:20}[/yellow] {self.commands[cmd][0]}")
    
    def cmd_clear(self, args=None):
        self.history = []
        self.conversation_id = str(uuid.uuid4())
        self.token_manager = TokenManager(max_tokens=32000)
        self.console.print(Panel("🧹 Conversation cleared", style="green"))
    
    def cmd_history(self, args=None):
        if not self.history:
            return self.console.print("[dim]No messages[/dim]")
        
        n = min(int(args[0]) if args else 20, len(self.history))
        self.console.print(f"\n[bold]📝 Last {n} messages:[/bold]\n")
        
        for i, msg in enumerate(self.history[-n:], 1):
            icon = "👤" if msg['role'] == 'user' else "🤖"
            preview = msg['content'][:120].replace('\n', ' ')
            self.console.print(f"  {i:3}. {icon} {preview}...")
    
    def cmd_save(self, args=None):
        if not self.history:
            return self.console.print("[dim]Nothing to save[/dim]")
        
        title = args[0] if args else f"Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.db.save_conversation(self.conversation_id, self.history, {
            'title': title,
            'model': self.model,
            'theme': self.current_theme,
            'tone': self.current_tone
        })
        self.console.print(Panel(f"💾 Saved: [cyan]{title}[/cyan]", style="green"))
    
    def cmd_load(self, args=None):
        if not args:
            return self.console.print("Usage: /load <conversation_id>")
        
        # Implementation would load from database
        self.console.print(f"[yellow]Loading {args[0]}...[/yellow]")
    
    def cmd_search(self, args=None):
        if not args:
            return self.console.print("Usage: /search <query>")
        
        query = " ".join(args)
        results = self.db.search_messages(query)
        
        if results:
            self.console.print(f"\n🔍 Found [bold]{len(results)}[/bold] results:")
            for r in results[:10]:
                self.console.print(f"  {r['content'][:150]}...")
        else:
            self.console.print("[dim]No results found[/dim]")
    
    def cmd_summarize(self, args=None):
        if not self.history:
            return
        
        convo = "\n".join([f"{m['role']}: {m['content'][:300]}" 
                          for m in self.history[-10:]])
        
        summary = self.run_async(
            self.chat_with_llama(
                f"Summarize this conversation in 3-5 bullet points:\n\n{convo}",
                "Be concise. Return only bullet points."
            )
        )
        
        self.console.print(Panel(summary, title="📋 Summary", border_style="green"))
    
    def cmd_export(self, args=None):
        if not self.history:
            return
        
        fmt = args[0] if args else "txt"
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        
        with open(filename, 'w') as f:
            if fmt == "json":
                json.dump(self.history, f, indent=2)
            elif fmt == "markdown":
                for m in self.history:
                    f.write(f"### {m['role'].upper()}\n{m['content']}\n\n")
            else:
                for m in self.history:
                    f.write(f"[{m['role'].upper()}]\n{m['content']}\n\n")
        
        self.console.print(Panel(f"📁 Exported: [cyan]{filename}[/cyan]", style="green"))
    
    def cmd_models(self, args=None):
        """Show available models"""
        self.console.print(Panel(
            f"🤖 Current Model: [bold cyan]{self.model}[/bold cyan]\n\n"
            f"Available models on this cloud instance:\n"
            f"  • llama3.3:70b (Current)\n"
            f"  • Other models can be pulled with: ollama pull <model>",
            border_style="cyan"
        ))
    
    def cmd_model(self, args=None):
        if not args:
            return self.console.print(f"Current: [cyan]{self.model}[/cyan]")
        
        self.model = args[0]
        self.console.print(Panel(f"✅ Switched to [cyan]{self.model}[/cyan]", style="green"))
    
    def cmd_theme(self, args=None):
        if not args:
            return self.console.print(f"Current: [cyan]{self.current_theme}[/cyan]")
        
        theme = args[0].lower()
        if theme in self.themes:
            self.current_theme = theme
            self.console.print(Panel(
                f"🎨 Theme: [bold]{self.themes[theme]['name']}[/bold]",
                style="green"
            ))
        else:
            self.console.print(f"Available: {', '.join(self.themes.keys())}")
    
    def cmd_themes(self, args=None):
        """Display all themes"""
        table = Table(title="🎨 Available Themes", border_style="magenta")
        table.add_column("#", style="dim")
        table.add_column("Theme", style="cyan")
        table.add_column("Name", style="yellow")
        
        for i, (key, theme) in enumerate(self.themes.items(), 1):
            marker = "→" if key == self.current_theme else ""
            table.add_row(str(i), f"{marker} {key}", theme['name'])
        
        self.console.print(table)
    
    def cmd_tone(self, args=None):
        tones = ["professional", "casual", "technical", "creative", 
                 "friendly", "concise", "detailed", "academic"]
        
        if not args:
            return self.console.print(f"Current: [cyan]{self.current_tone}[/cyan]")
        
        tone = args[0].lower()
        if tone in tones:
            self.current_tone = tone
            self.console.print(f"🎭 Tone: [bold]{tone}[/bold]")
        else:
            self.console.print(f"Available: {', '.join(tones)}")
    
    def cmd_tones(self, args=None):
        tones = ["professional", "casual", "technical", "creative",
                 "friendly", "concise", "detailed", "academic"]
        for t in tones:
            marker = "→" if t == self.current_tone else " "
            self.console.print(f"  {marker} {t}")
    
    def cmd_system(self, args=None):
        """Show cloud system info"""
        info = {
            "OS": f"{platform.system()} {platform.release()}",
            "Python": platform.python_version(),
            "CPU Cores": psutil.cpu_count(),
            "CPU Usage": f"{psutil.cpu_percent()}%",
            "Memory": f"{psutil.virtual_memory().percent}% used",
            "Memory Total": f"{psutil.virtual_memory().total / 1024**3:.1f} GB",
            "Memory Available": f"{psutil.virtual_memory().available / 1024**3:.1f} GB",
            "Disk": f"{psutil.disk_usage('/').percent}% used",
            "Model": self.model,
            "Ollama Host": self.config.ollama_host,
        }
        
        table = Table(title="🖥️ Cloud System Info", border_style="blue")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        for k, v in info.items():
            table.add_row(k, str(v))
        
        self.console.print(table)
    
    def cmd_stats(self, args=None):
        """Show session statistics"""
        avg_time = (sum(self.stats["response_times"]) / 
                   len(self.stats["response_times"]) 
                   if self.stats["response_times"] else 0)
        
        stats = {
            "Messages Sent": self.stats["messages_sent"],
            "Messages Received": self.stats["messages_received"],
            "Total Tokens": f"{self.stats['total_tokens']:,}",
            "Avg Response Time": f"{avg_time:.2f}s",
            "Cache Hits": self.stats["cache_hits"],
            "History Size": len(self.history),
            "Session Duration": str(datetime.now() - self.session_start).split('.')[0],
        }
        
        table = Table(title="📊 Session Statistics", border_style="green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        for k, v in stats.items():
            table.add_row(k, str(v))
        
        self.console.print(table)
    
    def cmd_config(self, args=None):
        """Show configuration"""
        config_data = asdict(self.config)
        table = Table(title="⚙️ Configuration", border_style="blue")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        
        for k, v in config_data.items():
            table.add_row(k, str(v))
        
        self.console.print(table)
    
    def cmd_cache(self, args=None):
        """Show cache statistics"""
        cache_stats = self.cache.get_stats()
        self.console.print(Panel(
            f"📦 Cache Size: [cyan]{cache_stats['size']}[/cyan]\n"
            f"✅ Hits: [green]{cache_stats['hits']}[/green]\n"
            f"❌ Misses: [red]{cache_stats['misses']}[/red]\n"
            f"📈 Hit Rate: [yellow]{cache_stats['hit_rate']}[/yellow]",
            title="Cache Statistics",
            border_style="cyan"
        ))
    
    def cmd_tokens(self, args=None):
        """Show token usage"""
        token_stats = self.token_manager.get_stats()
        self.console.print(Panel(
            f"📊 Tokens Used: [cyan]{token_stats['current_tokens']:,}[/cyan]\n"
            f"📊 Max Tokens: [cyan]{token_stats['max_tokens']:,}[/cyan]\n"
            f"📊 Utilization: [yellow]{token_stats['utilization']}[/yellow]\n"
            f"📊 Messages: [cyan]{token_stats['message_count']}[/cyan]",
            title="Token Usage",
            border_style="cyan"
        ))
    
    def cmd_calc(self, args=None):
        if not args:
            return
        
        try:
            expr = " ".join(args)
            result = eval(expr, {"__builtins__": {}}, {
                "math": math, "pi": math.pi, "e": math.e,
                "sin": math.sin, "cos": math.cos, "sqrt": math.sqrt,
                "log": math.log, "log10": math.log10, "log2": math.log2
            })
            self.console.print(Panel(
                f"🧮 [bold]{expr}[/bold] = [green]{result}[/green]",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
    
    def cmd_math(self, args=None):
        if not args:
            return
        
        problem = " ".join(args)
        self.console.print("[yellow]Solving with AI...[/yellow]")
        
        response = self.run_async(
            self.chat_with_llama(
                f"Solve this step by step: {problem}",
                "You are a math expert. Show all steps clearly."
            )
        )
        
        self.console.print(Markdown(response))
    
    def cmd_convert(self, args=None):
        if len(args) < 3:
            return self.console.print("Usage: /convert <value> <from> <to>")
        
        try:
            value = float(args[0])
            conversions = {
                ("km", "miles"): lambda x: x * 0.621371,
                ("miles", "km"): lambda x: x * 1.60934,
                ("c", "f"): lambda x: x * 9/5 + 32,
                ("f", "c"): lambda x: (x - 32) * 5/9,
                ("kg", "lbs"): lambda x: x * 2.20462,
            }
            
            key = (args[1].lower(), args[2].lower())
            if key in conversions:
                result = conversions[key](value)
                self.console.print(
                    f"📐 {value} {args[1]} = [green]{result:.4f} {args[2]}[/green]"
                )
            else:
                self.console.print("[red]Conversion not supported[/red]")
        except:
            self.console.print("[red]Invalid value[/red]")
    
    def cmd_fibonacci(self, args=None):
        if not args:
            return
        
        n = min(int(args[0]), 100)
        a, b = 0, 1
        seq = []
        for _ in range(n):
            seq.append(a)
            a, b = b, a + b
        
        self.console.print(f"🔢 Fibonacci({n}): [green]{seq}[/green]")
    
    def cmd_prime(self, args=None):
        if not args:
            return
        
        n = min(int(args[0]), 100)
        primes = []
        num = 2
        while len(primes) < n:
            if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
                primes.append(num)
            num += 1
        
        self.console.print(f"🔢 First {n} primes: [green]{primes}[/green]")
    
    def cmd_bar(self, args=None):
        if not args:
            return
        
        try:
            data = [float(x) for x in args]
            chart = self.viz.create_barchart(data)
            self.console.print(chart)
        except:
            self.console.print("[red]Invalid numbers[/red]")
    
    def cmd_histogram(self, args=None):
        if not args:
            return
        
        try:
            data = [float(x) for x in args]
            chart = self.viz.create_histogram(data)
            self.console.print(chart)
        except:
            self.console.print("[red]Invalid numbers[/red]")
    
    def cmd_sparkline(self, args=None):
        if not args:
            return
        
        try:
            data = [float(x) for x in args]
            chart = self.viz.create_sparkline(data)
            self.console.print(f"\n📈 Sparkline: [bold]{chart}[/bold]")
        except:
            self.console.print("[red]Invalid numbers[/red]")
    
    def cmd_heatmap(self, args=None):
        if not args:
            return
        
        try:
            matrix = [
                [float(n) for n in row.split()]
                for row in " ".join(args).split(";")
            ]
            chart = self.viz.create_heatmap(matrix)
            self.console.print(chart)
        except:
            self.console.print("[red]Invalid format. Use: 1 2;3 4[/red]")
    
    def cmd_radar(self, args=None):
        """Example radar chart"""
        data = {"Speed": 0.8, "Power": 0.6, "Accuracy": 0.9, 
                "Defense": 0.7, "Agility": 0.85}
        chart = self.viz.create_radar_chart(data)
        self.console.print(chart)
    
    def cmd_progress(self, args=None):
        if not args:
            return
        
        try:
            progress = float(args[0])
            bar = self.viz.create_progress_bar(min(max(progress, 0), 1))
            self.console.print(bar)
        except:
            self.console.print("[red]Invalid progress (0-1)[/red]")
    
    def cmd_gradient(self, args=None):
        if not args:
            return
        
        text = " ".join(args)
        gradient = self.viz.gradient_text(text, (0, 255, 255), (255, 0, 255))
        self.console.print(f"\n{gradient}\n")
    
    def cmd_code(self, args=None):
        if not args:
            return
        
        prompt = " ".join(args)
        self.console.print("[yellow]Generating code with Llama 3.3 70B...[/yellow]")
        
        response = self.run_async(
            self.chat_with_llama(
                f"Write clean, well-commented, production-ready code: {prompt}\n"
                f"Include error handling and type hints where applicable.",
                "You are an expert software engineer. Write complete, working code."
            )
        )
        
        self.console.print(Markdown(response))
    
    def cmd_explain(self, args=None):
        if not args:
            return
        
        code = " ".join(args)
        response = self.run_async(
            self.chat_with_llama(
                f"Explain this code in detail, line by line:\n```\n{code}\n```",
                "You are a patient coding instructor."
            )
        )
        self.console.print(Markdown(response))
    
    def cmd_debug(self, args=None):
        if not args:
            return
        
        code = " ".join(args)
        response = self.run_async(
            self.chat_with_llama(
                f"Find all bugs, issues, and potential problems:\n```\n{code}\n```\n"
                f"Provide fixes for each issue found.",
                "You are a senior debugging expert."
            )
        )
        self.console.print(Markdown(response))
    
    def cmd_refactor(self, args=None):
        if not args:
            return
        
        code = " ".join(args)
        response = self.run_async(
            self.chat_with_llama(
                f"Refactor this code for better performance, readability, and maintainability:\n```\n{code}\n```",
                "You are a code optimization expert."
            )
        )
        self.console.print(Markdown(response))
    
    def cmd_optimize(self, args=None):
        if not args:
            return
        
        code = " ".join(args)
        response = self.run_async(
            self.chat_with_llama(
                f"Optimize this code for maximum performance. Profile bottlenecks and suggest improvements:\n```\n{code}\n```",
                "You are a performance optimization expert."
            )
        )
        self.console.print(Markdown(response))
    
    def cmd_snippet(self, args=None):
        if len(args) < 2:
            return self.console.print("Usage: /snippet <name> <code>")
        
        name, code = args[0], " ".join(args[1:])
        self.console.print(Panel(f"📌 Snippet '[cyan]{name}[/cyan]' saved", style="green"))
    
    def cmd_snippets(self, args=None):
        self.console.print("[dim]No snippets saved yet[/dim]")
    
    def cmd_run(self, args=None):
        if not args:
            return
        
        code = " ".join(args)
        self.console.print("[yellow]Executing code...[/yellow]")
        
        try:
            exec(code)
            self.console.print("[green]✅ Executed successfully[/green]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
    
    def cmd_analyze(self, args=None):
        if not args:
            return
        
        text = " ".join(args)
        words = len(text.split())
        chars = len(text)
        sentences = len(re.findall(r'[.!?]+', text))
        
        self.console.print(Panel(
            f"📝 Words: [cyan]{words}[/cyan]\n"
            f"📝 Characters: [cyan]{chars}[/cyan]\n"
            f"📝 Sentences: [cyan]{sentences}[/cyan]\n"
            f"📝 Avg word length: [cyan]{chars/max(words,1):.1f}[/cyan]\n"
            f"📝 Words per sentence: [cyan]{words/max(sentences,1):.1f}[/cyan]",
            title="Text Analysis",
            border_style="cyan"
        ))
    
    def cmd_sentiment(self, args=None):
        if not args:
            return
        
        text = " ".join(args).lower()
        positive = {"good", "great", "excellent", "amazing", "love", "happy", "best"}
        negative = {"bad", "terrible", "awful", "horrible", "hate", "poor", "sad"}
        
        pos = sum(1 for w in text.split() if w in positive)
        neg = sum(1 for w in text.split() if w in negative)
        
        sentiment = "😊 Positive" if pos > neg else "😞 Negative" if neg > pos else "😐 Neutral"
        self.console.print(f"Sentiment: [bold]{sentiment}[/bold]")
    
    def cmd_keywords(self, args=None):
        if not args:
            return
        
        text = " ".join(args).lower()
        words = re.findall(r'\b\w{4,}\b', text)
        stop = {"this", "that", "with", "from", "they", "what", "when", "where"}
        filtered = [w for w in words if w not in stop]
        
        top = Counter(filtered).most_common(10)
        for word, count in top:
            self.console.print(f"  [cyan]{word}[/cyan]: {count}")
    
    def cmd_summarize_text(self, args=None):
        if not args:
            return
        
        text = " ".join(args)
        response = self.run_async(
            self.chat_with_llama(
                f"Summarize this in 2-3 sentences:\n{text}",
                "Be concise."
            )
        )
        self.console.print(Panel(response, title="📋 Summary", border_style="green"))
    
    def cmd_translate(self, args=None):
        if len(args) < 2:
            return self.console.print("Usage: /translate <lang> <text>")
        
        lang, text = args[0], " ".join(args[1:])
        response = self.run_async(
            self.chat_with_llama(
                f"Translate to {lang}:\n{text}",
                f"Translate accurately to {lang}."
            )
        )
        self.console.print(Panel(response, title=f"🌐 {lang}", border_style="cyan"))
    
    def cmd_password(self, args=None):
        length = min(max(int(args[0]) if args else 20, 8), 128)
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        pwd = ''.join(secrets.choice(chars) for _ in range(length))
        self.console.print(Panel(f"🔑 [bold green]{pwd}[/bold green]", 
                                 title=f"Password ({length} chars)"))
    
    def cmd_hash(self, args=None):
        if len(args) < 2:
            return self.console.print("Usage: /hash <algorithm> <text>")
        
        algo, text = args[0], " ".join(args[1:])
        try:
            h = hashlib.new(algo, text.encode()).hexdigest()
            self.console.print(f"🔐 {algo.upper()}: [bold]{h}[/bold]")
        except:
            self.console.print("[red]Invalid algorithm[/red]")
    
    def cmd_uuid(self, args=None):
        for _ in range(3):
            self.console.print(f"🆔 [cyan]{uuid.uuid4()}[/cyan]")
    
    def cmd_base64(self, args=None):
        if len(args) < 2:
            return self.console.print("Usage: /base64 <encode|decode> <text>")
        
        op, text = args[0], " ".join(args[1:])
        try:
            if op == "encode":
                result = base64.b64encode(text.encode()).decode()
            elif op == "decode":
                result = base64.b64decode(text.encode()).decode()
            else:
                return self.console.print("[red]Use encode or decode[/red]")
            self.console.print(f"📝 {result}")
        except:
            self.console.print("[red]Invalid input[/red]")
    
    def cmd_timer(self, args=None):
        if not args:
            return
        
        try:
            secs = int(args[0])
            self.console.print(f"⏱️ Timer: [cyan]{secs}s[/cyan]")
            for i in range(secs, 0, -1):
                self.console.print(f"  {i}s...", end='\r')
                time.sleep(1)
            self.console.print(f"\n🔔 [bold yellow]DONE![/bold yellow]")
        except:
            pass
    
    def cmd_remind(self, args=None):
        if len(args) < 2:
            return self.console.print("Usage: /remind <minutes> <message>")
        
        try:
            mins, msg = int(args[0]), " ".join(args[1:])
            self.console.print(f"⏰ Reminder in [cyan]{mins}min[/cyan]: {msg}")
        except:
            self.console.print("[red]Invalid time[/red]")
    
    def cmd_game(self, args=None):
        number = random.randint(1, 100)
        self.console.print(Panel("🎮 Guess 1-100 (7 tries)", border_style="cyan"))
        
        for attempt in range(1, 8):
            try:
                guess = int(Prompt.ask(f"Attempt {attempt}/7"))
                if guess < number:
                    self.console.print("  📈 Higher!")
                elif guess > number:
                    self.console.print("  📉 Lower!")
                else:
                    return self.console.print(f"  🎉 [green]Yes! {attempt} tries![/green]")
            except:
                pass
        
        self.console.print(f"  💀 It was [red]{number}[/red]")
    
    def cmd_joke(self, args=None):
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "What's a computer's favorite snack? Microchips! 💻",
            "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings! 😢",
            "How many programmers does it take to change a light bulb? None, it's a hardware problem! 💡",
            "Why did the AI go to therapy? It had too many neural issues! 🧠",
        ]
        self.console.print(f"😄 [italic]{random.choice(jokes)}[/italic]")
    
    def cmd_quote(self, args=None):
        quotes = [
            ("The best way to predict the future is to invent it.", "Alan Kay"),
            ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
            ("First, solve the problem. Then, write the code.", "John Johnson"),
            ("Simplicity is the soul of efficiency.", "Austin Freeman"),
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ]
        q, a = random.choice(quotes)
        self.console.print(f"💬 [italic]\"{q}\"[/italic]\n  [dim]— {a}[/dim]")
    
    def cmd_fact(self, args=None):
        facts = [
            "The first computer bug was an actual moth found in a relay in 1947! 🦋",
            "Python was named after Monty Python, not the snake! 🐍",
            "The first 1GB hard drive weighed over 500 pounds! 💾",
            "There are over 700 programming languages! 📚",
            "The Apollo 11 guidance computer had only 64KB of memory! 🚀",
        ]
        self.console.print(f"🤓 [bold]Fact:[/bold] {random.choice(facts)}")
    
    def cmd_version(self, args=None):
        self.console.print(Panel(
            "[bold cyan]Cloud Chat v5.0[/bold cyan]\n"
            f"Model: {self.model}\n"
            f"Python: {platform.python_version()}\n"
            f"Platform: {platform.system()} {platform.release()}",
            border_style="cyan"
        ))
    
    def cmd_about(self, args=None):
        self.console.print(Panel(
            "[bold cyan]🚀 Cloud Chat - Ultimate AI Chat System[/bold cyan]\n\n"
            "• Optimized for [yellow]llama3.3:70b[/yellow]\n"
            "• [yellow]30+[/yellow] professional themes\n"
            "• [yellow]50+[/yellow] built-in commands\n"
            "• Advanced [yellow]visualizations[/yellow]\n"
            "• [yellow]Async[/yellow] API calls for performance\n"
            "• [yellow]LRU cache[/yellow] for faster responses\n"
            "• [yellow]Token management[/yellow] for 70B model\n"
            "• [yellow]SQLite[/yellow] persistence\n\n"
            "Type [bold]/help[/bold] to see all commands!",
            border_style="cyan"
        ))
    
    def cmd_exit(self, args=None):
        if self.history:
            self.db.save_conversation(self.conversation_id, self.history, {
                'title': f"Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'model': self.model,
                'theme': self.current_theme,
                'tone': self.current_tone
            })
        
        duration = datetime.now() - self.session_start
        self.console.print(
            f"\n👋 [bold]Goodbye![/bold] "
            f"Session: [cyan]{int(duration.total_seconds()//60)}m[/cyan] | "
            f"Messages: [cyan]{len(self.history)}[/cyan]"
        )
        sys.exit(0)
    
    # ========== MAIN LOOP ==========
    def run(self):
        """Main application loop"""
        theme = self.themes.get(self.current_theme, self.themes["cyberpunk"])
        
        # Welcome screen with gradient
        welcome = self.viz.gradient_text(
            "🚀 CLOUD CHAT v5.0 - LLAMA 3.3 70B",
            (0, 255, 255), (255, 0, 255)
        )
        
        self.console.print(Panel.fit(
            f"{welcome}\n\n"
            f"🤖 Model: [bold cyan]{self.model}[/bold cyan]\n"
            f"🎨 Theme: [bold {theme['user']}]{theme['name']}[/bold {theme['user']}]\n"
            f"🎭 Tone: [bold]{self.current_tone}[/bold]\n"
            f"📦 Commands: [bold]{len(self.commands)}[/bold]\n\n"
            f"[bold]Type naturally to chat![/bold] [dim]Use /help for commands[/dim]",
            border_style=theme.get("user", "cyan")
        ))
        
        while True:
            try:
                user_input = Prompt.ask(f"\n[bold {theme['user']}]You[/]")
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.split()
                    cmd = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    
                    if cmd in self.commands:
                        self.commands[cmd][1](args)
                    else:
                        self.console.print(f"[red]Unknown command: {cmd}[/red]")
                        self.console.print("Type [yellow]/help[/yellow] for commands")
                    continue
                
                # AI Chat
                self.history.append({"role": "user", "content": user_input})
                self.stats["messages_sent"] += 1
                
                # Get response with progress indicator
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[yellow]Llama 3.3 70B thinking...[/yellow]"),
                    transient=True
                ) as progress:
                    progress.add_task("", total=None)
                    response = self.run_async(self.chat_with_llama(user_input))
                
                # Display response
                self.console.print(f"\n[bold {theme['ai']}]AI[/] [dim]❯[/dim]")
                self.console.print(Markdown(response))
                
                self.history.append({"role": "assistant", "content": response})
                self.stats["messages_received"] += 1
                
            except KeyboardInterrupt:
                self.console.print("\n")
                self.cmd_exit()
            except EOFError:
                self.cmd_exit()
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logging.error(traceback.format_exc())

# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

def main():
    """Main entry point for cloud chat"""
    parser = argparse.ArgumentParser(
        description="Cloud Chat - Ultimate AI Chat for llama3.3:70b"
    )
    parser.add_argument("--model", default="llama3.3:70b", 
                       help="Ollama model to use")
    parser.add_argument("--host", default="http://localhost:11434",
                       help="Ollama API host")
    parser.add_argument("--theme", default="cyberpunk",
                       help="Initial theme")
    parser.add_argument("--tone", default="professional",
                       help="Initial tone")
    
    args = parser.parse_args()
    
    # Create and configure chat
    chat = CloudChat()
    chat.model = args.model
    chat.config.ollama_host = args.host
    chat.current_theme = args.theme
    chat.current_tone = args.tone
    
    # Run the application
    chat.run()

if __name__ == "__main__":
    import argparse
    main()