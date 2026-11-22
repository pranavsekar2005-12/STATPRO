import numpy as np
import pandas as pd
from scipy import stats


def _effect_label(value, small, medium, large):
    value = abs(value)
    if value >= large:
        return "Large"
    if value >= medium:
        return "Medium"
    if value >= small:
        return "Small"
    return "Negligible"


def perform_t_test(df, group_column, value_column, groups=None, alpha=0.05, equal_var=False):
    """Independent two-sample t-test (Welch by default)."""

    data = df[[group_column, value_column]].dropna().copy()
    data[value_column] = pd.to_numeric(data[value_column], errors="coerce")
    data = data.dropna()

    categories = list(groups) if groups is not None else list(data[group_column].unique())

    if len(categories) != 2:
        raise ValueError("The t-test needs exactly two groups to compare.")

    group1 = data.loc[data[group_column] == categories[0], value_column]
    group2 = data.loc[data[group_column] == categories[1], value_column]

    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group needs at least two observations.")

    result = stats.ttest_ind(group1, group2, equal_var=equal_var)

    pooled_sd = np.sqrt(((len(group1) - 1) * group1.var() + (len(group2) - 1) * group2.var())
                        / (len(group1) + len(group2) - 2))
    cohen_d = (group1.mean() - group2.mean()) / pooled_sd if pooled_sd > 0 else np.nan

    return {
        "test": "Welch's Independent T-Test" if not equal_var else "Student's Independent T-Test",
        "group_1": str(categories[0]),
        "group_2": str(categories[1]),
        "n_1": int(len(group1)),
        "n_2": int(len(group2)),
        "mean_1": group1.mean(),
        "mean_2": group2.mean(),
        "std_1": group1.std(),
        "std_2": group2.std(),
        "t_statistic": result.statistic,
        "p_value": result.pvalue,
        "cohen_d": cohen_d,
        "effect_size": _effect_label(cohen_d, 0.2, 0.5, 0.8),
        "alpha": alpha,
        "significant": result.pvalue < alpha,
        "data": data[data[group_column].isin(categories)],
    }


def perform_anova(df, group_column, value_column, alpha=0.05):
    """One-way ANOVA across two or more groups."""

    data = df[[group_column, value_column]].dropna().copy()
    data[value_column] = pd.to_numeric(data[value_column], errors="coerce")
    data = data.dropna()

    grouped = [(name, g[value_column].to_numpy()) for name, g in data.groupby(group_column)]
    grouped = [(name, s) for name, s in grouped if len(s) >= 2]
    samples = [s for _, s in grouped]

    if len(samples) < 2:
        raise ValueError("ANOVA requires at least two groups with two or more observations each.")

    result = stats.f_oneway(*samples)

    grand_mean = data[value_column].mean()
    ss_between = sum(len(s) * (s.mean() - grand_mean) ** 2 for s in samples)
    ss_total = ((data[value_column] - grand_mean) ** 2).sum()
    eta_sq = ss_between / ss_total if ss_total > 0 else np.nan

    levene = stats.levene(*samples)

    summary = (
        data.groupby(group_column)[value_column]
        .agg(["count", "mean", "std", "min", "max"])
        .rename(columns={"count": "N", "mean": "Mean", "std": "Std Dev", "min": "Min", "max": "Max"})
    )

    return {
        "test": "One-Way ANOVA",
        "f_statistic": result.statistic,
        "p_value": result.pvalue,
        "df_between": len(samples) - 1,
        "df_within": len(data) - len(samples),
        "eta_squared": eta_sq,
        "effect_size": _effect_label(eta_sq, 0.01, 0.06, 0.14),
        "levene_p": levene.pvalue,
        "group_summary": summary,
        "alpha": alpha,
        "significant": result.pvalue < alpha,
        "data": data,
    }


def perform_chi_square(df, column1, column2, alpha=0.05):
    """Chi-square test of independence."""

    contingency_table = pd.crosstab(df[column1], df[column2])

    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        raise ValueError("Both columns must contain at least two categories.")

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    n = contingency_table.to_numpy().sum()
    k = min(contingency_table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k)) if n and k else np.nan
    low_expected = float((expected < 5).mean())

    return {
        "test": "Chi-Square Test of Independence",
        "chi_square": chi2,
        "degrees_of_freedom": dof,
        "p_value": p_value,
        "cramers_v": cramers_v,
        "effect_size": _effect_label(cramers_v, 0.1, 0.3, 0.5),
        "low_expected_share": low_expected,
        "alpha": alpha,
        "significant": p_value < alpha,
        "contingency_table": contingency_table,
        "expected_frequencies": pd.DataFrame(
            expected, index=contingency_table.index, columns=contingency_table.columns
        ),
    }


def perform_one_sample_t_test(df, column, population_mean, alpha=0.05):
    """Compare a sample mean against a hypothesised population mean."""

    sample = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(sample) < 2:
        raise ValueError("At least two observations are required.")

    result = stats.ttest_1samp(sample, population_mean)
    sd = sample.std()
    ci = stats.t.interval(1 - alpha, len(sample) - 1, loc=sample.mean(), scale=stats.sem(sample))

    return {
        "test": "One-Sample T-Test",
        "n": int(len(sample)),
        "sample_mean": sample.mean(),
        "population_mean": population_mean,
        "t_statistic": result.statistic,
        "p_value": result.pvalue,
        "ci_low": ci[0],
        "ci_high": ci[1],
        "cohen_d": (sample.mean() - population_mean) / sd if sd > 0 else np.nan,
        "alpha": alpha,
        "significant": result.pvalue < alpha,
        "sample": sample,
    }


def perform_normality_test(df, column, alpha=0.05):
    """Shapiro–Wilk normality test (uses up to 5,000 observations)."""

    sample = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(sample) < 3:
        raise ValueError("At least three observations are required.")
    if len(sample) > 5000:
        sample = sample.sample(5000, random_state=42)

    result = stats.shapiro(sample)

    return {
        "test": "Shapiro–Wilk Normality Test",
        "n": int(len(sample)),
        "w_statistic": result.statistic,
        "p_value": result.pvalue,
        "skewness": stats.skew(sample),
        "kurtosis": stats.kurtosis(sample),
        "alpha": alpha,
        "normal": result.pvalue >= alpha,
        "sample": sample,
    }
