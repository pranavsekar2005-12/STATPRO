import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules.descriptive import calculate_descriptive_statistics
from modules.shared import get_dataset, save_result
from modules.ui import (
    PALETTE, PRIMARY, card, dataset_chip, default_index, donut, empty_state, is_id_like, fmt, footer, kpi_cards,
    page_header, section, show_fig, stat_row, style_fig,
)

df = get_dataset()
page_header("Descriptive Statistics", "Summaries of central tendency, dispersion and shape for every variable.",
            eyebrow="Analysis",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

try:
    result = calculate_descriptive_statistics(df)
except ValueError as error:
    empty_state("Cannot compute statistics", str(error), "error")
    st.stop()

stats_df = result["statistics"]
numeric_cols = stats_df.index.tolist()
cat_cols = list(result["frequency_tables"].keys())

save_result("descriptive", "Descriptive Statistics", "Descriptive",
            {"Numeric variables": len(numeric_cols), "Categorical variables": len(cat_cols)},
            tables={"Summary statistics": stats_df.round(4).reset_index().rename(columns={"index": "Variable"})})

tab_var, tab_table, tab_cat, tab_group = st.tabs(
    [":material/query_stats: Variable Explorer", ":material/table_chart: Summary Table",
     ":material/category: Categorical", ":material/workspaces: Group Comparison"]
)

with tab_var:
    var = st.selectbox("Select a numeric variable", numeric_cols, index=default_index(numeric_cols), key="desc_var")
    s = df[var].dropna()
    row = stats_df.loc[var]
    kpi_cards([
        {"label": "Mean", "value": fmt(row["mean"], 2), "icon": "functions", "tone": "indigo"},
        {"label": "Median", "value": fmt(row["median"], 2), "icon": "align_vertical_center", "tone": "blue"},
        {"label": "Std Deviation", "value": fmt(row["std"], 2), "icon": "swap_vert", "tone": "coral"},
        {"label": "Observations", "value": f"{int(row['count']):,}", "icon": "tag", "tone": "yellow",
         "delta": f"{int(row['missing'])} missing", "delta_tone": "down" if row["missing"] else "up"},
    ])
    c1, c2 = st.columns([1.7, 1], gap="medium")
    with c1:
        with card("hist"):
            h1, h2 = st.columns([2, 1])
            with h1:
                section(f"Distribution of {var}", "Histogram with box plot")
            bins = h2.slider("Bins", 5, 80, 25, key="desc_bins", label_visibility="collapsed")
            fig = make_subplots(rows=2, cols=1, row_heights=[0.2, 0.8], shared_xaxes=True, vertical_spacing=0.03)
            fig.add_trace(go.Box(x=s, marker_color=PRIMARY, fillcolor="rgba(96,91,255,.15)", name=var,
                                 boxpoints="outliers", hoverinfo="x"), row=1, col=1)
            fig.add_trace(go.Histogram(x=s, nbinsx=bins, marker_color=PRIMARY, opacity=0.85, name="Count",
                                       hovertemplate="%{x}<br>Count: %{y}<extra></extra>"), row=2, col=1)
            fig.add_vline(x=row["mean"], line_dash="dot", line_color=PALETTE[2], row=2, col=1)
            fig.add_vline(x=row["median"], line_dash="dash", line_color=PALETTE[4], row=2, col=1)
            fig.update_yaxes(showticklabels=False, row=1, col=1)
            show_fig(style_fig(fig, height=380, legend=False))
            st.caption("Orange dotted line = mean · green dashed line = median")
    with c2:
        with card("shape"):
            section("Shape & Spread")
            stat_row([("Min", fmt(row["min"], 2)), ("Max", fmt(row["max"], 2))])
            stat_row([("Q1", fmt(row["25%"], 2)), ("Q3", fmt(row["75%"], 2))])
            stat_row([("Range", fmt(row["range"], 2)), ("IQR", fmt(row["iqr"], 2))])
            stat_row([("Variance", fmt(row["variance"], 2)), ("CV", f"{row['cv %']:.1f}%" if row["cv %"] == row["cv %"] else "—")])
            stat_row([("Skewness", f"{row['skewness']:.3f}"), ("Kurtosis", f"{row['kurtosis']:.3f}")])
            sk = row["skewness"]
            shape = ("approximately symmetric" if abs(sk) < 0.5 else
                     "moderately " + ("right" if sk > 0 else "left") + "-skewed" if abs(sk) < 1 else
                     "highly " + ("right" if sk > 0 else "left") + "-skewed")
            st.caption(f"The distribution is **{shape}** (skewness {sk:.2f}).")

    with card("boxes"):
        section("Compare Variables", "Box plots on a standardised (z-score) scale")
        sel = st.multiselect("Variables", numeric_cols, default=[c for c in numeric_cols if not is_id_like(c)][:6],
                             key="desc_box")
        if sel:
            fig = go.Figure()
            for i, c in enumerate(sel):
                v = df[c].dropna()
                z = (v - v.mean()) / v.std() if v.std() else v * 0
                fig.add_trace(go.Box(y=z, name=c, marker_color=PALETTE[i % len(PALETTE)], boxmean=True))
            show_fig(style_fig(fig, height=360, legend=False))

with tab_table:
    with card("table"):
        section("Summary Statistics", "All numeric variables")
        cols = ["count", "mean", "median", "std", "variance", "min", "25%", "50%", "75%", "max",
                "range", "iqr", "cv %", "skewness", "kurtosis", "missing"]
        st.dataframe(stats_df[cols].style.format("{:,.3f}"), width="stretch")
        st.download_button("Download as CSV", stats_df[cols].to_csv().encode(), "descriptive_statistics.csv",
                           "text/csv", icon=":material/download:")

with tab_cat:
    if not cat_cols:
        empty_state("No categorical variables", "This dataset only contains numeric columns.", "category")
    else:
        cvar = st.selectbox("Select a categorical variable", cat_cols, key="desc_cat")
        freq = result["frequency_tables"][cvar]
        labels = ["Missing" if str(i) == "nan" else str(i) for i in freq.index]
        c1, c2 = st.columns([1, 1.3], gap="medium")
        with c1:
            with card("catdonut"):
                section(f"{cvar} share")
                top = freq.head(8)
                show_fig(donut(labels[: len(top)], top.values.tolist(), str(len(freq)), "categories"))
        with c2:
            with card("cattable"):
                section("Frequency Table")
                table = freq.to_frame("Count")
                table.index = labels
                table.index.name = cvar
                table["Percent"] = table["Count"] / table["Count"].sum() * 100
                table["Cumulative %"] = table["Percent"].cumsum()
                st.dataframe(table, width="stretch", height=330, column_config={
                    "Percent": st.column_config.ProgressColumn("Percent", format="%.1f%%", min_value=0, max_value=100),
                    "Cumulative %": st.column_config.NumberColumn(format="%.1f%%"),
                })

with tab_group:
    if not cat_cols:
        empty_state("No grouping variables", "Group comparison needs at least one categorical column.", "workspaces")
    else:
        c1, c2 = st.columns(2)
        gvar = c1.selectbox("Group by", cat_cols, key="desc_gvar")
        mvar = c2.selectbox("Measure", numeric_cols, key="desc_mvar")
        grp = df.groupby(gvar)[mvar].agg(["count", "mean", "median", "std", "min", "max"])
        with card("group"):
            section(f"{mvar} by {gvar}")
            fig = go.Figure()
            for i, (name, g) in enumerate(df.dropna(subset=[gvar]).groupby(gvar)):
                fig.add_trace(go.Violin(y=g[mvar], name=str(name), box_visible=True, meanline_visible=True,
                                        line_color=PALETTE[i % len(PALETTE)], opacity=0.85))
            show_fig(style_fig(fig, height=360, legend=False))
            st.dataframe(grp.style.format("{:,.2f}"), width="stretch")

footer()
