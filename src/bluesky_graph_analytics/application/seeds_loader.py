"""Load and validate seed_profiles.yaml (DEO 6.2)."""

from pathlib import Path

from returns.result import Failure, Result, Success

from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.seeds.seed_file import (
    SeedFile,
    SeedFileLoader,
    SeedFileValidationError,
)


def load_seed_file(settings: AppSettings) -> Result[SeedFile, DomainError]:
    path = Path(settings.collection.seed_source_file)
    loader = SeedFileLoader(enforce_mvp_bounds=settings.collection.enforce_mvp_seed_count)
    try:
        return Success(loader.load(path))
    except SeedFileValidationError as exc:
        return Failure(DomainError(code=ErrorCode.VALIDATION, message=str(exc)))
