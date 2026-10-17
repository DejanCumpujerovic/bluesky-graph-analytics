"""Similarity layer dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.data_access import list_snapshots
from bluesky_graph_analytics.interfaces.streamlit.i18n import t, translate_columns


def metric_label(metric: str) -> str:
    return t(f"metrics.{metric}.name", default=metric)


st.header(t("nav.similarity"))
st.markdown(t("similarity.intro"))
runs = list_snapshots()
if not runs:
    st.warning(t("common.no_runs"))
    st.stop()
snap = st.selectbox(
    t("common.snapshot"), [r["snapshot_id"] for r in runs], help=t("common.snapshot_help")
)
snap_dir = Path(DATA_DIR) / "results" / snap
if not snap_dir.is_dir():
    st.warning(t("common.no_results", snapshot=snap))
    st.stop()

metric = st.selectbox(
    t("similarity.metric"),
    ["jaccard", "adamic_adar", "overlap"],
    format_func=metric_label,
    help=t("similarity.metric_help"),
)
st.caption(t(f"metrics.{metric}.description"))
parquet_path = snap_dir / f"similarity_{metric}.parquet"
if parquet_path.is_file():
    df = pd.read_parquet(parquet_path)
    if df.empty or "value" not in df.columns:
        st.info(t("similarity.empty"))
    else:
        value_col = t("columns.value")
        st.subheader(t("similarity.distribution_title"))
        st.caption(t("similarity.distribution_caption"))
        pair_col = t("similarity.distribution_x")
        dist = pd.DataFrame({pair_col: range(len(df)), value_col: df["value"].to_numpy()})
        st.bar_chart(dist, x=pair_col, y=value_col)

        st.subheader(t("similarity.scatter_title"))
        st.caption(t("similarity.scatter_caption"))
        st.scatter_chart(translate_columns(df), x=t("columns.overlap_size"), y=value_col)
else:
    st.info(t("common.missing_file", name=parquet_path.name))

corr_path = snap_dir / "metric_correlation.csv"
if corr_path.is_file():
    corr = pd.read_csv(corr_path)
    st.subheader(t("similarity.correlation_title"))
    st.caption(t("similarity.correlation_caption"))
    if not corr.empty and {"metric_a", "metric_b", "spearman"}.issubset(corr.columns):
        pivot = corr.pivot(index="metric_a", columns="metric_b", values="spearman")
        pivot = pivot.rename(index=metric_label, columns=metric_label)
        pivot.index.name = t("columns.metric_a")
        pivot.columns.name = t("columns.metric_b")
        st.dataframe(pivot.style.background_gradient(cmap="viridis", axis=None))
    elif not corr.empty:
        st.dataframe(translate_columns(corr))
    else:
        st.info(t("similarity.correlation_empty"))

top_path = snap_dir / "top_pairs.csv"
if top_path.is_file():
    top = pd.read_csv(top_path)
    if not top.empty:
        st.subheader(t("similarity.top_title"))
        st.caption(t("similarity.top_caption"))
        if "metric_name" in top.columns:
            top["metric_name"] = top["metric_name"].map(metric_label)
        page_size = 50
        page = st.number_input(t("common.page"), min_value=1, value=1, step=1)
        start = (page - 1) * page_size
        st.dataframe(translate_columns(top.iloc[start : start + page_size]))
    else:
        st.info(t("similarity.top_empty"))
