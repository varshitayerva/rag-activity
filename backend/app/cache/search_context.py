"""Search context and retrieval result models."""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


@dataclass
class Chunk:
    """A single text chunk with metadata."""

    chunk_id: str
    text: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        return cls(**data)


@dataclass
class SearchResult:
    """Result from hybrid search (vector + BM25)."""

    chunks: List[Chunk]
    search_type: str = "hybrid"
    query: Optional[str] = None
    filter_applied: Optional[Dict[str, Any]] = None
    latency_ms: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "search_type": self.search_type,
            "query": self.query,
            "filter_applied": self.filter_applied,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        chunks = [Chunk.from_dict(c) for c in data.get("chunks", [])]
        return cls(
            chunks=chunks,
            search_type=data.get("search_type", "hybrid"),
            query=data.get("query"),
            filter_applied=data.get("filter_applied"),
            latency_ms=data.get("latency_ms", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class GenerationRequest:
    """Request to generate a response."""

    query: str
    chunks: List[Chunk]
    stream: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Generated response with sources."""

    text: str
    sources: List[Dict[str, Any]]
    input_tokens: int
    output_tokens: int
    model: str = "claude-sonnet-4-20250514"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "sources": self.sources,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "model": self.model,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationResponse":
        return cls(
            text=data.get("text", ""),
            sources=data.get("sources", []),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            model=data.get("model", "claude-sonnet-4-20250514"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
