"""
NEO Guardian - Modelos de Base de Datos
========================================
Define los modelos SQLAlchemy con seguridad integrada.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, Index, event
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
import uuid

from app.core.security import password_manager, encryption_manager


def generate_uuid() -> str:
    """Genera un UUID único."""
    return str(uuid.uuid4())


class Base(AsyncAttrs, DeclarativeBase):
    """Clase base para todos los modelos."""
    pass


class User(Base):
    """
    Modelo de usuario con seguridad integrada.
    
    Características de seguridad:
    - Contraseñas hasheadas con Argon2
    - Email encriptado en reposo
    - Tracking de intentos de login fallidos
    - Bloqueo de cuenta después de múltiples intentos
    """
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email_encrypted = Column(String(500), nullable=False)  # Email encriptado
    password_hash = Column(String(255), nullable=False)
    
    # Seguridad
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Roles
    roles = Column(String(255), default="user")  # Comma-separated roles
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_active', 'is_active'),
    )
    
    def set_password(self, password: str):
        """Hashea y establece la contraseña."""
        self.password_hash = password_manager.hash_password(password)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def verify_password(self, password: str) -> bool:
        """Verifica la contraseña."""
        return password_manager.verify_password(password, self.password_hash)
    
    def set_email(self, email: str):
        """Encripta y establece el email."""
        self.email_encrypted = encryption_manager.encrypt(email)
    
    def get_email(self) -> str:
        """Desencripta y retorna el email."""
        return encryption_manager.decrypt(self.email_encrypted)
    
    def get_roles_list(self) -> List[str]:
        """Retorna lista de roles."""
        return [r.strip() for r in self.roles.split(",") if r.strip()]
    
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def record_failed_login(self):
        """Registra un intento de login fallido."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Bloquear por 30 minutos después de 5 intentos
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def record_successful_login(self):
        """Registra un login exitoso."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.now(timezone.utc)


class APIKey(Base):
    """
    API Keys para acceso programático.
    
    Seguridad:
    - Solo se almacena el hash de la key
    - Scopes limitados por key
    - Expiración configurable
    """
    
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    key_prefix = Column(String(10), nullable=False)  # Primeros caracteres para identificación
    
    # Permisos
    scopes = Column(String(500), default="read")  # Comma-separated scopes
    
    # Expiración
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_apikey_hash', 'key_hash'),
        Index('idx_apikey_user', 'user_id'),
    )
    
    def is_expired(self) -> bool:
        """Verifica si la API key ha expirado."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def get_scopes_list(self) -> List[str]:
        """Retorna lista de scopes."""
        return [s.strip() for s in self.scopes.split(",") if s.strip()]
    
    def has_scope(self, scope: str) -> bool:
        """Verifica si tiene un scope específico."""
        return scope in self.get_scopes_list() or "admin" in self.get_scopes_list()


class NEOObject(Base):
    """
    Objetos Cercanos a la Tierra (Near Earth Objects).
    
    Almacena datos de la API de NASA.
    """
    
    __tablename__ = "neo_objects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    neo_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Características físicas
    estimated_diameter_min_km = Column(Float, nullable=True)
    estimated_diameter_max_km = Column(Float, nullable=True)
    
    # Peligrosidad
    is_potentially_hazardous = Column(Boolean, default=False)
    is_sentry_object = Column(Boolean, default=False)
    
    # Órbita
    absolute_magnitude = Column(Float, nullable=True)
    
    # Metadata
    first_observation_date = Column(DateTime(timezone=True), nullable=True)
    last_observation_date = Column(DateTime(timezone=True), nullable=True)
    nasa_jpl_url = Column(String(500), nullable=True)
    
    # Cache
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    close_approaches = relationship("CloseApproach", back_populates="neo_object", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_neo_hazardous', 'is_potentially_hazardous'),
        Index('idx_neo_name', 'name'),
    )


class CloseApproach(Base):
    """
    Aproximaciones cercanas de NEOs a la Tierra.
    """
    
    __tablename__ = "close_approaches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    neo_object_id = Column(String(36), ForeignKey("neo_objects.id"), nullable=False)
    
    # Datos de aproximación
    close_approach_date = Column(DateTime(timezone=True), nullable=False)
    epoch_date_close_approach = Column(Integer, nullable=True)
    
    # Velocidad
    relative_velocity_kmh = Column(Float, nullable=True)
    relative_velocity_kms = Column(Float, nullable=True)
    
    # Distancia
    miss_distance_km = Column(Float, nullable=True)
    miss_distance_lunar = Column(Float, nullable=True)
    miss_distance_astronomical = Column(Float, nullable=True)
    
    # Órbita
    orbiting_body = Column(String(50), default="Earth")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    neo_object = relationship("NEOObject", back_populates="close_approaches")
    
    __table_args__ = (
        Index('idx_approach_date', 'close_approach_date'),
        Index('idx_approach_neo', 'neo_object_id'),
    )


class Alert(Base):
    """
    Alertas de NEOs peligrosos para usuarios.
    """
    
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Configuración de alerta
    alert_type = Column(String(50), nullable=False)  # "hazardous", "close_approach", "custom"
    threshold_distance_km = Column(Float, nullable=True)
    threshold_diameter_km = Column(Float, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user = relationship("User", back_populates="alerts")


class AuditLog(Base):
    """
    Log de auditoría de seguridad.
    
    Registra todas las acciones sensibles del sistema.
    """
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Evento
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    
    # Detalles
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)  # JSON con detalles adicionales
    
    # Resultado
    status = Column(String(20), nullable=False)  # "success", "failure", "warning"
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_timestamp', 'created_at'),
    )
