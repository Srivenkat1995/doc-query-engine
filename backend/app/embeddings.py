from __future__ import annotations

from functools import lru_cache
from typing import Protocol, Sequence, runtime_checkable

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one fixed-width vector for each input text."""


class LocalEmbeddingProvider:
    """Local sentence-transformers provider with a build-time model cache."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


@lru_cache
def get_embedding_provider() -> LocalEmbeddingProvider:
    return LocalEmbeddingProvider()
