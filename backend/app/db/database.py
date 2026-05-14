"""
PG-AGI Database Connection Manager
Uses the configured DATABASE_URL when provided, and falls back to SQLite.
On Vercel, the SQLite fallback is moved to /tmp to avoid read-only bundle errors.
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Base

settings = get_settings()
DEFAULT_POSTGRES_PLACEHOLDER = "postgresql+asyncpg://postgres:postgres@localhost:5432/pgagi_db"


def _default_sqlite_url() -> str:
    if os.getenv("VERCEL"):
        sqlite_path = os.path.join("/tmp", "pgagi.db")
    else:
        db_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sqlite_path = os.path.join(db_dir, "pgagi.db")

    return f"sqlite+aiosqlite:///{sqlite_path}"


configured_url = settings.DATABASE_URL.strip()
use_configured_database = bool(configured_url) and configured_url != DEFAULT_POSTGRES_PLACEHOLDER

DATABASE_URL = configured_url if use_configured_database else _default_sqlite_url()

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Create all database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency injection for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
