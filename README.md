# VPBank AI Financial Coach Backend – Hackathon Solution

A production-ready backend for the VPBank Hackathon (Track: Financial 6-Jar Coaching), delivering a smart, multi-agent AI system that helps users manage their finances using the proven "6-Jar" method. Built for real-world deployment, this project combines advanced AI orchestration, robust business logic, and modern API design.

---

**Team of 5:**
- **Phan Trọng Đài** – AI Engineer, Backend Developer, Team Leader (me)
- Huỳnh Quốc Huy & Nguyễn Trọng Doanh ([Frontend](https://github.com/HCMUS-HQHuy/VPBANK-HACKATHON))
- Vũ Đình Ngọc Bảo & Lê Minh Hoàng (Cloud/Ops)

---

## TL;DR

### Multi-agent System
![Multi-agent system](image/README_2025-07-25-20-43-56.png)

### Tech Stack
![Tech stack](image/README_2025-07-25-20-45-10.png)

### Slide Presentation
Check our [slide](https://www.canva.com/design/DAGtbu7Joyw/C_bgRw29fAdxmTAOw00Obg/edit)

### Result
2nd round participants, ranked ~100th out of 1000+ teams!

---

## 🚀 What is this repo?

This is the **backend solution** for VPBank Hackathon, Track 9: Financial Innovation (6-Jar Coaching):

- Modular, multi-agent AI system for personal finance
- Implements the classic 6-jar budgeting method (T. Harv Eker)
- FastAPI REST API with MongoDB
- Full Vietnamese & English support
- Comprehensive automated and interactive testing

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend System Architecture              │
├─────────────────────────────────────────────────────────────┤
│  🌐 REST API Layer (FastAPI)                               │
│  ├── Authentication (JWT)                                   │
│  ├── Jar, Transaction, Fee, Plan, User Settings Endpoints   │
│  ├── AI Chat Interface (Orchestrator)                       │
├─────────────────────────────────────────────────────────────┤
│  🛠️ Service Layer (Business Logic)                         │
│  ├── JarManagementService, TransactionService, etc.         │
│  ├── OrchestratorService (AI Agent Bridge)                  │
│  ├── FinancialServices, Adapters, Security                  │
├─────────────────────────────────────────────────────────────┤
│  🗄️ Data Access Layer (MongoDB)                            │
│  ├── User, Jar, Transaction, Fee, Plan, Conversation, Lock  │
├─────────────────────────────────────────────────────────────┤
│  🤖 Agent System Integration                                │
│  ├── Orchestrator, Classifier, Knowledge, Plan, Fee, Jar    │
│  └── 100% compatible with original lab agents               │
└─────────────────────────────────────────────────────────────┘
```

- **Multi-agent orchestration:** 7 specialized agents (Classifier, Jar, Fee, Plan, Fetcher, Knowledge, Orchestrator)
- **Async, modular, extensible:** All business logic is async and separated by domain
- **AI-powered:** Natural language chat, automatic classification, proactive financial advice
- **6-Jar system:** Smart, flexible implementation of the classic budgeting method

---

## 🌟 Main Features

- **Multi-Agent AI Orchestration:** 7 agents coordinate to deliver context-aware, intelligent financial coaching.
- **6-Jar Budgeting System:** Implements T. Harv Eker's method with automatic jar creation, rebalancing, and validation.
- **AI Chat Interface:** Natural language chat with the orchestrator agent, supporting Vietnamese and English, with context retention and agent handoff.
- **Production-Ready Security:** JWT authentication, password hashing, user isolation, CORS, and input validation.
- **Backend Business Logic:** All calculations, validation, and financial rules are enforced server-side for data integrity and security.
- **Extensible & Modular:** Each feature is a separate service, agent, and API router—easy to extend or adapt for new requirements.
- **Vietnamese Localization:** Native support for Vietnamese language and financial context.
- **Modern API Design:** FastAPI, async MongoDB, Pydantic models, OpenAPI docs, and robust error handling.

---

## ⚡ Setup & Run

### 1. Prerequisites
- Python 3.8+
- MongoDB (local or Atlas)
- Google Gemini API key(s)

### 2. Clone & Install
```bash
git clone <repo-url>
cd vpb_hackathon
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your MongoDB, JWT, and Google API key(s)
```

### 4. Start the Backend
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the Backend
```bash
cd frontend
python fully_test.py         # Full API and agent test suite
python chat_simulator.py     # Interactive chat simulator
python mock.py               # Focused API scenario tests
```

---

## 📚 More Info

- [Backend details and API docs](backend/README.md)
