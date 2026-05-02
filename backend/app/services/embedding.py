from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self._model: SentenceTransformer | None = None

    def _ensure_model(self) -> SentenceTransformer:
        if self.provider != "sentence_transformers":
            raise RuntimeError(f"Unsupported embedding provider: {self.provider}")
        if self._model is None:
            logger.info("[embedding] loading model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure_model()
        vectors = model.encode(
            texts,
            batch_size=64,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


embedding_service = EmbeddingService()
