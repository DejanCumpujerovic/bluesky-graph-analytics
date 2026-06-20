"""Train/test split strategies (random MVP, temporal in Faza 2)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from random import Random

from bluesky_graph_analytics.domain.value_objects import DID


@dataclass(frozen=True, slots=True)
class EdgeSplitResult:
    train_edges: list[tuple[DID, DID]]
    test_edges: list[tuple[DID, DID]]
    warning: str | None = None


class SplitStrategy(ABC):
    @abstractmethod
    def split(
        self,
        edges: list[tuple[DID, DID]],
        *,
        test_fraction: float,
        random_seed: int,
    ) -> EdgeSplitResult:
        """Split directed edges into train and test sets."""


class RandomStratifiedSplit(SplitStrategy):
    """Random split stratified by target node (seed) — §5.10, §5.13."""

    def split(
        self,
        edges: list[tuple[DID, DID]],
        *,
        test_fraction: float,
        random_seed: int,
    ) -> EdgeSplitResult:
        rng = Random(random_seed)
        by_seed: dict[DID, list[tuple[DID, DID]]] = {}
        for edge in edges:
            _follower, seed = edge
            by_seed.setdefault(seed, []).append(edge)

        train: list[tuple[DID, DID]] = []
        test: list[tuple[DID, DID]] = []
        for seed_edges in by_seed.values():
            shuffled = list(seed_edges)
            rng.shuffle(shuffled)
            n_test = max(1, int(len(shuffled) * test_fraction)) if len(shuffled) > 1 else 0
            if len(shuffled) == 1:
                n_test = 0
            test.extend(shuffled[:n_test])
            train.extend(shuffled[n_test:])

        warning = (
            "Random 90/10 split (stratified by seed): AUC may be inflated 5–15% vs temporal split. "
            "Temporal split planned for Phase 2."
        )
        return EdgeSplitResult(train_edges=train, test_edges=test, warning=warning)
