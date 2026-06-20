"""Export ZIP for sharing (DEO 8.6)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from returns.result import Failure, Result, Success

from bluesky_graph_analytics.application.dto import ExportRequestDTO
from bluesky_graph_analytics.application.ports.follow_repository import FollowRepository
from bluesky_graph_analytics.application.ports.profile_repository import ProfileRepository
from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.services.layers._common import results_dir_for
from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.value_objects import SnapshotId
from bluesky_graph_analytics.infrastructure.pseudonymization import Pseudonymizer


class ExportService:
    def __init__(
        self,
        profiles: ProfileRepository,
        follows: FollowRepository,
        runs: RunRepository,
        settings: AppSettings,
    ) -> None:
        self._profiles = profiles
        self._follows = follows
        self._runs = runs
        self._settings = settings

    async def export(self, request: ExportRequestDTO) -> Result[Path, DomainError]:
        snapshot_id = SnapshotId(request.snapshot_id or self._settings.collection.snapshot_id)
        if not request.anonymized:
            return Failure(
                DomainError(
                    code=ErrorCode.VALIDATION,
                    message="MVP export supports --format anonymized only",
                )
            )
        salt = self._settings.pseudonym_salt
        if not salt or len(salt.encode()) < 32:
            return Failure(
                DomainError(
                    code=ErrorCode.VALIDATION,
                    message="PSEUDONYM_SALT required for anonymized export",
                )
            )

        run_result = await self._runs.get_by_snapshot_id(snapshot_id)
        if isinstance(run_result, Failure):
            return run_result
        run = run_result.unwrap()
        if run is None:
            return Failure(
                DomainError(code=ErrorCode.NOT_FOUND, message=f"No run for {snapshot_id}")
            )

        pseudo = Pseudonymizer(
            salt.encode()[:64] if len(salt) < 64 else salt.encode(),
            digest_size=self._settings.ethics.pseudonym_digest_size,
        )
        profiles = (await self._profiles.list_for_snapshot(snapshot_id)).unwrap()
        follows = (await self._follows.list_by_snapshot(snapshot_id)).unwrap()

        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path(DATA_DIR) / "anonymized"
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = (
            Path(request.output)
            if request.output
            else (out_dir / f"bga_export_{snapshot_id}_{ts}.zip")
        )

        results = results_dir_for(snapshot_id)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            file_manifest: list[dict[str, Any]] = []
            prof_rows = [
                pseudo.anonymize_profile(
                    p, exclude_fields=tuple(self._settings.ethics.exclude_fields_on_export)
                )
                for p in profiles
            ]
            follow_rows: list[dict[str, object]] = [
                {
                    "follower_did": pseudo.hash_did(r.follower_did),
                    "followee_did": pseudo.hash_did(r.followee_did),
                    "snapshot_id": str(r.snapshot_id),
                }
                for r in follows
            ]
            _add_parquet(zf, "profiles.parquet", prof_rows, file_manifest)
            _add_parquet(zf, "follows.parquet", follow_rows, file_manifest)

            for member in results.rglob("*"):
                if member.is_file():
                    arcname = member.relative_to(results).as_posix()
                    data = member.read_bytes()
                    zf.writestr(arcname, data)
                    file_manifest.append(
                        {
                            "name": arcname,
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "rows": _row_count_hint(member, data),
                        }
                    )

            fingerprint = hashlib.blake2b(salt.encode(), digest_size=8).hexdigest()[:16]
            communities_count = _communities_count(results / "community_stats.csv")
            manifest = {
                "export_version": "1.0",
                "snapshot_id": str(snapshot_id),
                "exported_at": datetime.now(UTC).isoformat(),
                "run_id": run.id,
                "git_commit_hash": run.git_commit_hash,
                "config_snapshot": run.config_snapshot,
                "pseudonym_salt_fingerprint": fingerprint,
                "stats": {
                    "n_profiles": len(profiles),
                    "n_seeds": len([p for p in profiles if p.is_seed]),
                    "n_follows": len(follows),
                    "n_communities": communities_count,
                },
                "files": file_manifest,
            }
            manifest_data = json.dumps(manifest, indent=2).encode()
            zf.writestr("manifest.json", manifest_data)
            file_manifest.append(
                {
                    "name": "manifest.json",
                    "sha256": hashlib.sha256(manifest_data).hexdigest(),
                    "rows": None,
                }
            )
            readme_data = (
                "README.txt",
                "Bluesky Graph Analytics anonymized export. Cite snapshot_id and git_commit_hash.",
            )[1].encode()
            zf.writestr("README.txt", readme_data)
            file_manifest.append(
                {
                    "name": "README.txt",
                    "sha256": hashlib.sha256(readme_data).hexdigest(),
                    "rows": None,
                }
            )

        return Success(zip_path)


def _add_parquet(
    zf: zipfile.ZipFile,
    name: str,
    rows: list[dict[str, object]],
    file_manifest: list[dict[str, Any]],
) -> None:
    import io

    buf = io.BytesIO()
    pd.DataFrame(rows).to_parquet(buf, index=False)
    data = buf.getvalue()
    zf.writestr(name, data)
    file_manifest.append(
        {
            "name": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "rows": len(rows),
        }
    )


def _row_count_hint(path: Path, data: bytes) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        text = data.decode("utf-8", errors="ignore")
        return max(0, len([line for line in text.splitlines() if line.strip()]) - 1)
    if suffix == ".json":
        try:
            loaded = json.loads(data.decode("utf-8"))
            return len(loaded) if isinstance(loaded, (list, dict)) else None
        except Exception:  # noqa: BLE001
            return None
    return None


def _communities_count(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        df = pd.read_csv(path)
        return int(len(df))
    except Exception:  # noqa: BLE001
        return 0
