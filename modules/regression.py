import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def _design_matrix(frame, feature_columns):
    """Numeric predictors stay numeric; categorical ones become dummy variables."""
    X = frame[feature_columns].copy()
    categorical = [c for c in feature_columns if not pd.api.types.is_numeric_dtype(X[c])]
    if categorical:
        X = pd.get_dummies(X, columns=categorical, drop_first=True, dtype=float)
    return X.apply(pd.to_numeric, errors="coerce").astype(float), categorical


def perform_linear_regression(df, target_column, feature_columns, test_size=0.20, random_state=42):
    """Train and evaluate a multiple linear regression model (OLS)."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")
    if not feature_columns:
        raise ValueError("Select at least one predictor variable.")
    if target_column in feature_columns:
        raise ValueError("The target cannot also be a predictor.")

    data = df[[target_column] + list(feature_columns)].copy()
    data[target_column] = pd.to_numeric(data[target_column], errors="coerce")
    data = data.dropna()

    if len(data) < 10:
        raise ValueError("At least 10 complete observations are required.")

    X, categorical = _design_matrix(data, list(feature_columns))
    y = data[target_column].astype(float)

    constant = [c for c in X.columns if X[c].nunique() < 2]
    if constant:
        raise ValueError(f"These predictors have no variation: {', '.join(constant)}")
    if y.nunique() < 2:
        raise ValueError("The target must contain at least two distinct values.")
    if X.shape[1] >= len(data) - 2:
        raise ValueError("Too many predictors for the number of observations.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    X_train_sm = sm.add_constant(X_train, has_constant="add")
    model = sm.OLS(y_train, X_train_sm).fit()

    X_test_sm = sm.add_constant(X_test, has_constant="add").reindex(columns=X_train_sm.columns)
    predictions = model.predict(X_test_sm)

    test_r2 = r2_score(y_test, predictions) if len(y_test) >= 2 else np.nan

    coef_table = pd.DataFrame({
        "Coefficient": model.params,
        "Std Error": model.bse,
        "t": model.tvalues,
        "p-value": model.pvalues,
        "CI 2.5%": model.conf_int()[0],
        "CI 97.5%": model.conf_int()[1],
    })

    return {
        "model": model,
        "target": target_column,
        "features": list(feature_columns),
        "categorical_features": categorical,
        "design_columns": list(X.columns),
        "n_obs": int(len(data)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "r_squared": model.rsquared,
        "adjusted_r_squared": model.rsquared_adj,
        "f_pvalue": model.f_pvalue,
        "test_mae": mean_absolute_error(y_test, predictions),
        "test_rmse": mean_squared_error(y_test, predictions) ** 0.5,
        "test_r_squared": test_r2,
        "predictions": pd.DataFrame({"Actual": y_test, "Predicted": predictions}),
        "fitted": pd.DataFrame({"Fitted": model.fittedvalues, "Residual": model.resid}),
        "coefficients": model.params,
        "p_values": model.pvalues,
        "coef_table": coef_table,
        "summary_text": model.summary().as_text(),
    }


def predict_single(result, values):
    """Predict the target for one set of predictor values (dict feature -> value)."""
    row = pd.DataFrame([values])
    cats = result["categorical_features"]
    if cats:
        row = pd.get_dummies(row, columns=cats, dtype=float)
    row = row.reindex(columns=result["design_columns"], fill_value=0.0).astype(float)
    row = sm.add_constant(row, has_constant="add").reindex(columns=result["model"].params.index, fill_value=0.0)
    pred = result["model"].get_prediction(row).summary_frame(alpha=0.05)
    return float(pred["mean"].iloc[0]), float(pred["obs_ci_lower"].iloc[0]), float(pred["obs_ci_upper"].iloc[0])
