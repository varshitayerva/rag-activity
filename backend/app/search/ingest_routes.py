"""Document ingestion routes with pgvector + BM25 hybrid indexing."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
import logging
import os
import io
from typing import Optional
from backend.app.database.postgres import db_client
from backend.app.search.hybrid_search import HybridSearchService
from backend.app.search.embeddings import EmbeddingsClient
from backend.app.validation import validate_file_upload, sanitize_filename
from backend.app.auth import require_auth, require_demo_mode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ingestion"])

# Import singleton from routes module
from backend.app.search.routes import get_hybrid_search_service

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    department: str = Form(default="General"),
    category: str = Form(default="General"),
    api_key: str = Depends(require_auth)
):
    """Ingest a document and add to vector store."""
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file
        is_valid, error = validate_file_upload(file.filename, file_size)
        if not is_valid:
            logger.warning(f"Invalid file upload: {error}")
            raise HTTPException(status_code=400, detail=error)

        # Get file extension
        file_ext = file.filename.split('.')[-1].lower()

        # Parse content based on file type
        if file_ext == 'txt':
            text_content = content.decode('utf-8')
        elif file_ext == 'md':
            text_content = content.decode('utf-8')
        elif file_ext == 'pdf':
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
            except ImportError:
                logger.error("PyPDF2 not installed for PDF parsing")
                text_content = content.decode('utf-8', errors='ignore')
        elif file_ext == 'docx':
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text_content = "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                logger.error("python-docx not installed for DOCX parsing")
                text_content = content.decode('utf-8', errors='ignore')
        else:
            text_content = content.decode('utf-8', errors='ignore')

        if not text_content or len(text_content.strip()) == 0:
            raise HTTPException(status_code=400, detail="Document is empty")

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)

        # Add document to database
        doc_id = db_client.add_document(
            filename=safe_filename,
            content_type=file_ext,
            file_size=file_size,
            department=department,
            category=category
        )

        # Create chunks using simple fixed-size chunking
        chunk_size = 500
        overlap = 100
        chunks = []

        sentences = text_content.split('.')
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + "."

        if current_chunk:
            chunks.append(current_chunk.strip())

        chunk_list = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                'chunk_index': i,
                'text': chunk,
                'section': None,
                'page_number': None
            }
            chunk_list.append(chunk_dict)

        db_client.add_chunks(doc_id, chunk_list)

        # Index chunks in hybrid search (pgvector + BM25)
        try:
            hybrid_search = get_hybrid_search_service()
            full_chunks = []
            for i, chunk_text in enumerate(chunk_list):
                full_chunks.append({
                    'document_id': doc_id,
                    'chunk_index': i,
                    'text': chunk_text['text'],
                    'section': chunk_text.get('section'),
                    'page_number': chunk_text.get('page_number'),
                    'department': department,
                    'category': category
                })
            hybrid_search.index_chunks(full_chunks)
            logger.info(f"Indexed {len(full_chunks)} chunks in hybrid search")
        except Exception as e:
            logger.error(f"Failed to index chunks in hybrid search: {e}")
            raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

        logger.info(f"Document ingested: {safe_filename} ({len(chunk_list)} chunks)")

        return {
            "status": "success",
            "document_id": doc_id,
            "filename": safe_filename,
            "chunks_created": len(chunk_list),
            "file_size": file_size
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")
