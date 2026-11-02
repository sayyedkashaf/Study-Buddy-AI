# 🎓 Study Buddy AI

> An agentic AI application that acts as your personal study assistant.  
> Upload your syllabus, chat with AI agents, get personalized study plans, and track your progress.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Gemini](https://img.shields.io/badge/Google-Gemini%203.8%20Flash-blue?logo=googlegemini)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- **📄 Syllabus Upload & Parsing** — Upload PDF syllabi, auto-extract topics, and index them for semantic search.
- **💬 Agentic Chat** — Multi-agent system with intelligent routing (Planner, Assignment Helper, Memory).
- **📅 Study Plan Generator** — AI-powered personalized study schedules with weighted topic distribution.
- **📊 Attendance Tracker** — Track class attendance, get percentage warnings, and receive AI-powered advice.
- **🧠 Conversation Memory** — RAG-based context retrieval across chat sessions.

---

## 🏗️ Architecture

```text
User → Streamlit UI → FastAPI Backend
                          │
                    ┌─────┴─────┐
                    │Orchestrator│
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
         PlannerAgent AssignmentAgent MemoryAgent
              │           │           │
              └───────────┼───────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
           ChromaDB     SQLite       Redis
           (vectors)  (structured)  (cache)
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core programming language |
| **FastAPI** | Backend API |
| **Streamlit** | Frontend interface |
| **Google Gemini API** | AI model inference |
| **SQLite** | Primary database |
| **ChromaDB** | Vector database for RAG |
| **Redis** | Optional caching |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git
- Google Gemini API key ([Get one from Google AI Studio](https://aistudio.google.com/apikey))
- Redis (optional)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/study-buddy.git
cd study-buddy

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env

# Edit .env and add your GEMINI_API_KEY

# 5. Start FastAPI backend (Terminal 1)
uvicorn api.main:app --reload --port 8000

# 6. Start Streamlit frontend (Terminal 2)
streamlit run app.py

# 7. Open http://localhost:8501
```

---

## 🔑 Environment Variables

```env
# Required
GEMINI_API_KEY=your_gemini_api_key

# Gemini models
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FAST_MODEL=gemini-3.8-flash

# Optional
DATABASE_URL=sqlite:///./data/study_buddy.db
REDIS_HOST=localhost
REDIS_PORT=6379
CHROMA_PATH=./data/chroma
DEBUG=True
LOG_LEVEL=INFO
```

---

## 📁 Project Structure

```text
study-buddy/
├── app.py
├── api/
│   ├── main.py
│   ├── routes/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── planner.py
│   │   └── attendance.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── orchestrator.py
│   │   ├── planner_agent.py
│   │   ├── assignment_agent.py
│   │   └── memory_agent.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── pdf_parser.py
│   │   ├── vector_store.py
│   │   ├── cache_service.py
│   │   ├── study_planner.py
│   │   └── embeddings.py
│   ├── models/
│   │   ├── database.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── study_plan.py
│   │   └── attendance.py
│   └── core/
│       ├── config.py
│       └── dependencies.py
├── data/
│   ├── uploads/
│   └── chroma/
├── tests/
│   ├── test_agents.py
│   ├── test_pdf_parser.py
│   └── test_vector_store.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 📖 API Documentation

Once the backend is running, visit:

**http://localhost:8000/docs**

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/message` | Send a message to the agentic chat system |
| `POST` | `/documents/upload` | Upload and index a syllabus PDF |
| `GET` | `/documents/list` | List uploaded documents |
| `POST` | `/planner/generate` | Generate a study plan |
| `GET` | `/planner/{user_id}` | Get study plans |
| `POST` | `/attendance/mark` | Mark class attendance |
| `GET` | `/attendance/{user_id}/{subject_id}` | Get attendance statistics |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_pdf_parser.py -v

# Run with coverage
pytest tests/ -v --cov=api
```

---

## 🚀 Deployment

### Streamlit Cloud (Frontend)

1. Push the project to GitHub.
2. Visit [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your repository.
4. Configure the required environment variables/secrets.

### Railway (Backend)

1. Push the project to GitHub.
2. Connect your repository to [Railway](https://railway.app/).
3. Add the required environment variables, including `GEMINI_API_KEY`.
4. Update `API_URL` in `app.py` if needed.

---

## 📈 Future Improvements

- [ ] Quiz Generator Agent
- [ ] Google Calendar integration
- [ ] Spaced repetition (SM-2 algorithm)
- [ ] Collaborative study groups
- [ ] Mobile-responsive React frontend
- [ ] Multi-user authentication (OAuth2)

---

**Built with** ❤️ using FastAPI • Streamlit • Google Gemini • SQLite • ChromaDB • Redis
