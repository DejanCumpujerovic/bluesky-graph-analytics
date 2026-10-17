"""Compare two snapshots (DEO 8.5)."""

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.config import load_settings
from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.comparison import compare_seeds, is_sampled
from bluesky_graph_analytics.interfaces.streamlit.data_access import (
    followers_by_seed,
    list_snapshots,
    seed_profiles,
)
from bluesky_graph_analytics.interfaces.streamlit.i18n import t


def run_label(run: dict[str, Any]) -> str:
    return f"{run['snapshot_id']} ({str(run['started_at'])[:10]})"


def auc_by_method(snapshot_id: str) -> dict[str, float]:
    path = Path(DATA_DIR) / "results" / snapshot_id / "prediction_results.csv"
    if not path.is_file():
        return {}
    df = pd.read_csv(path)
    if df.empty or not {"method", "auc"}.issubset(df.columns):
        return {}
    return {str(k): float(v) for k, v in df.groupby("method", sort=False)["auc"].first().items()}


def fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


st.header(t("nav.comparison"))
st.markdown(t("comparison.intro"))

runs = [r for r in list_snapshots() if r["status"] == "completed"]
if len(runs) < 2:
    st.info(t("comparison.need_two"))
    st.stop()

by_id = {r["snapshot_id"]: r for r in runs}
ids = list(by_id)
col_before, col_after = st.columns(2)
before_id = col_before.selectbox(
    t("comparison.before"),
    ids,
    index=1,
    format_func=lambda s: run_label(by_id[s]),
    help=t("comparison.before_help"),
)
after_id = col_after.selectbox(
    t("comparison.after"),
    ids,
    index=0,
    format_func=lambda s: run_label(by_id[s]),
    help=t("comparison.after_help"),
)
if before_id == after_id:
    st.info(t("comparison.same"))
    st.stop()
before, after = by_id[before_id], by_id[after_id]
if str(before["started_at"]) > str(after["started_at"]):
    st.warning(t("comparison.order_warning"))

sampled_before, sampled_after = is_sampled(before), is_sampled(after)
if sampled_before or sampled_after:
    sampled = ", ".join(r["snapshot_id"] for r in (before, after) if is_sampled(r))
    st.warning(t("comparison.sampled_warning", snapshots=sampled))

changes = compare_seeds(
    seed_profiles(before_id),
    seed_profiles(after_id),
    followers_by_seed(before_id),
    followers_by_seed(after_id),
)
if not changes:
    st.info(t("comparison.no_common_seeds"))
    st.stop()

seed_col = t("comparison.col_seed")

st.subheader(t("comparison.growth_title"))
st.caption(t("comparison.growth_caption"))
growth = pd.DataFrame(
    {
        seed_col: [c.handle for c in changes],
        t("comparison.col_followers_before"): [c.followers_before for c in changes],
        t("comparison.col_followers_after"): [c.followers_after for c in changes],
        t("comparison.col_followers_delta"): [f"{c.followers_delta:+d}" for c in changes],
    }
)
st.dataframe(growth, hide_index=True)

st.subheader(t("comparison.churn_title"))
st.caption(t("comparison.churn_caption"))
if sampled_after:
    st.info(t("comparison.churn_unavailable"))
else:
    churn: dict[str, list[Any]] = {
        seed_col: [c.handle for c in changes],
        t("comparison.col_collected_before"): [c.collected_before for c in changes],
        t("comparison.col_retained"): [c.retained for c in changes],
        t("comparison.col_lost"): [c.lost for c in changes],
        t("comparison.col_retained_share"): [f"{c.retained_share:.1%}" for c in changes],
    }
    if not sampled_before:
        churn[t("comparison.col_new")] = [c.new for c in changes]
    st.dataframe(pd.DataFrame(churn), hide_index=True)
    if sampled_before:
        st.caption(t("comparison.new_unavailable"))

st.subheader(t("comparison.summary_title"))
st.caption(t("comparison.summary_caption"))
rows: list[tuple[str, Any, Any]] = []
stat_rows = [
    ("collection", "profiles_collected", "comparison.row_profiles"),
    ("collection", "follows_collected", "comparison.row_edges"),
    ("similarity", "pairs_computed", "comparison.row_similarity_pairs"),
    ("community", "num_communities", "comparison.row_communities"),
    ("community", "modularity", "comparison.row_modularity"),
]
for section, key, label in stat_rows:
    rows.append(
        (
            t(label),
            before["stats"].get(section, {}).get(key),
            after["stats"].get(section, {}).get(key),
        )
    )
auc_before, auc_after = auc_by_method(before_id), auc_by_method(after_id)
for method in dict.fromkeys([*auc_before, *auc_after]):
    rows.append(
        (
            t("comparison.row_auc", method=t(f"methods.{method}", default=method)),
            auc_before.get(method),
            auc_after.get(method),
        )
    )
summary = pd.DataFrame(
    {
        t("comparison.col_indicator"): [r[0] for r in rows],
        before_id: [fmt(r[1]) for r in rows],
        after_id: [fmt(r[2]) for r in rows],
    }
)
st.dataframe(summary, hide_index=True)

if any(r["stats"].get("community", {}).get("num_communities") == 0 for r in (before, after)):
    modularity_min = load_settings().analysis.community.modularity_min
    st.caption(t("comparison.no_communities_note", min=modularity_min))
