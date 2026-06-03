from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db, init_db
from backend.app.ingestion.service import IngestionService
from backend.app.schemas import IngestRequest, IngestResponse, DocumentResponse, DocumentDetailResponse
from backend.app.config import get_settings

app = FastAPI(title="Technical Support Copilot - Ingestion Service")

settings = get_settings()


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ingestion"}


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    department: str = None,
    category: str = None,
    strategy: str = "semantic",
    db: Session = Depends(get_db)
):
    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")

        if file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            file_type = "pdf"
        elif file.content_type in ["text/markdown", "text/plain"] or file.filename.endswith(".md"):
            file_type = "markdown"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Use .pdf or .md files"
            )

        service = IngestionService(db)
        result = service.ingest_document(
            file_content=file_content,
            filename=file.filename,
            file_type=file_type,
            department=department,
            category=category,
            strategy=strategy
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents", response_model=list[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    try:
        service = IngestionService(db)
        documents = service.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    try:
        service = IngestionService(db)
        document = service.get_document(doc_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/compare")
async def compare_chunking_strategies(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")

        file_type = "pdf" if file.content_type == "application/pdf" else "markdown"
        service = IngestionService(db)

        fixed_result = service.ingest_document(
            file_content=file_content,
            filename=f"{file.filename}_fixed",
            file_type=file_type,
            strategy="fixed"
        )

        semantic_result = service.ingest_document(
            file_content=file_content,
            filename=f"{file.filename}_semantic",
            file_type=file_type,
            strategy="semantic"
        )

        return {
            "fixed": fixed_result,
            "semantic": semantic_result,
            "comparison": {
                "fixed_chunks": fixed_result["chunks_created"],
                "semantic_chunks": semantic_result["chunks_created"],
                "fixed_tokens": fixed_result["tokens_total"],
                "semantic_tokens": semantic_result["tokens_total"],
                "token_reduction": f"{((fixed_result['tokens_total'] - semantic_result['tokens_total']) / fixed_result['tokens_total'] * 100):.1f}%"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
