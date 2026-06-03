from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from backend.app.ingestion.parser import get_parser
from backend.app.ingestion.chunker import FixedChunker, SemanticChunker, Chunk
from backend.app.ingestion.metadata import MetadataExtractor
from backend.app.models import Document, Chunk as ChunkModel


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.fixed_chunker = FixedChunker(chunk_size=500, overlap=100)
        self.semantic_chunker = SemanticChunker(min_chunk_length=100)

    def ingest_document(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        department: Optional[str] = None,
        category: Optional[str] = None,
        strategy: str = "semantic"
    ) -> dict:
        doc_id = str(uuid.uuid4())

        parser = get_parser(file_type)
        text, page_count, parser_metadata = parser.parse(file_content)

        metadata = MetadataExtractor.extract(
            filename=filename,
            file_type=file_type,
            page_count=page_count,
            department=department,
            category=category,
            extra_metadata=parser_metadata
        )

        if strategy == "semantic":
            chunks = self.semantic_chunker.chunk(text)
        else:
            chunks = self.fixed_chunker.chunk(text)

        total_tokens = sum(chunk.token_count for chunk in chunks)

        doc = Document(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            department=department or "General",
            category=category or "Uncategorized",
            page_count=page_count,
            total_tokens=total_tokens,
            chunks_created=len(chunks),
            chunking_strategy=strategy,
            doc_metadata=metadata
        )
        self.db.add(doc)
        self.db.flush()

        chunk_models = []
        for chunk in chunks:
            chunk_model = ChunkModel(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                text=chunk.text,
                chunk_index=chunk.index,
                section=chunk.section,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                chunk_metadata={
                    "department": department or "General",
                    "category": category or "Uncategorized"
                }
            )
            chunk_models.append(chunk_model)
            self.db.add(chunk_model)

        self.db.commit()

        return {
            "doc_id": doc_id,
            "filename": filename,
            "chunks_created": len(chunks),
            "strategy": strategy,
            "tokens_total": total_tokens,
            "page_count": page_count,
            "metadata": metadata,
            "chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text[:100] + "...",
                    "token_count": chunk.token_count,
                    "section": chunk.section
                }
                for chunk in chunk_models[:3]
            ]
        }

    def get_document(self, doc_id: str) -> dict:
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return None

        chunks = self.db.query(ChunkModel).filter(ChunkModel.document_id == doc_id).all()

        return {
            "id": doc.id,
            "filename": doc.filename,
            "chunks_created": doc.chunks_created,
            "strategy": doc.chunking_strategy,
            "tokens_total": int(doc.total_tokens),
            "page_count": doc.page_count,
            "chunks": [
                {
                    "id": c.id,
                    "text": c.text,
                    "section": c.section,
                    "page_number": c.page_number,
                    "token_count": int(c.token_count)
                }
                for c in chunks
            ]
        }

    def list_documents(self) -> List[dict]:
        docs = self.db.query(Document).all()
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "chunks_created": doc.chunks_created,
                "strategy": doc.chunking_strategy,
                "tokens_total": int(doc.total_tokens),
                "uploaded_at": doc.uploaded_at.isoformat(),
                "department": doc.department,
                "category": doc.category
            }
            for doc in docs
        ]
