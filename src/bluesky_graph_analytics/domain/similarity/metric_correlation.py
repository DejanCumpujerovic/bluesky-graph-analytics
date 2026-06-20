"""Cross-metric correlation (DEO 8.1)."""

from dataclasses import dataclass

import pandas as pd
from scipy.stats import kendalltau, spearmanr


@dataclass(frozen=True, slots=True)
class MetricCorrelationRow:
    metric_a: str
    metric_b: str
    spearman: float
    kendall: float
    rbo_at_50: float


def _rbo_at_k(list_a: list[str], list_b: list[str], k: int = 50) -> float:
    """Rank-biased overlap for two ranked ID lists (top-k)."""
    if not list_a and not list_b:
        return 1.0
    if not list_a or not list_b:
        return 0.0
    a = list_a[:k]
    b = list_b[:k]
    depth = min(len(a), len(b), k)
    if depth == 0:
        return 0.0
    overlap = 0.0
    for d in range(1, depth + 1):
        sa = set(a[:d])
        sb = set(b[:d])
        overlap += len(sa & sb) / d / depth
    return overlap


def compute_metric_correlations(
    scores: list[tuple[str, str, str, float]],
    *,
    rbo_k: int = 50,
) -> list[MetricCorrelationRow]:
    """scores: (node_u, node_v, metric_name, value)."""
    if not scores:
        return []
    df = pd.DataFrame(scores, columns=["node_u", "node_v", "metric", "value"])
    df = df.drop_duplicates(subset=["node_u", "node_v", "metric"], keep="first")
    pivot = df.pivot(index=["node_u", "node_v"], columns="metric", values="value")
    pivot.columns = [str(c) for c in pivot.columns]
    metrics = list(pivot.columns)
    rows: list[MetricCorrelationRow] = []
    for i, ma in enumerate(metrics):
        for mb in metrics[i:]:
            joined = pd.DataFrame({"a": pivot[ma], "b": pivot[mb]}).dropna()
            if len(joined) < 2:
                sp = kd = rbo = 0.0
            else:
                sp = float(spearmanr(joined["a"], joined["b"]).statistic or 0.0)
                kd = float(kendalltau(joined["a"], joined["b"]).statistic or 0.0)
                flat = joined.reset_index()
                flat["pair"] = flat["node_u"].astype(str) + "|" + flat["node_v"].astype(str)
                rank_a = flat.sort_values("a", ascending=False)["pair"].tolist()
                rank_b = flat.sort_values("b", ascending=False)["pair"].tolist()
                rbo = _rbo_at_k(rank_a, rank_b, k=rbo_k)
            rows.append(
                MetricCorrelationRow(
                    metric_a=ma,
                    metric_b=mb,
                    spearman=sp,
                    kendall=kd,
                    rbo_at_50=rbo,
                )
            )
    return rows
