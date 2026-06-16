# 🛡️ AegisAI – The Autonomous SRE Brain

> **45+ AI-powered features · GPU‑accelerated on AMD MI300X (192 GB) · From logs to resolution in seconds**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)](https://fastapi.tiangolo.com)
[![Gradio](https://img.shields.io/badge/Gradio-5.0%2B-orange)](https://gradio.app)
[![AMD MI300X](https://img.shields.io/badge/GPU-AMD%20MI300X%20192GB-red)](https://amd.com)
[![Ollama](https://img.shields.io/badge/Ollama-Llama3-blueviolet)](https://ollama.ai)

---

## 🎯 What is AegisAI?

**AegisAI** is a fully autonomous **Site Reliability Engineering (SRE)** platform that detects, diagnoses, and resolves incidents in real-time. It combines:

- 🤖 **Multi-Agent LLM System** – Independent agents for monitoring, diagnosis, remediation, and alerting
- 🧠 **Retrieval-Augmented Generation (RAG)** – ChromaDB vector store for context-aware responses
- 📊 **Reinforcement Learning Triage** – Q-learning agent that learns optimal priorities from history
- ⚡ **1-Click Model Fine-Tuning** – QLoRA on AMD MI300X (train custom SRE model in 15 minutes)
- 🔐 **Enterprise-Grade Security** – JWT auth, RBAC, PII masking, prompt injection detection
- 📈 **GPU-Accelerated Processing** – Handles 10,000+ log lines in seconds

**Perfect for:** SRE teams, DevOps engineers, platform teams, and incident commanders who want AI-powered incident resolution at scale.

---

## ✨ Hero Features

### 🔍 **Live Diagnosis**
Paste server logs → AI detects anomalies, pinpoints root causes, and proposes fixes instantly.

### 📊 **Bulk PDF Reports**
Upload 100+ log lines → Get professional multi-page PDF with severity charts, RCA trees, and executive summaries.

### 🧠 **Smart Analytics**
Ask questions in plain English (*"Show me critical incidents this month"*) → AI converts to SQL, executes, displays results.

### 🛰️ **Live Monitor**
Real-time log streaming with color-coded severity, auto-incident creation, and AI co-pilot assistance.

### 📈 **Dependency Graph**
Interactive service map showing blast-radius analysis — see exactly which services fail if component X goes down.

### 🤖 **AI Copilot**
Chat with Llama3, DeepSeek, or your fine-tuned model. Switch models at runtime. Context-aware across all incidents.

### ⚙️ **Fine-Tuning & Vision**
Train custom SRE models on your own incident data with one click. Analyze screenshots and dashboards with LLaVA.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Async Core)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         AI Agent Pipeline (Multi-Threaded)               │  │
│  │  • Monitor Agent (Anomaly Detection)                     │  │
│  │  • Diagnosis Agent (Root Cause Analysis)                 │  │
│  │  • Remediation Agent (Fix Suggestions)                   │  │
│  │  • Alerting Agent (Slack/Email/Teams)                    │  │
│  │  • Code-Fix Agent (Patch Generation)                     │  │
│  │  • Sentiment Analyzer                                    │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │           RAG & Memory (ChromaDB)                        │  │
│  │  • Incident Vector Store                                │  │
│  │  • Long-Term Context Memory                              │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │       LLM Serving Engine (Ollama)                        │  │
│  │  • Llama3-8B (Primary Ops)                               │  │
│  │  • DeepSeek-R1-7B (SQL Generation)                       │  │
│  │  • Mistral-7B & LLaVA-7B (Multimodal)                    │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │    Hardware Acceleration (AMD MI300X)                    │  │
│  │  • 192 GB HBM3 Ultra-High Bandwidth VRAM                │  │
│  │  • Flash Attention Integration                           │  │
│  │  • Unsloth QLoRA Optimization                            │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │      Security & Infrastructure                          │  │
│  │  • Prompt Injection Guardrails                           │  │
│  │  • Redis Rate Limiting (60 req/min)                      │  │
│  │  • JWT Auth + Role-Based Access Control (RBAC)           │  │
│  │  • Celery Background Tasks                               │  │
│  │  • Audit Logging (Every Action)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                ┌───────────▼────────────┐
                │   Gradio Frontend      │
                │   (16 Integrated Tabs) │
                └───────────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI/ML Models** | Llama3-8B, DeepSeek-R1-7B, Mistral-7B, LLaVA-7B |
| **LLM Serving** | Ollama (local, GPU-accelerated) |
| **Fine-Tuning** | Unsloth (QLoRA), PEFT, bitsandbytes, HuggingFace |
| **Vector Database** | ChromaDB, Sentence-Transformers |
| **Backend** | FastAPI, Uvicorn, Celery, Pydantic |
| **Database** | SQLite (WAL mode), Redis (cache & sessions) |
| **Auth & Security** | JWT, bcrypt, RBAC, PII masking, injection detection |
| **Frontend** | Gradio 5, Plotly, Custom CSS (glassmorphism) |
| **GPU Acceleration** | AMD MI300X (192 GB HBM3), ROCm 7.0, PyTorch |
| **Reporting** | ReportLab (PDF generation) |
| **Image Processing** | Pillow, Tesseract OCR, LLaVA |
| **ML Utilities** | NumPy, scipy, statsmodels (Granger causality) |

---

## 📦 Installation

### Prerequisites

- **Python 3.10+** with pip
- **AMD MI300X GPU** (or CPU fallback – auto-detected)
- **ROCm 7.0** installed and configured
- **Ollama** installed and running

### Step 1: Clone Repository

```bash
git clone https://github.com/amanmukati09/cloud-hackathon-tcs-amd.git
cd cloud-hackathon-tcs-amd
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Pull Models with Ollama

Make sure Ollama is running (`ollama serve` in another terminal), then:

```bash
ollama pull llama3:8b              # Primary chat & diagnosis
ollama pull deepseek-r1:7b         # SQL generation for analytics
ollama pull mistral:7b             # Alternative reasoning model
ollama pull llava:7b               # Vision model for images
```

### Step 5: Initialize Database & Admin User

```bash
python backend/create_admin.py
```

Follow prompts to set admin email and password.

### Step 6: Start Log Generator (Optional, for demos)

```bash
./start_logs.sh &
```

### Step 7: Start Backend

```bash
python backend/main.py
```

**Expected Output:**
```
✅ GPU Detected: AMD Instinct MI300X (192GB VRAM)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 8: Start Frontend

In a new terminal:

```bash
python frontend/app.py
```

**Access the UI:**
- **Local:** http://localhost:7860
- **Public:** A `.gradio.live` URL will be displayed in the terminal (share with team)

---

## 🚀 Usage Guide

### First Login

1. Open http://localhost:7860 in your browser
2. Click **Login** tab
3. Enter admin credentials created in setup
4. You're in! 🎉

### Feature Quick-Start

| Feature | How to Use | Expected Result |
|---------|-----------|-----------------|
| **Live Diagnosis** | Paste error logs → click **Analyze Logs** | AI shows anomaly type, root cause, remediation steps |
| **Bulk PDF Analysis** | Upload `.log` file (100+ lines) → click **PDF Report** | Professional PDF with charts, RCA, timeline |
| **AI Copilot Chat** | Type any SRE question → click **Send** | Streaming response with incident context |
| **Smart Analytics** | Type *"Critical incidents this month?"* → **Ask AI** | AI generates SQL, shows results in table |
| **Live Monitor** | Click **▶️ Start** (log generator running) | Real-time log stream, auto-incident creation |
| **Train Custom Model** | Select base model → **Start Training** (15 min) | Fine-tuned model ready for chat |
| **Dependency Graph** | Click **Refresh Graph** → click nodes | Service map with blast-radius analysis |
| **RL Triage** | Click **Train RL Agent** → **Refresh Queue** | Incidents sorted by AI-predicted priority |
| **SQL Runner** (Admin) | Type SQL → **Execute** | Query results displayed instantly |
| **Knowledge Base** | Click **Generate KB** → search articles | AI-curated docs from resolved incidents |

---

## 🎯 Workflow Examples

### Example 1: End-to-End Incident Resolution

```
1. Live Diagnosis → Paste logs
   ↓
2. Click Analyze
   ↓
3. Review root cause and remediation
   ↓
4. Click Auto-Remediate (for safe fixes)
   ↓
5. Incident saved automatically
   ↓
6. Go to Incident History → Export PDF or Generate Runbook
```

### Example 2: Live Monitoring Session

```
1. Start log generator: ./start_logs.sh &
   ↓
2. Go to Live Monitor tab
   ↓
3. Click ▶️ Start
   ↓
4. Watch real-time log stream (color-coded)
   ↓
5. CRITICAL incidents auto-appear in Active Incidents panel
   ↓
6. Use AI Chat to ask questions about the stream
   ↓
7. Click ⏹️ Stop → get summary report
```

### Example 3: Train & Deploy Custom Model

```
1. Go to Train Model tab
   ↓
2. Select base model (Llama3 recommended)
   ↓
3. Click Start Training (15-20 min)
   ↓
4. Progress bar shows training loss
   ↓
5. Test model in built-in chat
   ↓
6. Model auto-registers in AI Copilot dropdown
   ↓
7. All team members can use it immediately
```

---

## 📂 Project Structure

```
amd-aegis-sre/
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── auth.py                      # JWT + bcrypt authentication
│   ├── models.py                    # SQLAlchemy ORM (15 tables)
│   ├── guardrails.py                # PII masking & injection detection
│   ├── gpu_utils.py                 # AMD MI300X auto-detection
│   ├── cache.py                     # Redis caching utilities
│   ├── chroma_store.py              # ChromaDB vector store
│   ├── create_admin.py              # Admin setup script
│   ├── seed_data.py                 # Mock production data
│   │
│   ├── agents/                      # 🤖 AI Pipeline
│   │   ├── chat.py                  # Multi-model orchestration
│   │   ├── diagnosis.py             # Root-cause analysis
│   │   ├── monitor.py               # Anomaly detection
│   │   ├── remediation.py           # Fix suggestions
│   │   ├── alerting.py              # Email/Slack/Teams
│   │   ├── code_fixer.py            # Patch generation
│   │   ├── sentiment.py             # Sentiment analysis
│   │   ├── runbook.py               # Auto-generate runbooks
│   │   ├── knowledge_base.py        # KB auto-compilation
│   │   ├── vision_analyzer.py       # LLaVA image analysis
│   │   ├── gpu_trainer.py           # QLoRA fine-tuning
│   │   ├── dependency_graph.py      # Service topology
│   │   ├── causal_graph.py          # Granger causality
│   │   ├── rl_triage.py             # Q-learning prioritization
│   │   ├── nl_to_sql.py             # NL-to-SQL compiler
│   │   ├── pdf_generator.py         # PDF reports
│   │   ├── bulk_processor.py        # Batch log processing
│   │   └── health_scorer.py         # System health gauge
│   │
│   ├── routers/                     # 🧭 API Endpoints
│   │   ├── admin.py                 # Admin management
│   │   ├── incidents.py             # Incident CRUD
│   │   ├── chat.py                  # Chat sessions
│   │   ├── diagnosis.py             # Log analysis
│   │   ├── community.py             # Forum endpoints
│   │   ├── notifications.py         # Alert management
│   │   ├── workflow.py              # Automation workflows
│   │   ├── audit.py                 # Audit logs
│   │   ├── api_keys.py              # API key management
│   │   ├── dashboard.py             # Dashboard data
│   │   ├── live_monitor.py          # Real-time streaming
│   │   ├── dependency.py            # Topology data
│   │   ├── rl_triage.py             # Priority routing
│   │   ├── sql_runner.py            # Query interface
│   │   └── analytics.py             # Trend analysis
│   │
│   ├── middleware/
│   │   └── rate_limit.py            # Redis rate limiting
│   │
│   └── utils/
│       └── audit_logger.py          # Event tracing
│
├── frontend/                        # 🎨 Gradio UI
│   ├── app.py                       # Main coordinator
│   ├── auth.py                      # Login/logout views
│   ├── chat.py                      # AI copilot panel
│   ├── diagnosis.py                 # Diagnosis dashboard
│   ├── incidents.py                 # Incident search
│   ├── notifications.py             # Alerts UI
│   ├── community.py                 # Forum UI
│   ├── admin.py                     # Admin dashboard
│   ├── css.py                       # Glassmorphism styling
│   │
│   ├── pages/                       # 📑 Feature Modules
│   │   ├── bulk_analysis.py         # Multi-file analysis
│   │   ├── model_training.py        # Training UI
│   │   ├── dependency_graph.py      # Service graph view
│   │   ├── rl_triage.py             # Priority queue view
│   │   ├── sql_runner.py            # Query UI
│   │   ├── live_monitor.py          # Real-time dashboard
│   │   ├── smart_analytics.py       # Trend analysis
│   │   └── demo_tour.py             # Guided walkthrough
│   │
│   ├── components/                  # 🧱 Reusable Widgets
│   │   ├── cards.py                 # Metric cards
│   │   ├── progress.py              # Progress bars
│   │   └── headers.py               # Layout headers
│   │
│   └── styles/
│       └── bulk_analysis.py         # Custom CSS
│
├── dummy_sites/
│   └── log_generator.py             # Simulated telemetry
│
├── logs/
│   └── live_stream.log              # Log stream output
│
├── requirements.txt                 # Python dependencies
├── start_logs.sh                    # Log generator script
└── README.md                        # This file
```

---

## 🔐 Security & Compliance

| Feature | Implementation |
|---------|-----------------|
| **Authentication** | JWT tokens with bcrypt password hashing |
| **Authorization** | Role-Based Access Control (Admin vs User) |
| **Data Privacy** | PII masking (emails, API keys, IPs) |
| **Injection Protection** | Prompt injection detection & filtering |
| **Command Safety** | Destructive command blocking (rm, delete, etc.) |
| **Rate Limiting** | 60 requests/minute per user (Redis-backed) |
| **Audit Trail** | Every action logged (timestamp, user, IP, details) |
| **API Keys** | Scoped, revocable tokens with expiration |
| **Session Management** | Secure session storage in Redis |

---

## 🎬 Demo Tour

Click the **🎬 Demo** button in the navigation bar to see a guided walkthrough of 5 hero features with interactive overlays.

---

## 📊 Benchmarks

| Metric | Value |
|--------|-------|
| **Log Processing Speed** | 10,000+ lines/second |
| **Average Diagnosis Time** | 2-5 seconds |
| **Model Fine-Tuning Time** | 15-20 minutes (on MI300X) |
| **RAG Query Latency** | <200ms (ChromaDB) |
| **Real-Time Monitor FPS** | 60+ FPS (color-coded) |
| **Inference Throughput** | 100+ tokens/second (Llama3) |

---

## 🚀 Advanced Features

### Fine-Tune Your Own Model
```python
# After selecting base model in UI:
# 1. System auto-detects training data from incident history
# 2. Applies QLoRA optimization (4-bit quantization)
# 3. Trains on AMD MI300X (192 GB VRAM)
# 4. Exports as GGUF format
# 5. Auto-registers in Ollama
# 6. Available in AI Copilot dropdown
```

### Query with Natural Language
```
User: "Show me critical incidents from last week grouped by service"
→ AI converts to SQL
→ Executes securely
→ Returns formatted table
→ Explains findings
```

### Analyze Screenshots & Dashboards
```
User: Uploads screenshot of Kubernetes dashboard
→ LLaVA vision model analyzes image
→ Extracts error messages
→ Recommends actions
```

---

## 🤝 Team & Credits

| Name | Role |
|------|------|
| **Aman Mukati** | AI/ML Architect – Multi-agent pipeline, QLoRA fine-tuning, RL, RAG |
| **Amitesh Thakur** | Full-Stack & GPU – Backend API, Live Monitor, PDF, streaming, GPU detection |
| **Karan Singh Rana** | UI/UX & Design – Gradio dashboard, 16 tabs, CSS system, product design |

*Built with ❤️ at the **TCS AMD Hackathon 2026***

---

## 🙏 Acknowledgements

- **AMD** – MI300X GPU & ROCm 7.0
- **Ollama** – Local LLM serving
- **Unsloth** – Fast QLoRA fine-tuning
- **Gradio** – Flexible UI framework
- **ChromaDB** – Vector database
- **HuggingFace** – Models & transformers

---

## 📄 License

**MIT License** – See [LICENSE](LICENSE) file for details.

```
Copyright (c) 2026 Aman Mukati

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software... (full text in LICENSE file)
```

---

## 📞 Support & Contributions

### Report Issues
```
👉 https://github.com/amanmukati09/cloud-hackathon-tcs-amd/issues
```

### Fork & Contribute
```
1. Fork the repo
2. Create feature branch: git checkout -b feature/your-feature
3. Commit changes: git commit -m "Add feature"
4. Push: git push origin feature/your-feature
5. Open Pull Request
```

### Questions?
- 📧 Email: amanmukati@yahoo.com
- 💬 Discussions: [GitHub Discussions](https://github.com/amanmukati09/cloud-hackathon-tcs-amd/discussions)

---

## 🌟 Roadmap

- [ ] Kubernetes-native deployment (Helm charts)
- [ ] Multi-tenancy enhancements
- [ ] More LLM model support
- [ ] Mobile app (React Native)
- [ ] Enterprise SLA tracking
- [ ] Custom webhook integrations
- [ ] Advanced RBAC policies
- [ ] Data retention policies

---

<div align="center">

### **AegisAI** – *Because your infrastructure deserves an intelligent shield.* 🛡️

[⭐ Star us on GitHub](https://github.com/amanmukati09/cloud-hackathon-tcs-amd) | [📖 Read Docs](#) | [🐛 Report Bug](https://github.com/amanmukati09/cloud-hackathon-tcs-amd/issues)

</div>