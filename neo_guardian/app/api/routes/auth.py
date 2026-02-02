"""
NEO Guardian - Router de Autenticación
=======================================
Endpoints para registro, login y gestión de tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from typing import Optional

from app.core.auth import jwt_manager, UserCreate, UserLogin, TokenPair
from app.core.security import password_manager, input_sanitizer
from app.models.database import get_db
from app.models.models import User
from app.api.dependencies import (
    get_current_user,
    log_audit_event
)
from app.middleware.rate_limit import limiter


router = APIRouter(prefix="/auth", tags=["Autenticación"])


class RegisterResponse(BaseModel):
    """Respuesta de registro."""
    message: str
    user_id: str
    username: str


class LoginResponse(BaseModel):
    """Respuesta de login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Petición de refresh token."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Petición de cambio de contraseña."""
    current_password: str
    new_password: str = Field(..., min_length=12)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra un nuevo usuario.
    
    Seguridad implementada:
    - Validación de fortaleza de contraseña
    - Sanitización de inputs
    - Email encriptado en base de datos
    - Rate limiting (5 intentos/minuto)
    """
    # Verificar si el username ya existe
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        await log_audit_event(
            db=db,
            action="register_failed",
            status="failure",
            request=request,
            error_message=f"Username ya existe: {user_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Crear usuario
    user = User(
        username=input_sanitizer.sanitize_input(user_data.username),
        roles="user"
    )
    user.set_email(user_data.email)
    user.set_password(user_data.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log de auditoría
    await log_audit_event(
        db=db,
        action="user_registered",
        status="success",
        request=request,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id
    )
    
    return RegisterResponse(
        message="Usuario registrado exitosamente",
        user_id=user.id,
        username=user.username
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia sesión y obtiene tokens JWT.
    
    Seguridad implementada:
    - Bloqueo de cuenta tras 5 intentos fallidos
    - Logging de intentos fallidos
    - Rate limiting (10 intentos/minuto)
    - Tokens con expiración corta
    """
    # Buscar usuario
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await log_audit_event(
            db=db,
            action="login_failed",
            status="failure",
            request=request,
            error_message="Usuario no encontrado"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Verificar si está bloqueado
    if user.is_locked():
        await log_audit_event(
            db=db,
            action="login_blocked",
            status="failure",
            request=request,
            user_id=user.id,
            error_message="Cuenta bloqueada"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada temporalmente. Intente en 30 minutos."
        )
    
    # Verificar contraseña
    if not user.verify_password(credentials.password):
        user.record_failed_login()
        await db.commit()
        
        await log_audit_event(
            db=db,
            action="login_failed",
            status="failure",
            request=request,
            user_id=user.id,
            error_message=f"Contraseña incorrecta. Intentos: {user.failed_login_attempts}"
        )
        
        remaining = 5 - user.failed_login_attempts
        detail = "Credenciales inválidas"
        if remaining > 0 and remaining <= 3:
            detail += f". {remaining} intentos restantes."
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    
    # Login exitoso
    user.record_successful_login()
    await db.commit()
    
    # Generar tokens
    token_pair = jwt_manager.create_token_pair(
        user_id=user.id,
        roles=user.get_roles_list()
    )
    
    # Log de auditoría
    await log_audit_event(
        db=db,
        action="login_success",
        status="success",
        request=request,
        user_id=user.id
    )
    
    return LoginResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
        user={
            "id": user.id,
            "username": user.username,
            "roles": user.get_roles_list()
        }
    )


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene nuevos tokens usando un refresh token.
    
    Seguridad:
    - Refresh token de un solo uso (rotación)
    - Validación completa del token
    """
    # Obtener user_id del refresh token para logging
    user_id = jwt_manager.extract_user_id(refresh_data.refresh_token)
    
    # Intentar refresh
    new_tokens = jwt_manager.refresh_access_token(refresh_data.refresh_token)
    
    if not new_tokens:
        await log_audit_event(
            db=db,
            action="token_refresh_failed",
            status="failure",
            request=request,
            user_id=user_id,
            error_message="Refresh token inválido o expirado"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )
    
    # Obtener roles actualizados del usuario
    if user_id:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            new_tokens = jwt_manager.create_token_pair(
                user_id=user.id,
                roles=user.get_roles_list()
            )
    
    await log_audit_event(
        db=db,
        action="token_refreshed",
        status="success",
        request=request,
        user_id=user_id
    )
    
    return new_tokens


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cierra sesión revocando el token actual.
    """
    # Obtener el token del header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        jwt_manager.revoke_token(token)
    
    await log_audit_event(
        db=db,
        action="logout",
        status="success",
        request=request,
        user_id=current_user.id
    )
    
    return {"message": "Sesión cerrada exitosamente"}


@router.post("/change-password")
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cambia la contraseña del usuario.
    
    Seguridad:
    - Requiere contraseña actual
    - Validación de nueva contraseña
    - Rate limiting estricto
    """
    # Verificar contraseña actual
    if not current_user.verify_password(password_data.current_password):
        await log_audit_event(
            db=db,
            action="password_change_failed",
            status="failure",
            request=request,
            user_id=current_user.id,
            error_message="Contraseña actual incorrecta"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Validar nueva contraseña
    is_valid, errors = password_manager.validate_password_strength(
        password_data.new_password
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors)
        )
    
    # Cambiar contraseña
    current_user.set_password(password_data.new_password)
    await db.commit()
    
    await log_audit_event(
        db=db,
        action="password_changed",
        status="success",
        request=request,
        user_id=current_user.id
    )
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene información del usuario actual.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.get_email(),
        "roles": current_user.get_roles_list(),
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
