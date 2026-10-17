"""Community detection dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.config import load_settings
from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.data_access import list_snapshots, snapshot_run
from bluesky_graph_analytics.interfaces.streamlit.i18n import t, translate_columns

st.header(t("nav.communities"))
st.markdown(t("communities.intro"))
runs = list_snapshots()
if not runs:
    st.warning(t("common.no_runs"))
    st.stop()
snap = st.selectbox(
    t("common.snapshot"), [r["snapshot_id"] for r in runs], help=t("common.snapshot_help")
)
snap_dir = Path(DATA_DIR) / "results" / snap
run = snapshot_run(snap)
mod_q = run["stats"].get("community", {}).get("modularity") if run else None
if mod_q is not None:
    st.metric(
        t("communities.modularity"), f"{float(mod_q):.3f}", help=t("communities.modularity_help")
    )

stats_path = snap_dir / "community_stats.csv"
stats = pd.read_csv(stats_path) if stats_path.is_file() and stats_path.stat().st_size > 0 else None
if stats is not None and stats.empty and mod_q is not None:
    modularity_min = load_settings().analysis.community.modularity_min
    st.info(t("communities.below_threshold", q=f"{float(mod_q):.3f}", min=modularity_min))
elif stats is not None:
    st.subheader(t("communities.stats_title"))
    st.caption(t("communities.stats_caption"))
    st.dataframe(translate_columns(stats))
    id_col = "community_id" if "community_id" in stats.columns else "id"
    if "size" in stats.columns:
        st.subheader(t("communities.size_title"))
        st.caption(t("communities.size_caption"))
        x, y = t("communities.size_x"), t("communities.size_y")
        sizes = pd.DataFrame({x: stats[id_col].astype(str), y: stats["size"]})
        st.bar_chart(sizes, x=x, y=y)
    if "top_terms" in stats.columns and len(stats):
        cid = st.selectbox(t("communities.select"), stats[id_col].tolist())
        row = stats.loc[stats[id_col] == cid].iloc[0]
        terms = str(row["top_terms"]).split("|")
        weights = list(range(len(terms), 0, -1))
        st.subheader(t("communities.terms_title"))
        st.caption(t("communities.terms_caption"))
        x, y = t("communities.terms_x"), t("communities.terms_y")
        wc = pd.DataFrame({x: terms, y: weights[: len(terms)]})
        st.bar_chart(wc, x=x, y=y, sort=False)
else:
    st.info(t("communities.empty"))

html_path = snap_dir / "community_graph.html"
if html_path.is_file():
    st.subheader(t("communities.graph_title"))
    st.caption(t("communities.graph_caption"))
    st.components.v1.html(html_path.read_text(encoding="utf-8"), height=600, scrolling=True)

png_path = snap_dir / "community_graph.png"
if png_path.is_file():
    st.subheader(t("communities.image_title"))
    st.caption(t("communities.image_caption"))
    st.image(str(png_path))
