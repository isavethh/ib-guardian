"""
NEO Guardian - Configuración de Base de Datos
==============================================
Configuración async de SQLAlchemy con SQLite.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from typing import AsyncGenerator

from app.core.config import get_settings
from app.models.models import Base


settings = get_settings()

# Crear engine async
engine = create_async_engine(
    settings.database.database_url,
    echo=settings.server.debug,
    future=True,
)

# Configurar session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Inicializa la base de datos creando todas las tablas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos.
    
    Yields:
        AsyncSession: Sesión de base de datos.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
