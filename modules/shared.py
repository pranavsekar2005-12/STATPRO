
import streamlit as st
import pandas as pd
from pathlib import Path


def load_custom_css():
    """Load STATPRO custom styling."""

    css_path = Path("assets/style.css")

    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )


def get_dataset():
    """Upload and share one dataset across all pages."""

    if "statpro_df" not in st.session_state:
        st.session_state.statpro_df = None

    if "statpro_filename" not in st.session_state:
        st.session_state.statpro_filename = None

    with st.sidebar:
        st.markdown("## 📊 STATPRO")
        st.caption("Statistical Analysis Workspace")
        st.divider()

        uploaded_file = st.file_uploader(
            "Upload your dataset",
            type=["csv", "xlsx"],
            key="statpro_uploader",
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.lower().endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.session_state.statpro_df = df
                st.session_state.statpro_filename = uploaded_file.name

                st.success("Dataset loaded successfully")

            except Exception as error:
                st.error(f"Upload failed: {error}")

        if st.session_state.statpro_df is not None:
            st.divider()
            st.caption(
                f"Current dataset: {st.session_state.statpro_filename}"
            )
            st.caption(
                f"{len(st.session_state.statpro_df):,} records"
            )

    return st.session_state.statpro_df
