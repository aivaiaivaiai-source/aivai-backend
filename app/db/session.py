from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

_read_engine = create_async_engine(
    settings.DATABASE_READ_URL,
    echo=False,
    pool_pre_ping=True,
)
async_read_session_maker = async_sessionmaker(
    _read_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Prefer read replica when POSTGRES_READ_SERVER is set; else primary."""
    async with async_read_session_maker() as session:
        yield session
