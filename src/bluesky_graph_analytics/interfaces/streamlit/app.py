"""Legacy Streamlit entry; prefer Home.py via `bga dashboard`."""

import streamlit as st

from bluesky_graph_analytics.infrastructure.observability import health_notes

st.set_page_config(page_title="Bluesky Graph Analytics", page_icon="🕸️", layout="wide")
st.title("Bluesky Graph Analytics")
st.json(health_notes())
