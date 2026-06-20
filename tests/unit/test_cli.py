"""CLI smoke tests."""

from typer.testing import CliRunner

from bluesky_graph_analytics.interfaces.cli.main import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
