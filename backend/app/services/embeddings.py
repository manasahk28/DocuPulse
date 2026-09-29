from __future__ import annotations

from typing import Iterable, List

from fastembed import TextEmbedding


class EmbeddingService:
    """Lightweight ONNX-based embedding service (fastembed) for 384-dim dense vectors."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: TextEmbedding | None = None

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def generate_embeddings(self, texts: Iterable[str]) -> List[List[float]]:
        """Encode a batch of texts into 384-dimensional float vectors for pgvector storage."""
        text_list = list(texts)
        if not text_list:
            return []

        return [vec.tolist() for vec in self.model.embed(text_list)]
