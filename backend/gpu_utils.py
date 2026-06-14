"""
GPU/CPU Auto-Detection Utility
Detects AMD MI300X via amd-smi plain text or rocm-smi, NVIDIA via nvidia-smi.
"""

import os
import subprocess
import re

class GPUDetector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._detect()
        return cls._instance
    
    def _run_cmd(self, cmd, timeout=10):
        """Run a shell command and return stdout, stderr, returncode."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            return "", str(e), -1
    
    def _detect(self):
        self.gpu_available = False
        self.gpu_type = "CPU"
        self.gpu_name = "None"
        self.gpu_memory_gb = 0
        
        # ── Method 1: Parse amd-smi plain text output ──
        stdout, stderr, code = self._run_cmd("amd-smi 2>/dev/null")
        
        if code == 0 and stdout:
            # Look for GPU name like "Instinct MI300X"
            name_match = re.search(r'Instinct\s+MI\w+', stdout)
            if name_match:
                self.gpu_available = True
                self.gpu_type = "AMD"
                self.gpu_name = f"AMD {name_match.group(0)}"
                
                # Extract memory: look for "283/196592 MB" pattern
                mem_match = re.search(r'(\d+)/(\d+)\s*MB', stdout)
                if mem_match:
                    total_mem_mb = int(mem_match.group(2))
                    self.gpu_memory_gb = total_mem_mb / 1024
                else:
                    self.gpu_memory_gb = 192  # Default MI300X
                
                print(f"✅ AMD GPU: {self.gpu_name} ({self.gpu_memory_gb:.0f}GB VRAM)")
                return
        
        # ── Method 2: rocm-smi ────────────────────
        stdout, stderr, code = self._run_cmd("rocm-smi 2>/dev/null")
        
        if code == 0 and 'GPU' in stdout:
            self.gpu_available = True
            self.gpu_type = "AMD"
            
            # Try to get GPU name from amd-smi list
            stdout2, _, code2 = self._run_cmd("amd-smi list 2>/dev/null")
            if code2 == 0 and stdout2:
                name_match = re.search(r'Instinct\s+MI\w+', stdout2)
                if name_match:
                    self.gpu_name = f"AMD {name_match.group(0)}"
                else:
                    self.gpu_name = "AMD Instinct GPU"
            else:
                self.gpu_name = "AMD Instinct GPU"
            
            # Get VRAM from rocm-smi
            vram_match = re.search(r'VRAM%', stdout)
            if vram_match:
                self.gpu_memory_gb = 192  # MI300X
            else:
                self.gpu_memory_gb = 192
            
            print(f"✅ AMD GPU (rocm-smi): {self.gpu_name} ({self.gpu_memory_gb:.0f}GB)")
            return
        
        # ── Method 3: Check ROCm path directly ────
        rocm_path = os.environ.get('ROCM_PATH', '/opt/rocm')
        if os.path.exists(f"{rocm_path}/bin/rocminfo"):
            self.gpu_available = True
            self.gpu_type = "AMD"
            self.gpu_name = "AMD Instinct MI300X"
            self.gpu_memory_gb = 192
            print(f"✅ AMD GPU (ROCm detected): {self.gpu_name} ({self.gpu_memory_gb:.0f}GB)")
            return
        
        # ── Method 4: NVIDIA ──────────────────────
        stdout, _, code = self._run_cmd(
            "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null"
        )
        if code == 0 and stdout:
            self.gpu_available = True
            self.gpu_type = "NVIDIA"
            parts = stdout.split(',')
            self.gpu_name = parts[0].strip()
            mem_str = parts[1].strip().split()[0] if len(parts) > 1 else "0"
            self.gpu_memory_gb = int(mem_str) / 1024
            print(f"✅ NVIDIA GPU: {self.gpu_name} ({self.gpu_memory_gb:.0f}GB)")
            return
        
        print("💻 No GPU detected - CPU mode")
    
    def get_config(self):
        return {
            "gpu_available": self.gpu_available,
            "gpu_type": self.gpu_type,
            "gpu_name": self.gpu_name,
            "gpu_memory_gb": round(self.gpu_memory_gb, 1),
            "batch_size": 32 if self.gpu_available else 4,
            "can_fine_tune": self.gpu_available and self.gpu_memory_gb > 20,
            "device": "cuda" if self.gpu_available else "cpu"
        }
    
    def get_ollama_gpu_env(self):
        """Environment variables for Ollama GPU acceleration."""
        if self.gpu_type == "AMD":
            return {
                "HSA_OVERRIDE_GFX_VERSION": "9.4.2",
                "ROCR_VISIBLE_DEVICES": "0",
                "HIP_VISIBLE_DEVICES": "0",
                "OLLAMA_NUM_GPU": "1",
                "OLLAMA_GPU_LAYERS": "999"
            }
        return {}

gpu_detector = GPUDetector()