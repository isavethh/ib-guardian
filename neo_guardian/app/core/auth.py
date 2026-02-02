"""
NEO Guardian - Sistema de Autenticación JWT
============================================
Implementa autenticación robusta con:
- JWT Access Tokens (corta duración)
- Refresh Tokens (larga duración)
- Blacklist de tokens revocados
- Protección contra replay attacks
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

from app.core.config import get_settings
from app.core.security import (
    password_manager,
    token_generator,
    input_sanitizer
)


class TokenPayload(BaseModel):
    """Payload del JWT token."""
    sub: str  # Subject (user_id)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    jti: str  # JWT ID (único)
    type: str  # "access" o "refresh"
    roles: list = []


class TokenPair(BaseModel):
    """Par de tokens de acceso y refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Segundos hasta expiración


class UserCreate(BaseModel):
    """Schema para creación de usuario."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=12)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Valida y sanitiza el username."""
        # Solo alfanuméricos y guiones bajos
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError(
                'Username solo puede contener letras, números y guiones bajos'
            )
        return input_sanitizer.sanitize_input(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida la fortaleza de la contraseña."""
        is_valid, errors = password_manager.validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v


class UserLogin(BaseModel):
    """Schema para login de usuario."""
    username: str
    password: str


class JWTManager:
    """
    Gestor de tokens JWT con características de seguridad avanzadas.
    
    Características:
    - Tokens de corta duración (access) y larga duración (refresh)
    - JTI único para cada token (previene replay attacks)
    - Blacklist de tokens revocados
    - Validación estricta de claims
    """
    
    # Blacklist en memoria (en producción usar Redis)
    _token_blacklist: set = set()
    
    def __init__(self):
        """Inicializa el gestor JWT."""
        self._settings = get_settings().security
    
    def create_access_token(
        self,
        user_id: str,
        roles: list = None,
        additional_claims: Dict[str, Any] = None
    ) -> Tuple[str, datetime]:
        """
        Crea un token de acceso JWT.
        
        Args:
            user_id: ID del usuario.
            roles: Lista de roles del usuario.
            additional_claims: Claims adicionales.
            
        Returns:
            Tuple[str, datetime]: (token, fecha_expiracion)
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=self._settings.access_token_expire_minutes
        )
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": token_generator.generate_secure_token(16),
            "type": "access",
            "roles": roles or []
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm
        )
        
        return token, expire
    
    def create_refresh_token(self, user_id: str) -> Tuple[str, datetime]:
        """
        Crea un token de refresh.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Tuple[str, datetime]: (token, fecha_expiracion)
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self._settings.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": token_generator.generate_secure_token(16),
            "type": "refresh"
        }
        
        token = jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm
        )
        
        return token, expire
    
    def create_token_pair(
        self,
        user_id: str,
        roles: list = None
    ) -> TokenPair:
        """
        Crea un par de tokens (access + refresh).
        
        Args:
            user_id: ID del usuario.
            roles: Lista de roles.
            
        Returns:
            TokenPair: Par de tokens.
        """
        access_token, access_exp = self.create_access_token(user_id, roles)
        refresh_token, _ = self.create_refresh_token(user_id)
        
        expires_in = int(
            (access_exp - datetime.now(timezone.utc)).total_seconds()
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
    
    def verify_token(
        self,
        token: str,
        expected_type: str = "access"
    ) -> Optional[TokenPayload]:
        """
        Verifica y decodifica un token JWT.
        
        Args:
            token: Token JWT a verificar.
            expected_type: Tipo esperado ("access" o "refresh").
            
        Returns:
            TokenPayload si el token es válido, None si no.
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm]
            )
            
            # Verificar tipo de token
            if payload.get("type") != expected_type:
                return None
            
            # Verificar si está en blacklist
            jti = payload.get("jti")
            if jti and jti in self._token_blacklist:
                return None
            
            return TokenPayload(**payload)
            
        except ExpiredSignatureError:
            # Token expirado
            return None
        except JWTError:
            # Token inválido
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoca un token añadiéndolo a la blacklist.
        
        Args:
            token: Token a revocar.
            
        Returns:
            bool: True si se revocó exitosamente.
        """
        try:
            # Decodificar sin verificar expiración para obtener JTI
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            if jti:
                self._token_blacklist.add(jti)
                return True
            return False
            
        except JWTError:
            return False
    
    def refresh_access_token(
        self,
        refresh_token: str,
        roles: list = None
    ) -> Optional[TokenPair]:
        """
        Genera nuevo par de tokens usando refresh token.
        
        Args:
            refresh_token: Token de refresh válido.
            roles: Roles del usuario.
            
        Returns:
            TokenPair si el refresh token es válido, None si no.
        """
        payload = self.verify_token(refresh_token, expected_type="refresh")
        
        if not payload:
            return None
        
        # Revocar el refresh token usado (rotación de tokens)
        self.revoke_token(refresh_token)
        
        # Crear nuevo par de tokens
        return self.create_token_pair(payload.sub, roles)
    
    def extract_user_id(self, token: str) -> Optional[str]:
        """
        Extrae el user_id de un token sin verificación completa.
        Solo para logging/debugging.
        
        Args:
            token: Token JWT.
            
        Returns:
            str: User ID o None.
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
                options={"verify_exp": False}
            )
            return payload.get("sub")
        except JWTError:
            return None


class CSRFProtection:
    """
    Protección contra Cross-Site Request Forgery.
    """
    
    _csrf_tokens: Dict[str, datetime] = {}
    TOKEN_LIFETIME_MINUTES = 60
    
    @classmethod
    def generate_token(cls, session_id: str) -> str:
        """
        Genera un token CSRF para una sesión.
        
        Args:
            session_id: ID de la sesión del usuario.
            
        Returns:
            str: Token CSRF.
        """
        token = token_generator.generate_csrf_token()
        cls._csrf_tokens[token] = datetime.now(timezone.utc)
        return token
    
    @classmethod
    def validate_token(cls, token: str) -> bool:
        """
        Valida un token CSRF.
        
        Args:
            token: Token CSRF a validar.
            
        Returns:
            bool: True si el token es válido.
        """
        if token not in cls._csrf_tokens:
            return False
        
        created_at = cls._csrf_tokens[token]
        now = datetime.now(timezone.utc)
        
        # Verificar que no haya expirado
        if (now - created_at) > timedelta(minutes=cls.TOKEN_LIFETIME_MINUTES):
            del cls._csrf_tokens[token]
            return False
        
        # Token de un solo uso
        del cls._csrf_tokens[token]
        return True
    
    @classmethod
    def cleanup_expired(cls):
        """Limpia tokens CSRF expirados."""
        now = datetime.now(timezone.utc)
        expired = [
            token for token, created in cls._csrf_tokens.items()
            if (now - created) > timedelta(minutes=cls.TOKEN_LIFETIME_MINUTES)
        ]
        for token in expired:
            del cls._csrf_tokens[token]


# Instancia singleton
jwt_manager = JWTManager()
