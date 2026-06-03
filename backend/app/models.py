from sqlalchemy import Column, String, Integer, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    department = Column(String(100))
    category = Column(String(100))
    page_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    chunks_created = Column(Integer, default=0)
    chunking_strategy = Column(String(50), default="semantic")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(JSON, default={})

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False)
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section = Column(String(255))
    page_number = Column(Integer)
    token_count = Column(Integer, default=0)
    embedding_vector = Column(JSON)
    chunk_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
