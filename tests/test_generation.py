import pytest
import asyncio
import json
from backend.app.generation.service import GenerationService
from backend.app.generation.models import Chunk, ChunkMetadata


@pytest.fixture
def generation_service():
    """Initialize generation service for testing."""
    return GenerationService()


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        Chunk(
            text="To restart a pod, use the command: kubectl rollout restart deployment/[deployment-name] -n [namespace]. This will create new pods and terminate old ones.",
            score=0.95,
            source="kubernetes-guide.pdf",
            chunk_id="chunk-1",
            metadata=ChunkMetadata(
                section="Troubleshooting",
                page=42,
                doc_id="doc-1",
                source="kubernetes-guide.pdf",
            ),
        ),
        Chunk(
            text="Another way to restart a pod is to delete it directly: kubectl delete pod [pod-name] -n [namespace]. The deployment controller will automatically create a replacement.",
            score=0.87,
            source="kubernetes-guide.pdf",
            chunk_id="chunk-2",
            metadata=ChunkMetadata(
                section="Troubleshooting",
                page=43,
                doc_id="doc-1",
                source="kubernetes-guide.pdf",
            ),
        ),
    ]


@pytest.mark.asyncio
async def test_generate_streaming(generation_service, sample_chunks):
    """Test streaming generation produces correct format."""
    query = "How do I restart a pod?"

    events = []
    async for event in generation_service.generate_streaming(query, sample_chunks):
        if event.strip():
            events.append(json.loads(event.strip()))

    assert len(events) >= 3
    assert events[0]["type"] == "metadata"
    assert "sources" in events[0]
    assert events[0]["sources"][0]["doc"] == "kubernetes-guide.pdf"

    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0
    assert all("content" in e for e in token_events)

    done_event = events[-1]
    assert done_event["type"] == "done"
    assert "input_tokens" in done_event
    assert "output_tokens" in done_event


@pytest.mark.asyncio
async def test_generate_non_streaming(generation_service, sample_chunks):
    """Test non-streaming generation."""
    query = "How do I restart a pod?"

    result = await generation_service.generate(query, sample_chunks)

    assert "response" in result
    assert "sources" in result
    assert "input_tokens" in result
    assert "output_tokens" in result
    assert result["sources"][0]["doc"] == "kubernetes-guide.pdf"


def test_extract_sources(generation_service, sample_chunks):
    """Test source extraction from chunks."""
    sources = generation_service.extract_sources(sample_chunks)

    assert len(sources) == 1
    assert sources[0].doc == "kubernetes-guide.pdf"
    assert sources[0].section == "Troubleshooting"


def test_hallucination_prevention(generation_service):
    """Test that system prompt enforces hallucination prevention."""
    from backend.app.generation.prompts import SYSTEM_PROMPT

    assert "MUST answer based ONLY" in SYSTEM_PROMPT
    assert "don't have reliable information" in SYSTEM_PROMPT.lower()
    assert "source attribution" in SYSTEM_PROMPT or "cite" in SYSTEM_PROMPT.lower()
