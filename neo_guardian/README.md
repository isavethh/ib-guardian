# 🚀 NEO Guardian - Sistema de Monitoreo de Asteroides

<div align="center">

![NEO Guardian](https://img.shields.io/badge/NEO-Guardian-6366f1?style=for-the-badge&logo=rocket&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Security](https://img.shields.io/badge/Security-Enterprise-10b981?style=for-the-badge&logo=shield&logoColor=white)

**Sistema de monitoreo de Near Earth Objects (NEOs) con características de ciberseguridad de nivel empresarial**

[Demo](#demo) • [Instalación](#instalación) • [Seguridad](#características-de-seguridad) • [API](#documentación-api) • [MIT Solve](#mit-solve)

</div>

---

## 📋 Descripción

NEO Guardian es un sistema innovador diseñado para el **MIT Solve Challenge** que combina:

1. **Monitoreo Espacial**: Seguimiento en tiempo real de asteroides cercanos a la Tierra usando la API oficial de NASA
2. **Ciberseguridad Avanzada**: Implementación de mejores prácticas de seguridad para protección de datos y usuarios
3. **Análisis de Riesgos**: Sistema de alertas basado en proximidad y características de los NEOs

### 🎯 Problema que Resuelve

La detección temprana de objetos espaciales potencialmente peligrosos es crucial para la seguridad global. NEO Guardian democratiza el acceso a estos datos mientras implementa un modelo de seguridad robusto que puede ser replicado en otras aplicaciones críticas.

---

## 🔐 Características de Seguridad

Este proyecto fue diseñado con **ciberseguridad como prioridad**, implementando:

### Autenticación y Autorización

| Característica | Implementación | Archivo |
|---------------|---------------|---------|
| JWT Tokens | Access + Refresh tokens con rotación | `app/core/auth.py` |
| Argon2id Hashing | Ganador de Password Hashing Competition | `app/core/security.py` |
| API Keys | Tokens hasheados con scopes | `app/api/routes/api_keys.py` |
| Role-Based Access | Control granular de permisos | `app/api/dependencies.py` |

### Protección de Datos

| Característica | Implementación | Detalle |
|---------------|---------------|---------|
| Encriptación AES-256 | Fernet (Cryptography) | Emails encriptados en reposo |
| Sanitización de Inputs | Bleach + Regex | Prevención XSS, SQL Injection |
| Validación Estricta | Pydantic v2 | Schemas tipados y validados |

### Defensas Activas

| Característica | Implementación | Configuración |
|---------------|---------------|---------------|
| Rate Limiting | SlowAPI | 60 req/min, 1000 req/hora |
| Brute Force Protection | Account Lockout | 5 intentos → 30 min bloqueo |
| Security Headers | Custom Middleware | CSP, HSTS, X-Frame-Options |
| CORS | FastAPI Middleware | Orígenes configurables |

### Auditoría y Logging

| Característica | Implementación | Uso |
|---------------|---------------|-----|
| Structured Logging | Structlog + JSON | Logs parseables automáticamente |
| Security Audit Trail | AuditLog Model | Registro de todas las acciones |
| Sensitive Data Redaction | Custom Processor | Passwords/tokens ocultados en logs |

---

## 🛠️ Tecnologías

```
Backend:
├── Python 3.11+
├── FastAPI 0.109
├── SQLAlchemy 2.0 (Async)
├── Pydantic 2.5
└── SQLite (Async)

Seguridad:
├── python-jose (JWT)
├── argon2-cffi
├── cryptography (Fernet)
├── passlib
└── bleach

APIs:
├── NASA NEO API
└── httpx (Async HTTP)

Frontend:
├── HTML5 + Tailwind CSS
├── Chart.js
└── Vanilla JavaScript
```

---

## 📦 Instalación

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes)
- API Key de NASA (gratuita en https://api.nasa.gov)

### Pasos

1. **Clonar el repositorio**
```bash
cd neo_guardian
```

2. **Crear entorno virtual**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Copiar plantilla
copy .env.example .env

# Editar .env con tus valores:
# - NASA_API_KEY: Tu API key de NASA
# - JWT_SECRET_KEY: Generar con: python -c "import secrets; print(secrets.token_hex(32))"
# - ENCRYPTION_KEY: Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

5. **Iniciar el servidor**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Acceder a la aplicación**
- Frontend: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs (solo en DEBUG=true)

---

## 📚 Documentación API

### Endpoints Públicos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estado del servicio |
| GET | `/health` | Health check |
| GET | `/api/v1/neo/today` | Estadísticas de hoy |
| POST | `/api/v1/auth/register` | Registro de usuario |
| POST | `/api/v1/auth/login` | Inicio de sesión |

### Endpoints Autenticados

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/neo/feed` | Lista de NEOs | JWT |
| GET | `/api/v1/neo/hazardous` | Solo peligrosos | JWT |
| GET | `/api/v1/neo/{id}` | Detalle de NEO | JWT |
| GET | `/api/v1/neo/analysis/closest` | NEOs más cercanos | JWT |
| POST | `/api/v1/api-keys` | Crear API Key | JWT |
| GET | `/api/v1/auth/me` | Info usuario actual | JWT |

### Ejemplo de Uso

```python
import httpx

# Login
response = httpx.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "mi_usuario", "password": "MiContraseña123!"}
)
tokens = response.json()

# Consultar NEOs peligrosos
response = httpx.get(
    "http://localhost:8000/api/v1/neo/hazardous",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)
hazardous_neos = response.json()
```

---

## 🔒 Política de Contraseñas

NEO Guardian implementa una política de contraseñas robusta:

- ✅ Mínimo 12 caracteres
- ✅ Al menos una mayúscula
- ✅ Al menos una minúscula  
- ✅ Al menos un número
- ✅ Al menos un carácter especial (!@#$%^&*...)
- ✅ Sin patrones predecibles (123, abc, etc.)

---

## 📊 Estructura del Proyecto

```
neo_guardian/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Autenticación
│   │   │   ├── neo.py           # NEOs endpoints
│   │   │   └── api_keys.py      # Gestión API keys
│   │   └── dependencies.py      # Dependencies seguridad
│   ├── core/
│   │   ├── config.py            # Configuración
│   │   ├── security.py          # Encriptación, hashing
│   │   ├── auth.py              # JWT manager
│   │   └── logging.py           # Logging estructurado
│   ├── middleware/
│   │   ├── security.py          # Headers de seguridad
│   │   └── rate_limit.py        # Rate limiting
│   ├── models/
│   │   ├── models.py            # Modelos SQLAlchemy
│   │   └── database.py          # Configuración DB
│   ├── services/
│   │   └── nasa_client.py       # Cliente NASA API
│   └── main.py                  # Aplicación FastAPI
├── static/
│   └── index.html               # Frontend
├── logs/                        # Logs de auditoría
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🏆 MIT Solve

Este proyecto está diseñado para el **MIT Solve Global Challenges**:

### Categoría: Global Health Security / Climate & Environment

**Propuesta de Valor:**
1. Democratización del acceso a datos espaciales críticos
2. Modelo de seguridad replicable para aplicaciones gubernamentales
3. Framework de auditoría para sistemas de alerta temprana
4. Educación pública sobre amenazas espaciales

### Impacto

- 🌍 **Global**: Datos de NASA accesibles mundialmente
- 🔐 **Seguro**: Modelo de seguridad enterprise-grade
- 📚 **Educativo**: Código abierto y documentado
- ⚡ **Escalable**: Arquitectura moderna async

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Añade nueva funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

Desarrollado con ❤️ para demostrar habilidades de ciberseguridad en desarrollo de software.

---

<div align="center">

**🚀 NEO Guardian - Protegiendo la Tierra, un asteroide a la vez 🌍**

</div>
