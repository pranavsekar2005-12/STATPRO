
from scipy import stats
from statsmodels.stats.oneway import anova_oneway
import pandas as pd


def perform_t_test(df, group_column, value_column):
    """Perform an independent two-sample t-test."""

    groups = df[[group_column, value_column]].dropna()
    categories = groups[group_column].unique()

    if len(categories) != 2:
        raise ValueError("The grouping column must contain exactly two groups.")

    group1 = groups.loc[
        groups[group_column] == categories[0], value_column
    ]

    group2 = groups.loc[
        groups[group_column] == categories[1], value_column
    ]

    result = stats.ttest_ind(group1, group2, equal_var=False)

    return {
        "test": "Welch's Independent T-Test",
        "group_1": str(categories[0]),
        "group_2": str(categories[1]),
        "mean_1": group1.mean(),
        "mean_2": group2.mean(),
        "t_statistic": result.statistic,
        "p_value": result.pvalue,
        "significant": result.pvalue < 0.05,
    }


def perform_anova(df, group_column, value_column):
    """Perform a one-way ANOVA across three or more groups."""

    groups = df[[group_column, value_column]].dropna()

    samples = [
        group[value_column].to_numpy()
        for _, group in groups.groupby(group_column)
    ]

    if len(samples) < 2:
        raise ValueError("ANOVA requires at least two groups.")

    result = stats.f_oneway(*samples)

    return {
        "test": "One-Way ANOVA",
        "f_statistic": result.statistic,
        "p_value": result.pvalue,
        "significant": result.pvalue < 0.05,
    }


def perform_chi_square(df, column1, column2):
    """Perform a Chi-square test of independence."""

    contingency_table = pd.crosstab(
        df[column1],
        df[column2]
    )

    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        raise ValueError("Both columns must contain at least two categories.")

    chi2, p_value, degrees_of_freedom, expected = (
        stats.chi2_contingency(contingency_table)
    )

    return {
        "test": "Chi-Square Test of Independence",
        "chi_square": chi2,
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "contingency_table": contingency_table,
        "expected_frequencies": expected,
    }
