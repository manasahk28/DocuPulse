# DocuPulse — AI Document Intelligence System

**DocuPulse** is a full-stack **Retrieval-Augmented Generation (RAG)** application that lets you upload PDF and text documents, index them into a PostgreSQL (`pgvector`) vector database, and have multi-turn, grounded Q&A conversations powered by Groq LLMs.

---

## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  React Frontend  │────▶│  FastAPI Backend   │────▶│  RAG Pipeline        │────▶│   Groq API   │
│  (Vite + TS +    │◀────│  (/upload, /query) │◀────│  (Chunk → Embed →    │◀────│   LLM Chat   │
│   Tailwind v4)   │     │                    │     │   Hybrid Retrieve)   │     │              │
└──────────────────┘     └────────────────────┘     └──────────┬───────────┘     └──────────────┘
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │  PostgreSQL +        │
                                                    │  pgvector (HNSW) +   │
                                                    │  Full-Text (GIN)     │
                                                    └──────────────────────┘
```

### Key Features

- **Layout-Aware Document Ingestion**: Extracts text from PDFs (`pypdf` layout mode) and plain-text files while preserving structure and paragraph boundaries.
- **Semantic Sentence Chunking**: Splits documents into ~200-word overlapping chunks using NLTK's Punkt sentence tokenizer.
- **Hybrid Vector + Full-Text Search**: Combines 768-dimensional dense embeddings (`sentence-transformers/all-mpnet-base-v2` + `pgvector` HNSW cosine similarity) with PostgreSQL `tsvector` GIN keyword search.
- **Multi-Query Expansion & Context Windowing**: Automatically generates alternative search phrasings via Groq LLM and expands retrieved chunks with neighboring passages (`±1` chunk index).
- **Conversational Memory**: Maintains multi-turn chat history so follow-up questions resolve naturally in context.
- **Mauve Haze UI**: Responsive React 19 + Tailwind CSS v4 interface with drag-and-drop uploads and GitHub-Flavored Markdown rendering.

---

## Repository Structure

```
DocSystem/
├── README.md                        # Main project documentation
├── .gitignore                       # Root Git ignore rules
├── backend/                         # FastAPI + RAG Backend
│   ├── .env.example                 # Template for backend environment variables
│   ├── .python-version              # Python 3.12 version pin for deployment
│   ├── requirements.txt             # Python dependencies (CPU-optimized PyTorch)
│   ├── README.md                    # Backend setup & architecture guide
│   ├── docs/
│   │   └── API.md                   # Detailed REST API endpoint reference
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, CORS, lifespan hooks
│   │   ├── routes/
│   │   │   ├── upload.py            # POST /upload, GET /chunks, POST /debug/upload
│   │   │   └── query.py             # POST /query, POST /query/stream (SSE)
│   │   └── services/
│   │       ├── embeddings.py        # SentenceTransformer 768-d embedding service
│   │       ├── retrieval.py         # PostgreSQL + pgvector + tsvector hybrid store
│   │       └── rag_pipeline.py      # End-to-end ingestion, retrieval & generation
│   └── tests/
│       └── test_pipeline_failures.py # Unit & edge-case test suite
└── frontend/                        # React 19 + TypeScript + Vite Frontend
    ├── .env.example                 # Template for frontend environment variables
    ├── package.json                 # Frontend dependencies & scripts
    ├── index.html                   # HTML shell
    ├── vite.config.ts               # Vite configuration
    ├── README.md                    # Frontend documentation
    └── src/
        ├── api/
        │   └── client.ts            # Axios client for /upload and /query
        ├── components/
        │   ├── Chat.tsx             # Chat interface, message list & input bar
        │   ├── MarkdownMessage.tsx  # Markdown & table renderer
        │   ├── Sidebar.tsx          # Collapsible sidebar & drag-and-drop uploader
        │   └── WelcomeContent.tsx   # Onboarding cards
        ├── hooks/
        │   ├── useChat.ts           # Conversation state & history management
        │   └── useUpload.ts         # File upload state hook
        ├── pages/
        │   └── Home.tsx             # Main layout page
        ├── App.tsx                  # Root React component
        ├── main.tsx                 # Application bootstrap
        └── index.css                # Tailwind CSS & Mauve Haze theme tokens
```

---

## Quick Start (Local Development)

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** & **npm**
- **PostgreSQL 16+** with the `pgvector` extension (local Docker or cloud [Neon.tech](https://neon.tech))
- **Groq API Key** ([console.groq.com](https://console.groq.com))

### 1. Start the Backend (`http://localhost:8000`)

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in DATABASE_URL & GROQ_API_KEY
Copy-Item .env.example .env

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend (`http://localhost:5173`)

Open a second terminal:

```powershell
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

Open **http://localhost:5173** in your browser to upload a document and start chatting.

---

## Cloud Deployment

1. **Database ([Neon](https://neon.tech))**: Create a free Neon PostgreSQL project and copy the connection string (`DATABASE_URL`). `DocuPulse` automatically enables `pgvector` and initializes tables on startup.
2. **Backend ([Render](https://render.com) / [Railway](https://railway.app))**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: `DATABASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL=openai/gpt-oss-20b`
3. **Frontend ([Vercel](https://vercel.com))**:
   - **Root Directory**: `frontend`
   - **Environment Variables**: `VITE_API_URL=https://<your-backend-domain>`

---

## Documentation

- [Backend Guide](backend/README.md)
- [REST API Reference](backend/docs/API.md)
- [Frontend Guide](frontend/README.md)
