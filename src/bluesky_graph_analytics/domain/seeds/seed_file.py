"""Seed file models and validation (DEO 6.2)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from bluesky_graph_analytics.constants import SEED_FILE_MAX_COUNT, SEED_FILE_MIN_COUNT
from bluesky_graph_analytics.domain.value_objects import DID, Handle


class SeedFileValidationError(ValueError):
    """Invalid seed_profiles.yaml — map to DomainError in application layer."""


class SeedEntry(BaseModel):
    handle: Handle
    topic: str = Field(min_length=1)
    did: DID | None = None
    notes: str | None = None
    added_by: str | None = None
    added_at: date | None = None


class SeedFile(BaseModel):
    seeds: list[SeedEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_duplicates(self) -> SeedFile:
        handles: set[str] = set()
        dids: set[str] = set()
        for entry in self.seeds:
            h = str(entry.handle).lower()
            if h in handles:
                msg = f"Duplicate handle in seed file: {entry.handle}"
                raise ValueError(msg)
            handles.add(h)
            if entry.did is not None:
                d = str(entry.did)
                if d in dids:
                    msg = f"Duplicate DID in seed file: {entry.did}"
                    raise ValueError(msg)
                dids.add(d)
        return self


class SeedFileLoader:
    """Validates seed_profiles.yaml; stops collection before API on failure."""

    def __init__(self, *, enforce_mvp_bounds: bool = True) -> None:
        self._enforce_mvp_bounds = enforce_mvp_bounds

    def load(self, path: Path) -> SeedFile:
        if not path.is_file():
            msg = f"Seed file not found: {path}"
            raise SeedFileValidationError(msg)

        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        if not isinstance(raw, dict):
            msg = "Seed file must be a YAML mapping with a 'seeds' list"
            raise SeedFileValidationError(msg)

        try:
            seed_file = SeedFile.model_validate(raw)
        except ValueError as exc:
            raise SeedFileValidationError(str(exc)) from exc

        count = len(seed_file.seeds)
        if self._enforce_mvp_bounds:
            if count < SEED_FILE_MIN_COUNT:
                msg = (
                    f"Seed file has {count} entries; MVP requires "
                    f"{SEED_FILE_MIN_COUNT}–{SEED_FILE_MAX_COUNT}"
                )
                raise SeedFileValidationError(msg)
            if count > SEED_FILE_MAX_COUNT:
                msg = f"Seed file has {count} entries; maximum is {SEED_FILE_MAX_COUNT}"
                raise SeedFileValidationError(msg)

        return seed_file

    @staticmethod
    def handles_for_topic(seed_file: SeedFile, topic: str) -> list[Handle]:
        return [entry.handle for entry in seed_file.seeds if entry.topic == topic]

    @staticmethod
    def all_handles(seed_file: SeedFile) -> list[Handle]:
        return [entry.handle for entry in seed_file.seeds]

    @staticmethod
    def known_dids(seed_file: SeedFile) -> dict[Handle, DID]:
        return {entry.handle: entry.did for entry in seed_file.seeds if entry.did is not None}
