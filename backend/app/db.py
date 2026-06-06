"""Database engine and init helper."""
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

engine = create_async_engine(settings.DATABASE_URL, future=True)


async def init_db() -> None:
    """Create all tables defined on Base.metadata (no-op if they already exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
