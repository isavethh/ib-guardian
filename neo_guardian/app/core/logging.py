"""
NEO Guardian - Sistema de Logging Estructurado
===============================================
Logging seguro con estructlog para auditoría y debugging.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Any, Dict
import structlog
from structlog.typing import EventDict

from app.core.config import get_settings


def setup_logging():
    """
    Configura el sistema de logging estructurado.
    
    Características:
    - Logs JSON para procesamiento automático
    - Separación de logs de aplicación y auditoría
    - Sanitización de datos sensibles
    - Rotación de archivos (a implementar con logrotate)
    """
    settings = get_settings()
    
    # Crear directorio de logs
    log_dir = Path(settings.logging.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar nivel de log
    log_level = getattr(logging, settings.logging.log_level.upper(), logging.INFO)
    
    # Procesadores de structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _sanitize_sensitive_data,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configurar structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Formatter para salida JSON
    json_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer()
        ]
    )
    
    # Formatter para consola (desarrollo)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(settings.logging.log_file)
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(log_level)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.server.debug:
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(json_formatter)
    console_handler.setLevel(log_level)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Logger específico para auditoría
    if settings.logging.enable_audit_log:
        audit_handler = logging.FileHandler(settings.logging.audit_log_file)
        audit_handler.setFormatter(json_formatter)
        audit_handler.setLevel(logging.INFO)
        
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
    
    return structlog.get_logger()


def _sanitize_sensitive_data(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict
) -> EventDict:
    """
    Sanitiza datos sensibles antes de loggear.
    
    Oculta:
    - Contraseñas
    - Tokens
    - API keys
    - Emails
    """
    sensitive_keys = {
        "password", "pwd", "secret", "token", "api_key", "apikey",
        "authorization", "auth", "credential", "private_key",
        "access_token", "refresh_token", "email"
    }
    
    def sanitize_value(key: str, value: Any) -> Any:
        key_lower = key.lower()
        
        for sensitive in sensitive_keys:
            if sensitive in key_lower:
                if isinstance(value, str):
                    if len(value) > 8:
                        return f"{value[:4]}...{value[-4:]}"
                    return "***REDACTED***"
                return "***REDACTED***"
        
        if isinstance(value, dict):
            return {k: sanitize_value(k, v) for k, v in value.items()}
        
        return value
    
    return {k: sanitize_value(k, v) for k, v in event_dict.items()}


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Obtiene un logger con contexto.
    
    Args:
        name: Nombre del logger (módulo).
        
    Returns:
        Logger configurado.
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def get_audit_logger() -> logging.Logger:
    """
    Obtiene el logger de auditoría.
    
    Usar para eventos de seguridad importantes.
    """
    return logging.getLogger("audit")


class SecurityAuditLogger:
    """
    Logger especializado para eventos de seguridad.
    
    Registra eventos críticos con formato estandarizado.
    """
    
    def __init__(self):
        self._logger = get_audit_logger()
        self._struct_logger = get_logger("security")
    
    def _format_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formatea un evento de seguridad."""
        return {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        }
    
    def log_authentication(
        self,
        success: bool,
        user_id: str = None,
        username: str = None,
        ip_address: str = None,
        method: str = "password",
        failure_reason: str = None
    ):
        """Registra un evento de autenticación."""
        event = self._format_event(
            event_type="authentication",
            severity="info" if success else "warning",
            details={
                "success": success,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "method": method,
                "failure_reason": failure_reason
            }
        )
        
        if success:
            self._logger.info(json.dumps(event))
        else:
            self._logger.warning(json.dumps(event))
    
    def log_authorization(
        self,
        allowed: bool,
        user_id: str,
        resource: str,
        action: str,
        required_permission: str = None
    ):
        """Registra un evento de autorización."""
        event = self._format_event(
            event_type="authorization",
            severity="info" if allowed else "warning",
            details={
                "allowed": allowed,
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "required_permission": required_permission
            }
        )
        
        if allowed:
            self._logger.info(json.dumps(event))
        else:
            self._logger.warning(json.dumps(event))
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,  # read, create, update, delete
        success: bool = True
    ):
        """Registra acceso a datos sensibles."""
        event = self._format_event(
            event_type="data_access",
            severity="info",
            details={
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "success": success
            }
        )
        self._logger.info(json.dumps(event))
    
    def log_security_alert(
        self,
        alert_type: str,
        severity: str,  # low, medium, high, critical
        description: str,
        ip_address: str = None,
        user_id: str = None,
        additional_data: Dict[str, Any] = None
    ):
        """Registra una alerta de seguridad."""
        event = self._format_event(
            event_type="security_alert",
            severity=severity,
            details={
                "alert_type": alert_type,
                "description": description,
                "ip_address": ip_address,
                "user_id": user_id,
                "additional_data": additional_data or {}
            }
        )
        
        if severity in ("high", "critical"):
            self._logger.error(json.dumps(event))
        elif severity == "medium":
            self._logger.warning(json.dumps(event))
        else:
            self._logger.info(json.dumps(event))
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        limit: str
    ):
        """Registra cuando se excede el rate limit."""
        self.log_security_alert(
            alert_type="rate_limit_exceeded",
            severity="medium",
            description=f"Rate limit exceeded for endpoint {endpoint}",
            ip_address=ip_address,
            additional_data={
                "endpoint": endpoint,
                "limit": limit
            }
        )
    
    def log_injection_attempt(
        self,
        injection_type: str,  # sql, command, xss
        ip_address: str,
        payload: str,
        endpoint: str
    ):
        """Registra un intento de inyección detectado."""
        # Truncar payload por seguridad
        safe_payload = payload[:100] + "..." if len(payload) > 100 else payload
        
        self.log_security_alert(
            alert_type="injection_attempt",
            severity="high",
            description=f"{injection_type.upper()} injection attempt detected",
            ip_address=ip_address,
            additional_data={
                "injection_type": injection_type,
                "payload_preview": safe_payload,
                "endpoint": endpoint
            }
        )


# Singleton del security logger
security_logger = SecurityAuditLogger()
