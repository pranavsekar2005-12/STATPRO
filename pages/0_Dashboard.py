import numpy as np
import plotly.graph_objects as go
import streamlit as st

from modules.data_quality import analyze_data_quality
from modules.shared import get_dataset, load_demo
from modules.ui import (
    PALETTE, PRIMARY, bar_list, card, dataset_chip, default_index, donut, footer, icon, kpi_cards,
    page_header, section, show_fig, style_fig,
)

df = get_dataset()

# ------------------------------------------------------------------ empty state
if df is None:
    page_header("Welcome to STATPRO", "Upload a dataset to unlock your statistical analysis workspace.",
                eyebrow="Dashboard")
    st.markdown(
        f"""<div class="sp-hero">
              <div class="eyebrow">Statistical analysis platform</div>
              <h2>From raw data to defensible insight.</h2>
              <p>Profile data quality, explore distributions, test hypotheses, measure relationships and
                 build regression models — then export a polished report in PDF or Excel.</p>
              <div class="steps">
                <div class="step"><span class="n">1</span>Upload CSV / Excel in the sidebar</div>
                <div class="step"><span class="n">2</span>Run analyses from the menu</div>
                <div class="step"><span class="n">3</span>Export your report</div>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 2.2], vertical_alignment="center")
    if c1.button("Try the demo dataset", type="primary", icon=":material/science:", width="stretch"):
        load_demo()
        st.rerun()
    c2.caption("240 customer records · 9 variables · includes missing values, duplicates and outliers to explore.")

    st.write("")
    features = [
        ("verified", "indigo", "Data Quality", "Completeness, duplicates, outliers and one-click cleaning tools."),
        ("bar_chart", "blue", "Descriptive Statistics", "Central tendency, spread, shape and frequency tables."),
        ("science", "coral", "Hypothesis Testing", "T-tests, ANOVA, Chi-square and normality with effect sizes."),
        ("hub", "yellow", "Correlation", "Pearson, Spearman and Kendall matrices with significance."),
        ("trending_up", "mint", "Regression", "Multiple OLS regression, diagnostics and what-if predictions."),
        ("description", "indigo", "Reports & Export", "Download cleaned data, Excel workbooks and PDF reports."),
    ]
    st.markdown(
        '<div class="sp-feature-grid">' + "".join(
            f'<div class="sp-feature"><div class="sp-kpi-icon tone-{t}">{icon(i)}</div><h5>{n}</h5><p>{d}</p></div>'
            for i, t, n, d in features) + "</div>",
        unsafe_allow_html=True,
    )
    footer()
    st.stop()

# ------------------------------------------------------------------ dashboard
quality = analyze_data_quality(df)
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = [c for c in df.columns if c not in numeric_cols]

page_header("Dashboard", "A live overview of your dataset and analysis workspace.",
            eyebrow="Overview", right_html=dataset_chip(st.session_state.statpro_filename, len(df)))

kpi_cards([
    {"label": "Total Records", "value": f"{len(df):,}", "icon": "table_rows", "tone": "blue"},
    {"label": "Variables", "value": df.shape[1], "icon": "view_column", "tone": "yellow",
     "delta": f"{len(numeric_cols)} numeric · {len(categorical_cols)} categorical"},
    {"label": "Missing Cells", "value": f"{quality['missing_cells']:,}", "icon": "help", "tone": "coral",
     "delta": f"{(1 - quality['completeness']) * 100:.1f}% of all cells",
     "delta_tone": "down" if quality["missing_cells"] else "up"},
    {"label": "Quality Score", "value": f"{quality['quality_score']}%", "icon": "verified", "tone": "indigo",
     "delta": f"{quality['duplicate_count']} duplicate rows", "delta_tone": "down" if quality["duplicate_count"] else "up"},
])

left, right = st.columns([1.75, 1], gap="medium")

with left:
    with card("trend"):
        if numeric_cols:
            h1, h2 = st.columns([2, 1])
            with h1:
                section("Distribution Explorer", "Smoothed frequency profile of the selected variable")
            var = h2.selectbox("Variable", numeric_cols, index=default_index(numeric_cols), label_visibility="collapsed", key="dash_var")
            series = df[var].dropna()
            counts, edges = np.histogram(series, bins=min(24, max(6, int(np.sqrt(len(series))))))
            centers = (edges[:-1] + edges[1:]) / 2
            fig = go.Figure(go.Scatter(
                x=centers, y=counts, mode="lines+markers", line=dict(color=PRIMARY, width=3, shape="spline"),
                marker=dict(size=7, color="#fff", line=dict(color=PRIMARY, width=2)),
                fill="tozeroy", fillcolor="rgba(96,91,255,0.10)",
                hovertemplate=f"{var} ≈ %{{x:,.1f}}<br>Count: %{{y}}<extra></extra>",
            ))
            fig.add_vline(x=series.mean(), line_dash="dot", line_color="#FF8F6B",
                          annotation_text=f"mean {series.mean():,.1f}", annotation_font_color="#FF8F6B")
            show_fig(style_fig(fig, height=330, legend=False))
        else:
            section("Distribution Explorer")
            st.info("No numeric variables available for visualization.")

with right:
    with card("types"):
        section("Variable Types", "Composition of the dataset")
        types = df.dtypes.astype(str).replace({"int64": "Integer", "float64": "Decimal", "object": "Text",
                                               "bool": "Boolean", "category": "Category"}).value_counts()
        show_fig(donut(types.index.tolist(), types.values.tolist(), str(df.shape[1]), "variables", height=330))

l2, r2 = st.columns([1.75, 1], gap="medium")
with l2:
    with card("preview"):
        section("Dataset Preview", f"First 12 of {len(df):,} records")
        st.dataframe(df.head(12), width="stretch", hide_index=True, height=360)

with r2:
    with card("complete"):
        section("Column Completeness", "Share of non-missing values per variable")
        comp = (df.notna().mean()).sort_values()
        rows = [(c, v, f"{v * 100:.0f}%") for c, v in comp.items()]
        bar_list(rows[:12])
        if len(rows) > 12:
            st.caption(f"+ {len(rows) - 12} more fully listed on the Data Quality page")

if categorical_cols:
    with card("cat"):
        h1, h2 = st.columns([2, 1])
        with h1:
            section("Category Breakdown", "Record counts by category, split by a second variable")
        cat = h2.selectbox("Category", categorical_cols, label_visibility="collapsed", key="dash_cat")
        counts = df[cat].fillna("Missing").astype(str).value_counts().head(15)
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=PALETTE[: len(counts)],
                               marker_line_width=0, hovertemplate="%{x}: %{y}<extra></extra>"))
        show_fig(style_fig(fig, height=280, legend=False))

st.write("")
section("Quick Actions", "Jump straight into an analysis")
q = st.columns(5)
q[0].page_link("pages/1_Data_Quality.py", label="Clean data", icon=":material/cleaning_services:")
q[1].page_link("pages/2_Descriptive_Statistics.py", label="Describe", icon=":material/bar_chart:")
q[2].page_link("pages/3_Hypothesis_Testing.py", label="Test hypotheses", icon=":material/science:")
q[3].page_link("pages/5_Regression_Analysis.py", label="Build a model", icon=":material/trending_up:")
q[4].page_link("pages/6_Reports.py", label="Export report", icon=":material/download:")

footer()
