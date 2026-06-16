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

┌──────────────────┐ ┌──────────────────────────────────────────────┐ ┌─────────────────────┐
│ Log Sources │ │ FastAPI Backend │ │ Gradio Frontend │
│ (files, APIs, │─────▶│ ┌──────────────────────────────────────────┐│─────▶│ (16 tabs) │
│ simulators) │ │ │ AI Agent Pipeline ││ │ │
└──────────────────┘ │ │ • Monitor Agent (anomaly detection) ││ └─────────────────────┘
│ │ • Diagnosis Agent (root cause) ││
│ │ • Remediation Agent (fix suggestions) ││
│ │ • Alerting Agent (email/Slack/Teams) ││
│ │ • Code‑Fix Agent (patch generation) ││
│ │ • Sentiment Analyzer ││
│ └───────────────┬──────────────────────────┘│
│ │ │
│ ┌───────────────▼──────────────────────────┐│
│ │ RAG & Memory (ChromaDB) ││
│ │ • Incident vector store ││
│ │ • Chat long‑term memory ││
│ └───────────────┬──────────────────────────┘│
│ │ │
│ ┌───────────────▼──────────────────────────┐│
│ │ LLM Serving (Ollama) ││
│ │ • Llama3‑8B (primary) ││
│ │ • DeepSeek‑R1‑7B (SQL generation) ││
│ │ • Mistral‑7B (alternative) ││
│ │ • LLaVA‑7B (vision) ││
│ │ • Fine‑tuned Aegis‑SRE (GGUF) ││
│ └───────────────┬──────────────────────────┘│
│ │ │
│ ┌───────────────▼──────────────────────────┐│
│ │ GPU Acceleration (AMD MI300X) ││
│ │ • QLoRA fine‑tuning (Unsloth) ││
│ │ • Batch embedding generation ││
│ │ • Flash Attention ││
│ │ • 192 GB HBM3 VRAM ││
│ └──────────────────────────────────────────┘│
│ │
│ ┌──────────────────────────────────────────┐│
│ │ Security & Infrastructure ││
│ │ • Guardrails (PII, injection, commands) ││
│ │ • Rate Limiter (Redis) ││
│ │ • JWT Auth + RBAC ││
│ │ • Audit Logger ││
│ │ • Background Workers (Celery) ││
│ └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘


## 🗂️ Project Structure

cloud-hackathon-tcs-amd/
├── backend/
│ ├── main.py # FastAPI entry point
│ ├── auth.py # JWT + bcrypt authentication
│ ├── models.py # SQLAlchemy models (15 tables)
│ ├── guardrails.py # PII masking, injection detection
│ ├── gpu_utils.py # AMD MI300X auto‑detection
│ ├── cache.py # Redis caching utilities
│ ├── chroma_store.py # ChromaDB vector store interface
│ ├── create_admin.py # Admin user creation script
│ ├── seed_data.py # Test data seeder
│ ├── agents/
│ │ ├── chat.py # Multi‑model chat agent
│ │ ├── diagnosis.py # Root‑cause analysis agent
│ │ ├── monitor.py # Anomaly detection agent
│ │ ├── remediation.py # Remediation suggestion agent
│ │ ├── alerting.py # Email/Slack/Teams alerting
│ │ ├── code_fixer.py # Code patch generation
│ │ ├── sentiment.py # User sentiment analysis
│ │ ├── predictor.py # Incident prediction engine
│ │ ├── clustering.py # Incident clustering
│ │ ├── rca_tree.py # RCA tree visualisation
│ │ ├── runbook.py # Runbook auto‑generation
│ │ ├── knowledge_base.py # KB article generation
│ │ ├── memory.py # Chat long‑term memory
│ │ ├── gamification.py # Points, badges, leaderboard
│ │ ├── vision_analyzer.py # LLaVA image analysis
│ │ ├── image_analyzer.py # OCR‑based image analysis
│ │ ├── log_streamer.py # Live log streaming
│ │ ├── live_monitor.py # Real‑time monitoring engine
│ │ ├── gpu_trainer.py # QLoRA fine‑tuning pipeline
│ │ ├── dependency_graph.py # Service dependency graph
│ │ ├── causal_graph.py # Granger causality engine
│ │ ├── rl_triage.py # RL incident prioritisation
│ │ ├── nl_to_sql.py # Natural language → SQL
│ │ ├── pdf_generator.py # PDF report generation
│ │ ├── bulk_processor.py # Bulk log processor
│ │ ├── health_scorer.py # System health score
│ │ └── benchmark.py # AI performance benchmark
│ ├── routers/
│ │ ├── admin.py # Admin dashboard endpoints
│ │ ├── incidents.py # Incident CRUD endpoints
│ │ ├── chat.py # Chat + model endpoints
│ │ ├── diagnosis.py # Diagnosis + image analysis
│ │ ├── community.py # Forum endpoints
│ │ ├── notifications.py # Notification endpoints
│ │ ├── workflow.py # Autonomous workflow
│ │ ├── audit.py # Audit log viewer
│ │ ├── workspace.py # Multi‑tenant workspaces
│ │ ├── api_keys.py # API key management
│ │ ├── workers.py # Background task workers
│ │ ├── dashboard.py # Dashboard summary
│ │ ├── timeline.py # Incident timeline
│ │ ├── bulk_pdf.py # Bulk analysis + PDF
│ │ ├── train.py # Model training endpoints
│ │ ├── dependency.py # Dependency graph endpoints
│ │ ├── causal.py # Causal graph endpoints
│ │ ├── rl_triage.py # RL triage endpoints
│ │ ├── sql_runner.py # Admin SQL runner
│ │ ├── live_monitor.py # Live monitor endpoints
│ │ └── analytics.py # Smart analytics endpoints
│ ├── middleware/
│ │ └── rate_limit.py # Redis rate limiter
│ └── utils/
│ └── audit_logger.py # Audit logging utility
├── frontend/
│ ├── app.py # Main Gradio application
│ ├── auth.py # Login/register/logout UI
│ ├── chat.py # AI Copilot UI
│ ├── diagnosis.py # Live Diagnosis UI
│ ├── incidents.py # Incident History UI
│ ├── notifications.py # Notifications UI
│ ├── tickets.py # Support Tickets UI
│ ├── community.py # Community Forum UI
│ ├── admin.py # Admin Dashboard UI
│ ├── css.py # Premium CSS (glass‑morphism)
│ ├── utils.py # Frontend utilities
│ ├── pages/
│ │ ├── bulk_analysis.py # Bulk Analysis page
│ │ ├── model_training.py # Model Training page
│ │ ├── dependency_graph.py # Dependency Graph page
│ │ ├── causal_graph.py # Causal Graph page
│ │ ├── rl_triage.py # RL Triage page
│ │ ├── sql_runner.py # SQL Runner page
│ │ ├── live_monitor.py # Live Monitor page
│ │ ├── smart_analytics.py # Smart Analytics page
│ │ └── demo_tour.py # Demo Tour overlay
│ ├── components/
│ │ ├── cards.py # Reusable card layouts
│ │ ├── progress.py # Progress bars & spinners
│ │ └── headers.py # Section headers
│ └── styles/
│ └── bulk_analysis.py # Page‑specific CSS
├── dummy_sites/
│ └── log_generator.py # Realistic log simulator
├── logs/
│ └── live_stream.log # Default log file (auto‑created)
├── start_logs.sh # Quick log generator launcher
├── requirements.txt # Python dependencies
└── README.md # This file



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


