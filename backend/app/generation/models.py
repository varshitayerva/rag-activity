from pydantic import BaseModel
from typing import Optional, List


class ChunkMetadata(BaseModel):
    section: Optional[str] = None
    page: Optional[int] = None
    doc_id: Optional[str] = None
    source: Optional[str] = None


class Chunk(BaseModel):
    text: str
    score: float
    source: str
    chunk_id: str
    metadata: ChunkMetadata


class GenerateRequest(BaseModel):
    query: str
    chunks: List[Chunk]
    stream: bool = True


class SourceAttribution(BaseModel):
    doc: str
    section: Optional[str] = None
    chunk_id: Optional[str] = None


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class ConfidenceScore(BaseModel):
    overall_confidence: float
    source_coverage: float
    hallucination_risk: float
    answer_completeness: float
    uncertainty_markers: int
    confidence_level: str
