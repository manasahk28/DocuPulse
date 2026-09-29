from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pgvector.psycopg2 import register_vector


# Database connection URL — set via DATABASE_URL env var or defaults to local PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/doc_intelligence",
)


class RetrievalService:
    """PostgreSQL + pgvector integration for document chunk storage and retrieval."""

    def __init__(self, database_url: str | None = None) -> None:
        # Establish connection to PostgreSQL (reads latest DATABASE_URL from env)
        self.database_url = database_url or os.getenv("DATABASE_URL", DATABASE_URL)
        self._connect()

        # Create the document_chunks table and indexes if they don't exist
        self._init_schema()

    def _connect(self) -> None:
        """Open (or reopen) the PostgreSQL connection and register pgvector."""
        self.conn = psycopg2.connect(self.database_url)
        self.conn.autocommit = True

        # Ensure the pgvector extension exists BEFORE registering the vector type
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Register pgvector type so psycopg2 can handle vector columns
        register_vector(self.conn)

    def _ensure_connection(self) -> None:
        """Reconnect if the cloud DB (e.g. Neon) closed an idle connection."""
        try:
            if self.conn.closed:
                self._connect()
            else:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1;")
        except Exception:
            self._connect()

    def _init_schema(self) -> None:
        """Create the pgvector extension and document_chunks table on first run."""
        with self.conn.cursor() as cur:
            # Enable the pgvector extension for vector similarity search
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Table stores each chunk with its embedding vector(768) for cosine search
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id              TEXT PRIMARY KEY,
                    document_id     TEXT NOT NULL,
                    chunk_index     INTEGER NOT NULL,
                    content         TEXT NOT NULL,
                    source          TEXT NOT NULL DEFAULT 'unknown',
                    embedding       vector(768) NOT NULL
                );
            """)

            # Index for fast cosine similarity queries using HNSW
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON document_chunks
                USING hnsw (embedding vector_cosine_ops);
            """)

            # Index for filtering by document_id (used in metadata filtering)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                ON document_chunks (document_id);
            """)

            # Index for filtering by source (document type / filename)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_source
                ON document_chunks (source);
            """)

            # ── Full-text search support (tsvector + GIN) ─────────────────
            # Add a generated tsvector column for keyword / BM25-style search
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'document_chunks' AND column_name = 'tsv'
                    ) THEN
                        ALTER TABLE document_chunks
                            ADD COLUMN tsv tsvector
                            GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
                    END IF;
                END $$;
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_tsv
                ON document_chunks USING gin (tsv);
            """)

    def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Insert document chunks with embeddings into PostgreSQL."""
        if not texts:
            return

        # Build rows: (id, document_id, chunk_index, content, source, embedding)
        rows = []
        sources_to_replace: set[str] = set()
        for chunk_id, text, embedding, meta in zip(ids, texts, embeddings, metadatas):
            src = meta.get("source", "unknown")
            if src and src != "unknown":
                sources_to_replace.add(src)
            rows.append((
                chunk_id,
                meta.get("document_id", ""),
                meta.get("chunk_index", 0),
                text,
                src,
                embedding,  # pgvector accepts list[float] directly
            ))

        # Bulk insert using execute_values for efficiency (replacing prior uploads of the same filename)
        self._ensure_connection()
        with self.conn.cursor() as cur:
            if sources_to_replace:
                cur.execute(
                    "DELETE FROM document_chunks WHERE source = ANY(%s)",
                    (list(sources_to_replace),),
                )
            execute_values(
                cur,
                """
                INSERT INTO document_chunks (id, document_id, chunk_index, content, source, embedding)
                VALUES %s
                ON CONFLICT (id) DO NOTHING
                """,
                rows,
                template="(%s, %s, %s, %s, %s, %s::vector)",
            )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_filter: Optional[str] = None,
        document_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks using pgvector cosine similarity (<=>).

        Supports optional filtering by source (filename) or document_id.
        Results are first ranked by similarity, then ordered by chunk_index
        to preserve document context.
        """
        # Build the WHERE clause dynamically based on optional filters
        conditions: List[str] = []
        params: List[Any] = [query_embedding]  # $1 is always the query vector

        if source_filter:
            conditions.append("source = %s")
            params.append(source_filter)

        if document_id_filter:
            conditions.append("document_id = %s")
            params.append(document_id_filter)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Use cosine distance (<=>) for similarity ranking
        # Lower distance = more similar; we return 1 - distance as similarity score
        sql = f"""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                source,
                (embedding <=> %s::vector) AS distance
            FROM document_chunks
            {where_clause}
            ORDER BY distance ASC
            LIMIT %s
        """

        # Replace the first %s with the query vector, then append top_k
        # Rebuild params: query_embedding for the <=> operator, then filters, then limit
        query_params: List[Any] = [query_embedding]
        if source_filter:
            query_params.append(source_filter)
        if document_id_filter:
            query_params.append(document_id_filter)
        query_params.append(top_k)

        self._ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, query_params)
            rows = cur.fetchall()

        # Convert rows to the standard chunk format used by the pipeline
        output: List[Dict[str, Any]] = []
        for row in rows:
            output.append({
                "content": row["content"],
                "metadata": {
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "source": row["source"],
                },
                "distance": float(row["distance"]),
            })

        return output

    # ── Keyword / Full-Text Search ─────────────────────────────────────────

    def keyword_search(
        self,
        query_text: str,
        top_k: int = 5,
        source_filter: Optional[str] = None,
        document_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Full-text search using PostgreSQL tsvector + ts_rank.

        Complements vector cosine search by catching exact keyword/number matches
        that embedding models often miss.
        """
        conditions: List[str] = ["tsv @@ websearch_to_tsquery('english', %s)"]
        params: List[Any] = [query_text]

        if source_filter:
            conditions.append("source = %s")
            params.append(source_filter)
        if document_id_filter:
            conditions.append("document_id = %s")
            params.append(document_id_filter)

        where_clause = "WHERE " + " AND ".join(conditions)
        params.append(top_k)

        sql = f"""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                source,
                ts_rank(tsv, websearch_to_tsquery('english', %s)) AS rank
            FROM document_chunks
            {where_clause}
            ORDER BY rank DESC
            LIMIT %s
        """

        # params order: rank query_text, WHERE query_text, [filters...], limit
        rank_params: List[Any] = [query_text] + params

        self._ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, rank_params)
            rows = cur.fetchall()

        return [
            {
                "content": row["content"],
                "metadata": {
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "source": row["source"],
                },
                "distance": 1.0 - min(float(row["rank"]), 1.0),  # convert rank→distance
            }
            for row in rows
        ]

    def get_neighbor_chunks(
        self,
        document_id: str,
        chunk_indices: List[int],
        window: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Fetch neighboring chunks (chunk_index ± window) for context expansion.
        Returns chunks not already in the provided chunk_indices.
        """
        if not chunk_indices:
            return []

        # Build set of all indices we want (original ± window)
        target_indices: set[int] = set()
        for idx in chunk_indices:
            for offset in range(-window, window + 1):
                if idx + offset >= 0:
                    target_indices.add(idx + offset)

        # Remove indices we already have
        new_indices = target_indices - set(chunk_indices)
        if not new_indices:
            return []

        placeholders = ",".join(["%s"] * len(new_indices))
        sql = f"""
            SELECT id, document_id, chunk_index, content, source
            FROM document_chunks
            WHERE document_id = %s AND chunk_index IN ({placeholders})
            ORDER BY chunk_index ASC
        """
        params: List[Any] = [document_id] + sorted(new_indices)

        self._ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [
            {
                "content": row["content"],
                "metadata": {
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "source": row["source"],
                },
                "distance": 0.99,  # neighbor, not directly retrieved
            }
            for row in rows
        ]

    def close(self) -> None:
        """Close the database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
