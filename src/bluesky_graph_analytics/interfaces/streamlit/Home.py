"""Streamlit dashboard entry (DEO 8.5)."""

import streamlit as st

from bluesky_graph_analytics.interfaces.streamlit.i18n import t

st.set_page_config(page_title=t("app.title"), page_icon="🕸️", layout="wide")

# views/ — not pages/, so Streamlit does not auto-discover routes.
navigation = st.navigation(
    [
        st.Page("views/0_Home.py", title=t("nav.home"), default=True),
        st.Page("views/1_Overview.py", title=t("nav.overview"), url_path="overview"),
        st.Page("views/2_Similarity.py", title=t("nav.similarity"), url_path="similarity"),
        st.Page("views/3_Communities.py", title=t("nav.communities"), url_path="communities"),
        st.Page("views/4_Predictions.py", title=t("nav.predictions"), url_path="predictions"),
        st.Page("views/5_Comparison.py", title=t("nav.comparison"), url_path="comparison"),
    ]
)
navigation.run()
