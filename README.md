# STATPRO — Statistical Analysis & Reporting

A Streamlit workspace for profiling, analysing and reporting on tabular data, with a clean SaaS-dashboard UI
(visual language inspired by the *Base — SaaS Dashboard UI Kit* by Jiangyu on Figma Community, CC BY 4.0).

## Features

| Page | What it does |
|---|---|
| **Dashboard** | KPI tiles, distribution explorer, variable-type donut, completeness bars, category breakdown, quick actions |
| **Data Quality** | Quality score gauge, missing-value chart & map, variable profile, IQR outliers, duplicates, one-click cleaning (dedupe, drop/fill missing, remove outliers) with change log and reset |
| **Descriptive Statistics** | Per-variable explorer (histogram + box, shape & spread), full summary table (CSV export), categorical frequencies, group comparison (violin) |
| **Hypothesis Testing** | Welch/Student t-test, one-way ANOVA (η², Levene), Chi-square (Cramér's V), one-sample t-test, Shapiro–Wilk normality with Q-Q plot; adjustable α |
| **Correlation** | Pearson / Spearman / Kendall heatmap, ranked pairs with p-values, scatter explorer with OLS trend line |
| **Regression** | Multiple OLS with automatic dummy encoding, train/test metrics, coefficient plot with 95% CI, diagnostics, what-if prediction with prediction interval, full statsmodels summary |
| **Reports & Export** | Pick analyses to include, then download a branded PDF report, a multi-sheet Excel workbook, or the cleaned CSV |

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

Then open http://localhost:8501. Upload a CSV/Excel file in the sidebar, or click **Use demo dataset**
(`data/sample_customers.csv`, 240 rows with deliberate missing values, duplicates and outliers).

## Project layout

```
app.py                 # entry point + navigation
pages/                 # one script per page
modules/               # analysis logic (stats) + ui.py (design system) + report.py (PDF/Excel)
assets/                # style.css, logo
.streamlit/config.toml # theme
```
