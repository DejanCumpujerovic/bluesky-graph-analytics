"""Link prediction pipeline — split, negatives, heuristics, Node2Vec+LR (§5.13)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import networkx as nx
import numpy as np
from sklearn.linear_model import LogisticRegression

from bluesky_graph_analytics.domain.prediction.directed_heuristics import DIRECTED_HEURISTICS
from bluesky_graph_analytics.domain.prediction.evaluation import (
    PredictionMetricsRow,
    evaluate_scores,
)
from bluesky_graph_analytics.domain.prediction.negative_sampling import (
    common_neighbor_filtered_negatives,
)
from bluesky_graph_analytics.domain.prediction.split_strategy import RandomStratifiedSplit
from bluesky_graph_analytics.domain.value_objects import DID


@dataclass(frozen=True, slots=True)
class PredictionPipelineResult:
    metrics: list[PredictionMetricsRow]
    split_warning: str | None
    roc_curves: dict[str, tuple[list[int], list[float]]]
    top_predicted_links: list[tuple[DID, DID, float]]


def _labels_and_scores(
    pairs: list[tuple[DID, DID]],
    labels: list[int],
    scorer: Callable[[nx.DiGraph, DID, DID], float],
    train_graph: nx.DiGraph,
) -> tuple[list[int], list[float]]:
    y_true: list[int] = []
    y_score: list[float] = []
    for (u, v), label in zip(pairs, labels, strict=True):
        y_true.append(label)
        y_score.append(float(scorer(train_graph, u, v)))
    return y_true, y_score


def _hadamard_features(
    graph: nx.DiGraph,
    model: Any,
    pairs: list[tuple[DID, DID]],
) -> np.ndarray:
    feats: list[list[float]] = []
    for u, v in pairs:
        if u not in model.wv or v not in model.wv:
            feats.append([0.0] * int(model.vector_size))
        else:
            feats.append((model.wv[u] * model.wv[v]).tolist())
    return np.array(feats, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class Node2VecParams:
    dimensions: int = 64
    walk_length: int = 80
    num_walks: int = 10
    p: float = 1.0
    q: float = 1.0
    workers: int = 1


def run_prediction_pipeline(
    train_graph: nx.DiGraph,
    all_edges: list[tuple[DID, DID]],
    seeds: set[DID],
    *,
    test_fraction: float = 0.1,
    random_seed: int = 42,
    k_values: list[int] | None = None,
    negative_ratio: float = 1.0,
    node2vec: Node2VecParams | None = None,
) -> PredictionPipelineResult:
    k_values = k_values or [10, 50, 100]
    n2v = node2vec or Node2VecParams()
    split = RandomStratifiedSplit().split(
        all_edges, test_fraction=test_fraction, random_seed=random_seed
    )

    train_g = nx.DiGraph()
    train_g.add_edges_from(split.train_edges)

    test_pos = split.test_edges
    test_neg = common_neighbor_filtered_negatives(
        train_g,
        seeds,
        test_pos,
        ratio=negative_ratio,
        random_seed=random_seed,
    )
    test_pairs = test_pos + test_neg
    test_labels = [1] * len(test_pos) + [0] * len(test_neg)

    all_metrics: list[PredictionMetricsRow] = []
    roc_curves: dict[str, tuple[list[int], list[float]]] = {}
    ranking_scores: dict[tuple[DID, DID], list[float]] = {}

    for name, fn in DIRECTED_HEURISTICS.items():
        scorer = cast(Callable[[nx.DiGraph, DID, DID], float], fn)
        y_true, y_score = _labels_and_scores(test_pairs, test_labels, scorer, train_g)
        roc_curves[name] = (list(y_true), list(y_score))
        for (u, v), score, label in zip(test_pairs, y_score, test_labels, strict=True):
            if label == 0:
                ranking_scores.setdefault((u, v), []).append(float(score))
        all_metrics.extend(evaluate_scores(y_true, y_score, method=name, k_values=k_values))

    # Node2Vec + LogisticRegression
    if train_g.number_of_edges() > 0:
        from node2vec import Node2Vec

        walker = Node2Vec(
            train_g,
            dimensions=n2v.dimensions,
            walk_length=n2v.walk_length,
            num_walks=n2v.num_walks,
            p=n2v.p,
            q=n2v.q,
            workers=n2v.workers,
        )
        n2v_model = walker.fit(window=5, min_count=1, batch_words=4)

        train_pos = split.train_edges
        train_neg = common_neighbor_filtered_negatives(
            train_g, seeds, train_pos, ratio=negative_ratio, random_seed=random_seed
        )
        train_pairs = train_pos + train_neg
        train_labels = [1] * len(train_pos) + [0] * len(train_neg)
        x_train = _hadamard_features(train_g, n2v_model, train_pairs)
        clf = LogisticRegression(max_iter=1000, random_state=random_seed)
        clf.fit(x_train, np.array(train_labels))

        x_test = _hadamard_features(train_g, n2v_model, test_pairs)
        probas = clf.predict_proba(x_test)[:, 1].tolist()
        roc_curves["node2vec_logreg"] = (list(test_labels), list(probas))
        for (u, v), score, label in zip(test_pairs, probas, test_labels, strict=True):
            if label == 0:
                ranking_scores.setdefault((u, v), []).append(float(score))
        all_metrics.extend(
            evaluate_scores(test_labels, probas, method="node2vec_logreg", k_values=k_values)
        )

    ranked = sorted(
        ((u, v, float(np.mean(scores))) for (u, v), scores in ranking_scores.items() if scores),
        key=lambda item: -item[2],
    )
    return PredictionPipelineResult(
        metrics=all_metrics,
        split_warning=split.warning,
        roc_curves=roc_curves,
        top_predicted_links=ranked,
    )
