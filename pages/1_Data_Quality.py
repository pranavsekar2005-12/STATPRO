import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.data_quality import analyze_data_quality, outlier_bounds
from modules.shared import get_dataset, save_result, update_dataset
from modules.ui import (
    PALETTE, PRIMARY, SEQ_SCALE, badge, card, dataset_chip, default_index, empty_state, footer, kpi_cards,
    page_header, section, show_fig, style_fig, verdict,
)

df = get_dataset()
page_header("Data Quality", "Evaluate completeness, consistency and potential outliers — then clean in one click.",
            eyebrow="Overview",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

result = analyze_data_quality(df)
save_result(
    "quality", "Data Quality Assessment", "Data Quality",
    {"Records": result["total_rows"], "Variables": result["total_columns"],
     "Missing cells": result["missing_cells"], "Duplicate rows": result["duplicate_count"],
     "Potential outliers": sum(result["outlier_counts"].values()), "Quality score": f"{result['quality_score']}%"},
    tables={"Variable profile": result["profile"].reset_index()},
)

score = result["quality_score"]
kpi_cards([
    {"label": "Quality Score", "value": f"{score}%", "icon": "verified", "tone": "indigo",
     "delta": "Excellent" if score >= 95 else "Good" if score >= 85 else "Needs attention",
     "delta_tone": "up" if score >= 85 else "down"},
    {"label": "Missing Cells", "value": f"{result['missing_cells']:,}", "icon": "help", "tone": "coral",
     "delta": f"{len(result['missing_summary'])} variables affected"},
    {"label": "Duplicate Rows", "value": f"{result['duplicate_count']:,}", "icon": "content_copy", "tone": "yellow",
     "delta": f"{result['uniqueness'] * 100:.1f}% unique records"},
    {"label": "Potential Outliers", "value": f"{sum(result['outlier_counts'].values()):,}", "icon": "scatter_plot",
     "tone": "blue", "delta": "IQR rule (1.5 × IQR)"},
])

left, right = st.columns([1, 1.6], gap="medium")
with left:
    with card("score"):
        section("Quality Dimensions", "Weighted: completeness 50% · uniqueness 30% · validity 20%")
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score, number=dict(suffix="%", font=dict(size=40, color="#030229")),
            gauge=dict(axis=dict(range=[0, 100], tickcolor="#C9C9D6"), bar=dict(color=PRIMARY, thickness=0.28),
                       bgcolor="#F2F1FF", borderwidth=0,
                       steps=[dict(range=[0, 70], color="#FFF1EC"), dict(range=[70, 85], color="#FFF8E4"),
                              dict(range=[85, 100], color="#EAFBF3")]),
        ))
        show_fig(style_fig(fig, height=230, legend=False))
        dims = pd.DataFrame({"Dimension": ["Completeness", "Uniqueness", "Validity"],
                             "Score": [result["completeness"], result["uniqueness"], result["validity"]]})
        for _, r in dims.iterrows():
            st.progress(float(r["Score"]), text=f"**{r['Dimension']}** · {r['Score'] * 100:.1f}%")

with right:
    with card("missing"):
        section("Missing Values by Variable", "Count and share of empty cells")
        if result["missing_summary"].empty:
            verdict("sig", "No missing values detected", "Every cell in the dataset contains a value.")
        else:
            miss = result["missing_summary"].sort_values(ascending=True).reset_index()
            miss.columns = ["Variable", "Missing"]
            miss["Share"] = miss["Missing"] / len(df) * 100
            fig = go.Figure(go.Bar(
                y=miss["Variable"], x=miss["Missing"], orientation="h", marker_color=PALETTE[2],
                text=[f"{v} · {s:.1f}%" for v, s in zip(miss["Missing"], miss["Share"])], textposition="outside",
                hovertemplate="%{y}: %{x} missing<extra></extra>",
            ))
            show_fig(style_fig(fig, height=max(220, 60 + 34 * len(miss)), legend=False))
        if result["missing_cells"]:
            with st.expander("Missing-value map (first 200 rows)", icon=":material/grid_on:"):
                sample = df.head(200).isnull().astype(int)
                fig = px.imshow(sample.T, color_continuous_scale=[[0, "#F2F1FF"], [1, "#FF8F6B"]], aspect="auto")
                fig.update_coloraxes(showscale=False)
                show_fig(style_fig(fig, height=300, legend=False))

tab_profile, tab_out, tab_dup, tab_clean = st.tabs(
    [":material/table_view: Variable Profile", ":material/scatter_plot: Outliers",
     ":material/content_copy: Duplicates", ":material/cleaning_services: Clean Data"]
)

with tab_profile:
    with card("profile"):
        section("Variable Profile", "Type, completeness, cardinality and outliers for every column")
        st.dataframe(
            result["profile"], width="stretch",
            column_config={
                "Missing %": st.column_config.ProgressColumn("Missing %", min_value=0, max_value=100, format="%.1f%%"),
                "Outliers": st.column_config.NumberColumn("Outliers", format="%d"),
            },
        )
        if not result["numeric_summary"].empty:
            section("Numeric Summary")
            st.dataframe(result["numeric_summary"].style.format("{:,.2f}"), width="stretch")

with tab_out:
    with card("outliers"):
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            st.info("No numeric variables available for outlier analysis.")
        else:
            c1, c2 = st.columns([1, 1.4], gap="large")
            with c1:
                section("Outliers per Variable", "Values beyond 1.5 × IQR from the quartiles")
                odf = pd.DataFrame(list(result["outlier_counts"].items()), columns=["Variable", "Outliers"])
                fig = go.Figure(go.Bar(x=odf["Variable"], y=odf["Outliers"], marker_color=PALETTE[3],
                                       hovertemplate="%{x}: %{y}<extra></extra>"))
                show_fig(style_fig(fig, height=320, legend=False))
            with c2:
                var = st.selectbox("Inspect variable", numeric_cols, index=default_index(numeric_cols), key="dq_out_var")
                s = df[var].dropna()
                low, high = outlier_bounds(s)
                fig = go.Figure(go.Box(x=s, name=var, marker_color=PRIMARY, boxpoints="outliers",
                                       fillcolor="rgba(96,91,255,.12)", line=dict(color=PRIMARY)))
                show_fig(style_fig(fig, height=200, legend=False))
                flagged = df[(df[var] < low) | (df[var] > high)]
                st.markdown(f"Bounds: **{low:,.2f}** to **{high:,.2f}** · {badge(f'{len(flagged)} flagged', 'warn')}",
                            unsafe_allow_html=True)
                if len(flagged):
                    st.dataframe(flagged, width="stretch", height=180)
            st.caption("Potential outliers are flagged for investigation — they are not automatically errors.")

with tab_dup:
    with card("dups"):
        section("Duplicate Records", "Rows that exactly match another row")
        if result["duplicate_count"] == 0:
            verdict("sig", "No duplicate records", "Each row in the dataset is unique.")
        else:
            verdict("warn", f"{result['duplicate_count']} duplicate rows detected",
                    "Duplicates can bias counts and statistics. Remove them in the <b>Clean Data</b> tab.")
            st.dataframe(df[df.duplicated(keep=False)].sort_values(list(df.columns)), width="stretch", height=260)

with tab_clean:
    with card("clean"):
        section("Cleaning Tools", "Changes apply to the working dataset used by every page. Use Reset in the sidebar to undo.")
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown("**Remove duplicates**")
            st.caption(f"{result['duplicate_count']} exact duplicate rows found.")
            if st.button("Remove duplicates", icon=":material/delete_sweep:", disabled=result["duplicate_count"] == 0,
                         width="stretch"):
                update_dataset(df.drop_duplicates(), f"Removed {result['duplicate_count']} duplicate rows")
                st.toast("Duplicates removed", icon=":material/check_circle:")
                st.rerun()
        with c2:
            st.markdown("**Handle missing values**")
            miss_cols = result["missing_summary"].index.tolist()
            strategy = st.selectbox("Strategy", ["Drop rows with missing values", "Fill with mean (numeric)",
                                                 "Fill with median (numeric)", "Fill with mode (most frequent)"],
                                    key="dq_strategy")
            cols = st.multiselect("Columns", miss_cols, default=miss_cols, key="dq_cols")
            if st.button("Apply", icon=":material/auto_fix_high:", disabled=not cols, width="stretch"):
                new = df.copy()
                if strategy.startswith("Drop"):
                    new = new.dropna(subset=cols)
                else:
                    for c in cols:
                        if strategy.startswith("Fill with mode"):
                            mode = new[c].mode(dropna=True)
                            if len(mode):
                                new[c] = new[c].fillna(mode.iloc[0])
                        elif pd.api.types.is_numeric_dtype(new[c]):
                            new[c] = new[c].fillna(new[c].mean() if "mean" in strategy else new[c].median())
                update_dataset(new, f"{strategy} → {', '.join(cols)}")
                st.toast("Missing values handled", icon=":material/check_circle:")
                st.rerun()
        with c3:
            st.markdown("**Remove outliers**")
            num_cols = df.select_dtypes(include="number").columns.tolist()
            ocols = st.multiselect("Columns", num_cols, key="dq_ocols")
            if st.button("Remove outlier rows", icon=":material/filter_alt:", disabled=not ocols, width="stretch"):
                mask = pd.Series(False, index=df.index)
                for c in ocols:
                    s = df[c].dropna()
                    lo, hi = outlier_bounds(s)
                    mask |= (df[c] < lo) | (df[c] > hi)
                update_dataset(df[~mask], f"Removed {int(mask.sum())} outlier rows ({', '.join(ocols)})")
                st.toast(f"Removed {int(mask.sum())} rows", icon=":material/check_circle:")
                st.rerun()

        if st.session_state.statpro_log:
            st.divider()
            section("Change Log")
            for entry in st.session_state.statpro_log:
                st.markdown(f"- {entry}")

footer()
