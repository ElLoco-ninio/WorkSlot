"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async engine
database_url = settings.DATABASE_URL
import os
print(f"DEBUG: All Env Keys: {list(os.environ.keys())}")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

try:
    # Basic masking for logs
    safe_url = database_url.split("@")[-1] if "@" in database_url else "UNKNOWN"
    print(f"DEBUG: Attempting to connect to database at: {safe_url}")
except Exception:
    print("DEBUG: Could not parse database URL for logging")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    poolclass=NullPool if settings.ENVIRONMENT == "testing" else None,
    pool_size=settings.DATABASE_POOL_SIZE if settings.ENVIRONMENT != "testing" else None,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if settings.ENVIRONMENT != "testing" else None,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

