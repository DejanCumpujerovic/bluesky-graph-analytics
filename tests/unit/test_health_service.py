"""Health service checks."""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from bluesky_graph_analytics.application.services.health_service import run_health
from bluesky_graph_analytics.config import AppSettings


@pytest.mark.asyncio
async def test_run_health_ok(db_engine: AsyncEngine, test_settings: AppSettings) -> None:
    def _alembic_output(cmd: list[str], **kwargs: object) -> str:
        if "heads" in cmd:
            return "0004 (head)\n"
        return "0004\n"

    with patch(
        "bluesky_graph_analytics.application.services.health_service.subprocess.check_output",
        side_effect=_alembic_output,
    ):
        payload, code = await run_health(db_engine, test_settings, check_api=False)
    assert code == 0
    assert payload["status"] == "healthy"
    assert payload["checks"]["database"]["ok"] is True


@pytest.mark.asyncio
async def test_run_health_api_check(db_engine: AsyncEngine, test_settings: AppSettings) -> None:
    def _alembic_output(cmd: list[str], **kwargs: object) -> str:
        if "heads" in cmd:
            return "0004 (head)\n"
        return "0004\n"

    with (
        patch(
            "bluesky_graph_analytics.application.services.health_service.subprocess.check_output",
            side_effect=_alembic_output,
        ),
        patch(
            "bluesky_graph_analytics.application.services.health_service.httpx.Client"
        ) as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.get.return_value.status_code = 200
        payload, code = await run_health(db_engine, test_settings, check_api=True)
    assert code == 0
    assert payload["checks"]["api"]["ok"] is True
