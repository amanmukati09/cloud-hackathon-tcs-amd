# 🛡️ AegisAI – AI‑Powered Incident Management Platform

**AegisAI** is an enterprise‑grade Site Reliability Engineering (SRE) platform that combines **multi‑agent AI**, **Retrieval‑Augmented Generation (RAG)**, and **autonomous remediation** to detect, diagnose, and resolve infrastructure incidents in real time.

## 🚀 Features (25+)

### Core Platform
- **🔐 Authentication** – JWT‑based login/register with role‑based access (Admin / User)
- **📊 Admin Dashboard** – Real‑time analytics, incident predictions, anomaly clusters
- **👥 User Management** – Admin can inspect and manage all users

### AI & Intelligence
- **🤖 Multi‑Agent Pipeline** – Monitor → Diagnose → Remediate (3 specialized AI agents)
- **🧠 RAG (ChromaDB)** – Semantic search across 235+ past incidents for context‑aware answers
- **🦙 Multi‑Model Support** – Llama 3, DeepSeek R1, Mistral 7B (switchable in real time)
- **⚡ Streaming Responses** – Token‑by‑token AI output (ChatGPT‑style)
- **🔧 Auto‑Remediation** – Autonomous workflow: detect → diagnose → execute fixes
- **🌳 RCA Trees** – Visual root‑cause‑analysis trees
- **💻 Code Fix Generation** – AI generates actual code patches and configs
- **📋 Runbook Automation** – Generates executable recovery playbooks from resolved incidents
- **😤 Sentiment Analysis** – Detects user frustration and auto‑escalates
- **🔮 Incident Prediction** – ML‑based early warning system
- **🔬 Anomaly Clustering** – Auto‑groups similar incidents

### Collaboration & Productivity
- **🌐 Community Dashboard** – Twitter/X‑style feed with posts, comments, and likes
- **🎫 Support Tickets** – Escalation system with admin Q&A
- **🔔 Notifications** – Real‑time alerts for incidents, tickets, and admin actions

### Enterprise Features
- **📁 Bulk Log Upload** – Upload `.log` files for analysis
- **📥 Export** – CSV and professional PDF incident reports
- **🔔 Smart Alerting** – Slack & Microsoft Teams webhook integration
- **⚡ Redis Caching** – Performance boost with automatic invalidation
- **🐳 Docker Compose** – One‑command containerized deployment

## 🏗️ Architecture

┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ Frontend │────▶│ Backend │────▶│ Ollama │
│ (Gradio) │ │ (FastAPI) │ │ (Llama3 etc) │
└─────────────┘ └──────┬───────┘ └─────────────┘
│
┌──────┴───────┐
│ ChromaDB │
│ (Vector DB) │
└──────────────┘

## 📦 Quick Start (Local)

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 1. Clone
```bash
git clone https://github.com/YOUR_USERNAME/aegis-ai.git
cd aegis-ai

chmod +x setup.sh
./setup.sh

python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

ollama serve &
ollama pull llama3
ollama pull deepseek-r1:7b
ollama pull mistral:7b

python backend/create_admin.py

# Terminal 1 - Backend
python backend/main.py

# Terminal 2 - Frontend
python frontend/app.py

Open http://localhost:7860

docker compose up -d --build
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull deepseek-r1:7b
docker exec -it ollama ollama pull mistral:7b

🎮 How to Test Every Feature
#	Feature	How to Test
1	Login/Register	Create account or login as admin
2	Live Diagnosis	Paste logs → Click "Analyze Logs"
3	Multi‑Model	Select DeepSeek/Mistral in AI Copilot
4	Streaming	Send a message → Watch tokens appear
5	Auto‑Remediate	Paste logs → Click "Auto‑Remediate"
6	RCA Tree	Paste logs → Click "RCA Tree"
7	Code Fix	Paste logs → Click "Code Fix"
8	Runbook	Select resolved incident → "Generate Runbook"
9	Sentiment	Type "This is broken, help!" in chat
10	Predictions	Admin → Analytics → AI Predictions
11	Clusters	Admin → Analytics → Incident Clusters
12	Community	Post, comment, like in Community tab
13	Tickets	Submit ticket → Admin answers
14	Export	Incident History → Export CSV/PDF
15	Alerts	Admin → Alert Settings → Configure Slack


🛠️ Tech Stack
Layer	Technology
Frontend	Gradio 5.x
Backend	FastAPI, Uvicorn
AI Models	Ollama (Llama3, DeepSeek R1, Mistral 7B)
Vector DB	ChromaDB
Database	SQLite
Cache	fakeredis (Redis‑compatible)
Auth	JWT (python‑jose)
PDF	ReportLab
Container	Docker Compose

📁 Project Structure

aegis-ai/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── auth.py                 # JWT authentication
│   ├── models.py               # SQLAlchemy models
│   ├── chroma_store.py         # ChromaDB integration
│   ├── cache.py                # Redis caching
│   ├── guardrails.py           # PII masking & security
│   ├── create_admin.py         # Admin user creation
│   ├── agents/
│   │   ├── monitor.py          # Anomaly detection agent
│   │   ├── diagnosis.py        # Root cause analysis agent
│   │   ├── remediation.py      # Remediation suggestion agent
│   │   ├── chat.py             # Conversational AI agent
│   │   ├── sentiment.py        # Sentiment analysis
│   │   ├── predictor.py        # Incident prediction (ML)
│   │   ├── clustering.py       # Anomaly clustering
│   │   ├── rca_tree.py         # RCA tree generation
│   │   ├── code_fixer.py       # Code fix generation
│   │   ├── runbook.py          # Runbook automation
│   │   └── alerting.py         # Slack/Teams alerts
│   └── routers/
│       ├── diagnosis.py        # /diagnose, /upload-logs
│       ├── incidents.py        # /my-incidents, resolve, export
│       ├── chat.py             # /chat/message, /chat/sessions
│       ├── community.py        # /community/posts, comments
│       ├── admin.py            # /admin/metrics, users, tickets
│       ├── notifications.py    # /notifications
│       └── workflow.py         # /workflow/auto-remediate
├── frontend/
│   ├── app.py                  # Main Gradio UI
│   ├── css.py                  # Custom CSS styling
│   ├── utils.py                # Shared utilities
│   ├── auth.py                 # Login/Register/Logout
│   ├── diagnosis.py            # Diagnosis tab functions
│   ├── chat.py                 # AI Copilot functions
│   ├── incidents.py            # Incident history functions
│   ├── tickets.py              # Support ticket functions
│   ├── notifications.py        # Notification functions
│   ├── admin.py                # Admin dashboard functions
│   └── community.py            # Community feed functions
├── data/
│   └── chroma/                 # ChromaDB persistence
├── docker-compose.yml          # Docker deployment
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── setup.sh                    # One‑command setup script
└── README.md                   # This file

🏆 Hackathon Ready
25+ features fully implemented

RAG with user isolation (users only see their own incidents)

Multi‑agent pipeline with guardrails

Real‑time streaming responses

One‑command setup via setup.sh

Docker support for production deployment

📄 License
MIT License

👥 Team
Built with ❤️ for the hackathon.

Made for hackathons. Built for production.