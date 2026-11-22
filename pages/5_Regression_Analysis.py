import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.regression import perform_linear_regression, predict_single
from modules.shared import get_dataset, save_result
from modules.ui import (
    PALETTE, PRIMARY, badge, card, dataset_chip, empty_state, fmt, fmt_p, footer, kpi_cards,
    page_header, section, show_fig, style_fig, verdict,
)

df = get_dataset()
page_header("Regression Analysis", "Build a multiple linear regression model, evaluate it and make predictions.",
            eyebrow="Analysis",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

numeric_cols = df.select_dtypes(include="number").columns.tolist()
if not numeric_cols:
    empty_state("No numeric target available", "Regression needs a numeric dependent variable.", "trending_up")
    st.stop()

candidate_predictors = [c for c in df.columns
                        if c in numeric_cols or 2 <= df[c].nunique() <= 20]

with card("setup"):
    section("Model Setup", "Ordinary least squares · categorical predictors are dummy-encoded automatically")
    c1, c2 = st.columns([1, 2.4])
    target = c1.selectbox("Target (dependent variable)", numeric_cols, index=len(numeric_cols) - 1, key="rg_target")
    options = [c for c in candidate_predictors if c != target]
    default = [c for c in options if c in numeric_cols and c.lower() != "id"][:3]
    features = c2.multiselect("Predictors (independent variables)", options, default=default, key="rg_feats")
    c3, c4, _ = st.columns([1, 1, 2.4])
    test_size = c3.slider("Test set size", 0.1, 0.5, 0.2, 0.05, key="rg_test", format="%.2f")
    seed = c4.number_input("Random seed", 0, 9999, 42, key="rg_seed")
    run = st.button("Train model", type="primary", icon=":material/model_training:", disabled=not features)

if run:
    try:
        res = perform_linear_regression(df, target, features, test_size, int(seed))
        st.session_state.res_rg = res
        save_result("regression", f"Linear Regression: {target}", "Regression", {
            "Target": target, "Predictors": ", ".join(features), "Observations": res["n_obs"],
            "R²": fmt(res["r_squared"], 4), "Adjusted R²": fmt(res["adjusted_r_squared"], 4),
            "Model p-value (F)": fmt_p(res["f_pvalue"]), "Test R²": fmt(res["test_r_squared"], 4),
            "Test RMSE": fmt(res["test_rmse"], 3), "Test MAE": fmt(res["test_mae"], 3)},
            tables={"Coefficients": res["coef_table"].round(5).reset_index().rename(columns={"index": "Term"})},
            interpretation=f"The model explains {res['r_squared'] * 100:.1f}% of the variance in {target} "
                           f"on the training data.")
    except Exception as error:  # noqa: BLE001
        st.error(str(error), icon=":material/error:")

res = st.session_state.get("res_rg")
if not res:
    st.write("")
    empty_state("No model trained yet", "Choose a target and predictors above, then click Train model.", "model_training")
    footer()
    st.stop()

st.write("")
if res["target"] != target or res["features"] != features:
    st.info(f"Showing the last trained model ({res['target']} ~ {' + '.join(res['features'])}). "
            "Click **Train model** to refit with the current selection.", icon=":material/info:")

r2 = res["r_squared"]
kpi_cards([
    {"label": "R² (train)", "value": f"{r2:.3f}", "icon": "insights", "tone": "indigo",
     "delta": f"Adjusted R² {res['adjusted_r_squared']:.3f}"},
    {"label": "R² (test)", "value": fmt(res["test_r_squared"], 3), "icon": "fact_check", "tone": "mint",
     "delta": f"{res['n_test']} held-out rows"},
    {"label": "RMSE (test)", "value": fmt(res["test_rmse"], 2), "icon": "straighten", "tone": "coral",
     "delta": f"MAE {fmt(res['test_mae'], 2)}"},
    {"label": "Observations", "value": f"{res['n_obs']:,}", "icon": "dataset", "tone": "blue",
     "delta": f"{res['n_train']} train · {res['n_test']} test"},
])

if res["f_pvalue"] < 0.05:
    verdict("sig", "The model is statistically significant",
            f"F-test p = {fmt_p(res['f_pvalue'])}. The predictors jointly explain "
            f"<b>{r2 * 100:.1f}%</b> of the variance in <b>{res['target']}</b>.")
else:
    verdict("nsig", "The model is not statistically significant",
            f"F-test p = {fmt_p(res['f_pvalue'])}. The predictors do not reliably explain {res['target']}.")

tab_coef, tab_fit, tab_pred, tab_sum = st.tabs([":material/table_chart: Coefficients", ":material/scatter_plot: Diagnostics",
                                                ":material/calculate: Predict", ":material/article: Full Summary"])

with tab_coef:
    c1, c2 = st.columns([1.2, 1], gap="medium")
    coef = res["coef_table"]
    with c1:
        with card("coefs"):
            section("Coefficient Estimates", "Effect of a one-unit change in each predictor, holding others constant")
            view = coef.copy()
            view["Significant"] = view["p-value"].apply(lambda p: "✓" if p < 0.05 else "")
            st.dataframe(view.style.format({c: "{:,.4f}" for c in coef.columns}), width="stretch")
            eq = " + ".join(f"{v:,.3f}·{k}" for k, v in res["coefficients"].items() if k != "const")
            st.caption(f"**{res['target']}** = {res['coefficients'].get('const', 0):,.3f} + {eq}")
    with c2:
        with card("coefplot"):
            section("Coefficient Plot", "Estimate with 95% confidence interval")
            cp = coef.drop(index="const", errors="ignore")
            colors = [PRIMARY if p < 0.05 else "#C9C9D6" for p in cp["p-value"]]
            fig = go.Figure(go.Scatter(
                x=cp["Coefficient"], y=cp.index, mode="markers", marker=dict(color=colors, size=11),
                error_x=dict(type="data", symmetric=False, array=cp["CI 97.5%"] - cp["Coefficient"],
                             arrayminus=cp["Coefficient"] - cp["CI 2.5%"], color="#B5B5C8", thickness=2),
                hovertemplate="%{y}: %{x:,.4f}<extra></extra>"))
            fig.add_vline(x=0, line_dash="dot", line_color=PALETTE[2])
            show_fig(style_fig(fig, height=max(260, 60 * len(cp) + 80), legend=False))
            st.markdown(f"{badge('Significant (p < 0.05)', 'info')} &nbsp; {badge('Not significant', 'warn')}",
                        unsafe_allow_html=True)

with tab_fit:
    c1, c2 = st.columns(2, gap="medium")
    pred = res["predictions"]
    with c1:
        with card("avp"):
            section("Actual vs Predicted", "Held-out test set — points on the line are perfect predictions")
            lo, hi = float(min(pred.min())), float(max(pred.max()))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color=PALETTE[2], dash="dash"),
                                     name="Perfect fit"))
            fig.add_trace(go.Scatter(x=pred["Actual"], y=pred["Predicted"], mode="markers", name="Test rows",
                                     marker=dict(color=PRIMARY, size=9, opacity=0.75)))
            fig.update_xaxes(title="Actual")
            fig.update_yaxes(title="Predicted")
            show_fig(style_fig(fig, height=360))
    with c2:
        with card("resid"):
            section("Residuals vs Fitted", "Training data — look for random scatter around zero")
            fit = res["fitted"]
            fig = go.Figure(go.Scatter(x=fit["Fitted"], y=fit["Residual"], mode="markers",
                                       marker=dict(color=PALETTE[1], size=7, opacity=0.65)))
            fig.add_hline(y=0, line_dash="dash", line_color=PALETTE[2])
            fig.update_xaxes(title="Fitted values")
            fig.update_yaxes(title="Residual")
            show_fig(style_fig(fig, height=360, legend=False))
    with card("residhist"):
        section("Residual Distribution")
        fig = go.Figure(go.Histogram(x=res["fitted"]["Residual"], marker_color=PRIMARY, opacity=0.8, nbinsx=30))
        show_fig(style_fig(fig, height=260, legend=False))

with tab_pred:
    with card("predict"):
        section("What-if Prediction", "Enter predictor values to estimate the target with a 95% prediction interval")
        inputs = {}
        cols = st.columns(min(3, len(res["features"])) or 1)
        for i, f in enumerate(res["features"]):
            col = cols[i % len(cols)]
            if f in res["categorical_features"]:
                inputs[f] = col.selectbox(f, sorted(df[f].dropna().astype(str).unique().tolist()), key=f"pr_{f}")
            else:
                s = pd.to_numeric(df[f], errors="coerce").dropna()
                inputs[f] = col.number_input(f, value=float(round(s.median(), 2)), key=f"pr_{f}")
        # categorical inputs must match original dtype for dummy column names
        for f in res["categorical_features"]:
            orig = df[f].dropna()
            match = orig[orig.astype(str) == inputs[f]]
            if len(match):
                inputs[f] = match.iloc[0]
        try:
            yhat, lo, hi = predict_single(res, inputs)
            st.markdown(
                f"""<div class="sp-hero" style="padding:22px 26px;margin:10px 0 0">
                      <div class="eyebrow">Predicted {res['target']}</div>
                      <h2 style="margin:4px 0">{yhat:,.2f}</h2>
                      <p>95% prediction interval: {lo:,.2f} — {hi:,.2f}</p></div>""",
                unsafe_allow_html=True)
        except Exception as error:  # noqa: BLE001
            st.error(f"Prediction failed: {error}")

with tab_sum:
    with card("summary"):
        section("Statsmodels OLS Summary")
        st.code(res["summary_text"], language=None)
        st.download_button("Download summary (.txt)", res["summary_text"].encode(), "regression_summary.txt",
                           icon=":material/download:")

footer()
