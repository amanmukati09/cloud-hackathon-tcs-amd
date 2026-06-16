# 🛡️ AegisAI – The Autonomous SRE Brain

> **45+ AI-powered features · GPU‑accelerated on AMD MI300X (192 GB) · From logs to resolution in seconds**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)](https://fastapi.tiangolo.com)
[![Gradio](https://img.shields.io/badge/Gradio-5.0%2B-orange)](https://gradio.app)
[![AMD MI300X](https://img.shields.io/badge/GPU-AMD%20MI300X%20192GB-red)](https://amd.com)
[![Ollama](https://img.shields.io/badge/Ollama-Llama3%20%7C%20DeepSeek%20%7C%20Mistral%20%7C%20LLaVA-blueviolet)](https://ollama.ai)

AegisAI is a fully autonomous Site Reliability Engineering (SRE) platform that detects, diagnoses, and resolves incidents in real time.  
It combines a **multi‑agent LLM system**, **retrieval‑augmented generation (RAG)** with ChromaDB, **reinforcement‑learning triage**, **1‑click model fine‑tuning (QLoRA on MI300X)**, and **enterprise‑grade security guardrails**. The platform processes 10 000+ log lines in seconds, learns optimal incident priorities from historical data, and lets any team train a custom SRE model in 15 minutes.

---

## 📖 Table of Contents
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🗂️ Project Structure](#️-project-structure)
- [🧰 Tech Stack](#-tech-stack)
- [📦 Installation](#-installation)
- [🚀 Usage](#-usage)
- [🎥 Demo](#-demo)
- [🤝 Team](#-team)
- [📄 License](#-license)

## ✨ Features

### 🔍 Incident Lifecycle Management
- **Live Diagnosis** – Paste or upload server logs; AI detects anomalies, pinpoints root causes, and proposes remediation in one click.
- **Bulk Log Analysis & PDF Reports** – Upload 1 000+ log lines → GPU‑accelerated batch processing produces a professional, multi‑page PDF with severity charts, RCA trees, timelines, and executive summaries.
- **Incident History** – Search, filter, and export your incident database. Download individual incidents as CSV or PDF, and delete entries you no longer need.
- **Incident Timeline** – Visual, step‑by‑step reconstruction of an incident’s lifecycle – from first detection to final resolution.
- **Runbook Generation** – One‑click creation of executable runbooks from any resolved incident; shareable, repeatable, and editable.

### 🛰️ Real‑Time Monitoring & Visualization
- **Live Site Monitor** – Connect to multiple log sources simultaneously. Real‑time, colour‑coded log stream with automatic incident creation, CRITICAL‑severity email/Slack alerts, and an AI co‑pilot that answers questions about the current stream.
- **Dependency Graph** – Interactive, force‑directed service map showing how components relate. Click any node to see its **blast radius** – exactly which services would be affected if it failed.
- **System Health Score** – Dynamic 0‑100 gauge computed every minute from live incident data. Displays active critical counts, open incidents, and resolution rate.
- **Causal Incident Graph** – Uses Granger‑causality tests to determine *which service actually caused* another to fail, with confidence scores and directional arrows.
- **Active Incidents Panel** – See all currently open incidents, sorted by RL‑predicted priority, with quick links to full details and one‑click PDF downloads.

### 🧠 AI & Machine Learning
- **Multi‑Model AI Copilot** – Chat with **Llama3‑8B**, **DeepSeek‑R1‑7B**, **Mistral‑7B**, or your own fine‑tuned model. Switch models at runtime and receive streaming, token‑by‑token responses.
- **Smart Analytics** – Ask questions in plain English (e.g., *“Show me critical incidents this month”*). The AI converts your question to SQL, executes it against your incident database, and displays formatted tables with explanations.
- **RL Triage** – A **reinforcement‑learning agent** (Q‑learning) that learns optimal incident priorities from historical resolution data. The more incidents you resolve, the smarter the prioritisation becomes.
- **Autonomous SRE Agent** – A multi‑step reasoning pipeline: **observe logs → detect anomaly → diagnose root cause → suggest remediation → execute safe commands**.
- **Semantic Log Search (Incident DNA)** – GPU‑accelerated embeddings via Sentence‑Transformers. Search your incident database by **meaning**, not just keywords – find related incidents in milliseconds.
- **1‑Click Model Fine‑Tuning** – Fine‑tune Llama3 (or Mistral) on your own incident data using QLoRA on the MI300X. The trained model is exported as GGUF, registered in Ollama, and ready to use in the AI Copilot. Includes a built‑in chat to test your model immediately.
- **Image Analysis (LLaVA)** – Upload screenshots of error messages, dashboards, or monitoring tools. The **LLaVA vision model** describes what it sees, extracts log text, and recommends actions.

### 🔐 Enterprise‑Grade Security
- **JWT Authentication** – Secure login with bcrypt password hashing and token‑based sessions.
- **Role‑Based Access Control (RBAC)** – **Admin** vs. **Standard User**. Admin‑only features include SQL Runner, user management, global model training, and system configuration.
- **AI Guardrails** – Every LLM call is protected by:
  - **PII Masking** (regex‑based redaction of emails, API keys, IP addresses)
  - **Prompt Injection Detection** (jailbreak attempts blocked)
  - **Destructive Command Blocking** (forbidden commands prevented)
- **Rate Limiting** – 60 requests per minute per user, enforced via Redis.
- **Audit Logging** – Every action (login, incident creation, chat deletion) is recorded with timestamp, user, IP address, and details.
- **API Key Management** – Generate scoped, revocable API keys for programmatic access with optional expiration dates.

### 📚 Knowledge Management & Collaboration
- **Auto‑Generated Knowledge Base** – AI analyses all resolved incidents and automatically creates structured articles with symptoms, root cause, solution, prevention, and difficulty rating. Full‑text semantic search across all articles.
- **Community Forum** – Team‑wide posts, nested comments, and likes for collaborative incident discussion.
- **Support Tickets** – Built‑in escalation system: users submit questions, admins answer, and both parties receive in‑app notifications.
- **Gamification** – Earn points and badges for creating incidents, resolving them quickly, posting in the community, and more. Team leaderboard included.

### 🛠️ Developer & Admin Tools
- **SQL Runner** – Dark, terminal‑style SQL IDE for admins. Execute SELECT queries with safety checks; INSERT/UPDATE/DELETE with confirmation. Preset queries and table‑schema explorer included.
- **Data Explorer** – Pre‑built pandas analyses: severity distribution, component breakdown, daily trends, top users, and more – all with one click.
- **AI Benchmark Card** – Real‑time performance metrics: diagnosis accuracy, remediation rate, average resolution time, GPU acceleration status, and feature count.
- **Notification System** – In‑app notifications for new incidents, ticket answers, chat deletions, and system events. Mark all as read with one click.
- **Demo Tour** – One‑click guided walkthrough that highlights the 5 hero features with an overlay, helping new users (and judges) understand the platform instantly.

## 🏗️ Architecture

```text
 [ Log Sources ] ───> ┌──────────────────────────────────────────────┐
 (Files, APIs,        │               FastAPI Backend                │
  Simulators)         │ ┌──────────────────────────────────────────┐ │
                      │ │  AI Agent Pipeline                       │ │
                      │ │  • Monitor Agent (Anomaly Detection)     │ │
                      │ │  • Diagnosis Agent (Root Cause Analysis) │ │
                      │ │  • Remediation Agent (Fix Suggestions)   │ │
                      │ │  • Alerting Agent (Slack/Teams/Email)    │ │
                      │ │  • Code-Fix Agent (Patch Generation)     │ │
                      │ │  • Sentiment Analyzer                    │ │
                      │ └──────────────────────┬───────────────────┘ │
                      │                        ▼                     │
                      │ ┌──────────────────────────────────────────┐ │
                      │ │  RAG & Memory (ChromaDB)                 │ │
                      │ │  • Incident Vector Store                 │ │
                      │ │  • Long-Term Context Memory Store        │ │
                      │ └──────────────────────┬───────────────────┘ │
                      │                        ▼                     │
                      │ ┌──────────────────────────────────────────┐ │
                      │ │  LLM Serving Engine (Ollama)             │ │
                      │ │  • Llama3-8B (Primary Ops Core)          │ │
                      │ │  • DeepSeek-R1-7B (Structured SQL Gen)   │ │
                      │ │  • Mistral-7B & LLaVA-7B (Multimodal)    │ │
                      │ └──────────────────────┬───────────────────┘ │
                      │                        ▼                     │
                      │ ┌──────────────────────────────────────────┐ │
                      │ │  Hardware Acceleration (AMD MI300X)      │ │
                      │ │  • 192 GB HBM3 Ultra-High Bandwidth VRAM │ │
                      │ │  • Unsloth QLoRA Optimization Engine     │ │
                      │ │  • Native Flash Attention Integration    │ │
                      │ └──────────────────────┬───────────────────┘ │
                      │                        ▼                     │
                      │ ┌──────────────────────────────────────────┐ │
                      │ │  Security & Core Infrastructure          │ │
                      │ │  • Prompt Injection Guardrails & Audits  │ │
                      │ │  • Redis Rate Limiting / JWT Auth + RBAC │ │
                      │ │  • Async Task Delegation via Celery      │ │
                      │ └──────────────────────────────────────────┘ │
                      └───────────────────────┬──────────────────────┘
                                              │
                                              ▼
                      ┌──────────────────────────────────────────────┐
                      │          Gradio Frontend Interface           │
                      │  • 16 Integrated Operator Control Tabs       │
                      │  • Analytics, Real-Time Monitoring & Triage  │
                      └──────────────────────────────────────────────┘

```

## 🗂️ Project Structure

<details>
<summary>📂 Click to expand the full repository map</summary>

```text
cloud-hackathon-tcs-amd/
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── auth.py                     # JWT + bcrypt authentication system
│   ├── models.py                   # SQLAlchemy ORM models (15 relational tables)
│   ├── guardrails.py               # Security layer: PII masking & injection detection
│   ├── gpu_utils.py                # Hardware layer: AMD MI300X auto-detection engine
│   ├── cache.py                    # Performance layer: Redis caching layer utilities
│   ├── chroma_store.py             # Database layer: ChromaDB vector store interface
│   ├── create_admin.py             # Provisioning script: Admin user initialization
│   ├── seed_data.py                # Database seed script: Mock production telemetry
│   ├── agents/                     # 🤖 Core AI Agent Execution Pipeline
│   │   ├── chat.py                 # Intelligent multi-model orchestration agent
│   │   ├── diagnosis.py            # Deep root-cause analysis context compiler
│   │   ├── monitor.py              # Real-time anomaly detection heuristics parser
│   │   ├── remediation.py          # Auto-healing recommendation & script compiler
│   │   ├── alerting.py             # Outbound communication (Email, Slack, Teams)
│   │   ├── code_fixer.py           # Automated code patch & diff generation pipeline
│   │   ├── sentiment.py            # Real-time operator sentiment analyzer
│   │   ├── predictor.py            # Proactive system incident prediction matrix
│   │   ├── clustering.py           # Log event grouping & signature matching engine
│   │   ├── rca_tree.py             # Root Cause Analysis tree data structures
│   │   ├── runbook.py              # Contextual runbook auto-generation processor
│   │   ├── knowledge_base.py       # SRE documentation & knowledge base auto-compiler
│   │   ├── memory.py               # Conversational persistent long-term memory
│   │   ├── gamification.py         # Engagement tier: Leaderboard, metrics, badges
│   │   ├── vision_analyzer.py      # Multimodal layer: LLaVA image context analysis
│   │   ├── image_analyzer.py       # Traditional computer vision: OCR log analyzer
│   │   ├── log_streamer.py         # Async event loop live log streaming module
│   │   ├── live_monitor.py         # Active monitoring polling engine
│   │   ├── gpu_trainer.py          # LLM tuning: Unsloth QLoRA fine-tuning script
│   │   ├── dependency_graph.py     # Microservice topology dependency graph builder
│   │   ├── causal_graph.py         # Stat engine: Granger causality mapping processor
│   │   ├── rl_triage.py            # Reinforcement Learning incident prioritization
│   │   ├── nl_to_sql.py            # Query layer: Natural language to SQL compiler
│   │   ├── pdf_generator.py        # Executive reporting: PDF compiler backend
│   │   ├── bulk_processor.py       # Batch log ingestion & multi-threading layer
│   │   ├── health_scorer.py        # Composite real-time system health score utility
│   │   └── benchmark.py            # Inference speed & execution performance tracer
│   ├── routers/                    # 🧭 FastAPI API Endpoints & Route Triggers
│   │   ├── admin.py                # System management & administrative panel routes
│   │   ├── incidents.py            # Incident management CRUD operations data pipe
│   │   ├── chat.py                 # Interactive chat session context streams
│   │   ├── diagnosis.py            # Log analysis & visual telemetry parser entries
│   │   ├── community.py            # SRE collaborative internal forum endpoints
│   │   ├── notifications.py        # Push notification message queues
│   │   ├── workflow.py             # Autonomous recovery workflow orchestration
│   │   ├── audit.py                # Read-only historic system audit log viewer
│   │   ├── workspace.py            # Corporate multi-tenant isolation partitions
│   │   ├── api_keys.py             # Programmatic service token management
│   │   ├── workers.py              # Background Celery task tracking routes
│   │   ├── dashboard.py            # Aggregated core operations data payload
│   │   ├── timeline.py             # Sequential incident event chain chronological paths
│   │   ├── bulk_pdf.py             # Bulk operations report export trigger
│   │   ├── train.py                # Hyperparameter tuning execution endpoints
│   │   ├── dependency.py           # Topology mapping engine data adapters
│   │   ├── causal.py               # Causality correlation processing endpoints
│   │   ├── rl_triage.py            # Intelligent priority queue routing layer
│   │   ├── sql_runner.py           # Database query inspection terminal adapter
│   │   ├── live_monitor.py         # Active telemetry updates pipeline
│   │   └── analytics.py            # Trend insight engine computation entry points
│   ├── middleware/
│   │   └── rate_limit.py           # Security middleware: Redis sliding-window limit
│   └── utils/
│       └── audit_logger.py         # Immutable secure event tracing system logger
├── frontend/                       # 🎨 UI & Dashboard Presentation Layer (Gradio)
│   ├── app.py                      # Main UI coordinator & tab initialization
│   ├── auth.py                     # Session guard: Login, verification & logout views
│   ├── chat.py                     # Real-time SRE AI Copilot assistance panel
│   ├── diagnosis.py                # Live telemetry diagnosis system dashboard
│   ├── incidents.py                # Historical incident search & response logs
│   ├── notifications.py            # Operator live system update notifications UI
│   ├── tickets.py                  # Operational help-desk ticketing client view
│   ├── community.py                # Shared learning center internal team bulletin
│   ├── admin.py                    # High-level system administration & analytics
│   ├── css.py                      # Dynamic styling sheets (Glassmorphic theme UI)
│   ├── utils.py                    # Frontend formatting and widget helpers
│   ├── pages/                      # 📑 Component view modules
│   │   ├── bulk_analysis.py        # Multi-file log analysis console view
│   │   ├── model_training.py       # Fine-tuning job configuration dashboard
│   │   ├── dependency_graph.py     # Reactive service structure canvas frame
│   │   ├── causal_graph.py         # Time-series impact graph view
│   │   ├── rl_triage.py            # Dynamic priority tracking panel
│   │   ├── sql_runner.py           # Secure runtime query scratchpad interface
│   │   ├── live_monitor.py         # Real-time updating telemetry dashboard
│   │   ├── smart_analytics.py      # Trend analysis & pattern graph aggregates
│   │   └── demo_tour.py            # Interactive system walkthrough module
│   ├── components/                 # 🧱 Modular Reusable Gradio Widgets
│   │   ├── cards.py                # High-contrast metric display grid templates
│   │   ├── progress.py             # Computation status tracking timelines
│   │   └── headers.py              # Consistent responsive layout boundaries
│   └── styles/
│       └── bulk_analysis.py        # Isolated file analysis layout custom rules
├── dummy_sites/
│   └── log_generator.py            # Local telemetry pipeline log engine simulator
├── logs/
│   └── live_stream.log             # Primary streaming target file (Auto-generated)
├── start_logs.sh                   # Automator script: Log stream execution manager
├── requirements.txt                # Fixed framework dependencies manifest
└── README.md                       # Comprehensive operational guide

```



## 🧰 Tech Stack

| Category | Technologies |
|----------|--------------|
| **AI/ML Models** | Llama3‑8B, DeepSeek‑R1‑7B, Mistral‑7B, LLaVA‑7B (vision) |
| **LLM Serving** | Ollama (local, GPU‑accelerated) |
| **Fine‑Tuning** | Unsloth (QLoRA), PEFT, bitsandbytes, Hugging Face Transformers |
| **Vector Database & RAG** | ChromaDB, Sentence‑Transformers |
| **Agent Framework** | Custom multi‑agent pipeline (Monitor, Diagnosis, Remediation, Code‑Fix, Alerting, Sentiment) |
| **Reinforcement Learning** | Q‑learning (NumPy), Granger causality (statsmodels), Pearson correlation (scipy) |
| **Backend Framework** | FastAPI (async REST), Uvicorn, Celery (background workers), Pydantic (validation) |
| **Database & Caching** | SQLite (WAL mode for concurrency), Redis (caching, rate‑limiting, session store) |
| **Authentication & Security** | JWT (JSON Web Tokens), bcrypt (password hashing), RBAC (role‑based access control) |
| **AI Safety** | PII masking (regex), prompt injection detection, destructive command blocking |
| **Frontend** | Gradio 5 (16 tabs), Plotly (interactive charts), Custom CSS (glass‑morphism design) |
| **GPU Acceleration** | AMD MI300X (192 GB HBM3), ROCm 7.0, Flash Attention, PyTorch |
| **PDF Generation** | ReportLab (professional multi‑page reports with charts and tables) |
| **Image Processing** | Pillow, Tesseract OCR, LLaVA (vision‑language model) |
| **DevOps & Scripts** | Shell scripts (start_logs.sh, auto‑setup), GitHub |
| **Monitoring & Logging** | Custom log generators (ecommerce, API gateway, database scenarios), Python logging |
| **Testing & Quality** | Custom guardrails tester, synthetic data generator, security test suite |


## 📦 Installation

### Prerequisites
- **Python 3.10+** with pip
- **AMD MI300X GPU** (or CPU fallback – automatically detected)
- **ROCm 7.0** installed and configured
- **Ollama** installed and running (`ollama serve`)

### 1. Clone the Repository
```bash
git clone https://github.com/amanmukati09/cloud-hackathon-tcs-amd.git
cd cloud-hackathon-tcs-amd

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

ollama pull llama3                 # Primary chat & diagnosis (8B params)
ollama pull deepseek-r1:7b         # SQL generation for Smart Analytics
ollama pull mistral:7b             # Alternative model
ollama pull llava:7b               # Vision model for image analysis

python backend/create_admin.py

./start_logs.sh # For live monitoring 

python backend/main.py sleep 5

Expected Output: 

✅ AMD GPU: AMD Instinct MI300X (192GB VRAM)
INFO:     Uvicorn running on http://0.0.0.0:8000

python frontend/app.py &

The frontend will be available at http://localhost:7860 (and a temporary public URL and click that).

## 🚀 Usage

### Getting Started
1. Open your browser to **http://localhost:7860** (or the public `.gradio.live` URL shown in the terminal).
2. **Login** with the admin credentials you created during setup, or click the **Register** tab to create a new account.
3. Explore the **16 tabs** – each one is a complete feature module.

### Feature Quick‑Start Guide

| Tab | What to Do | Expected Result |
|-----|------------|-----------------|
| **Live Diagnosis** | Paste server logs (e.g., `[ERROR] nginx worker crashed`) → click **Analyze Logs** | AI displays anomaly type, root cause, and remediation steps |
| **Bulk Analysis** | Upload a `.log` file with 100+ lines → click **Analyze Logs** → click **PDF Report** | Downloads a professional PDF with severity charts and RCA |
| **AI Copilot** | Type any SRE question → click **Send** | Streaming AI response with context from past incidents |
| **Smart Analytics** | Type *"Show me critical incidents this month"* → click **Ask AI** | AI generates SQL, executes it, displays results in a table |
| **Live Monitor** | Click **▶️ Start** (ensure log generator is running) | Real‑time log stream with color‑coded lines and active incidents |
| **Train Model** | Select base model → click **Start Training** → wait ~15 min → chat with your model | Fine‑tuned model appears in the built‑in chat and AI Copilot |
| **Dependency Graph** | Click **Refresh Graph** → click any node | Visual service map with blast‑radius analysis |
| **RL Triage** | Click **Train RL Agent** → click **Refresh Queue** | Incidents sorted by AI‑predicted priority (P1‑P5) |
| **SQL Runner** (Admin) | Type `SELECT * FROM incidents LIMIT 10` → click **Execute** | Query results in a scrollable table |
| **Knowledge Base** | Click **Generate Knowledge Base** → type a query → click **Search** | AI‑curated articles from resolved incidents |

### Key Workflows

**End‑to‑End Incident Resolution:**
1. Go to **Live Diagnosis** → paste logs → click **Analyze**.
2. Review the anomaly, root cause, and remediation.
3. Click **Auto‑Remediate** to execute safe fixes.
4. The incident is saved to **Incident History** automatically.
5. Go to **Incident History** → click the incident → **Generate Runbook** or **Export PDF**.

**Live Monitoring Workflow:**
1. Start the log generator: `./start_logs.sh &`
2. Go to **Live Monitor** → click **▶️ Start**.
3. Watch the real‑time log stream.
4. CRITICAL incidents auto‑create and appear in the Active Incidents panel.
5. Use the AI Chat to ask questions about the live stream.
6. Click **⏹️ Stop** to end the session and get a summary.

**Model Training Workflow:**
1. Go to **Train Model** → select a base model → click **Start Training**.
2. Wait ~15 minutes (progress bar shows steps and loss).
3. When complete, use the built‑in chat to test your model immediately.
4. Log out and log back in – your fine‑tuned model now appears in the **AI Copilot** dropdown.

**Admin Dashboard Monitoring:**
1. After login, the admin dashboard shows **System Health Score**, **AI Benchmark Card**, and **Analytics Charts**.
2. Use **User Management** to view, inspect, or delete user accounts.
3. Use **SQL Runner** to query the database directly.
4. Use **Alert Settings** to configure email/Slack/Teams notifications.

### 🎬 Demo Mode
Click the **🎬 Demo** button in the top navigation bar to see a guided overview of the 5 hero features. Click **✕ Close** to dismiss.

## 🎥 Demo

[![AegisAI Demo](https://img.shields.io/badge/Watch_Demo-YouTube-red)](https://youtu.be/your-video-id)

*A 4‑minute walkthrough covering the 5 hero features: Live Diagnosis, Bulk PDF, Smart Analytics, Dependency Graph, and Live Monitor.*

---

## 🤝 Team

| Name | Role | Responsibilities |
|------|------|------------------|
| **Aman Mukati** | AI/ML Architect | Multi‑agent pipeline, fine‑tuning (QLoRA), RL triage, RAG integration, GPU optimisation |
| **Amitesh Thakur ** | Full‑Stack & GPU Integration | Backend API, Live Monitor, Bulk PDF processor, real‑time streaming, GPU auto‑detection |
| **Karan Singh Rana** | UI/UX & Product Design | Premium Gradio dashboard, Demo Tour, CSS design system, 16‑tab layout, user experience |

*Built with ❤️ at the **TCS AMD Hackathon 2026**.*

---

## 📄 License

MIT License

Copyright (c) 2026 Aman Mukati

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.   


---

## 🙏 Acknowledgements

- **AMD** for providing the MI300X GPU (192 GB) and ROCm 7.0 platform
- **Ollama** for local LLM serving
- **Unsloth** for fast QLoRA fine‑tuning
- **Gradio** for the flexible UI framework
- **ChromaDB** for vector storage
- **Hugging Face** for model access and transformers library
---

## 📬 Contact

For questions, issues, or contributions:
- **GitHub Issues:** [Create an issue](https://github.com/amanmukati09/cloud-hackathon-tcs-amd/issues)
---

> **AegisAI** – *Because your infrastructure deserves an intelligent shield.* 🛡️


