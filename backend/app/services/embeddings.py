from __future__ import annotations

from typing import Iterable, List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wrapper around sentence-transformers for generating 768-dim dense vectors."""

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2") -> None:
        # Load the embedding model once; cached in ~/.cache/huggingface after first download
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: Iterable[str]) -> List[List[float]]:
        """Encode a batch of texts into 768-dimensional float vectors for pgvector storage."""
        text_list = list(texts)
        if not text_list:
            return []

        # encode() returns numpy array of shape (n_texts, 768)
        vectors = self.model.encode(text_list, convert_to_numpy=True, show_progress_bar=False)
        # Convert to list[list[float]] for psycopg2 / pgvector compatibility
        return vectors.tolist()
