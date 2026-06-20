"""SQLAlchemy repository implementations (DEO 7)."""

from datetime import UTC, datetime
from typing import Any

from returns.result import Failure, Result, Success
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bluesky_graph_analytics.application.ports.deletion_repository import DeletionRepository
from bluesky_graph_analytics.application.ports.follow_repository import FollowRepository
from bluesky_graph_analytics.application.ports.profile_repository import ProfileRepository
from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.records import AnalysisRun, DeletionRecord, RunStatus
from bluesky_graph_analytics.application.run_stats import merge_section, merge_stat
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.mappers import (
    follow_to_domain,
    follow_to_row,
    profile_to_domain,
    profile_to_row,
)
from bluesky_graph_analytics.infrastructure.persistence.models import (
    DeletionRow,
    FollowRow,
    ProfileRow,
    RunRow,
)


def _row_to_run(row: RunRow) -> AnalysisRun:
    return AnalysisRun(
        id=row.id,
        label=row.label,
        snapshot_id=SnapshotId(row.snapshot_id),
        started_at=row.started_at,
        finished_at=row.finished_at,
        config_snapshot=row.config_snapshot,
        git_commit_hash=row.git_commit_hash,
        stats=row.stats or {},
        status=RunStatus(row.status),
    )


class SqlAlchemyProfileRepository(ProfileRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert(self, profile: Profile, *, run_id: int) -> Result[None, DomainError]:
        try:
            now = datetime.now(UTC)
            async with self._session_factory() as session:
                existing = await session.get(ProfileRow, (profile.did, run_id))
                row = profile_to_row(profile, run_id=run_id, now=now)
                if existing is not None:
                    row.created_at = existing.created_at
                await session.merge(row)
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def get(self, did: DID, *, run_id: int) -> Result[Profile | None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(ProfileRow, (did, run_id))
            if row is None:
                return Success(None)
            return Success(profile_to_domain(row))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def delete(self, did: DID) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                await session.execute(delete(ProfileRow).where(ProfileRow.did == did))
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def list_for_snapshot(
        self, snapshot_id: SnapshotId
    ) -> Result[list[Profile], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = (
                    select(ProfileRow)
                    .join(RunRow, ProfileRow.run_id == RunRow.id)
                    .where(RunRow.snapshot_id == snapshot_id)
                )
                rows = (await session.scalars(stmt)).all()
            return Success([profile_to_domain(r) for r in rows])
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def list_seeds(self, snapshot_id: SnapshotId) -> Result[list[Profile], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = (
                    select(ProfileRow)
                    .join(RunRow, ProfileRow.run_id == RunRow.id)
                    .join(
                        FollowRow,
                        (ProfileRow.did == FollowRow.followee_did)
                        & (FollowRow.snapshot_id == snapshot_id),
                    )
                    .where(
                        RunRow.snapshot_id == snapshot_id,
                        ProfileRow.is_seed.is_(True),
                    )
                    .distinct()
                )
                rows = (await session.scalars(stmt)).all()
            return Success([profile_to_domain(r) for r in rows])
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))


class SqlAlchemyFollowRepository(FollowRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_relations(self, relations: list[FollowRelation]) -> Result[int, DomainError]:
        try:
            fetched_at = datetime.now(UTC)
            async with self._session_factory() as session:
                for relation in relations:
                    await session.merge(follow_to_row(relation, fetched_at=fetched_at))
                await session.commit()
            return Success(len(relations))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def list_by_snapshot(
        self, snapshot_id: SnapshotId
    ) -> Result[list[FollowRelation], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = select(FollowRow).where(FollowRow.snapshot_id == snapshot_id)
                rows = (await session.scalars(stmt)).all()
            return Success([follow_to_domain(r) for r in rows])
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def list_for_seed(self, seed_did: DID) -> Result[list[FollowRelation], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = select(FollowRow).where(FollowRow.followee_did == seed_did)
                rows = (await session.scalars(stmt)).all()
            return Success([follow_to_domain(r) for r in rows])
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def delete_involving(self, did: DID) -> Result[int, DomainError]:
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    delete(FollowRow).where(
                        (FollowRow.follower_did == did) | (FollowRow.followee_did == did)
                    )
                )
                await session.commit()
            deleted = getattr(result, "rowcount", 0) or 0
            return Success(int(deleted))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def delete_by_snapshot(self, snapshot_id: SnapshotId) -> Result[int, DomainError]:
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    delete(FollowRow).where(FollowRow.snapshot_id == snapshot_id)
                )
                await session.commit()
            return Success(int(getattr(result, "rowcount", 0) or 0))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))


class SqlAlchemyRunRepository(RunRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, run: AnalysisRun) -> Result[AnalysisRun, DomainError]:
        try:
            async with self._session_factory() as session:
                row = RunRow(
                    snapshot_id=str(run.snapshot_id),
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    config_snapshot=run.config_snapshot,
                    git_commit_hash=run.git_commit_hash,
                    stats=run.stats,
                    status=run.status.value,
                    label=run.label,
                )
                session.add(row)
                await session.commit()
                await session.refresh(row)
            return Success(_row_to_run(row))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def get(self, run_id: int) -> Result[AnalysisRun | None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(RunRow, run_id)
            if row is None:
                return Success(None)
            return Success(_row_to_run(row))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def get_by_snapshot_id(
        self, snapshot_id: SnapshotId
    ) -> Result[AnalysisRun | None, DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = select(RunRow).where(RunRow.snapshot_id == snapshot_id)
                row = await session.scalar(stmt)
            if row is None:
                return Success(None)
            return Success(_row_to_run(row))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def update_stat(self, run_id: int, key: str, value: Any) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(RunRow, run_id)
                if row is None:
                    return Failure(
                        DomainError(code=ErrorCode.NOT_FOUND, message=f"run {run_id} not found")
                    )
                row.stats = merge_stat(row.stats or {}, key, value)
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def merge_stats_section(
        self, run_id: int, section: str, patch: dict[str, Any]
    ) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(RunRow, run_id)
                if row is None:
                    return Failure(
                        DomainError(code=ErrorCode.NOT_FOUND, message=f"run {run_id} not found")
                    )
                row.stats = merge_section(row.stats or {}, section, patch)
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def finalize_run(
        self, run_id: int, *, status: RunStatus = RunStatus.COMPLETED
    ) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(RunRow, run_id)
                if row is None:
                    return Failure(
                        DomainError(code=ErrorCode.NOT_FOUND, message=f"run {run_id} not found")
                    )
                row.finished_at = datetime.now(UTC)
                row.status = status.value
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def force_resnapshot(self, snapshot_id: SnapshotId) -> Result[None, DomainError]:
        snap = str(snapshot_id)
        try:
            async with self._session_factory() as session, session.begin():
                run_row = await session.scalar(select(RunRow).where(RunRow.snapshot_id == snap))
                if run_row is None:
                    return Success(None)

                run_ids_stmt = select(RunRow.id).where(RunRow.snapshot_id == snap)
                await session.execute(delete(FollowRow).where(FollowRow.snapshot_id == snap))
                await session.execute(delete(ProfileRow).where(ProfileRow.run_id.in_(run_ids_stmt)))
                archived = f"{snap}#archived-{run_row.id}"
                await session.execute(
                    update(RunRow)
                    .where(RunRow.id == run_row.id)
                    .values(
                        status=RunStatus.FORCE_RESNAPSHOT.value,
                        snapshot_id=archived,
                    )
                )
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))


class SqlAlchemyDeletionRepository(DeletionRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(self, entry: DeletionRecord) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                session.add(
                    DeletionRow(
                        did=str(entry.subject_did),
                        requested_at=entry.requested_at,
                        reason=entry.reason,
                        processed=entry.processed,
                        processed_at=entry.processed_at,
                    )
                )
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def list_pending(self) -> Result[list[DeletionRecord], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = select(DeletionRow).where(DeletionRow.processed.is_(False))
                rows = (await session.scalars(stmt)).all()
            return Success(
                [
                    DeletionRecord(
                        subject_did=r.did,
                        requested_at=r.requested_at,
                        reason=r.reason,
                        processed=r.processed,
                        processed_at=r.processed_at,
                    )
                    for r in rows
                ]
            )
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def is_deleted(self, did: DID) -> Result[bool, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(DeletionRow, did)
            return Success(row is not None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def load_deleted_set(self) -> Result[frozenset[DID], DomainError]:
        try:
            async with self._session_factory() as session:
                stmt = select(DeletionRow.did)
                rows = (await session.scalars(stmt)).all()
            return Success(frozenset(DID(d) for d in rows))
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))

    async def mark_processed(self, did: DID) -> Result[None, DomainError]:
        try:
            async with self._session_factory() as session:
                row = await session.get(DeletionRow, did)
                if row is None:
                    return Failure(
                        DomainError(code=ErrorCode.NOT_FOUND, message=f"deletion {did} not found")
                    )
                row.processed = True
                row.processed_at = datetime.now(UTC)
                await session.commit()
            return Success(None)
        except Exception as exc:  # noqa: BLE001
            return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))
