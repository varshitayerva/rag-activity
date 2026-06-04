"""Document ingestion routes with pgvector + BM25 hybrid indexing."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
import logging
import os
import io
from typing import Optional
from backend.app.database.postgres import db_client
from backend.app.search.hybrid_search import HybridSearchService
from backend.app.search.embeddings import EmbeddingsClient
from backend.app.search.semantic_chunker import HybridChunker
from backend.app.search.summary_generator import DocumentSummaryGenerator
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
    chunking_strategy: str = Form(default="semantic"),
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

        # Validate chunking strategy
        if chunking_strategy not in ["semantic", "fixed"]:
            chunking_strategy = "semantic"

        # Create chunks using semantic or fixed-size strategy
        hybrid_chunker = HybridChunker(chunk_size=500, overlap=100)
        chunk_list = hybrid_chunker.chunk(
            text=text_content,
            strategy=chunking_strategy,
            metadata={
                'page_number': 1,
                'section': None
            }
        )

        if not chunk_list:
            raise HTTPException(status_code=400, detail="Failed to chunk document")

        # Add document to database with chunking strategy
        doc_id = db_client.add_document(
            filename=safe_filename,
            content_type=file_ext,
            file_size=file_size,
            department=department,
            category=category,
            chunking_strategy=chunking_strategy
        )

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

        # Generate document summary for hierarchical indexing (optional)
        try:
            summary_gen = DocumentSummaryGenerator()

            # Use first 3 chunks to generate summary
            preview_text = "\n\n".join([c['text'] for c in chunk_list[:3]])
            summary = summary_gen.generate_summary(preview_text)

            if summary:
                try:
                    # Embed the summary
                    embeddings_client = EmbeddingsClient()
                    summary_embedding = embeddings_client.embed_query(summary)

                    # Extract key topics
                    key_topics = summary_gen.extract_key_topics(text_content)

                    # Store in database
                    db_client.add_document_summary(
                        document_id=doc_id,
                        summary=summary,
                        embedding=summary_embedding,
                        key_topics=key_topics,
                        chunk_count=len(chunk_list)
                    )
                    logger.info(f"Added summary for document {doc_id}")
                except Exception as embed_err:
                    logger.warning(f"Failed to add summary to database: {embed_err}")

        except Exception as e:
            logger.warning(f"Skipping summary generation: {e}")

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
