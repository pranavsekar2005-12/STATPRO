"""Dataset loading and session state shared across every STATPRO page."""

from datetime import datetime
from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st

from modules.ui import ROOT, inject_css

DEMO_PATH = ROOT / "data" / "sample_customers.csv"


def load_custom_css():
    """Backwards-compatible alias."""
    inject_css()


def _init_state():
    defaults = {
        "statpro_df": None,
        "statpro_original_df": None,
        "statpro_filename": None,
        "statpro_file_sig": None,
        "statpro_results": {},
        "statpro_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _read_file(name, data):
    if name.lower().endswith(".csv"):
        try:
            return pd.read_csv(BytesIO(data))
        except UnicodeDecodeError:
            return pd.read_csv(BytesIO(data), encoding="latin-1")
    return pd.read_excel(BytesIO(data))


def set_dataset(df, name):
    st.session_state.statpro_df = df
    st.session_state.statpro_original_df = df.copy()
    st.session_state.statpro_filename = name
    st.session_state.statpro_results = {}
    st.session_state.statpro_log = []
    for key in list(st.session_state.keys()):
        if str(key).startswith("res_"):
            del st.session_state[key]


def update_dataset(df, action):
    """Replace the working dataset after a cleaning action (original kept for reset)."""
    st.session_state.statpro_df = df.reset_index(drop=True)
    st.session_state.statpro_log.append(f"{datetime.now():%H:%M} · {action}")


def reset_dataset():
    if st.session_state.statpro_original_df is not None:
        st.session_state.statpro_df = st.session_state.statpro_original_df.copy()
        st.session_state.statpro_log = []


def clear_dataset():
    st.session_state.statpro_df = None
    st.session_state.statpro_original_df = None
    st.session_state.statpro_filename = None
    st.session_state.statpro_file_sig = None
    st.session_state.statpro_results = {}
    st.session_state.statpro_log = []
    st.session_state.statpro_uploader_v = st.session_state.get("statpro_uploader_v", 0) + 1


def load_demo():
    set_dataset(pd.read_csv(DEMO_PATH), DEMO_PATH.name)
    st.session_state.statpro_file_sig = "demo"


def get_dataset():
    _init_state()
    return st.session_state.statpro_df


def save_result(key, title, category, summary, tables=None, interpretation=""):
    """Store an analysis result so the Reports page can include it."""
    _init_state()
    st.session_state.statpro_results[key] = {
        "title": title,
        "category": category,
        "summary": {k: str(v) for k, v in summary.items()},
        "tables": tables or {},
        "interpretation": interpretation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def get_results():
    _init_state()
    return st.session_state.statpro_results


def render_sidebar():
    """Brand, dataset uploader and dataset status card."""
    _init_state()
    st.logo(str(ROOT / "assets" / "logo.svg"), size="large", icon_image=str(ROOT / "assets" / "icon.svg"))


def render_dataset_panel():
    with st.sidebar:
        st.markdown('<div class="sp-side-label">Dataset</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"],
            key=f"statpro_uploader_{st.session_state.get('statpro_uploader_v', 0)}",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            sig = f"{uploaded.name}:{uploaded.size}"
            if sig != st.session_state.statpro_file_sig:
                try:
                    df = _read_file(uploaded.name, uploaded.getvalue())
                    if df.empty:
                        st.error("The uploaded file contains no rows.")
                    else:
                        set_dataset(df, uploaded.name)
                        st.session_state.statpro_file_sig = sig
                        st.toast(f"Loaded {uploaded.name}", icon=":material/check_circle:")
                except Exception as error:  # noqa: BLE001
                    st.error(f"Upload failed: {error}")

        df = st.session_state.statpro_df
        if df is None:
            if st.button("Use demo dataset", icon=":material/science:", width="stretch"):
                load_demo()
                st.rerun()
        else:
            modified = len(st.session_state.statpro_log) > 0
            tag = '<span class="tag">Modified · cleaned</span>' if modified else '<span class="tag">Original</span>'
            st.markdown(
                f"""<div class="sp-dataset">
                      <div class="name">{escape(str(st.session_state.statpro_filename))}</div>
                      <div class="meta"><div><b>{len(df):,}</b>rows</div><div><b>{df.shape[1]}</b>columns</div>
                      <div><b>{int(df.isnull().sum().sum()):,}</b>missing</div></div>{tag}
                    </div>""",
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2 = st.columns(2)
            if c1.button("Reset", icon=":material/restart_alt:", width="stretch", disabled=not modified,
                         help="Restore the original uploaded data"):
                reset_dataset()
                st.rerun()
            if c2.button("Clear", icon=":material/delete:", width="stretch", help="Remove dataset"):
                clear_dataset()
                st.rerun()
