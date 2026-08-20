from app.embeddings import EMBEDDING_DIMENSIONS, EmbeddingProvider


class FakeEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [float(len(text))] + [0.0] * (EMBEDDING_DIMENSIONS - 1)
            for text in texts
        ]


def test_embedding_provider_contract_has_fixed_width_vectors() -> None:
    provider = FakeEmbeddingProvider()

    assert isinstance(provider, EmbeddingProvider)
    vectors = provider.embed(["invoice text", "vendor total"])

    assert len(vectors) == 2
    assert all(len(vector) == EMBEDDING_DIMENSIONS for vector in vectors)
