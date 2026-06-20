"""Ranking metrics for link prediction (§5.13)."""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


@dataclass(frozen=True, slots=True)
class PredictionMetricsRow:
    method: str
    auc: float
    precision_at_k: float
    recall_at_k: float
    k: int
    map_score: float


def _precision_recall_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int) -> tuple[float, float]:
    if len(y_true) == 0:
        return 0.0, 0.0
    order = np.argsort(-y_score)
    top = order[:k]
    hits = y_true[top].sum()
    precision = hits / k if k > 0 else 0.0
    recall = hits / y_true.sum() if y_true.sum() > 0 else 0.0
    return float(precision), float(recall)


def evaluate_scores(
    y_true: list[int],
    y_score: list[float],
    *,
    method: str,
    k_values: list[int],
) -> list[PredictionMetricsRow]:
    labels = np.array(y_true, dtype=np.int32)
    scores = np.array(y_score, dtype=np.float64)
    if len(np.unique(labels)) < 2:
        auc = 0.0
        map_score = 0.0
    else:
        auc = float(roc_auc_score(labels, scores))
        map_score = float(average_precision_score(labels, scores))

    rows: list[PredictionMetricsRow] = []
    for k in k_values:
        p, r = _precision_recall_at_k(labels, scores, k)
        rows.append(
            PredictionMetricsRow(
                method=method,
                auc=auc,
                precision_at_k=p,
                recall_at_k=r,
                k=k,
                map_score=map_score,
            )
        )
    return rows
