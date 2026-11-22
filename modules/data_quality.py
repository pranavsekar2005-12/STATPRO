import pandas as pd


def outlier_bounds(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def analyze_data_quality(df):
    """Generate a data quality summary for an uploaded dataset."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    missing_values = df.isnull().sum()
    missing_summary = missing_values[missing_values > 0]
    missing_cells = int(missing_values.sum())

    duplicate_count = int(df.duplicated().sum())

    numeric_columns = df.select_dtypes(include="number").columns
    numeric_summary = df[numeric_columns].describe().T if len(numeric_columns) else pd.DataFrame()

    outlier_counts = {}
    for column in numeric_columns:
        series = df[column].dropna()
        if series.empty:
            outlier_counts[column] = 0
            continue
        low, high = outlier_bounds(series)
        outlier_counts[column] = int(((series < low) | (series > high)).sum())

    profile = pd.DataFrame({
        "Type": df.dtypes.astype(str),
        "Non-Null": df.notnull().sum(),
        "Missing": missing_values,
        "Missing %": (missing_values / max(total_rows, 1) * 100).round(2),
        "Unique": df.nunique(dropna=True),
        "Outliers": pd.Series(outlier_counts).reindex(df.columns),
        "Example": [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "—" for c in df.columns],
    })
    profile.index.name = "Variable"

    completeness = 1 - missing_cells / total_cells if total_cells else 1
    uniqueness = 1 - duplicate_count / total_rows if total_rows else 1
    numeric_cells = int(df[numeric_columns].notna().sum().sum()) if len(numeric_columns) else 0
    validity = 1 - sum(outlier_counts.values()) / numeric_cells if numeric_cells else 1
    quality_score = round((0.5 * completeness + 0.3 * uniqueness + 0.2 * validity) * 100, 1)

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_cells": missing_cells,
        "missing_summary": missing_summary,
        "duplicate_count": duplicate_count,
        "numeric_summary": numeric_summary,
        "outlier_counts": outlier_counts,
        "profile": profile,
        "completeness": completeness,
        "uniqueness": uniqueness,
        "validity": validity,
        "quality_score": quality_score,
    }
