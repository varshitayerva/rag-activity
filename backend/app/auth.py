"""Authentication and rate limiting."""

import os
from fastapi import HTTPException, Request
from typing import Callable
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

VALID_API_KEYS = [
    os.getenv('API_KEY_1', 'sk-demo-key-12345'),
    os.getenv('API_KEY_2', 'sk-demo-key-67890'),
]

# Rate limiting: API key -> (request_count, reset_time)
rate_limit_store = {}
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # 1 minute

def verify_api_key(request: Request) -> str:
    """Verify API key from request header."""
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        logger.warning(f"Request from {request.client.host} without API key")
        raise HTTPException(status_code=401, detail="Missing API key")

    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key from {request.client.host}: {api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key

def check_rate_limit(api_key: str) -> bool:
    """Check if API key has exceeded rate limit."""
    current_time = time.time()

    if api_key not in rate_limit_store:
        rate_limit_store[api_key] = [0, current_time]

    count, reset_time = rate_limit_store[api_key]

    # Reset counter if window expired
    if current_time - reset_time > RATE_LIMIT_WINDOW:
        rate_limit_store[api_key] = [1, current_time]
        return True

    # Check if limit exceeded
    if count >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for API key: {api_key[:10]}...")
        return False

    # Increment counter
    rate_limit_store[api_key][0] += 1
    return True

async def require_auth(request: Request):
    """Dependency for protecting endpoints."""
    api_key = verify_api_key(request)

    if not check_rate_limit(api_key):
        logger.warning(f"Rate limit rejected for {api_key[:10]}...")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s"
        )

    return api_key

def require_demo_mode():
    """Allow requests without auth key in demo mode."""
    demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
    if demo_mode:
        logger.info("Running in DEMO_MODE - authentication disabled")
    return demo_mode
