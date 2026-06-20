"""Community detection dashboard (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.data_access import list_snapshots, snapshot_run

st.header("Communities")
runs = list_snapshots()
if not runs:
    st.warning("No runs in database.")
    st.stop()
snap = st.selectbox("Snapshot", [r["snapshot_id"] for r in runs])
snap_dir = Path(DATA_DIR) / "results" / snap
run = snapshot_run(snap)
mod_q = run["stats"].get("community", {}).get("modularity") if run else None
if mod_q is not None:
    st.metric("Global modularity Q", float(mod_q))

stats_path = snap_dir / "community_stats.csv"
if stats_path.is_file() and stats_path.stat().st_size > 0:
    stats = pd.read_csv(stats_path)
    st.subheader("Community stats")
    st.dataframe(stats)
    id_col = "community_id" if "community_id" in stats.columns else "id"
    if "size" in stats.columns:
        st.bar_chart(stats.set_index(id_col)["size"])
    if "top_terms" in stats.columns and len(stats):
        cid = st.selectbox("Community", stats[id_col].tolist())
        row = stats.loc[stats[id_col] == cid].iloc[0]
        terms = str(row["top_terms"]).split("|")
        weights = list(range(len(terms), 0, -1))
        st.subheader("Top terms (word cloud weights)")
        wc = pd.DataFrame({"term": terms, "weight": weights[: len(terms)]})
        st.bar_chart(wc.set_index("term"))
else:
    st.info("No community_stats.csv")

html_path = snap_dir / "community_graph.html"
if html_path.is_file():
    st.subheader("Graph")
    st.components.v1.html(html_path.read_text(encoding="utf-8"), height=600, scrolling=True)

png_path = snap_dir / "community_graph.png"
if png_path.is_file():
    st.image(str(png_path))
