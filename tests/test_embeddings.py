import pytest
from app.embeddings import EmbeddingsService


@pytest.fixture
def embeddings_service():
    return EmbeddingsService()


def test_embed_single_text(embeddings_service):
    text = "This is a test sentence for embedding."
    embedding = embeddings_service.embed(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(x, (int, float)) for x in embedding)


def test_embed_batch(embeddings_service):
    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence.",
    ]
    embeddings = embeddings_service.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 1536 for emb in embeddings)


def test_embed_empty_batch(embeddings_service):
    embeddings = embeddings_service.embed_batch([])
    assert embeddings == []


def test_embed_consistency(embeddings_service):
    text = "Same text twice."
    embedding1 = embeddings_service.embed(text)
    embedding2 = embeddings_service.embed(text)

    assert embedding1 == embedding2
