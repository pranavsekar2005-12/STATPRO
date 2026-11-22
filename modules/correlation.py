
import pandas as pd


def calculate_correlation(df, method="pearson"):
    """Calculate correlation between numeric variables."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    if method.lower() not in ["pearson", "spearman"]:
        raise ValueError("Method must be 'pearson' or 'spearman'.")

    numeric_data = df.select_dtypes(include="number")

    if numeric_data.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")

    correlation_matrix = numeric_data.corr(
        method=method.lower()
    )

    return {
        "method": method.title(),
        "correlation_matrix": correlation_matrix,
    }
