"""
NEO Guardian - Aplicación Principal
=====================================
Configuración de FastAPI con todas las medidas de seguridad.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import logging

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.models.database import init_db
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    TimingMiddleware
)
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.routes import auth, neo, api_keys, simulator
from app.services.nasa_client import nasa_client


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    
    Startup:
    - Inicializar logging
    - Inicializar base de datos
    - Verificar conexión con NASA API
    
    Shutdown:
    - Cerrar conexiones
    - Limpiar recursos
    """
    # Startup
    logger = setup_logging()
    logger.info(
        "Iniciando NEO Guardian",
        version=settings.app_version,
        environment=settings.server.environment
    )
    
    # Inicializar base de datos
    await init_db()
    logger.info("Base de datos inicializada")
    
    # Verificar NASA API
    try:
        stats = await nasa_client.get_today_stats()
        logger.info(
            "Conexión con NASA API verificada",
            neo_count=stats.get("total_count", 0)
        )
    except Exception as e:
        logger.warning(f"No se pudo verificar NASA API: {e}")
    
    yield
    
    # Shutdown
    await nasa_client.close()
    logger.info("NEO Guardian detenido")


# Crear aplicación
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## 🚀 NEO Guardian - Sistema de Monitoreo de Asteroides
    
    Sistema de monitoreo de Near Earth Objects (NEOs) con características
    de ciberseguridad avanzadas.
    
    ### Características de Seguridad
    
    - 🔐 **Autenticación JWT** con refresh tokens
    - 🛡️ **Rate Limiting** para prevenir abusos
    - 🔒 **Encriptación AES-256** para datos sensibles
    - 📝 **Auditoría completa** de acciones
    - 🧹 **Sanitización** de inputs
    - 🔑 **API Keys** para acceso programático
    
    ### Datos de NASA
    
    Utiliza la API oficial de NASA para obtener información en tiempo real
    sobre asteroides cercanos a la Tierra.
    
    ---
    
    **Autor**: Sistema desarrollado para MIT Solve Challenge
    """,
    docs_url="/docs" if settings.server.debug else None,
    redoc_url="/redoc" if settings.server.debug else None,
    openapi_url="/openapi.json" if settings.server.debug else None,
    lifespan=lifespan
)

# Añadir state para rate limiter
app.state.limiter = limiter

# Registrar handler de rate limit
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Middlewares (orden inverso de ejecución)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
        "X-CSRF-Token"
    ],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining"
    ]
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(neo.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(simulator.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz con información básica."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "documentation": "/docs" if settings.server.debug else "disabled"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Verifica:
    - Estado del servidor
    - Conexión con NASA API
    """
    health = {
        "status": "healthy",
        "checks": {
            "server": "ok",
            "nasa_api": "unknown"
        }
    }
    
    try:
        stats = await nasa_client.get_today_stats()
        health["checks"]["nasa_api"] = "ok"
    except Exception:
        health["checks"]["nasa_api"] = "degraded"
        health["status"] = "degraded"
    
    return health


@app.get("/api/v1/security-info", tags=["Info"])
async def security_info():
    """
    Información sobre las medidas de seguridad implementadas.
    
    Útil para auditorías y documentación.
    """
    return {
        "authentication": {
            "methods": ["JWT Bearer Token", "API Key"],
            "jwt_algorithm": settings.security.jwt_algorithm,
            "access_token_lifetime_minutes": settings.security.access_token_expire_minutes,
            "refresh_token_lifetime_days": settings.security.refresh_token_expire_days
        },
        "password_policy": {
            "min_length": settings.security.min_password_length,
            "require_uppercase": settings.security.require_uppercase,
            "require_lowercase": settings.security.require_lowercase,
            "require_digits": settings.security.require_digits,
            "require_special_chars": settings.security.require_special_chars,
            "algorithm": "Argon2id"
        },
        "rate_limiting": {
            "requests_per_minute": settings.security.rate_limit_per_minute,
            "requests_per_hour": settings.security.rate_limit_per_hour
        },
        "encryption": {
            "algorithm": "AES-256 (Fernet)",
            "encrypted_fields": ["email"]
        },
        "security_headers": [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Permissions-Policy"
        ],
        "protections": [
            "SQL Injection Detection",
            "XSS Prevention",
            "CSRF Protection",
            "Command Injection Detection",
            "Path Traversal Prevention",
            "Brute Force Protection (Account Lockout)"
        ]
    }


# Handler global de errores
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global de excepciones.
    
    En producción, oculta detalles del error.
    """
    logger = get_logger("error")
    
    # Log del error
    logger.error(
        "Unhandled exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    # Respuesta según ambiente
    if settings.server.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "Ha ocurrido un error. Por favor intente más tarde."
            }
        )
