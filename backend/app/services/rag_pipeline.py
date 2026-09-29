from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, Generator, List, Optional
from uuid import uuid4

import httpx
import nltk
from nltk.tokenize import sent_tokenize

# Ensure punkt_tab data is available (downloaded once, cached locally)
nltk.download("punkt_tab", quiet=True)

from app.services.embeddings import EmbeddingService
from app.services.retrieval import RetrievalService

# ── Negation keywords used by _detect_negation ──────────────────────────────
_NEGATION_WORDS = {
    "not", "no", "never", "neither", "nor", "without", "don't", "doesn't",
    "didn't", "isn't", "aren't", "wasn't", "weren't", "won't", "wouldn't",
    "shouldn't", "couldn't", "cannot", "can't", "hasn't", "haven't", "hadn't",
    "exclude", "excluding", "except", "lack", "lacking", "absent", "missing",
}

# ── Comparison keywords used by _detect_comparison_intent ───────────────────
_COMPARISON_WORDS = {
    "compare", "comparison", "contrast", "differ", "difference", "differences",
    "versus", "vs", "vs.", "distinguish", "relative", "similarities",
    "similarity", "between", "both",
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class RAGPipeline:
    """
    Modular RAG pipeline: chunking → pgvector retrieval → Groq LLM generation.

    Steps:
    1. Ingest: clean text → split into sentence-based chunks → embed → store in PostgreSQL.
    2. Query: embed user query → cosine similarity via pgvector → order by chunk_index
       → merge context → generate answer via Groq API (Llama 3).
    """

    def __init__(
        self,
        max_chunk_words: int = 200,
        top_k: int = 8,
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        database_url: str | None = None,
    ) -> None:
        self.max_chunk_words = max_chunk_words
        self.top_k = top_k

        # Initialize the embedding model (sentence-transformers, 768-dim vectors)
        self.embedding_service = EmbeddingService(model_name=embedding_model)

        # Initialize PostgreSQL + pgvector retrieval service
        self.retrieval_service = RetrievalService(database_url=database_url)

        # Groq API config
        self.groq_api_key = GROQ_API_KEY
        self.groq_model = GROQ_MODEL

        if not self.groq_api_key:
            print("WARNING: GROQ_API_KEY not set. Generation will not work.")

    # ── Text Cleaning ──────────────────────────────────────────────────────

    def load_and_clean_text(self, text: str) -> str:
        """Remove null bytes and collapse excessive whitespace while preserving newlines."""
        cleaned_text = text.replace("\x00", " ")
        # Normalize line endings, then collapse runs of 3+ newlines to 2
        cleaned_text = cleaned_text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        # Collapse horizontal whitespace (spaces/tabs) but NOT newlines
        cleaned_text = re.sub(r"[^\S\n]+", " ", cleaned_text)
        return cleaned_text.strip()

    # ── Semantic Chunking ──────────────────────────────────────────────────

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK's Punkt tokenizer.

        Handles abbreviations (Dr., U.S., e.g.) and decimal numbers correctly.
        Falls back to newline splitting for segments that are still very long.
        """
        # Split on double-newlines first to respect paragraph breaks
        paragraphs = re.split(r"\n{2,}", text)
        sentences: List[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            for sent in sent_tokenize(para):
                sent = sent.strip()
                if not sent:
                    continue
                # If a "sentence" is still very long (>100 words), split on newlines
                if len(sent.split()) > 100:
                    for sub in sent.split("\n"):
                        sub = sub.strip()
                        if sub:
                            sentences.append(sub)
                else:
                    sentences.append(sent)
        return sentences

    def split_text_into_chunks(
        self,
        text: str,
        max_chunk_words: int | None = None,
    ) -> List[str]:
        """
        Split text into overlapping chunks using sentence boundaries.

        Strategy:
        1. Split text into sentences.
        2. Accumulate sentences into chunks up to max_chunk_words.
        3. When a chunk is full, start the next chunk with the last 2 sentences
           for overlap/context continuity.
        """
        limit = max_chunk_words or self.max_chunk_words
        sentences = self._split_into_sentences(text)

        if not sentences:
            return []

        chunks: List[str] = []
        current_sentences: List[str] = []
        current_words = 0
        overlap_sentences = 2  # carry last N sentences into the next chunk

        for sentence in sentences:
            s_words = len(sentence.split())

            # If adding this sentence would exceed the limit and we have content, flush
            if current_words + s_words > limit and current_sentences:
                chunks.append(" ".join(current_sentences))
                # Start new chunk with overlap from end of previous
                overlap = current_sentences[-overlap_sentences:] if len(current_sentences) >= overlap_sentences else current_sentences[:]
                current_sentences = overlap
                current_words = sum(len(s.split()) for s in current_sentences)

            current_sentences.append(sentence)
            current_words += s_words

        # Flush remaining
        if current_sentences:
            remaining = " ".join(current_sentences)
            # Avoid creating a tiny final chunk that's mostly overlap
            if chunks and current_words < limit // 3:
                # Append to the last chunk instead
                chunks[-1] = chunks[-1] + " " + remaining
            else:
                chunks.append(remaining)

        return chunks

    # ── Document Indexing ──────────────────────────────────────────────────

    def index_document(self, text: str, source: str | None = None) -> Dict[str, Any]:
        """
        Full ingestion pipeline:
        1. Clean raw text.
        2. Split into semantic chunks.
        3. Generate 768-dim embeddings via sentence-transformers.
        4. Store chunks + embeddings in PostgreSQL document_chunks table.
        """
        cleaned_text = self.load_and_clean_text(text)
        chunks = self.split_text_into_chunks(cleaned_text)

        if not chunks:
            raise ValueError("No readable content found in the document")

        # Step 3: batch-embed all chunks
        embeddings = self.embedding_service.generate_embeddings(chunks)
        document_id = str(uuid4())

        # Prepare IDs and metadata for each chunk
        ids = [f"{document_id}-{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": idx,
                "source": source or "unknown",
            }
            for idx in range(len(chunks))
        ]

        # Step 4: insert into PostgreSQL via pgvector
        self.retrieval_service.add_documents(
            ids=ids,
            texts=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "source": source or "unknown",
        }

    # ── Multi-Query Generation ─────────────────────────────────────────────

    @staticmethod
    def _detect_negation(query: str) -> bool:
        """Return True if the query contains negation words."""
        tokens = set(re.findall(r"[a-z']+", query.lower()))
        return bool(tokens & _NEGATION_WORDS)

    def _generate_query_variations(self, query: str, n: int = 3) -> List[str]:
        """
        Use Groq LLM to generate N rephrased versions of the user's query.
        This improves retrieval recall — different phrasings catch different chunks.
        """
        if not self.groq_api_key:
            return [query]

        try:
            # If the query has negation, instruct the LLM to preserve the negation sense
            negation_hint = ""
            if self._detect_negation(query):
                negation_hint = (
                    "\nIMPORTANT: The question contains negation. "
                    "Make sure at least one variation explicitly preserves the negative sense "
                    "(e.g. 'what is excluded', 'which items are NOT covered'). "
                    "Also include one variation that asks for the POSITIVE side "
                    "(e.g. 'what IS included') so both matching and contrasting passages are retrieved."
                )

            response = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"Generate {n} alternative phrasings of the user's question. "
                                "Each should approach the topic from a different angle. "
                                "Return ONLY the questions, one per line, numbered. "
                                "Do not include the original question."
                                f"{negation_hint}"
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()

            # Parse numbered lines like "1. ..." or "1) ..."
            variations: List[str] = []
            for line in text.split("\n"):
                line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
                if line and len(line) > 10:
                    variations.append(line)
            return variations[:n]
        except Exception:
            return []

    # ── Retrieval ──────────────────────────────────────────────────────────

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int | None = None,
        source_filter: Optional[str] = None,
        document_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Multi-query retrieval using pgvector cosine similarity.

        Steps:
        1. Generate query variations via Groq LLM.
        2. Embed original query + all variations.
        3. Run pgvector cosine search for each embedding.
        4. Merge & deduplicate results, keeping best distance per chunk.
        5. Take top_k best results, re-ordered by chunk_index.
        """
        cleaned_query = self.load_and_clean_text(query)
        if not cleaned_query:
            raise ValueError("Query cannot be empty")

        k = top_k or self.top_k

        # Step 1: generate alternative phrasings
        variations = self._generate_query_variations(cleaned_query, n=3)
        all_queries = [cleaned_query] + variations

        # Step 2: embed all queries at once (batch)
        all_embeddings = self.embedding_service.generate_embeddings(all_queries)

        # Step 3: run search for each query, collecting results
        seen: Dict[str, Dict[str, Any]] = {}  # chunk_id → best result

        for embedding in all_embeddings:
            candidates = self.retrieval_service.query(
                query_embedding=embedding,
                top_k=k,
                source_filter=source_filter,
                document_id_filter=document_id_filter,
            )
            for c in candidates:
                chunk_id = c.get("metadata", {}).get("document_id", "") + "-" + str(c.get("metadata", {}).get("chunk_index", 0))
                # Keep the result with the smallest distance (most similar)
                if chunk_id not in seen or c.get("distance", 1.0) < seen[chunk_id].get("distance", 1.0):
                    seen[chunk_id] = c

        # Step 3b: keyword / full-text search for exact matches (numbers, acronyms)
        try:
            kw_results = self.retrieval_service.keyword_search(
                query_text=cleaned_query,
                top_k=k,
                source_filter=source_filter,
                document_id_filter=document_id_filter,
            )
            for c in kw_results:
                chunk_id = c.get("metadata", {}).get("document_id", "") + "-" + str(c.get("metadata", {}).get("chunk_index", 0))
                if chunk_id not in seen or c.get("distance", 1.0) < seen[chunk_id].get("distance", 1.0):
                    seen[chunk_id] = c
        except Exception:
            pass  # full-text column may not exist on older tables; degrade gracefully

        if not seen:
            return []

        # Step 4: rank merged results by distance, take top_k
        merged = sorted(seen.values(), key=lambda c: c.get("distance", 1.0))[:k]

        # Step 5: context window expansion — fetch neighbor chunks (±1)
        # Groups retrieved chunks by document_id to fetch neighbors per document
        from collections import defaultdict
        doc_chunks: Dict[str, List[int]] = defaultdict(list)
        for c in merged:
            doc_id = c.get("metadata", {}).get("document_id", "")
            chunk_idx = c.get("metadata", {}).get("chunk_index", 0)
            doc_chunks[doc_id].append(chunk_idx)

        # Fetch neighbors and add to seen (dedup by chunk_id)
        for doc_id, indices in doc_chunks.items():
            neighbors = self.retrieval_service.get_neighbor_chunks(
                document_id=doc_id,
                chunk_indices=indices,
                window=1,
            )
            for n in neighbors:
                nid = n.get("metadata", {}).get("document_id", "") + "-" + str(n.get("metadata", {}).get("chunk_index", 0))
                if nid not in seen:
                    seen[nid] = n

        # Step 6: re-rank all (original + neighbors), take final top_k
        final = sorted(seen.values(), key=lambda c: c.get("distance", 1.0))[:k]

        # Step 7: re-order by document position for coherent context
        final.sort(
            key=lambda c: (
                c.get("metadata", {}).get("document_id", ""),
                c.get("metadata", {}).get("chunk_index", 0),
            )
        )

        return final

    # ── Context Formatting ─────────────────────────────────────────────────

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks as numbered passages with source labels."""
        parts: List[str] = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "unknown")
            parts.append(f"[Passage {i} — {source}]\n{chunk['content']}")
        return "\n\n".join(parts)

    @staticmethod
    def _detect_comparison_intent(query: str) -> bool:
        """Return True if the query asks for a comparison across documents."""
        tokens = set(re.findall(r"[a-z.]+", query.lower()))
        return bool(tokens & _COMPARISON_WORDS)

    def _build_messages(self, query: str, context: str, chunks: List[Dict[str, Any]] | None = None) -> List[Dict[str, str]]:
        """Build the chat messages for Groq API."""
        is_comparison = self._detect_comparison_intent(query)
        is_negation = self._detect_negation(query)

        rules = [
            "You are a concise document analyst. Rules:",
            "- Answer ONLY from the provided passages.",
            "- Be direct. Do not repeat yourself or restate the source of information.",
            "- Vary your language — avoid using the same phrase more than once.",
            "- Use bullet points or numbered lists for multiple items.",
            "- When presenting tabular or structured data, format it as a Markdown table.",
            "- If the answer is not in the passages, say so briefly.",
            "- Do not add filler phrases like 'it is worth noting' or 'it is important to mention'.",
        ]

        if is_comparison:
            # Determine unique source names for the comparison prompt
            sources: List[str] = []
            if chunks:
                seen_srcs: set[str] = set()
                for c in chunks:
                    src = c.get("metadata", {}).get("source", "unknown")
                    if src not in seen_srcs:
                        seen_srcs.add(src)
                        sources.append(src)
            rules.append(
                "- The user is asking for a COMPARISON. Group your answer by source document. "
                "Clearly label which facts come from which source"
                + (f" ({', '.join(sources)})" if sources else "")
                + "."
            )

        if is_negation:
            rules.append(
                "- The question involves negation. Pay close attention to what is explicitly "
                "stated as NOT included, excluded, or absent."
            )

        system_msg = "\n".join(rules)
        user_msg = (
            f"Passages:\n\n{context}\n\n"
            f"Question: {query}"
        )
        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    # ── Answer Generation (Groq API) ──────────────────────────────────────

    def generate_answer(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Generate an answer using Groq API (Llama 3)."""
        if not retrieved_chunks:
            return "I could not find relevant context in the uploaded documents."

        if not self.groq_api_key:
            return "GROQ_API_KEY is not configured. Please set it as an environment variable."

        context = self._format_context(retrieved_chunks)
        messages = self._build_messages(query, context, chunks=retrieved_chunks)

        try:
            response = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                    "frequency_penalty": 0.6,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            return f"Groq API error: {e.response.status_code} — {e.response.text}"
        except Exception as e:
            return f"Generation failed: {str(e)}"

    def generate_answer_stream(
        self, query: str, retrieved_chunks: List[Dict[str, Any]]
    ) -> Generator[str, None, None]:
        """Stream answer tokens from Groq API."""
        if not retrieved_chunks:
            yield "I could not find relevant context in the uploaded documents."
            return

        if not self.groq_api_key:
            yield "GROQ_API_KEY is not configured. Please set it as an environment variable."
            return

        context = self._format_context(retrieved_chunks)
        messages = self._build_messages(query, context, chunks=retrieved_chunks)

        try:
            with httpx.stream(
                "POST",
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                    "frequency_penalty": 0.6,
                    "stream": True,
                },
                timeout=30.0,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"

    # ── Main Query Entrypoint ──────────────────────────────────────────────

    def answer_query(
        self,
        query: str,
        top_k: int | None = None,
        source_filter: Optional[str] = None,
        document_id_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full query pipeline:
        1. Retrieve top-k relevant chunks via pgvector cosine similarity.
        2. Generate answer using flan-t5-base with deterministic decoding.
        """
        chunks = self.retrieve_relevant_chunks(
            query=query,
            top_k=top_k,
            source_filter=source_filter,
            document_id_filter=document_id_filter,
        )
        answer = self.generate_answer(query=query, retrieved_chunks=chunks)

        return {
            "answer": answer,
            "context": chunks,
        }

    def answer_query_stream(
        self,
        query: str,
        top_k: int | None = None,
        source_filter: Optional[str] = None,
        document_id_filter: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Streaming version of answer_query — yields answer tokens incrementally."""
        chunks = self.retrieve_relevant_chunks(
            query=query,
            top_k=top_k,
            source_filter=source_filter,
            document_id_filter=document_id_filter,
        )
        yield from self.generate_answer_stream(query=query, retrieved_chunks=chunks)


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """Singleton factory — models and DB connection are loaded once at startup."""
    return RAGPipeline()
