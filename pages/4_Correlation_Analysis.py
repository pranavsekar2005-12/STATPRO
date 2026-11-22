import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.correlation import calculate_correlation, correlation_pairs, strength_label
from modules.shared import get_dataset, save_result
from modules.ui import (
    DIV_SCALE, PALETTE, PRIMARY, badge, card, dataset_chip, empty_state, fmt, fmt_p, footer, kpi_cards,
    page_header, section, show_fig, style_fig,
)

df = get_dataset()
page_header("Correlation Analysis", "Measure the strength and direction of relationships between numeric variables.",
            eyebrow="Analysis",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

numeric_cols = df.select_dtypes(include="number").columns.tolist()
# drop obvious identifier columns from the default selection
default_cols = [c for c in numeric_cols if not (c.lower() in ("id", "index") or c.lower().endswith("_id"))]

if len(numeric_cols) < 2:
    empty_state("Not enough numeric variables", "Correlation needs at least two numeric columns.", "hub")
    st.stop()

with card("settings"):
    c1, c2 = st.columns([1, 3])
    method = c1.radio("Method", ["Pearson", "Spearman", "Kendall"], key="cor_method",
                      help="Pearson: linear · Spearman: monotonic rank · Kendall: rank concordance (robust, small samples)")
    cols = c2.multiselect("Variables", numeric_cols, default=default_cols or numeric_cols, key="cor_cols")
    alpha = c2.select_slider("Significance level (α)", [0.01, 0.05, 0.10], value=0.05, key="cor_alpha")

if len(cols) < 2:
    st.warning("Select at least two variables.")
    st.stop()

matrix = calculate_correlation(df, method, cols)["correlation_matrix"]
pairs = correlation_pairs(df, cols, method)

if not pairs.empty:
    strongest = pairs.iloc[0]
    sig_count = int((pairs["p-value"] < alpha).sum())
    kpi_cards([
        {"label": "Variable pairs", "value": len(pairs), "icon": "hub", "tone": "indigo"},
        {"label": f"Significant at α={alpha}", "value": sig_count, "icon": "verified", "tone": "mint",
         "delta": f"{sig_count / len(pairs) * 100:.0f}% of pairs"},
        {"label": "Strongest pair", "value": f"{strongest['Coefficient']:+.3f}", "icon": "bolt", "tone": "coral",
         "delta": f"{strongest['Variable A']} ↔ {strongest['Variable B']}"},
        {"label": "Mean |r|", "value": f"{pairs['|r|'].mean():.3f}", "icon": "functions", "tone": "blue",
         "delta": strength_label(pairs["|r|"].mean())},
    ])
    save_result("correlation", f"{method} Correlation", "Correlation", {
        "Method": method, "Variables": len(cols), "Pairs": len(pairs), "Significant pairs": sig_count,
        "Strongest pair": f"{strongest['Variable A']} ↔ {strongest['Variable B']} (r = {strongest['Coefficient']:.3f})"},
        tables={"Correlation matrix": matrix.round(4).reset_index().rename(columns={"index": "Variable"}),
                "Pairs": pairs.drop(columns="|r|").round(4)})

left, right = st.columns([1.35, 1], gap="medium")
with left:
    with card("heat"):
        section(f"{method} Correlation Matrix", "Purple = positive · coral = negative")
        fig = px.imshow(matrix.round(2), text_auto=True, color_continuous_scale=DIV_SCALE, zmin=-1, zmax=1,
                        aspect="auto")
        fig.update_traces(hovertemplate="%{x} ↔ %{y}<br>r = %{z:.3f}<extra></extra>")
        fig.update_coloraxes(colorbar=dict(thickness=10, len=0.8, outlinewidth=0))
        show_fig(style_fig(fig, height=max(360, 46 * len(cols) + 80), legend=False))

with right:
    with card("pairs"):
        section("Ranked Relationships", "Sorted by absolute coefficient")
        if pairs.empty:
            st.info("Not enough valid data to compute pairwise correlations.")
        else:
            view = pairs.drop(columns="|r|").copy()
            view["Sig."] = view["p-value"].apply(lambda p: "✓" if p < alpha else "")
            st.dataframe(view, width="stretch", hide_index=True, height=max(360, 46 * len(cols) + 40),
                         column_config={
                             "Coefficient": st.column_config.NumberColumn(format="%+.3f"),
                             "p-value": st.column_config.NumberColumn(format="%.4f"),
                         })

with card("scatter"):
    section("Relationship Explorer", "Scatter plot with OLS trend line")
    c1, c2, c3 = st.columns(3)
    x = c1.selectbox("X variable", cols, key="cor_x",
                     index=cols.index(pairs.iloc[0]["Variable A"]) if not pairs.empty else 0)
    y_options = [c for c in cols if c != x]
    default_y = pairs.iloc[0]["Variable B"] if not pairs.empty and pairs.iloc[0]["Variable B"] in y_options else y_options[0]
    y = c2.selectbox("Y variable", y_options, key="cor_y", index=y_options.index(default_y))
    others = [c for c in df.columns if c not in numeric_cols and df[c].nunique() <= 12]
    color = c3.selectbox("Colour by (optional)", ["None"] + others, key="cor_color")
    plot_df = df[[x, y] + ([color] if color != "None" else [])].dropna()
    fig = px.scatter(plot_df, x=x, y=y, color=None if color == "None" else color, trendline="ols",
                     trendline_scope="overall", color_discrete_sequence=PALETTE,
                     trendline_color_override=PALETTE[2])
    if color == "None":
        fig.update_traces(marker=dict(color=PRIMARY, size=8, opacity=0.65), selector=dict(mode="markers"))
    show_fig(style_fig(fig, height=400))
    row = pairs[((pairs["Variable A"] == x) & (pairs["Variable B"] == y)) |
                ((pairs["Variable A"] == y) & (pairs["Variable B"] == x))]
    if not row.empty:
        r = row.iloc[0]
        kind = "good" if r["p-value"] < alpha else "info"
        st.markdown(
            f"{method} coefficient **{r['Coefficient']:+.3f}** · p = {fmt_p(r['p-value'])} · n = {r['N']} &nbsp; "
            f"{badge(r['Strength'] + ' ' + r['Direction'].lower(), kind)} "
            f"{badge('Significant' if r['p-value'] < alpha else 'Not significant', kind)}",
            unsafe_allow_html=True)
    st.caption("Correlation does not imply causation.")

footer()
