
import pandas as pd


def analyze_data_quality(df):
    """Generate a data quality summary for an uploaded dataset."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    total_rows = len(df)
    total_columns = len(df.columns)

    # Missing values
    missing_values = df.isnull().sum()
    missing_summary = missing_values[missing_values > 0]

    # Duplicate rows
    duplicate_count = int(df.duplicated().sum())

    # Numeric summary
    numeric_columns = df.select_dtypes(include="number").columns

    numeric_summary = df[numeric_columns].describe().T if len(numeric_columns) else pd.DataFrame()

    # Outlier counts using the IQR method
    outlier_counts = {}

    for column in numeric_columns:
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_counts[column] = int(
            ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
        )

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_summary": missing_summary,
        "duplicate_count": duplicate_count,
        "numeric_summary": numeric_summary,
        "outlier_counts": outlier_counts,
    }
