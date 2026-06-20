import pytest
from tests.fixtures.db import create_test_schema


@pytest.mark.asyncio
async def test_create_all_fixture() -> None:
    engine = await create_test_schema("sqlite+aiosqlite:///:memory:")
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
    assert "profiles" in tables
    await engine.dispose()
