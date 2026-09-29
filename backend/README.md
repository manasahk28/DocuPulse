# Document Intelligence System — Backend

A **Retrieval-Augmented Generation (RAG)** API that lets you upload PDF/text documents, index them into a PostgreSQL vector database, and ask natural-language questions answered by an LLM grounded in your documents.

## Architecture

```
┌────────────┐     ┌──────────────┐     ┌────────────────────┐     ┌───────────┐
│   Client    │────▶│  FastAPI API  │────▶│  RAG Pipeline      │────▶│  Groq API │
│  (frontend) │◀────│  (upload/     │◀────│  (chunk → embed →  │◀────│  Llama 3  │
│             │     │   query)      │     │   retrieve → gen)  │     │           │
└────────────┘     └──────────────┘     └────────┬───────────┘     └───────────┘
                                                 │
                                        ┌────────▼───────────┐
                                        │  PostgreSQL 16     │
                                        │  + pgvector        │
                                        │  (embeddings +     │
                                        │   full-text search)│
                                        └────────────────────┘
```

### Pipeline Steps

1. **Upload** — Extract text from PDF (layout mode) or plain text file.
2. **Clean** — Normalize whitespace, remove null bytes, preserve paragraph breaks.
3. **Chunk** — Split into ~200-word overlapping chunks using NLTK sentence tokenization.
4. **Embed** — Generate 768-dim vectors via `all-mpnet-base-v2` (sentence-transformers).
5. **Store** — Insert chunks + embeddings into PostgreSQL with pgvector HNSW index.
6. **Query** — Multi-query retrieval (LLM-generated query variations) + hybrid search (cosine similarity + full-text keyword matching) + context window expansion (±1 neighbor chunks).
7. **Generate** — Groq API (Llama 3.1 8B) synthesizes a grounded answer from retrieved passages.

## Tech Stack

| Component      | Technology                                     |
| -------------- | ---------------------------------------------- |
| Framework      | FastAPI 0.135                                  |
| Language       | Python 3.12                                    |
| Vector DB      | PostgreSQL 16 + pgvector (HNSW, cosine)        |
| Full-text      | PostgreSQL tsvector + GIN index                |
| Embeddings     | sentence-transformers/all-mpnet-base-v2 (768d) |
| LLM            | Groq API — Llama 3.1 8B Instant                |
| PDF Extraction | pypdf (layout mode)                            |
| Sentence Split | NLTK Punkt tokenizer                           |
| HTTP Client    | httpx (sync + streaming)                       |

## Prerequisites

- **Python 3.12+**
- **PostgreSQL 16** with the [pgvector](https://github.com/pgvector/pgvector) extension
- **Groq API key** — get one at [console.groq.com](https://console.groq.com)

### Quick PostgreSQL Setup (Docker)

```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  pgvector/pgvector:pg16
```

Then create the database:

```bash
docker exec -it pgvector psql -U postgres -c "CREATE DATABASE doc_intelligence;"
```

> **Note:** The example uses port `5433` to avoid conflicts with a local PostgreSQL on `5432`. Adjust `DATABASE_URL` accordingly.

## Installation

```bash
# Clone and enter the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

| Variable       | Required | Default                                                          | Description                     |
| -------------- | -------- | ---------------------------------------------------------------- | ------------------------------- |
| `DATABASE_URL` | Yes      | `postgresql://postgres:postgres@localhost:5432/doc_intelligence` | PostgreSQL connection string    |
| `GROQ_API_KEY` | Yes      | —                                                                | Groq API key for LLM generation |
| `GROQ_MODEL`   | No       | `llama-3.1-8b-instant`                                           | Groq model name                 |

Set them before starting the server:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/doc_intelligence"
$env:GROQ_API_KEY = "your-groq-api-key"
```

## Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server starts at **http://localhost:8000**. Interactive API docs at **http://localhost:8000/docs**.

## API Endpoints

| Method | Endpoint        | Description                              |
| ------ | --------------- | ---------------------------------------- |
| GET    | `/`             | Health check — confirms API is running   |
| GET    | `/health`       | Health status                            |
| POST   | `/upload`       | Upload and index a PDF or text file      |
| POST   | `/query`        | Ask a question — returns full answer     |
| POST   | `/query/stream` | Ask a question — streams answer via SSE  |
| GET    | `/chunks`       | Debug — list all stored chunks           |
| POST   | `/debug/upload` | Debug — preview chunking without storing |

See [docs/API.md](docs/API.md) for detailed request/response schemas and examples.

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v --tb=short
```

To skip integration tests (which require a running DB):

```bash
python -m pytest tests/ -v --tb=short -m "not integration"
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, lifespan, routers
│   ├── routes/
│   │   ├── upload.py            # POST /upload, GET /chunks, POST /debug/upload
│   │   └── query.py             # POST /query, POST /query/stream
│   └── services/
│       ├── embeddings.py        # SentenceTransformer wrapper (768-dim)
│       ├── retrieval.py         # PostgreSQL + pgvector + full-text search
│       └── rag_pipeline.py      # Core RAG orchestrator (chunk → retrieve → generate)
├── tests/
│   └── test_pipeline_failures.py  # 59 tests covering chunking, negation, comparison, etc.
├── requirements.txt
└── README.md
```

## Key Design Decisions

- **Hybrid search** — Cosine similarity (pgvector) catches semantic matches; full-text search (tsvector + GIN) catches exact keywords, numbers, and acronyms that embeddings miss.
- **Multi-query retrieval** — The LLM generates 3 query variations to improve recall. Different phrasings retrieve different relevant chunks.
- **Negation awareness** — Queries with negation words (`not`, `without`, `never`, etc.) trigger specialized query variations and system prompts so the LLM focuses on what's excluded.
- **Cross-document comparison** — Context passages include source labels (`[Passage 1 — report.pdf]`). Comparison queries trigger a prompt that groups findings by source document.
- **NLTK sentence tokenization** — Handles abbreviations (`Dr.`, `U.S.`, `e.g.`) and decimal numbers without false sentence splits.
- **Context window expansion** — After retrieving top-k chunks, neighboring chunks (±1) are fetched to provide surrounding context.
- **Overlapping chunks** — Last 2 sentences of each chunk carry over to the next, preventing information loss at boundaries.
