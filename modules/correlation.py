import pandas as pd
from scipy import stats

METHODS = ["pearson", "spearman", "kendall"]


def calculate_correlation(df, method="pearson", columns=None):
    """Correlation matrix between numeric variables."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    method = method.lower()
    if method not in METHODS:
        raise ValueError("Method must be 'pearson', 'spearman' or 'kendall'.")

    numeric_data = df.select_dtypes(include="number")
    if columns:
        numeric_data = numeric_data[columns]

    if numeric_data.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")

    return {
        "method": method.title(),
        "correlation_matrix": numeric_data.corr(method=method),
    }


def strength_label(r):
    r = abs(r)
    if r >= 0.8:
        return "Very strong"
    if r >= 0.6:
        return "Strong"
    if r >= 0.4:
        return "Moderate"
    if r >= 0.2:
        return "Weak"
    return "Very weak"


def correlation_pairs(df, columns, method="pearson"):
    """Every pair of variables with coefficient, p-value and strength label."""

    func = {"pearson": stats.pearsonr, "spearman": stats.spearmanr, "kendall": stats.kendalltau}[method.lower()]
    rows = []
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            pair = df[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(pair) < 3 or pair[a].nunique() < 2 or pair[b].nunique() < 2:
                continue
            res = func(pair[a], pair[b])
            r, p = float(res[0]), float(res[1])
            rows.append({
                "Variable A": a,
                "Variable B": b,
                "Coefficient": r,
                "|r|": abs(r),
                "p-value": p,
                "Direction": "Positive" if r > 0 else "Negative",
                "Strength": strength_label(r),
                "N": len(pair),
            })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("|r|", ascending=False).reset_index(drop=True)
    return out
