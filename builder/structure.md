# Project Structure: AI NARAGI Chatbot website

This document defines the folder architecture for the **AI NARAGI** project. The structure follows a decoupled full-stack approach, separating the user interface, API logic, and AI processing core to ensure simplicity and scalability.

## **Technology Stack**

To keep the development process accessible for beginners, the following stack is recommended:
- **Frontend:** React (Vite) + Tailwind CSS
- **Backend:** FastAPI (Python)
- **AI Core:** Python (HuggingFace, FAISS, LangChain/LlamaIndex)
- **Database:** SQLite3 (Relational) & FAISS (Vector Store)

## ** Technical Specifications **

### 1. Frontend (Client-side)
- **Framework:** React.js (via Vite)
- **Styling:** Tailwind CSS
- **State Management:** React Context API or Zustand
- **API Client:** Axios
- **Icons:** Lucide React

---

## **Directory Tree**

ai-naragi/
├── frontend/                # React Vite Application (React Vite + Tailwind)
│   ├── src/
│   │   ├── components/      # UI components (ChatBox, Sidebar, etc.)
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API call definitions (Axios/Fetch)
│   │   └── App.jsx
│   ├── public/              # Static assets
│   └── package.json
│
├── backend/                 # FastAPI Python Application
│   ├── app/
│   │   ├── api/             # API Route handlers (endpoints)
│   │   ├── core/            # Config, security, and global constants
│   │   ├── schemas/         # Pydantic models for validation
│   │   └── main.py          # Entry point for FastAPI
│   ├── requirements.txt
│   └── .env                 # Environment variables
│
├── llm_core/                 # AI & Linguistic Logic
│   ├── engine/              # LLM wrappers (Qwen2.5 7B Intruct integration)
│   ├── retrieval/           # RAG logic & FAISS indexing
│   └── utils/               # Japanese linguistic processing (Pitch Accent)
│
├── data/                    # Storage
│
├── docs/                    # Graduation Thesis Documentation
│   └── reports/
│
├── config/                  # Global configuration files
└── README.md