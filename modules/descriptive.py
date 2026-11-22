
import pandas as pd


def calculate_descriptive_statistics(df):
    """Calculate descriptive statistics for a dataset."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    numeric_data = df.select_dtypes(include="number")

    if numeric_data.empty:
        raise ValueError("The dataset has no numeric columns.")

    # Overall descriptive statistics
    statistics = numeric_data.describe().T

    # Additional statistics
    statistics["median"] = numeric_data.median()
    statistics["variance"] = numeric_data.var()
    statistics["range"] = numeric_data.max() - numeric_data.min()
    statistics["missing"] = numeric_data.isnull().sum()

    # Categorical frequency tables
    categorical_data = df.select_dtypes(
        include=["object", "category", "bool"]
    )

    frequency_tables = {
        column: df[column].value_counts(dropna=False)
        for column in categorical_data.columns
    }

    return {
        "statistics": statistics,
        "frequency_tables": frequency_tables,
    }
