"""
NEO Guardian - Middleware de Seguridad
=======================================
Headers de seguridad y protecciones adicionales.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import uuid

from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade headers de seguridad a todas las respuestas.
    
    Headers implementados:
    - X-Content-Type-Options: Previene MIME sniffing
    - X-Frame-Options: Previene clickjacking
    - X-XSS-Protection: Protección XSS del navegador
    - Strict-Transport-Security: Fuerza HTTPS
    - Content-Security-Policy: Política de contenido
    - Referrer-Policy: Control de referrer
    - Permissions-Policy: Control de features del navegador
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Procesa la petición y añade headers de seguridad."""
        
        response = await call_next(request)
        
        # Prevenir MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Protección XSS del navegador (legacy, pero útil)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Forzar HTTPS (solo en producción)
        settings = get_settings()
        if settings.server.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' api.nasa.gov; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (antes Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Remover headers que exponen información
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade un ID único a cada petición.
    Útil para tracking y debugging.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Añade request ID a la petición y respuesta."""
        
        # Generar o usar request ID existente
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Almacenar en el state de la petición
        request.state.request_id = request_id
        
        # Procesar petición
        response = await call_next(request)
        
        # Añadir a la respuesta
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que mide el tiempo de procesamiento.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Mide y añade tiempo de procesamiento."""
        
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response
