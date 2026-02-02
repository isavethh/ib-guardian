"""
NEO Guardian - Rate Limiting
=============================
Implementación de rate limiting para proteger la API.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings


settings = get_settings()

# Crear limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.security.rate_limit_per_minute}/minute",
        f"{settings.security.rate_limit_per_hour}/hour"
    ],
    storage_uri="memory://",  # En producción usar Redis
)


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    """
    Handler para cuando se excede el rate limit.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Has excedido el límite de peticiones. Intenta más tarde.",
            "retry_after": exc.detail
        }
    )
