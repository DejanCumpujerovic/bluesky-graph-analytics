"""Dashboard landing page (DEO 8.5)."""

import streamlit as st

from bluesky_graph_analytics.interfaces.streamlit.i18n import t

st.title(t("app.title"))
st.markdown(t("home.intro"))
st.info(t("home.read_only"))

st.subheader(t("home.pages_title"))
st.markdown(t("home.pages"))

st.subheader(t("home.glossary_title"))
st.markdown(t("home.glossary"))
