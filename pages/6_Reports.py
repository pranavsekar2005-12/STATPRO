from datetime import datetime

import streamlit as st

from modules.data_quality import analyze_data_quality
from modules.descriptive import calculate_descriptive_statistics
from modules.report import build_excel, build_pdf
from modules.shared import get_dataset, get_results, save_result
from modules.ui import (
    badge, card, dataset_chip, empty_state, footer, icon, kpi_cards, page_header, section,
)

df = get_dataset()
page_header("Reports & Export", "Assemble your analyses into a professional PDF or Excel report.",
            eyebrow="Output",
            right_html=dataset_chip(st.session_state.statpro_filename, len(df)) if df is not None else "")

if df is None:
    empty_state("No dataset loaded", "Upload a CSV or Excel file in the sidebar, or load the demo dataset.")
    st.stop()

# Make sure the core sections are always available, even if those pages were never opened.
results = get_results()
if "quality" not in results:
    q = analyze_data_quality(df)
    save_result("quality", "Data Quality Assessment", "Data Quality", {
        "Records": q["total_rows"], "Variables": q["total_columns"], "Missing cells": q["missing_cells"],
        "Duplicate rows": q["duplicate_count"], "Potential outliers": sum(q["outlier_counts"].values()),
        "Quality score": f"{q['quality_score']}%"}, tables={"Variable profile": q["profile"].reset_index()})
if "descriptive" not in results:
    try:
        d = calculate_descriptive_statistics(df)
        save_result("descriptive", "Descriptive Statistics", "Descriptive",
                    {"Numeric variables": len(d["statistics"]), "Categorical variables": len(d["frequency_tables"])},
                    tables={"Summary statistics": d["statistics"].round(4).reset_index().rename(columns={"index": "Variable"})})
    except ValueError:
        pass
results = get_results()

counts = {}
for r in results.values():
    counts[r["category"]] = counts.get(r["category"], 0) + 1

kpi_cards([
    {"label": "Analyses captured", "value": len(results), "icon": "inventory_2", "tone": "indigo"},
    {"label": "Hypothesis tests", "value": counts.get("Hypothesis Test", 0), "icon": "science", "tone": "coral"},
    {"label": "Models", "value": counts.get("Regression", 0), "icon": "trending_up", "tone": "mint"},
    {"label": "Data changes", "value": len(st.session_state.statpro_log), "icon": "cleaning_services",
     "tone": "yellow", "delta": "cleaning steps applied"},
])

left, right = st.columns([1.5, 1], gap="medium")

with left:
    with card("sections"):
        section("Report Contents", "Choose which analyses to include. Run tests on other pages to add more.")
        selected = {}
        for key, r in results.items():
            c1, c2 = st.columns([0.08, 0.92], vertical_alignment="center")
            on = c1.checkbox(r["title"], value=True, key=f"rep_{key}", label_visibility="collapsed")
            c2.markdown(f"**{r['title']}** &nbsp; {badge(r['category'])} "
                        f"<span style='color:#B5B5C8;font-size:.75rem'>{r['timestamp']}</span>",
                        unsafe_allow_html=True)
            if on:
                selected[key] = r
        if not any(r["category"] in ("Hypothesis Test", "Regression", "Correlation") for r in results.values()):
            st.info("Tip: run a hypothesis test, correlation or regression to include those results here.",
                    icon=":material/lightbulb:")
        st.write("")
        nav = st.columns(3)
        nav[0].page_link("pages/3_Hypothesis_Testing.py", label="Hypothesis tests", icon=":material/science:")
        nav[1].page_link("pages/4_Correlation_Analysis.py", label="Correlation", icon=":material/hub:")
        nav[2].page_link("pages/5_Regression_Analysis.py", label="Regression", icon=":material/trending_up:")

    with card("preview"):
        section("Preview", "Summary of each selected section")
        if not selected:
            st.caption("No sections selected.")
        for r in selected.values():
            with st.expander(r["title"], icon=":material/article:"):
                st.dataframe({"Metric": list(r["summary"].keys()), "Value": list(r["summary"].values())},
                             width="stretch", hide_index=True)
                if r.get("interpretation"):
                    st.caption(r["interpretation"])
                for tname, table in r["tables"].items():
                    st.markdown(f"**{tname}**")
                    st.dataframe(table, width="stretch", hide_index=True, height=min(300, 38 + 35 * len(table)))

with right:
    with card("settings"):
        section("Report Details")
        title = st.text_input("Report title", value=f"Statistical Analysis Report — {st.session_state.statpro_filename}")
        author = st.text_input("Prepared by", placeholder="Your name or team")
        notes = st.text_area("Executive notes", placeholder="Key findings, context or recommendations…", height=110)
        include_data = st.toggle("Include full dataset in Excel export", value=True)

    overview = {
        "Dataset": st.session_state.statpro_filename,
        "Records": f"{len(df):,}",
        "Variables": df.shape[1],
        "Numeric variables": len(df.select_dtypes(include='number').columns),
        "Missing cells": int(df.isnull().sum().sum()),
        "Duplicate rows": int(df.duplicated().sum()),
        "Cleaning steps": "; ".join(st.session_state.statpro_log) or "None (original data)",
        "Report date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M")

    with card("export"):
        section("Download", "All exports reflect the current working dataset")
        try:
            pdf = build_pdf(title, author, notes, overview, selected, df.head(10))
            st.download_button("PDF report", pdf, f"statpro_report_{stamp}.pdf", "application/pdf",
                               type="primary", icon=":material/picture_as_pdf:", width="stretch")
        except Exception as error:  # noqa: BLE001
            st.error(f"PDF generation failed: {error}")
        try:
            xlsx = build_excel(df, overview, selected, include_data)
            st.download_button("Excel workbook", xlsx, f"statpro_report_{stamp}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               icon=":material/table_view:", width="stretch")
        except Exception as error:  # noqa: BLE001
            st.error(f"Excel generation failed: {error}")
        st.download_button("Working dataset (CSV)", df.to_csv(index=False).encode("utf-8"),
                           f"statpro_data_{stamp}.csv", "text/csv", icon=":material/download:", width="stretch")
        st.markdown(f"<div style='color:#8A8AA0;font-size:.78rem;margin-top:6px'>{icon('info', 14)} "
                    f"{len(selected)} section(s) selected</div>", unsafe_allow_html=True)

footer()
