"""
NEO Guardian - Módulo de Seguridad Principal
=============================================
Este módulo implementa las funcionalidades core de ciberseguridad:
- Encriptación AES-256 (Fernet)
- Hashing seguro de contraseñas (Argon2)
- Validación y sanitización de inputs
- Generación segura de tokens
"""

import re
import secrets
import hashlib
import hmac
from typing import Optional, Tuple
from datetime import datetime, timezone
import bleach
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

from app.core.config import get_settings


class EncryptionManager:
    """
    Gestor de encriptación usando Fernet (AES-256-CBC).
    
    Fernet garantiza que los datos encriptados no pueden ser
    manipulados o leídos sin la clave correcta.
    
    Seguridad implementada:
    - AES-256 en modo CBC
    - HMAC-SHA256 para autenticación
    - Timestamps para prevenir replay attacks
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Inicializa el gestor de encriptación.
        
        Args:
            key: Clave Fernet en formato base64. Si no se proporciona,
                 se genera una nueva.
        """
        settings = get_settings()
        
        if key:
            self._key = key.encode() if isinstance(key, str) else key
        elif settings.security.encryption_key:
            self._key = settings.security.encryption_key.encode()
        else:
            # Generar nueva clave si no existe
            self._key = Fernet.generate_key()
            
        self._fernet = Fernet(self._key)
    
    def encrypt(self, data: str) -> str:
        """
        Encripta datos sensibles.
        
        Args:
            data: Texto plano a encriptar.
            
        Returns:
            str: Datos encriptados en base64.
        """
        if not data:
            raise ValueError("No se pueden encriptar datos vacíos")
        
        encrypted = self._fernet.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Desencripta datos.
        
        Args:
            encrypted_data: Datos encriptados en base64.
            
        Returns:
            str: Texto plano original.
            
        Raises:
            InvalidToken: Si los datos fueron manipulados o la clave es incorrecta.
        """
        if not encrypted_data:
            raise ValueError("No se pueden desencriptar datos vacíos")
        
        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise ValueError("Datos encriptados inválidos o manipulados")
    
    def encrypt_with_ttl(self, data: str, ttl_seconds: int) -> str:
        """
        Encripta datos con tiempo de vida limitado.
        
        Args:
            data: Texto plano a encriptar.
            ttl_seconds: Tiempo de vida en segundos.
            
        Returns:
            str: Datos encriptados con timestamp.
        """
        encrypted = self._fernet.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt_with_ttl(self, encrypted_data: str, ttl_seconds: int) -> str:
        """
        Desencripta datos verificando que no hayan expirado.
        
        Args:
            encrypted_data: Datos encriptados.
            ttl_seconds: Tiempo máximo de vida en segundos.
            
        Returns:
            str: Texto plano si no ha expirado.
            
        Raises:
            InvalidToken: Si los datos expiraron o son inválidos.
        """
        try:
            decrypted = self._fernet.decrypt(
                encrypted_data.encode('utf-8'),
                ttl=ttl_seconds
            )
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise ValueError("Datos expirados o inválidos")
    
    @staticmethod
    def generate_key() -> str:
        """Genera una nueva clave de encriptación."""
        return Fernet.generate_key().decode('utf-8')


class PasswordManager:
    """
    Gestor de contraseñas usando Argon2id.
    
    Argon2 es el ganador de la Password Hashing Competition (2015)
    y es resistente a:
    - Ataques de GPU
    - Ataques de side-channel
    - Ataques de tiempo
    
    Configuración segura:
    - Memory cost: 65536 KB (64 MB)
    - Time cost: 3 iteraciones
    - Parallelism: 4 threads
    """
    
    def __init__(self):
        """Inicializa el hasher con parámetros seguros."""
        self._hasher = PasswordHasher(
            time_cost=3,          # Iteraciones
            memory_cost=65536,    # 64 MB de memoria
            parallelism=4,        # 4 threads paralelos
            hash_len=32,          # Longitud del hash
            salt_len=16           # Longitud del salt
        )
        
        # Fallback con bcrypt para compatibilidad
        self._pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto"
        )
        
        self._settings = get_settings().security
    
    def validate_password_strength(self, password: str) -> Tuple[bool, list]:
        """
        Valida la fortaleza de una contraseña.
        
        Args:
            password: Contraseña a validar.
            
        Returns:
            Tuple[bool, list]: (es_válida, lista_de_errores)
        """
        errors = []
        
        if len(password) < self._settings.min_password_length:
            errors.append(
                f"La contraseña debe tener al menos "
                f"{self._settings.min_password_length} caracteres"
            )
        
        if self._settings.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Debe contener al menos una mayúscula")
        
        if self._settings.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Debe contener al menos una minúscula")
        
        if self._settings.require_digits and not re.search(r'\d', password):
            errors.append("Debe contener al menos un número")
        
        if self._settings.require_special_chars and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Debe contener al menos un carácter especial")
        
        # Verificar patrones comunes inseguros
        common_patterns = [
            r'(.)\1{2,}',  # Caracteres repetidos
            r'(012|123|234|345|456|567|678|789|890)',  # Secuencias numéricas
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Secuencias alfabéticas
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append("No debe contener patrones predecibles")
                break
        
        return len(errors) == 0, errors
    
    def hash_password(self, password: str) -> str:
        """
        Genera hash seguro de una contraseña.
        
        Args:
            password: Contraseña en texto plano.
            
        Returns:
            str: Hash Argon2id de la contraseña.
        """
        return self._hasher.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica una contraseña contra su hash.
        
        Args:
            password: Contraseña en texto plano.
            hashed: Hash almacenado.
            
        Returns:
            bool: True si la contraseña es correcta.
        """
        try:
            self._hasher.verify(hashed, password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Verifica si un hash necesita ser actualizado.
        
        Útil cuando se cambian los parámetros de hashing.
        """
        return self._hasher.check_needs_rehash(hashed)


class InputSanitizer:
    """
    Sanitizador de inputs para prevenir:
    - XSS (Cross-Site Scripting)
    - SQL Injection
    - Command Injection
    - Path Traversal
    """
    
    # Patrones peligrosos de SQL Injection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(;|\|\|)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bxp_\w+)",
    ]
    
    # Patrones de Command Injection
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(.*\)",
        r"`.*`",
        r"\|.*\|",
    ]
    
    # Patrones de Path Traversal
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.%2e/",
        r"%2e\./",
    ]
    
    @classmethod
    def sanitize_html(cls, text: str, allowed_tags: list = None) -> str:
        """
        Sanitiza HTML para prevenir XSS.
        
        Args:
            text: Texto con posible HTML malicioso.
            allowed_tags: Lista de tags HTML permitidos.
            
        Returns:
            str: Texto sanitizado.
        """
        if allowed_tags is None:
            allowed_tags = []  # Por defecto, no permitir ningún tag
        
        return bleach.clean(
            text,
            tags=allowed_tags,
            attributes={},
            strip=True
        )
    
    @classmethod
    def check_sql_injection(cls, text: str) -> Tuple[bool, str]:
        """
        Detecta posibles intentos de SQL Injection.
        
        Args:
            text: Texto a verificar.
            
        Returns:
            Tuple[bool, str]: (es_seguro, patrón_detectado)
        """
        text_upper = text.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return False, pattern
        
        return True, ""
    
    @classmethod
    def check_command_injection(cls, text: str) -> Tuple[bool, str]:
        """
        Detecta posibles intentos de Command Injection.
        
        Args:
            text: Texto a verificar.
            
        Returns:
            Tuple[bool, str]: (es_seguro, patrón_detectado)
        """
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return False, pattern
        
        return True, ""
    
    @classmethod
    def check_path_traversal(cls, path: str) -> Tuple[bool, str]:
        """
        Detecta intentos de Path Traversal.
        
        Args:
            path: Ruta a verificar.
            
        Returns:
            Tuple[bool, str]: (es_seguro, patrón_detectado)
        """
        path_lower = path.lower()
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path_lower, re.IGNORECASE):
                return False, pattern
        
        return True, ""
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitiza un nombre de archivo.
        
        Args:
            filename: Nombre de archivo original.
            
        Returns:
            str: Nombre de archivo seguro.
        """
        # Remover caracteres peligrosos
        safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Remover puntos al inicio (archivos ocultos)
        safe_filename = safe_filename.lstrip('.')
        
        # Limitar longitud
        if len(safe_filename) > 255:
            name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
            safe_filename = name[:250] + ('.' + ext if ext else '')
        
        return safe_filename or 'unnamed_file'
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Sanitización completa de input de usuario.
        
        Args:
            text: Input del usuario.
            
        Returns:
            str: Input sanitizado.
        """
        # Sanitizar HTML
        text = cls.sanitize_html(text)
        
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normalizar espacios en blanco
        text = ' '.join(text.split())
        
        return text.strip()


class TokenGenerator:
    """
    Generador de tokens seguros para diversos propósitos.
    """
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Genera un token criptográficamente seguro.
        
        Args:
            length: Longitud del token en bytes.
            
        Returns:
            str: Token hexadecimal.
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_url_safe_token(length: int = 32) -> str:
        """
        Genera un token seguro para URLs.
        
        Args:
            length: Longitud del token en bytes.
            
        Returns:
            str: Token URL-safe en base64.
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Genera una API key con formato estándar.
        
        Returns:
            str: API key con prefijo 'neo_'.
        """
        return f"neo_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Genera un token CSRF.
        
        Returns:
            str: Token CSRF.
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Genera hash de un token para almacenamiento seguro.
        
        Args:
            token: Token original.
            
        Returns:
            str: Hash SHA-256 del token.
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """
        Comparación de strings en tiempo constante.
        
        Previene ataques de timing al comparar tokens.
        
        Args:
            a: Primer string.
            b: Segundo string.
            
        Returns:
            bool: True si son iguales.
        """
        return hmac.compare_digest(a.encode(), b.encode())


# Instancias singleton para uso global
encryption_manager = EncryptionManager()
password_manager = PasswordManager()
input_sanitizer = InputSanitizer()
token_generator = TokenGenerator()
