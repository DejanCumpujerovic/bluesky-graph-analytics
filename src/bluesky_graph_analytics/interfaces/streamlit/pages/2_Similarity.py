"""Similarity layer dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.data_access import list_snapshots

st.header("Similarity")
runs = list_snapshots()
if not runs:
    st.warning("No runs in database.")
    st.stop()
snap = st.selectbox("Snapshot", [r["snapshot_id"] for r in runs])
snap_dir = Path(DATA_DIR) / "results" / snap
if not snap_dir.is_dir():
    st.warning("No analysis results for this snapshot.")
    st.stop()

metric = st.selectbox("Metric", ["jaccard", "adamic_adar", "overlap"])
parquet_path = snap_dir / f"similarity_{metric}.parquet"
if parquet_path.is_file():
    df = pd.read_parquet(parquet_path)
    if df.empty or "value" not in df.columns:
        st.info("No similarity pairs for this snapshot (graph too small or empty).")
    else:
        st.subheader("Distribution")
        st.bar_chart(df["value"])
        st.subheader("Overlap vs similarity")
        st.scatter_chart(df, x="overlap_size", y="value")
else:
    st.info(f"Missing {parquet_path.name}")

corr_path = snap_dir / "metric_correlation.csv"
if corr_path.is_file():
    corr = pd.read_csv(corr_path)
    if not corr.empty and {"metric_a", "metric_b", "spearman"}.issubset(corr.columns):
        st.subheader("Metric correlation heatmap (Spearman)")
        pivot = corr.pivot(index="metric_a", columns="metric_b", values="spearman")
        st.dataframe(pivot.style.background_gradient(cmap="viridis", axis=None))
    elif not corr.empty:
        st.subheader("Metric correlation heatmap (Spearman)")
        st.dataframe(corr)
    else:
        st.info("No metric correlations (not enough pairs).")

top_path = snap_dir / "top_pairs.csv"
if top_path.is_file():
    top = pd.read_csv(top_path)
    if not top.empty:
        st.subheader("Top pairs (pseudonymized)")
        page_size = 50
        page = st.number_input("Page", min_value=1, value=1, step=1)
        start = (page - 1) * page_size
        st.dataframe(top.iloc[start : start + page_size])
    else:
        st.info("No top pairs (not enough similarity scores).")
