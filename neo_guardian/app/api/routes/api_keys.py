"""
NEO Guardian - Router de API Keys
==================================
Gestión segura de API Keys para acceso programático.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from app.core.security import token_generator
from app.models.database import get_db
from app.models.models import User, APIKey
from app.api.dependencies import get_current_user, log_audit_event
from app.middleware.rate_limit import limiter


router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class APIKeyCreate(BaseModel):
    """Datos para crear una API Key."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default=["read"])
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Días hasta expiración. None = sin expiración"
    )


class APIKeyResponse(BaseModel):
    """Respuesta de API Key (sin la key completa)."""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[str]
    last_used_at: Optional[str]
    created_at: str
    is_active: bool


class APIKeyCreatedResponse(BaseModel):
    """Respuesta cuando se crea una API Key (única vez que se muestra completa)."""
    id: str
    name: str
    api_key: str  # Solo se muestra una vez
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[str]
    warning: str = "Guarda esta API key. No podrás verla de nuevo."


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_api_key(
    request: Request,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva API Key.
    
    ⚠️ IMPORTANTE: La API key completa solo se muestra una vez.
    Guárdala en un lugar seguro.
    
    Seguridad:
    - Solo se almacena el hash de la key
    - Rate limiting: 10 keys/hora
    - Scopes limitados por usuario
    """
    # Validar scopes permitidos
    allowed_scopes = ["read", "write", "alerts", "admin"]
    user_roles = current_user.get_roles_list()
    
    for scope in key_data.scopes:
        if scope not in allowed_scopes:
            raise HTTPException(
                status_code=400,
                detail=f"Scope inválido: {scope}"
            )
        # Solo admins pueden crear keys con scope admin
        if scope == "admin" and "admin" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para crear keys con scope admin"
            )
    
    # Generar API key
    raw_key = token_generator.generate_api_key()
    key_hash = token_generator.hash_token(raw_key)
    key_prefix = raw_key[:10]
    
    # Calcular expiración
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_in_days)
    
    # Crear registro
    api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=",".join(key_data.scopes),
        expires_at=expires_at
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # Log de auditoría
    await log_audit_event(
        db=db,
        action="api_key_created",
        status="success",
        request=request,
        user_id=current_user.id,
        resource_type="api_key",
        resource_id=api_key.id,
        details=f"name={key_data.name}, scopes={key_data.scopes}"
    )
    
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=raw_key,
        key_prefix=key_prefix,
        scopes=key_data.scopes,
        expires_at=expires_at.isoformat() if expires_at else None
    )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las API keys del usuario.
    
    No muestra la key completa por seguridad.
    """
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    
    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=key.get_scopes_list(),
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            created_at=key.created_at.isoformat() if key.created_at else "",
            is_active=key.is_active and not key.is_expired()
        )
        for key in keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoca (elimina) una API key.
    
    Esta acción es irreversible.
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key no encontrada"
        )
    
    # Desactivar en lugar de eliminar (para auditoría)
    api_key.is_active = False
    await db.commit()
    
    await log_audit_event(
        db=db,
        action="api_key_revoked",
        status="success",
        request=request,
        user_id=current_user.id,
        resource_type="api_key",
        resource_id=key_id
    )
    
    return {"message": "API key revocada exitosamente"}


@router.post("/{key_id}/regenerate", response_model=APIKeyCreatedResponse)
@limiter.limit("5/hour")
async def regenerate_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenera una API key existente.
    
    La key anterior será invalidada inmediatamente.
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key no encontrada"
        )
    
    # Generar nueva key
    raw_key = token_generator.generate_api_key()
    api_key.key_hash = token_generator.hash_token(raw_key)
    api_key.key_prefix = raw_key[:10]
    api_key.is_active = True
    
    await db.commit()
    
    await log_audit_event(
        db=db,
        action="api_key_regenerated",
        status="success",
        request=request,
        user_id=current_user.id,
        resource_type="api_key",
        resource_id=key_id
    )
    
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.get_scopes_list(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None
    )
