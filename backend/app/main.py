import os
from dotenv import load_dotenv

# Load .env file before importing anything else
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.search.routes import router as search_router
from backend.app.search.ingest_routes import router as ingest_router
from backend.app.search.feedback_routes import router as feedback_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.features_routes import router as features_router
from backend.app.api.auth_routes import router as auth_router
from backend.app.webhooks.routes import router as webhook_router
from backend.app.logging_config import setup_logging
from backend.app.database.postgres import db_client

logger = logging.getLogger(__name__)
setup_logging()


# CORS configuration - explicitly set allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

# Add production origins if configured
prod_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ALLOWED_ORIGINS.extend([o.strip() for o in prod_origins if o.strip()])

app = FastAPI(
    title="Technical Support Copilot - Ingestion Service",
    version="1.0.0",
    description="RAG system with semantic search and LLM generation"
)

# Add CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["Content-Type"],
    max_age=3600,
)

# Include routers
app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(feedback_router)
app.include_router(metrics_router)
app.include_router(auth_router)
app.include_router(features_router)
app.include_router(webhook_router)

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    try:
        db_client.init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Application shutting down")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "provider": "groq"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
