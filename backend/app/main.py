from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.query import router as query_router
from app.routes.upload import router as upload_router
from app.services.rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load embedding model and initialize PostgreSQL connection
    logger.info("Loading embedding model and connecting to PostgreSQL...")
    pipeline = get_rag_pipeline()
    logger.info("Embedding model loaded. PostgreSQL connected. Groq API ready.")
    yield
    # Shutdown: close the database connection cleanly
    logger.info("Shutting down — closing DB connection...")
    pipeline.retrieval_service.close()


app = FastAPI(title="Document Intelligence API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(query_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Document Intelligence API is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
