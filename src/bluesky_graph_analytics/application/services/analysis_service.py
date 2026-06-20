"""Orchestrates DEO 8 analysis layers."""

from __future__ import annotations

from returns.result import Failure, Result

from bluesky_graph_analytics.application.dto import AnalysisRequestDTO
from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.application.reproducibility import set_global_seeds, sha256_directory
from bluesky_graph_analytics.application.services.layers._common import refresh_run, results_dir_for
from bluesky_graph_analytics.application.services.layers.community_layer import (
    CommunityLayerService,
)
from bluesky_graph_analytics.application.services.layers.prediction_layer import (
    PredictionLayerService,
)
from bluesky_graph_analytics.application.services.layers.similarity_layer import (
    SimilarityLayerService,
)
from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.value_objects import SnapshotId


class AnalysisService:
    def __init__(
        self,
        runs: RunRepository,
        similarity: SimilarityLayerService,
        community: CommunityLayerService,
        prediction: PredictionLayerService,
        settings: AppSettings,
    ) -> None:
        self._runs = runs
        self._similarity = similarity
        self._community = community
        self._prediction = prediction
        self._settings = settings

    async def run_similarity(self, request: AnalysisRequestDTO) -> Result[AnalysisRun, DomainError]:
        set_global_seeds(self._settings.reproducibility.random_seed)
        snap = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        return await self._similarity.run(snap)

    async def run_community(self, request: AnalysisRequestDTO) -> Result[AnalysisRun, DomainError]:
        set_global_seeds(self._settings.reproducibility.random_seed)
        snap = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        return await self._community.run(snap)

    async def run_prediction(self, request: AnalysisRequestDTO) -> Result[AnalysisRun, DomainError]:
        set_global_seeds(self._settings.reproducibility.random_seed)
        snap = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        return await self._prediction.run(snap)

    async def run_all(self, request: AnalysisRequestDTO) -> Result[AnalysisRun, DomainError]:
        set_global_seeds(self._settings.reproducibility.random_seed)
        snap = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        run: AnalysisRun | None = None
        for layer in (self._similarity.run, self._community.run, self._prediction.run):
            result = await layer(snap)
            if isinstance(result, Failure):
                return result
            run = result.unwrap()
        assert run is not None and run.id is not None
        output_hash = sha256_directory(results_dir_for(snap))
        await self._runs.update_stat(run.id, "output_sha256", output_hash)
        await self._runs.finalize_run(run.id, status=RunStatus.COMPLETED)
        return await refresh_run(self._runs, run.id, run)

    async def run_analysis(self, request: AnalysisRequestDTO) -> Result[AnalysisRun, DomainError]:
        return await self.run_all(request)
