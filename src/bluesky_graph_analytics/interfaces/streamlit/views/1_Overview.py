"""Overview page (DEO 8.5)."""

from pathlib import Path

import pandas as pd
import streamlit as st

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.interfaces.streamlit.data_access import (
    language_distribution,
    list_snapshots,
    seed_follower_histogram,
    snapshot_run,
)
from bluesky_graph_analytics.interfaces.streamlit.i18n import t, translate_columns

st.header(t("nav.overview"))
st.markdown(t("overview.intro"))
runs = list_snapshots()
if not runs:
    st.warning(t("common.no_runs"))
    st.stop()

snap_ids = [r["snapshot_id"] for r in runs]
snap = st.selectbox(t("common.snapshot"), snap_ids, help=t("common.snapshot_help"))
run = snapshot_run(snap) if snap else None
if not run:
    st.stop()

coll = run["stats"].get("collection", {})
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("overview.seeds"), coll.get("seeds_valid", "—"), help=t("overview.seeds_help"))
c2.metric(
    t("overview.profiles"), coll.get("profiles_collected", "—"), help=t("overview.profiles_help")
)
c3.metric(t("overview.edges"), coll.get("follows_collected", "—"), help=t("overview.edges_help"))
c4.metric(
    t("overview.duration"), coll.get("duration_seconds", "—"), help=t("overview.duration_help")
)

st.subheader(t("overview.run_title"))
st.caption(t("overview.run_caption"))
st.json(
    {
        t("overview.run_id"): run["id"],
        t("overview.run_snapshot"): run["snapshot_id"],
        t("overview.run_status"): t(f"status.{run['status']}", default=run["status"]),
        t("overview.run_commit"): run["git_commit_hash"],
        t("overview.run_started"): run["started_at"],
        t("overview.run_finished"): run["finished_at"],
    }
)

hist = seed_follower_histogram(snap)
if hist:
    st.subheader(t("overview.seed_hist_title"))
    st.caption(t("overview.seed_hist_caption"))
    x, y = t("overview.seed_hist_x"), t("overview.seed_hist_y")
    hist_df = pd.DataFrame(hist, columns=[x, y])
    st.bar_chart(hist_df, x=x, y=y)

lang = language_distribution(snap)
if lang:
    st.subheader(t("overview.lang_title"))
    st.caption(t("overview.lang_caption"))
    x, y = t("overview.lang_x"), t("overview.lang_y")
    lang_df = pd.DataFrame({x: list(lang.keys()), y: list(lang.values())})
    lang_df = lang_df.sort_values(y, ascending=False).head(10)
    st.bar_chart(lang_df, x=x, y=y)

results_root = Path(DATA_DIR) / "results" / snap
if results_root.is_dir():
    comm_stats = results_root / "community_stats.csv"
    comm_df = (
        pd.read_csv(comm_stats)
        if comm_stats.is_file() and comm_stats.stat().st_size > 0
        else pd.DataFrame()
    )
    if not comm_df.empty:
        st.subheader(t("overview.communities_title"))
        st.caption(t("overview.communities_caption"))
        st.dataframe(translate_columns(comm_df))
    elif comm_stats.is_file():
        st.info(t("overview.communities_empty"))
