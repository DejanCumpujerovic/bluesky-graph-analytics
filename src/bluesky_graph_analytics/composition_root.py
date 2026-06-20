"""Manual dependency injection — single composition root (no DI framework)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from bluesky_graph_analytics.application.services.analysis_service import AnalysisService
from bluesky_graph_analytics.application.services.collection_service import CollectionService
from bluesky_graph_analytics.application.services.deletion_service import DeletionService
from bluesky_graph_analytics.application.services.export_service import ExportService
from bluesky_graph_analytics.application.services.layers.community_layer import (
    CommunityLayerService,
)
from bluesky_graph_analytics.application.services.layers.prediction_layer import (
    PredictionLayerService,
)
from bluesky_graph_analytics.application.services.layers.similarity_layer import (
    SimilarityLayerService,
)
from bluesky_graph_analytics.config import AppSettings, load_settings
from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import AtprotoBlueskyClient
from bluesky_graph_analytics.infrastructure.logging import configure_logging
from bluesky_graph_analytics.infrastructure.observability import configure_observability
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyDeletionRepository,
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


class AppContainer:
    def __init__(self, settings: AppSettings, engine: AsyncEngine) -> None:
        self.settings = settings
        self.engine = engine
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        bluesky = AtprotoBlueskyClient(
            service_url=settings.bluesky.api_base,
            handle=settings.bluesky_handle,
            app_password=settings.bluesky_app_password,
            auth_token=settings.bluesky_auth_token,
            requests_per_second=settings.bluesky.requests_per_second,
            timeout_seconds=settings.bluesky.timeout_seconds,
        )
        profiles = SqlAlchemyProfileRepository(session_factory)
        follows = SqlAlchemyFollowRepository(session_factory)
        runs = SqlAlchemyRunRepository(session_factory)
        deletions = SqlAlchemyDeletionRepository(session_factory)

        self.collection = CollectionService(bluesky, profiles, follows, deletions, runs, settings)
        similarity = SimilarityLayerService(runs, follows, profiles, settings)
        community = CommunityLayerService(runs, follows, profiles, settings)
        prediction = PredictionLayerService(runs, follows, profiles, settings)
        self.analysis = AnalysisService(runs, similarity, community, prediction, settings)
        self.export = ExportService(profiles, follows, runs, settings)
        self.deletion = DeletionService(deletions, engine, bluesky)


def build_container(cli_overrides: dict[str, Any] | None = None) -> AppContainer:
    settings = load_settings(cli_overrides=cli_overrides)
    configure_logging(
        settings.effective_log_level,
        log_format=settings.logging.format,
    )
    configure_observability(sentry_dsn=settings.effective_sentry_dsn)
    engine = create_async_engine(settings.storage.database_url, echo=False)
    return AppContainer(settings, engine)


async def dispose_container(container: AppContainer) -> None:
    await container.engine.dispose()
