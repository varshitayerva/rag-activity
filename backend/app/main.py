from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from backend.app.search.routes import router as search_router
from backend.app.api.metrics import router as metrics_router


class CORSHeaderMiddleware:
    """Custom CORS middleware to add headers explicitly."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Handle OPTIONS
        if scope["method"] == "OPTIONS":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"access-control-allow-origin", b"*"),
                    (b"access-control-allow-methods", b"GET,POST,PUT,DELETE,OPTIONS"),
                    (b"access-control-allow-headers", b"*"),
                    (b"access-control-expose-headers", b"*"),
                    (b"content-length", b"0"),
                ],
            })
            await send({"type": "http.response.body", "body": b""})
            return

        # Add headers to all responses
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-origin", b"*"))
                headers.append((b"access-control-allow-methods", b"GET,POST,PUT,DELETE,OPTIONS"))
                headers.append((b"access-control-allow-headers", b"*"))
                headers.append((b"access-control-expose-headers", b"*"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_cors)


# Create FastAPI app
app = FastAPI(
    title="Technical Support Copilot - Ingestion Service",
)

# Add custom CORS middleware
app.add_middleware(CORSHeaderMiddleware)

# Include routers
app.include_router(search_router)
app.include_router(metrics_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0", "provider": "groq"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
