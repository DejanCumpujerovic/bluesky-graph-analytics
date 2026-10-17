"""Link prediction dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.i18n import t, translate_columns

st.header(t("nav.predictions"))
st.warning(t("predictions.warning"))
st.markdown(t("predictions.intro"))

root = Path(DATA_DIR) / "results"
if not root.exists():
    st.warning(t("common.no_runs"))
    st.stop()

snapshots = sorted(p.name for p in root.iterdir() if p.is_dir())
snap = (
    st.selectbox(t("common.snapshot"), snapshots, help=t("common.snapshot_help"))
    if snapshots
    else None
)
if not snap:
    st.stop()

snap_dir = root / snap
results_path = snap_dir / "prediction_results.csv"
if results_path.is_file():
    results = pd.read_csv(results_path)
    if "method" in results.columns:
        results["method"] = results["method"].map(lambda m: t(f"methods.{m}", default=m))
    st.subheader(t("predictions.metrics_title"))
    st.markdown(t("predictions.metrics_caption"))
    st.dataframe(translate_columns(results))

roc_path = snap_dir / "roc_curves.png"
if roc_path.is_file():
    st.subheader(t("predictions.roc_title"))
    st.caption(t("predictions.roc_caption"))
    st.image(str(roc_path))

links_path = snap_dir / "top_predicted_links.csv"
if links_path.is_file():
    st.subheader(t("predictions.links_title"))
    st.caption(t("predictions.links_caption"))
    st.dataframe(translate_columns(pd.read_csv(links_path).head(100)))
