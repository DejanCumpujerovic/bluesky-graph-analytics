"""Collection use cases — 1-hop crawl (DEO 5 + DEO 7 runs/profiles)."""

from __future__ import annotations

import time
from collections import Counter
from datetime import UTC, datetime

import structlog
from returns.result import Failure, Result, Success

from bluesky_graph_analytics.application.dto import CollectRequestDTO
from bluesky_graph_analytics.application.ports.bluesky_client import BlueskyClient
from bluesky_graph_analytics.application.ports.deletion_repository import DeletionRepository
from bluesky_graph_analytics.application.ports.follow_repository import FollowRepository
from bluesky_graph_analytics.application.ports.profile_repository import ProfileRepository
from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.application.reproducibility import git_commit_hash, set_global_seeds
from bluesky_graph_analytics.application.seed_skipped import append_seed_skipped
from bluesky_graph_analytics.application.seeds_loader import load_seed_file
from bluesky_graph_analytics.config import AppSettings, settings_to_yaml
from bluesky_graph_analytics.constants import CRAWL_DEPTH
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.seeds.seed_file import SeedFile, SeedFileLoader
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import AtprotoBlueskyClient
from bluesky_graph_analytics.infrastructure.nlp import detect_profile_language

logger = structlog.get_logger(__name__)

_ACTIVE_SNAPSHOT_STATUSES = frozenset(
    {RunStatus.RUNNING, RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABORTED}
)


class CollectionService:
    def __init__(
        self,
        bluesky: BlueskyClient,
        profiles: ProfileRepository,
        follows: FollowRepository,
        deletions: DeletionRepository,
        runs: RunRepository,
        settings: AppSettings,
    ) -> None:
        self._bluesky = bluesky
        self._profiles = profiles
        self._follows = follows
        self._deletions = deletions
        self._runs = runs
        self._settings = settings

    async def collect(self, request: CollectRequestDTO) -> Result[dict[str, object], DomainError]:
        set_global_seeds(self._settings.reproducibility.random_seed)

        if CRAWL_DEPTH != 1:
            return Failure(
                DomainError(
                    code=ErrorCode.VALIDATION,
                    message="Only 1-hop crawl supported in Phase 1",
                )
            )

        seed_file_result = load_seed_file(self._settings)
        if isinstance(seed_file_result, Failure):
            return seed_file_result
        seed_file = seed_file_result.unwrap()
        known_dids = SeedFileLoader.known_dids(seed_file)

        handles = _handles_for_collect(request, seed_file)
        if not handles:
            return Failure(
                DomainError(
                    code=ErrorCode.VALIDATION,
                    message="No seed handles to collect (check seed file or CLI)",
                )
            )
        unique_handles = _dedupe_handles(handles)

        snapshot_id = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        existing = await self._runs.get_by_snapshot_id(snapshot_id)
        if isinstance(existing, Failure):
            return existing
        prior = existing.unwrap()
        if prior is not None and prior.status in _ACTIVE_SNAPSHOT_STATUSES:
            if not request.force_resnapshot:
                finished = prior.finished_at.isoformat() if prior.finished_at else "in progress"
                return Failure(
                    DomainError(
                        code=ErrorCode.VALIDATION,
                        message=(
                            f"Snapshot {snapshot_id!r} already exists "
                            f"(run_id={prior.id}, {prior.status.value} {finished}). "
                            "Use --force-resnapshot to delete and re-collect."
                        ),
                    )
                )
            forced = await self._runs.force_resnapshot(snapshot_id)
            if isinstance(forced, Failure):
                return forced

        blocked = await self._load_blocklist()
        coll = self._settings.collection
        nlp = self._settings.analysis.nlp
        started = datetime.now(UTC)
        t0 = time.perf_counter()

        run_draft = AnalysisRun(
            started_at=started,
            label=request.run_label,
            snapshot_id=snapshot_id,
            config_snapshot=settings_to_yaml(self._settings),
            git_commit_hash=git_commit_hash(),
            stats={},
            status=RunStatus.RUNNING,
        )
        created = await self._runs.create(run_draft)
        if isinstance(created, Failure):
            return created
        run = created.unwrap()
        assert run.id is not None
        run_id = run.id

        await self._runs.update_stat(run_id, "collection.seeds_total", len(unique_handles))

        termination_reasons: dict[str, str] = {}
        termination_counts: Counter[str] = Counter()
        skipped_reasons: Counter[str] = Counter()
        profiles_collected = 0
        follows_collected = 0
        seeds_valid = 0

        valid_seeds: list[tuple[Handle, DID, Profile]] = []
        for handle in unique_handles:
            seed_did: DID | None = known_dids.get(handle)
            if seed_did is None:
                resolved = await self._bluesky.resolve_handle(handle)
                if isinstance(resolved, Failure):
                    skipped_reasons["handle_not_found"] += 1
                    append_seed_skipped(
                        handle=handle,
                        did=None,
                        reason="handle_not_found",
                        detail=str(resolved.failure().message),
                    )
                    logger.warning("seed_skipped", handle=str(handle), reason="handle_not_found")
                    if coll.skip_invalid_seeds:
                        continue
                    return Failure(
                        DomainError(
                            code=ErrorCode.EXTERNAL_API,
                            message=f"Could not resolve handle {handle}",
                        )
                    )
                seed_did = resolved.unwrap()

            if await self._is_blocked_did(seed_did, blocked):
                skipped_reasons["blocked"] += 1
                append_seed_skipped(handle=handle, did=seed_did, reason="blocked")
                continue

            profile_result = await self._bluesky.fetch_profile(seed_did)
            if isinstance(profile_result, Failure):
                skipped_reasons["api_error"] += 1
                append_seed_skipped(
                    handle=handle,
                    did=seed_did,
                    reason="api_error",
                    detail=str(profile_result.failure().message),
                )
                if coll.skip_invalid_seeds:
                    continue
                return profile_result
            seed_profile = self._enrich_profile(
                profile_result.unwrap().model_copy(update={"is_seed": True}),
                nlp_threshold=nlp.langdetect_threshold,
            )

            if not self._seed_in_follower_range(seed_profile):
                skipped_reasons["out_of_range"] += 1
                append_seed_skipped(
                    handle=handle,
                    did=seed_did,
                    reason="out_of_range",
                    detail=(
                        f"followers_count={seed_profile.followers_count} "
                        f"range=[{coll.min_followers},{coll.max_followers}]"
                    ),
                )
                if not coll.skip_invalid_seeds:
                    return Failure(
                        DomainError(
                            code=ErrorCode.VALIDATION,
                            message=f"Seed {handle} outside follower range",
                        )
                    )
                continue

            valid_seeds.append((handle, seed_did, seed_profile))

        if not valid_seeds:
            await self._runs.merge_stats_section(
                run_id,
                "collection",
                {
                    "seeds_valid": 0,
                    "seeds_skipped": len(unique_handles),
                    "seeds_skipped_reasons": dict(skipped_reasons),
                },
            )
            await self._runs.finalize_run(run_id, status=RunStatus.FAILED)
            logger.error("collect_aborted", reason="no_valid_seeds", total=len(unique_handles))
            return Failure(
                DomainError(
                    code=ErrorCode.VALIDATION,
                    message="No valid seeds after filtering; collect aborted",
                    details={"abort": "no_valid_seeds"},
                )
            )

        logger.info(
            "seeds_validated",
            valid=len(valid_seeds),
            skipped=len(unique_handles) - len(valid_seeds),
            total=len(unique_handles),
        )

        for _handle, seed_did, seed_profile in valid_seeds:
            stored = await self._profiles.upsert(seed_profile, run_id=run_id)
            if isinstance(stored, Failure):
                return stored
            profiles_collected += 1

            if not isinstance(self._bluesky, AtprotoBlueskyClient):
                return Failure(
                    DomainError(
                        code=ErrorCode.EXTERNAL_API,
                        message="Paginated collect requires AtprotoBlueskyClient",
                    )
                )

            page_result = await self._bluesky.fetch_followers_paginated(
                seed_did,
                snapshot_id=snapshot_id,
                max_followers=coll.max_followers_per_seed,
                max_pages=coll.max_pages_per_seed,
                page_size=coll.followers_page_size,
            )
            if isinstance(page_result, Failure):
                return page_result
            page = page_result.unwrap()
            termination_reasons[seed_did] = page.reason.value
            termination_counts[page.reason.value] += 1

            for prof in page.profiles:
                if prof.did in blocked:
                    continue
                await self._profiles.upsert(
                    self._enrich_profile(prof, nlp_threshold=nlp.langdetect_threshold),
                    run_id=run_id,
                )
                profiles_collected += 1

            to_save = [r for r in page.relations if r.follower_did not in blocked]
            saved = await self._follows.save_relations(to_save)
            if isinstance(saved, Failure):
                return saved
            follows_collected += saved.unwrap()
            seeds_valid += 1

        duration = round(time.perf_counter() - t0, 1)
        seeds_skipped = len(unique_handles) - seeds_valid

        await self._runs.merge_stats_section(
            run_id,
            "collection",
            {
                "seeds_valid": seeds_valid,
                "seeds_skipped": seeds_skipped,
                "seeds_skipped_reasons": dict(skipped_reasons),
                "profiles_collected": profiles_collected,
                "follows_collected": follows_collected,
                "seed_termination_reasons": dict(termination_counts),
                "duration_seconds": duration,
            },
        )
        await self._runs.finalize_run(run_id, status=RunStatus.COMPLETED)

        return Success(
            {
                "run_id": run_id,
                "snapshot_id": str(snapshot_id),
                "seeds_collected": seeds_valid,
                "edges_saved": follows_collected,
                "seed_termination_reasons": termination_reasons,
            }
        )

    async def _load_blocklist(self) -> frozenset[DID]:
        blocklist_result = await self._deletions.load_deleted_set()
        if isinstance(blocklist_result, Failure):
            return frozenset()
        return blocklist_result.unwrap()

    async def _is_blocked_did(self, did: DID, blocked: frozenset[DID]) -> bool:
        if did in blocked:
            return True
        check = await self._deletions.is_deleted(did)
        return not isinstance(check, Failure) and check.unwrap()

    def _enrich_profile(self, profile: Profile, *, nlp_threshold: float) -> Profile:
        lang, conf = detect_profile_language(profile.description, threshold=nlp_threshold)
        return profile.model_copy(
            update={
                "detected_language": lang or profile.detected_language,
                "language_confidence": conf if lang else profile.language_confidence,
            }
        )

    def _seed_in_follower_range(self, profile: Profile) -> bool:
        coll = self._settings.collection
        return coll.min_followers <= profile.followers_count <= coll.max_followers


def _handles_for_collect(request: CollectRequestDTO, seed_file: SeedFile) -> list[Handle]:
    if request.seed_handles:
        handles = list(request.seed_handles)
        if request.topic:
            handles.extend(SeedFileLoader.handles_for_topic(seed_file, request.topic))
        return handles
    if request.topic:
        return SeedFileLoader.handles_for_topic(seed_file, request.topic)
    return SeedFileLoader.all_handles(seed_file)


def _dedupe_handles(handles: list[Handle]) -> list[Handle]:
    seen: set[str] = set()
    out: list[Handle] = []
    for h in handles:
        key = str(h).lower()
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out
