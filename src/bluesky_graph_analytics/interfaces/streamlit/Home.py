"""Streamlit dashboard entry (DEO 8.5)."""

import streamlit as st

st.set_page_config(page_title="Bluesky Graph Analytics", layout="wide")
st.title("Bluesky Graph Analytics")
st.markdown("Read-only dashboard over `data/results/<snapshot_id>/` outputs.")
st.info("Use sidebar pages: Overview, Similarity, Communities, Predictions.")
