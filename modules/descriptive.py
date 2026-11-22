import pandas as pd


def calculate_descriptive_statistics(df):
    """Calculate descriptive statistics for a dataset."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    numeric_data = df.select_dtypes(include="number")

    if numeric_data.empty:
        raise ValueError("The dataset has no numeric columns.")

    statistics = numeric_data.describe().T
    statistics["median"] = numeric_data.median()
    statistics["variance"] = numeric_data.var()
    statistics["range"] = numeric_data.max() - numeric_data.min()
    statistics["iqr"] = numeric_data.quantile(0.75) - numeric_data.quantile(0.25)
    statistics["cv %"] = (numeric_data.std() / numeric_data.mean().replace(0, pd.NA) * 100).astype(float)
    statistics["skewness"] = numeric_data.skew()
    statistics["kurtosis"] = numeric_data.kurt()
    statistics["missing"] = numeric_data.isnull().sum()

    categorical_data = df.select_dtypes(include=["object", "category", "bool", "string"])

    frequency_tables = {
        column: df[column].value_counts(dropna=False)
        for column in categorical_data.columns
    }

    return {
        "statistics": statistics,
        "frequency_tables": frequency_tables,
    }
