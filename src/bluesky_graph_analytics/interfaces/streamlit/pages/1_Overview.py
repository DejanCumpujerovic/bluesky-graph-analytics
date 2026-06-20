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

st.header("Overview")
runs = list_snapshots()
if not runs:
    st.warning("No runs in database. Run `bga collect` first.")
    st.stop()

snap_ids = [r["snapshot_id"] for r in runs]
snap = st.selectbox("Snapshot", snap_ids)
run = snapshot_run(snap) if snap else None
if not run:
    st.stop()

coll = run["stats"].get("collection", {})
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valid seeds", coll.get("seeds_valid", "—"))
c2.metric("Profiles collected", coll.get("profiles_collected", "—"))
c3.metric("Follow edges", coll.get("follows_collected", "—"))
c4.metric("Collection duration (s)", coll.get("duration_seconds", "—"))

st.subheader("Run metadata")
st.json(
    {
        "run_id": run["id"],
        "snapshot_id": run["snapshot_id"],
        "status": run["status"],
        "git_commit_hash": run["git_commit_hash"],
        "started_at": run["started_at"],
        "finished_at": run["finished_at"],
    }
)

hist = seed_follower_histogram(snap)
if hist:
    st.subheader("Seed follower count distribution")
    hist_df = pd.DataFrame(hist, columns=["followers_count", "count"])
    st.bar_chart(hist_df.set_index("followers_count"))

lang = language_distribution(snap)
if lang:
    st.subheader("Detected language distribution")
    lang_df = pd.DataFrame({"language": list(lang.keys()), "count": list(lang.values())})
    lang_df = lang_df.sort_values("count", ascending=False).head(10)
    st.bar_chart(lang_df.set_index("language"))

results_root = Path(DATA_DIR) / "results" / snap
if results_root.is_dir():
    comm_stats = results_root / "community_stats.csv"
    if comm_stats.is_file() and comm_stats.stat().st_size > 0:
        st.subheader("Community summary")
        st.dataframe(pd.read_csv(comm_stats))
    elif comm_stats.is_file():
        st.info("No communities detected for this snapshot (empty graph).")
