"""Test-only DB helpers — create_all() allowed here only (spec 1.9)."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from bluesky_graph_analytics.infrastructure.persistence.models import Base


async def create_test_schema(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine
