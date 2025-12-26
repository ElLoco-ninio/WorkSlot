"""Rate limiting middleware and utilities."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings


def get_api_key_or_ip(request: Request) -> str:
    """Get rate limit key from API key or IP address."""
    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:20]}"  # Use prefix for privacy
    
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key_or_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window",
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down your requests.",
            "retry_after": str(exc.detail),
        },
    )


# Decorator for custom rate limits
def rate_limit(limit: str):
    """Decorator for applying custom rate limits to endpoints."""
    return limiter.limit(limit)

