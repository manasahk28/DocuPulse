from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.services.rag_pipeline import get_rag_pipeline

router = APIRouter(prefix="", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    include_context: bool = False
    # Optional metadata filters for pgvector queries
    source_filter: Optional[str] = Field(default=None, description="Filter by source filename")
    document_id_filter: Optional[str] = Field(default=None, description="Filter by document ID")


@router.post("/query")
async def query_document(payload: QueryRequest) -> dict:
    """Standard query endpoint — returns full answer at once."""
    rag_pipeline = get_rag_pipeline()

    try:
        response = await run_in_threadpool(
            rag_pipeline.answer_query,
            payload.question,
            payload.top_k,
            payload.source_filter,
            payload.document_id_filter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to process query") from exc

    result = {"answer": response["answer"]}
    if payload.include_context:
        result["context"] = response["context"]

    return result


@router.post("/query/stream")
async def query_document_stream(payload: QueryRequest) -> StreamingResponse:
    """
    Streaming query endpoint for chat-like UI.
    Returns answer tokens as a text/event-stream (SSE).
    """
    rag_pipeline = get_rag_pipeline()

    def _generate():
        # yield tokens as server-sent events for real-time streaming
        for token in rag_pipeline.answer_query_stream(
            query=payload.question,
            top_k=payload.top_k,
            source_filter=payload.source_filter,
            document_id_filter=payload.document_id_filter,
        ):
            yield f"data: {token}\n\n"
        # Signal end of stream
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if proxied
        },
    )
