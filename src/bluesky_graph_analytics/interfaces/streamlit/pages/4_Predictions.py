"""Link prediction dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR

st.header("Predictions")
st.warning(
    "RANDOM split — AUC may be inflated 5–15% compared to a temporal split (see METHODOLOGY.md)."
)

root = Path(DATA_DIR) / "results"
if not root.exists():
    st.warning("No results yet.")
    st.stop()

snapshots = sorted(p.name for p in root.iterdir() if p.is_dir())
snap = st.selectbox("Snapshot", snapshots) if snapshots else None
if not snap:
    st.stop()

snap_dir = root / snap
results_path = snap_dir / "prediction_results.csv"
if results_path.is_file():
    st.subheader("Metrics by method")
    st.dataframe(pd.read_csv(results_path))

roc_path = snap_dir / "roc_curves.png"
if roc_path.is_file():
    st.subheader("ROC curves")
    st.image(str(roc_path))

links_path = snap_dir / "top_predicted_links.csv"
if links_path.is_file():
    st.subheader("Top predicted links")
    st.dataframe(pd.read_csv(links_path).head(100))
