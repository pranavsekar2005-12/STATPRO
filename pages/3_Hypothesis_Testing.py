import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from modules.hypothesis import (
    perform_anova, perform_chi_square, perform_normality_test, perform_one_sample_t_test, perform_t_test,
)
from modules.shared import get_dataset, save_result
from modules.ui import (
    PALETTE, PRIMARY, SEQ_SCALE, card, dataset_chip, default_index, empty_state, fmt, fmt_p, footer, page_header,
    section, show_fig, stat_row, style_fig, verdict,
)

df = get_dataset()
page_header("Hypothesis Testing", "Test differences and associations with significance levels and effect sizes.",
            eyebrow="Analysis",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

numeric_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = [c for c in df.columns if c not in numeric_cols or df[c].nunique() <= 10]
cat_cols = [c for c in cat_cols if 2 <= df[c].nunique() <= 50]

with card("settings"):
    c1, c2 = st.columns([1, 2.5])
    alpha = c1.select_slider("Significance level (α)", options=[0.01, 0.05, 0.10], value=0.05, key="ht_alpha")
    c2.markdown(
        f"<div style='padding-top:28px;color:#8A8AA0;font-size:.88rem'>Results are significant when "
        f"<b>p &lt; {alpha}</b>, i.e. there is less than a {alpha * 100:.0f}% chance of observing such a result "
        f"if the null hypothesis were true.</div>", unsafe_allow_html=True)

st.write("")


def decision(sig, alt_text, null_text, p):
    if sig:
        verdict("sig", "Statistically significant — reject H₀", f"{alt_text} (p = {fmt_p(p)} &lt; α = {alpha}).")
    else:
        verdict("nsig", "Not significant — fail to reject H₀", f"{null_text} (p = {fmt_p(p)} ≥ α = {alpha}).")


def run_guard(fn):
    try:
        return fn()
    except Exception as error:  # noqa: BLE001
        st.error(str(error), icon=":material/error:")
        return None


t1, t2, t3, t4, t5 = st.tabs([":material/compare_arrows: Two-Sample T-Test", ":material/stacked_bar_chart: ANOVA",
                              ":material/grid_on: Chi-Square", ":material/adjust: One-Sample T-Test",
                              ":material/ssid_chart: Normality"])

# ------------------------------------------------------------------ t-test
with t1:
    if not numeric_cols or not cat_cols:
        empty_state("Not enough variables", "Needs one numeric and one categorical variable.", "compare_arrows")
    else:
        with card("tt_in"):
            section("Compare the means of two groups", "Welch's t-test does not assume equal variances")
            c1, c2, c3 = st.columns(3)
            value = c1.selectbox("Numeric variable", numeric_cols, index=default_index(numeric_cols), key="tt_val")
            group = c2.selectbox("Grouping variable", cat_cols, key="tt_grp")
            levels = df[group].dropna().unique().tolist()
            chosen = c3.multiselect("Two groups to compare", levels, default=levels[:2], max_selections=2, key="tt_lv")
            equal_var = st.toggle("Assume equal variances (Student's t-test)", key="tt_eq")
            go_btn = st.button("Run t-test", type="primary", icon=":material/play_arrow:", key="tt_run",
                               disabled=len(chosen) != 2)
        if go_btn:
            res = run_guard(lambda: perform_t_test(df, group, value, chosen, alpha, equal_var))
            if res:
                st.session_state.res_tt = res
                save_result("ttest", f"T-Test: {value} by {group}", "Hypothesis Test", {
                    "Test": res["test"], "Groups": f"{res['group_1']} vs {res['group_2']}",
                    f"Mean ({res['group_1']})": fmt(res["mean_1"], 3), f"Mean ({res['group_2']})": fmt(res["mean_2"], 3),
                    "t statistic": fmt(res["t_statistic"], 4), "p-value": fmt_p(res["p_value"]),
                    "Cohen's d": fmt(res["cohen_d"], 3), "Significant": "Yes" if res["significant"] else "No"},
                    interpretation=("Significant" if res["significant"] else "No significant") +
                    f" difference in {value} between {res['group_1']} and {res['group_2']} at α = {alpha}.")
        res = st.session_state.get("res_tt")
        if res:
            st.write("")
            with card("tt_out"):
                section(res["test"], f"{res['group_1']} (n={res['n_1']}) vs {res['group_2']} (n={res['n_2']})")
                decision(res["significant"],
                         f"The mean differs between <b>{res['group_1']}</b> and <b>{res['group_2']}</b>",
                         "There is no evidence that the group means differ", res["p_value"])
                stat_row([("t statistic", fmt(res["t_statistic"], 3)), ("p-value", fmt_p(res["p_value"])),
                          (f"Mean · {res['group_1']}", fmt(res["mean_1"], 2)),
                          (f"Mean · {res['group_2']}", fmt(res["mean_2"], 2)),
                          ("Cohen's d", fmt(res["cohen_d"], 3)), ("Effect size", res["effect_size"])])
                data = res["data"]
                gcol, vcol = data.columns[0], data.columns[1]
                fig = go.Figure()
                for i, g in enumerate([res["group_1"], res["group_2"]]):
                    vals = data.loc[data[gcol].astype(str) == g, vcol]
                    fig.add_trace(go.Box(y=vals, name=g, marker_color=PALETTE[i], boxmean="sd", boxpoints="all",
                                         jitter=0.35, pointpos=0, marker=dict(size=4, opacity=0.5)))
                show_fig(style_fig(fig, height=360, legend=False))

# ------------------------------------------------------------------ ANOVA
with t2:
    if not numeric_cols or not cat_cols:
        empty_state("Not enough variables", "Needs one numeric and one categorical variable.", "stacked_bar_chart")
    else:
        with card("an_in"):
            section("Compare means across groups", "One-way analysis of variance")
            c1, c2 = st.columns(2)
            value = c1.selectbox("Numeric variable", numeric_cols, index=default_index(numeric_cols), key="an_val")
            group = c2.selectbox("Grouping variable", cat_cols, key="an_grp",
                                 index=min(1, len(cat_cols) - 1))
            go_btn = st.button("Run ANOVA", type="primary", icon=":material/play_arrow:", key="an_run")
        if go_btn:
            res = run_guard(lambda: perform_anova(df, group, value, alpha))
            if res:
                res["group"], res["value"] = group, value
                st.session_state.res_an = res
                save_result("anova", f"ANOVA: {value} by {group}", "Hypothesis Test", {
                    "Test": res["test"], "F statistic": fmt(res["f_statistic"], 4),
                    "df": f"({res['df_between']}, {res['df_within']})", "p-value": fmt_p(res["p_value"]),
                    "Eta squared": fmt(res["eta_squared"], 4), "Levene p-value": fmt_p(res["levene_p"]),
                    "Significant": "Yes" if res["significant"] else "No"},
                    tables={"Group summary": res["group_summary"].round(4).reset_index()},
                    interpretation=("At least one group mean differs" if res["significant"] else
                                    "No significant difference among group means") + f" for {value} across {group}.")
        res = st.session_state.get("res_an")
        if res:
            st.write("")
            with card("an_out"):
                section(f"{res['value']} across {res['group']}", res["test"])
                decision(res["significant"], "At least one group mean is different from the others",
                         "There is no evidence that the group means differ", res["p_value"])
                stat_row([("F statistic", fmt(res["f_statistic"], 3)), ("p-value", fmt_p(res["p_value"])),
                          ("df", f"{res['df_between']}, {res['df_within']}"), ("η² (eta²)", fmt(res["eta_squared"], 3)),
                          ("Effect size", res["effect_size"]), ("Levene p", fmt_p(res["levene_p"]))])
                if res["levene_p"] < alpha:
                    st.caption(":material/warning: Levene's test suggests unequal variances — interpret with care.")
                c1, c2 = st.columns([1.3, 1])
                with c1:
                    gs = res["group_summary"].reset_index()
                    fig = go.Figure(go.Bar(
                        x=gs.iloc[:, 0].astype(str), y=gs["Mean"], marker_color=PALETTE[: len(gs)],
                        error_y=dict(type="data", array=gs["Std Dev"], color="#C9C9D6", thickness=1.5),
                        hovertemplate="%{x}<br>Mean: %{y:,.2f}<extra></extra>"))
                    show_fig(style_fig(fig, height=330, legend=False, title="Group means ± 1 SD"))
                with c2:
                    st.dataframe(res["group_summary"].style.format("{:,.2f}"), width="stretch")

# ------------------------------------------------------------------ Chi-square
with t3:
    if len(cat_cols) < 2:
        empty_state("Not enough variables", "Needs two categorical variables.", "grid_on")
    else:
        with card("cs_in"):
            section("Test association between two categorical variables", "Chi-square test of independence")
            c1, c2 = st.columns(2)
            a = c1.selectbox("First variable", cat_cols, key="cs_a")
            b = c2.selectbox("Second variable", [c for c in cat_cols if c != a], key="cs_b")
            go_btn = st.button("Run Chi-square", type="primary", icon=":material/play_arrow:", key="cs_run")
        if go_btn:
            res = run_guard(lambda: perform_chi_square(df, a, b, alpha))
            if res:
                res["a"], res["b"] = a, b
                st.session_state.res_cs = res
                save_result("chisq", f"Chi-Square: {a} × {b}", "Hypothesis Test", {
                    "Test": res["test"], "Chi-square": fmt(res["chi_square"], 4),
                    "df": res["degrees_of_freedom"], "p-value": fmt_p(res["p_value"]),
                    "Cramér's V": fmt(res["cramers_v"], 4), "Significant": "Yes" if res["significant"] else "No"},
                    tables={"Contingency table": res["contingency_table"].reset_index()},
                    interpretation=(f"{a} and {b} are associated" if res["significant"] else
                                    f"No significant association between {a} and {b}") + f" at α = {alpha}.")
        res = st.session_state.get("res_cs")
        if res:
            st.write("")
            with card("cs_out"):
                section(f"{res['a']} × {res['b']}", res["test"])
                decision(res["significant"], f"<b>{res['a']}</b> and <b>{res['b']}</b> are associated",
                         "The variables appear to be independent", res["p_value"])
                stat_row([("χ² statistic", fmt(res["chi_square"], 3)), ("p-value", fmt_p(res["p_value"])),
                          ("df", res["degrees_of_freedom"]), ("Cramér's V", fmt(res["cramers_v"], 3)),
                          ("Effect size", res["effect_size"])])
                if res["low_expected_share"] > 0.2:
                    st.caption(f":material/warning: {res['low_expected_share'] * 100:.0f}% of expected counts are below 5 "
                               "— the chi-square approximation may be unreliable.")
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.imshow(res["contingency_table"], text_auto=True, color_continuous_scale=SEQ_SCALE,
                                    aspect="auto")
                    fig.update_coloraxes(showscale=False)
                    show_fig(style_fig(fig, height=320, legend=False, title="Observed counts"))
                with c2:
                    fig = px.imshow(res["expected_frequencies"].round(1), text_auto=True,
                                    color_continuous_scale=[[0, "#FFF4EF"], [1, "#FF8F6B"]], aspect="auto")
                    fig.update_coloraxes(showscale=False)
                    show_fig(style_fig(fig, height=320, legend=False, title="Expected counts (if independent)"))

# ------------------------------------------------------------------ One-sample
with t4:
    if not numeric_cols:
        empty_state("No numeric variables", "Needs a numeric variable.", "adjust")
    else:
        with card("os_in"):
            section("Compare a sample mean to a reference value", "One-sample t-test")
            c1, c2 = st.columns(2)
            value = c1.selectbox("Numeric variable", numeric_cols, index=default_index(numeric_cols), key="os_val")
            mu = c2.number_input("Hypothesised mean (μ₀)", value=float(round(df[value].mean(), 2)), key="os_mu")
            go_btn = st.button("Run one-sample t-test", type="primary", icon=":material/play_arrow:", key="os_run")
        if go_btn:
            res = run_guard(lambda: perform_one_sample_t_test(df, value, mu, alpha))
            if res:
                res["value"] = value
                st.session_state.res_os = res
                save_result("onesample", f"One-Sample T-Test: {value} vs {mu}", "Hypothesis Test", {
                    "Sample mean": fmt(res["sample_mean"], 3), "μ₀": mu, "t statistic": fmt(res["t_statistic"], 4),
                    "p-value": fmt_p(res["p_value"]), f"{(1 - alpha) * 100:.0f}% CI":
                    f"[{fmt(res['ci_low'], 3)}, {fmt(res['ci_high'], 3)}]",
                    "Significant": "Yes" if res["significant"] else "No"})
        res = st.session_state.get("res_os")
        if res:
            st.write("")
            with card("os_out"):
                section(f"{res['value']} vs μ₀ = {fmt(res['population_mean'], 2)}", res["test"])
                decision(res["significant"], "The population mean differs from the hypothesised value",
                         "The sample is consistent with the hypothesised mean", res["p_value"])
                stat_row([("Sample mean", fmt(res["sample_mean"], 2)), ("t statistic", fmt(res["t_statistic"], 3)),
                          ("p-value", fmt_p(res["p_value"])), ("CI low", fmt(res["ci_low"], 2)),
                          ("CI high", fmt(res["ci_high"], 2)), ("Cohen's d", fmt(res["cohen_d"], 3))])
                fig = go.Figure(go.Histogram(x=res["sample"], marker_color=PRIMARY, opacity=0.8, nbinsx=30))
                fig.add_vrect(x0=res["ci_low"], x1=res["ci_high"], fillcolor="rgba(96,91,255,.12)", line_width=0)
                fig.add_vline(x=res["population_mean"], line_color=PALETTE[2], line_dash="dash",
                              annotation_text="μ₀", annotation_font_color=PALETTE[2])
                fig.add_vline(x=res["sample_mean"], line_color=PALETTE[4], annotation_text="x̄",
                              annotation_font_color=PALETTE[4])
                show_fig(style_fig(fig, height=320, legend=False))

# ------------------------------------------------------------------ Normality
with t5:
    if not numeric_cols:
        empty_state("No numeric variables", "Needs a numeric variable.", "ssid_chart")
    else:
        with card("nm_in"):
            section("Check whether a variable is normally distributed", "Shapiro–Wilk test with Q-Q plot")
            value = st.selectbox("Numeric variable", numeric_cols, index=default_index(numeric_cols), key="nm_val")
            go_btn = st.button("Run normality test", type="primary", icon=":material/play_arrow:", key="nm_run")
        if go_btn:
            res = run_guard(lambda: perform_normality_test(df, value, alpha))
            if res:
                res["value"] = value
                st.session_state.res_nm = res
                save_result(f"normality_{value}", f"Normality: {value}", "Hypothesis Test", {
                    "W statistic": fmt(res["w_statistic"], 4), "p-value": fmt_p(res["p_value"]),
                    "Skewness": fmt(res["skewness"], 3), "Kurtosis": fmt(res["kurtosis"], 3),
                    "Normal": "Yes" if res["normal"] else "No"})
        res = st.session_state.get("res_nm")
        if res:
            st.write("")
            with card("nm_out"):
                section(f"Normality of {res['value']}", f"{res['test']} · n = {res['n']}")
                if res["normal"]:
                    verdict("sig", "Consistent with a normal distribution",
                            f"No evidence of non-normality (p = {fmt_p(res['p_value'])} ≥ α = {alpha}).")
                else:
                    verdict("warn", "Not normally distributed",
                            f"Shapiro–Wilk rejects normality (p = {fmt_p(res['p_value'])} &lt; α = {alpha}). "
                            "Consider non-parametric tests or a transformation.")
                stat_row([("W statistic", fmt(res["w_statistic"], 4)), ("p-value", fmt_p(res["p_value"])),
                          ("Skewness", fmt(res["skewness"], 3)), ("Excess kurtosis", fmt(res["kurtosis"], 3))])
                c1, c2 = st.columns(2)
                s = np.sort(res["sample"].to_numpy())
                theo = stats.norm.ppf((np.arange(1, len(s) + 1) - 0.5) / len(s))
                with c1:
                    fig = go.Figure(go.Scatter(x=theo, y=s, mode="markers", marker=dict(color=PRIMARY, size=6, opacity=.7)))
                    slope, intercept = np.polyfit(theo, s, 1)
                    fig.add_trace(go.Scatter(x=theo, y=slope * theo + intercept, mode="lines",
                                             line=dict(color=PALETTE[2], dash="dash")))
                    fig.update_xaxes(title="Theoretical quantiles")
                    fig.update_yaxes(title="Sample quantiles")
                    show_fig(style_fig(fig, height=330, legend=False, title="Q-Q plot"))
                with c2:
                    x = np.linspace(s.min(), s.max(), 200)
                    fig = go.Figure(go.Histogram(x=s, histnorm="probability density", marker_color=PRIMARY,
                                                 opacity=0.7, nbinsx=30))
                    fig.add_trace(go.Scatter(x=x, y=stats.norm.pdf(x, s.mean(), s.std()), mode="lines",
                                             line=dict(color=PALETTE[2], width=3)))
                    show_fig(style_fig(fig, height=330, legend=False, title="Histogram vs normal curve"))

footer()
