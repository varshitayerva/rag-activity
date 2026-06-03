from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class IngestRequest(BaseModel):
    department: Optional[str] = None
    category: Optional[str] = None
    strategy: str = "semantic"


class ChunkResponse(BaseModel):
    id: str
    text: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_created: int
    strategy: str
    tokens_total: int
    page_count: int
    metadata: Dict[str, Any]
    chunks: List[Dict[str, Any]]


class DocumentResponse(BaseModel):
    id: str
    filename: str
    chunks_created: int
    strategy: str
    tokens_total: int
    uploaded_at: Optional[datetime] = None
    department: Optional[str] = None
    category: Optional[str] = None


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    chunks_created: int
    strategy: str
    tokens_total: int
    page_count: int
    chunks: List[ChunkResponse]
