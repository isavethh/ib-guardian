"""
NEO Guardian - Dependencias de Seguridad
=========================================
Dependencies de FastAPI para autenticación y autorización.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.auth import jwt_manager, TokenPayload
from app.core.security import token_generator
from app.models.database import get_db
from app.models.models import User, APIKey, AuditLog


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def log_audit_event(
    db: AsyncSession,
    action: str,
    status: str,
    request: Request,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Registra un evento de auditoría.
    
    Args:
        db: Sesión de base de datos.
        action: Acción realizada.
        status: Estado del evento.
        request: Request de FastAPI.
        user_id: ID del usuario (opcional).
        resource_type: Tipo de recurso.
        resource_id: ID del recurso.
        details: Detalles adicionales.
        error_message: Mensaje de error si aplica.
    """
    # Obtener IP del cliente
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "unknown"
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent", "")[:500],
        details=details,
        status=status,
        error_message=error_message
    )
    
    db.add(audit_log)
    await db.commit()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Obtiene el usuario actual basado en JWT o API Key.
    
    Args:
        request: Request de FastAPI.
        credentials: Credenciales Bearer JWT.
        api_key: API Key en header.
        db: Sesión de base de datos.
        
    Returns:
        User: Usuario autenticado.
        
    Raises:
        HTTPException: Si no está autenticado o credenciales inválidas.
    """
    user = None
    auth_method = None
    
    # Intentar autenticación por JWT
    if credentials:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token, expected_type="access")
        
        if payload:
            result = await db.execute(
                select(User).where(User.id == payload.sub)
            )
            user = result.scalar_one_or_none()
            auth_method = "jwt"
    
    # Intentar autenticación por API Key
    if not user and api_key:
        # Hashear la API key para buscar
        key_hash = token_generator.hash_token(api_key)
        
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        api_key_obj = result.scalar_one_or_none()
        
        if api_key_obj and not api_key_obj.is_expired():
            # Obtener usuario asociado
            result = await db.execute(
                select(User).where(User.id == api_key_obj.user_id)
            )
            user = result.scalar_one_or_none()
            auth_method = "api_key"
            
            # Actualizar último uso
            from datetime import datetime, timezone
            api_key_obj.last_used_at = datetime.now(timezone.utc)
            await db.commit()
    
    if not user:
        await log_audit_event(
            db=db,
            action="authentication_failed",
            status="failure",
            request=request,
            error_message="Credenciales inválidas o expiradas"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verificar que el usuario está activo
    if not user.is_active:
        await log_audit_event(
            db=db,
            action="authentication_failed",
            status="failure",
            request=request,
            user_id=user.id,
            error_message="Cuenta desactivada"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada"
        )
    
    # Verificar que no está bloqueado
    if user.is_locked():
        await log_audit_event(
            db=db,
            action="authentication_failed",
            status="failure",
            request=request,
            user_id=user.id,
            error_message="Cuenta bloqueada temporalmente"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada temporalmente. Intente más tarde."
        )
    
    # Registrar en request state para uso posterior
    request.state.user = user
    request.state.auth_method = auth_method
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario actual está activo y verificado.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


def require_roles(required_roles: List[str]):
    """
    Factory de dependency para requerir roles específicos.
    
    Args:
        required_roles: Lista de roles requeridos (cualquiera de ellos).
        
    Returns:
        Dependency function.
    """
    async def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        user_roles = current_user.get_roles_list()
        
        # Admin tiene acceso a todo
        if "admin" in user_roles:
            return current_user
        
        # Verificar si tiene alguno de los roles requeridos
        if not any(role in user_roles for role in required_roles):
            await log_audit_event(
                db=db,
                action="authorization_failed",
                status="failure",
                request=request,
                user_id=current_user.id,
                error_message=f"Roles requeridos: {required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta acción"
            )
        
        return current_user
    
    return role_checker


def require_scope(required_scope: str):
    """
    Factory de dependency para requerir un scope específico (solo API Keys).
    
    Args:
        required_scope: Scope requerido.
        
    Returns:
        Dependency function.
    """
    async def scope_checker(
        request: Request,
        api_key: Optional[str] = Depends(api_key_header),
        db: AsyncSession = Depends(get_db)
    ):
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Se requiere API Key para este endpoint"
            )
        
        key_hash = token_generator.hash_token(api_key)
        
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida"
            )
        
        if not api_key_obj.has_scope(required_scope):
            await log_audit_event(
                db=db,
                action="scope_denied",
                status="failure",
                request=request,
                error_message=f"Scope requerido: {required_scope}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere scope: {required_scope}"
            )
        
        return api_key_obj
    
    return scope_checker


# Optional user (para endpoints públicos con funcionalidad extra para autenticados)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Obtiene el usuario actual si está autenticado, None si no.
    No lanza error si no hay autenticación.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token, expected_type="access")
        
        if not payload:
            return None
        
        result = await db.execute(
            select(User).where(User.id == payload.sub)
        )
        return result.scalar_one_or_none()
    except Exception:
        return None
