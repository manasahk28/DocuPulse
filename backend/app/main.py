from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Automatically load environment variables from backend/.env if present
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ[_key.strip()] = _val.strip().strip('"').strip("'")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.query import router as query_router
from app.routes.upload import router as upload_router
from app.services.rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize PostgreSQL connection and pre-warm ONNX model in background
    logger.info("Connecting to PostgreSQL and warming up embedding model...")
    pipeline = get_rag_pipeline()
    import threading
    threading.Thread(target=lambda: pipeline.embedding_service.model, daemon=True).start()
    logger.info("PostgreSQL connected. Groq API ready.")
    yield
    # Shutdown: close the database connection cleanly
    logger.info("Shutting down — closing DB connection...")
    pipeline.retrieval_service.close()


app = FastAPI(title="DocuPulse API", version="1.0.0", lifespan=lifespan)

_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [
    o.strip().rstrip("/")
    for o in os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_URL", "")).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(query_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "DocuPulse API is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
