"""STATPRO — entry point and navigation router.

Run with:  streamlit run app.py
"""

import streamlit as st

from modules.shared import render_dataset_panel, render_sidebar
from modules.ui import inject_css

st.set_page_config(
    page_title="STATPRO · Statistical Analysis",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar()

pages = {
    "Overview": [
        st.Page("pages/0_Dashboard.py", title="Dashboard", icon=":material/space_dashboard:", default=True),
        st.Page("pages/1_Data_Quality.py", title="Data Quality", icon=":material/verified:"),
    ],
    "Analysis": [
        st.Page("pages/2_Descriptive_Statistics.py", title="Descriptive Statistics", icon=":material/bar_chart:"),
        st.Page("pages/3_Hypothesis_Testing.py", title="Hypothesis Testing", icon=":material/science:"),
        st.Page("pages/4_Correlation_Analysis.py", title="Correlation", icon=":material/hub:"),
        st.Page("pages/5_Regression_Analysis.py", title="Regression", icon=":material/trending_up:"),
    ],
    "Output": [
        st.Page("pages/6_Reports.py", title="Reports & Export", icon=":material/description:"),
    ],
}

nav = st.navigation(pages)
render_dataset_panel()
nav.run()
