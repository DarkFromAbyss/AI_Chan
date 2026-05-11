# Project Structure and Technical Stack (AI NARAGI)

This document outlines the architecture, directory structure, and technical constraints of the AI NARAGI chatbot project.

---

## 1. Technology Stack
To ensure simplicity, high performance, and ease of deployment, the following technologies are selected:

### **Core Stack**
* **Language:** Python 3.10+ (Main language for Backend and AI logic).
* **Backend:** **FastAPI** (High performance, asynchronous, and easy to integrate with AI libraries).
* **Frontend:** **React.js (with Vite)** + **Tailwind CSS** (Fast development and modern UI).
* **Database:** * **SQLite:** For user data and chat history (simple, file-based).
    * **FAISS:** For vector storage and semantic search (Semantic Cache).
* **AI Framework:** **LangChain** & **LangGraph** (For orchestration and agentic workflows).

### **Environment & Deployment**
* **Environment Management:** `venv` or `Conda`.
* **API Communication:** REST API.

---

## 2. Component Descriptions

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Frontend** | React + Vite | User interface, real-time chat display, and Voicevox audio playback. |
| **Backend** | FastAPI | Routing, authentication, and bridging the UI with the AI Core. |
| **LLM Core** | LangChain/LangGraph | Prompt engineering, RAG logic, and processing the "Sensei" persona. |
| **Data** | FAISS + JSON/CSV | Storing processed vocabulary, Anki data, and vector indices. |
| **Models** | GGUF / Quantized | Storing local LLM weights (e.g., Qwen2.5-7B-Instruct-4bit). |

---

## 3. Directory Tree

```text
ai-naragi-project/
├── frontend/                # React Vite Application
│   ├── src/
│   │   ├── components/      # Reusable UI parts (ChatBox, Sidebar)
│   │   ├── hooks/           # Custom React hooks
│   │   └── services/        # API calls to Backend
│   └── package.json
├── backend/                 # FastAPI Application
│   ├── app/
│   │   ├── api/             # API Route definitions
│   │   ├── core/            # Configs (env, logging, constants)
│   │   └── main.py          # Entry point
│   └── requirements.txt
├── llm_core/                # AI & Logic Engine
│   ├── agents/              # LangGraph state machines
│   ├── chains/              # Specialized LangChain sequences
│   ├── prompts/             # System and template prompts
│   └── utils/               # Text/Pitch accent processing
├── data/                    # Data Storage
├── models/                  # Model Weights (Git-ignored)
├── docs/                    # Project documentation (rules.md, struct.md)
├── .env                     # Secret keys and API configurations
└── .gitignore               # Exclude models/ and __pycache__/
```

## 4. System Constraints & Conflict Prevention
To maintain a clean system and prevent conflicts between the Frontend, Backend, and LLM modules, the following limits are imposed:

* **Isolation of LLM Logic**: The backend must never contain raw LLM logic or prompt strings. It must only call functions/classes exported from llm_core.

* **Stateless Backend**: The Backend should remain stateless. All session management must be handled via the database or passed through the session_id in API requests.

* **Data Schema Enforcement**: All data exchanged between frontend -> backend -> llm_core must strictly follow Pydantic Schemas. Changing a schema requires updates in all three layers.

* **Local Model Privacy**: The models/ directory must be added to .gitignore. Large model files should never be pushed to GitHub to avoid repository bloat.

* **Thread Safety**: Since the AI model consumes high GPU/CPU resources, the Backend must use async/await for API endpoints to prevent blocking other user requests while the model is generating text.

* **Dependency Versioning**: All libraries must be locked in requirements.txt with specific versions (e.g., langchain==0.1.x) to prevent breaking changes during updates.