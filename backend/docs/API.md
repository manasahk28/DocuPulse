# API Reference

Base URL: `http://localhost:8000`

---

## Health

### `GET /`

Returns a message confirming the API is running.

**Response:**

```json
{
  "message": "Document Intelligence API is running"
}
```

### `GET /health`

**Response:**

```json
{
  "status": "ok"
}
```

---

## Upload

### `POST /upload`

Upload a PDF or text file. The file is extracted, cleaned, chunked, embedded, and stored in PostgreSQL.

**Content-Type:** `multipart/form-data`

**Form field:**

| Field  | Type | Required | Description                       |
| ------ | ---- | -------- | --------------------------------- |
| `file` | File | Yes      | A `.pdf`, `.txt`, or `.text` file |

**cURL example:**

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@report.pdf"
```

**Success response (200):**

```json
{
  "message": "Document uploaded and indexed successfully",
  "filename": "report.pdf",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "chunk_count": 12
}
```

**Error responses:**

| Status | Condition                       |
| ------ | ------------------------------- |
| 400    | Missing filename                |
| 400    | Unsupported file type           |
| 400    | Empty file                      |
| 400    | Text extraction failed          |
| 400    | No readable content in document |
| 500    | Indexing failed                 |

---

## Query

### `POST /query`

Ask a question about uploaded documents. Returns a complete answer.

**Content-Type:** `application/json`

**Request body:**

| Field                | Type    | Required | Default | Description                                     |
| -------------------- | ------- | -------- | ------- | ----------------------------------------------- |
| `question`           | string  | Yes      | —       | The question to ask (min 1 char)                |
| `top_k`              | integer | No       | 5       | Number of chunks to retrieve (1–20)             |
| `include_context`    | boolean | No       | false   | Include retrieved passages in response          |
| `source_filter`      | string  | No       | null    | Filter by source filename (e.g. `"report.pdf"`) |
| `document_id_filter` | string  | No       | null    | Filter by document ID                           |

**cURL example:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings?",
    "include_context": true,
    "top_k": 8
  }'
```

**Success response (200):**

```json
{
  "answer": "The report identifies three key findings: ...",
  "context": [
    {
      "content": "The inspection revealed 45 defects on the north elevation...",
      "metadata": {
        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "chunk_index": 3,
        "source": "report.pdf"
      },
      "distance": 0.321
    }
  ]
}
```

> The `context` field is only included when `include_context` is `true`.

**Error responses:**

| Status | Condition               |
| ------ | ----------------------- |
| 400    | Empty question          |
| 500    | Query processing failed |

---

### `POST /query/stream`

Same as `/query` but streams the answer as **Server-Sent Events (SSE)** for real-time display.

**Request body:** Same as `/query`.

**cURL example:**

```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the report"}' \
  --no-buffer
```

**Response:** `text/event-stream`

```
data: The

data: report

data: identifies

data: three

data: key

data: findings

data: ...

data: [DONE]
```

Each `data:` line contains one token. The stream ends with `data: [DONE]`.

---

## Debug Endpoints

### `GET /chunks`

List all stored chunks with truncated previews. Useful for inspecting what's in the database.

**Response:**

```json
{
  "total_chunks": 12,
  "chunks": [
    {
      "id": "a1b2c3d4-0",
      "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "chunk_index": 0,
      "source": "report.pdf",
      "preview": "The inspection report covers the north and south elevations of Building A...",
      "content_length": 847
    }
  ]
}
```

### `POST /debug/upload`

Upload a file and preview the extraction and chunking results **without storing anything** in the database.

**Content-Type:** `multipart/form-data`

**Form field:** Same as `/upload`.

**Response:**

```json
{
  "filename": "report.pdf",
  "raw_text_length": 15234,
  "raw_text_word_count": 2341,
  "raw_text_newline_count": 187,
  "cleaned_text_length": 14890,
  "cleaned_text_preview": "Document Intelligence Report\n\nSection 1: Overview...",
  "chunk_count": 12,
  "chunks": [
    {
      "index": 0,
      "word_count": 195,
      "preview": "Document Intelligence Report Section 1: Overview This report covers..."
    }
  ]
}
```

---

## Query Features

### Multi-Query Retrieval

When you send a question, the pipeline generates 3 alternative phrasings via the LLM before searching. This improves recall — different phrasings catch different relevant chunks.

### Hybrid Search

Each query runs **two** search strategies in parallel:

1. **Vector search** — pgvector cosine similarity (`<=>`) on 768-dim embeddings
2. **Keyword search** — PostgreSQL full-text search (`tsvector` + `ts_rank`) for exact terms

Results are merged and deduplicated, keeping the best match per chunk.

### Negation-Aware Queries

Queries containing negation words (e.g., _"What is NOT included?"_) are detected automatically. The system:

- Generates query variations that preserve the negative sense
- Adds a variation for the positive side (to retrieve contrasting context)
- Modifies the system prompt to focus on exclusions and absences

### Cross-Document Comparison

When you ask a comparison question (e.g., _"Compare the two reports"_), the system:

- Labels each passage with its source file: `[Passage 1 — report_A.pdf]`
- Instructs the LLM to group findings by source document

### Context Window Expansion

After retrieving the top-k chunks, the system also fetches neighboring chunks (±1 by chunk index) from the same document. This provides surrounding context that may be needed for a complete answer.

### Metadata Filtering

You can scope queries to a specific document or source file:

```json
{
  "question": "What defects were found?",
  "source_filter": "building_A_report.pdf"
}
```

```json
{
  "question": "What defects were found?",
  "document_id_filter": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```
