"""Compare two snapshots that share the same seed profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SeedChange:
    did: str
    handle: str
    followers_before: int
    followers_after: int
    collected_before: int
    collected_after: int
    retained: int
    lost: int
    new: int

    @property
    def followers_delta(self) -> int:
        return self.followers_after - self.followers_before

    @property
    def retained_share(self) -> float:
        return self.retained / self.collected_before if self.collected_before else 0.0


def is_sampled(run: dict[str, Any]) -> bool:
    reasons = run.get("stats", {}).get("collection", {}).get("seed_termination_reasons", {})
    return "max_followers_reached" in reasons


def compare_seeds(
    seeds_before: list[dict[str, Any]],
    seeds_after: list[dict[str, Any]],
    followers_before: dict[str, set[str]],
    followers_after: dict[str, set[str]],
) -> list[SeedChange]:
    after_by_did = {s["did"]: s for s in seeds_after}
    changes: list[SeedChange] = []
    for seed in seeds_before:
        did = seed["did"]
        if did not in after_by_did:
            continue
        before = followers_before.get(did, set())
        after = followers_after.get(did, set())
        changes.append(
            SeedChange(
                did=did,
                handle=seed["handle"] or did,
                followers_before=seed["followers_count"],
                followers_after=after_by_did[did]["followers_count"],
                collected_before=len(before),
                collected_after=len(after),
                retained=len(before & after),
                lost=len(before - after),
                new=len(after - before),
            )
        )
    return sorted(changes, key=lambda c: c.handle)
