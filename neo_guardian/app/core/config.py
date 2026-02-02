"""
NEO Guardian - Configuración Central
=====================================
Gestión segura de configuración usando Pydantic Settings.
Todas las variables sensibles se cargan desde variables de entorno.
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import secrets


class SecuritySettings(BaseSettings):
    """Configuración de seguridad del sistema."""
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Clave secreta para firmar JWT tokens"
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    
    # Encryption
    encryption_key: str = Field(
        default="",
        description="Clave Fernet para encriptación de datos sensibles"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, ge=10, le=1000)
    rate_limit_per_hour: int = Field(default=1000, ge=100, le=10000)
    
    # Password Policy
    min_password_length: int = Field(default=12)
    require_uppercase: bool = Field(default=True)
    require_lowercase: bool = Field(default=True)
    require_digits: bool = Field(default=True)
    require_special_chars: bool = Field(default=True)
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class NASASettings(BaseSettings):
    """Configuración de la API de NASA."""
    
    nasa_api_key: str = Field(default="DEMO_KEY")
    nasa_base_url: str = Field(default="https://api.nasa.gov")
    neo_feed_endpoint: str = Field(default="/neo/rest/v1/feed")
    neo_lookup_endpoint: str = Field(default="/neo/rest/v1/neo")
    
    # Timeouts (en segundos)
    api_timeout: int = Field(default=30, ge=5, le=120)
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class DatabaseSettings(BaseSettings):
    """Configuración de base de datos."""
    
    database_url: str = Field(
        default="sqlite+aiosqlite:///./neo_guardian.db"
    )
    
    # Pool configuration
    pool_size: int = Field(default=5, ge=1, le=20)
    max_overflow: int = Field(default=10, ge=0, le=50)
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class ServerSettings(BaseSettings):
    """Configuración del servidor."""
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    debug: bool = Field(default=False)
    environment: str = Field(default="production")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000"
    )
    
    @property
    def origins_list(self) -> List[str]:
        """Retorna lista de orígenes CORS permitidos."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class LoggingSettings(BaseSettings):
    """Configuración de logging."""
    
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/neo_guardian.log")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    enable_audit_log: bool = Field(default=True)
    audit_log_file: str = Field(default="logs/audit.log")
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class Settings(BaseSettings):
    """Configuración principal que agrupa todas las configuraciones."""
    
    app_name: str = Field(default="NEO Guardian")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(
        default="Sistema de Monitoreo de Objetos Cercanos a la Tierra"
    )
    
    # Sub-configuraciones
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    nasa: NASASettings = Field(default_factory=NASASettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la instancia de configuración (singleton cacheado).
    
    Returns:
        Settings: Instancia de configuración del sistema.
    """
    return Settings()
