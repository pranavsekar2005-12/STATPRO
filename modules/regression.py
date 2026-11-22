
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def perform_linear_regression(df, target_column, feature_columns):
    """Train and evaluate a multiple linear regression model."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    if not feature_columns:
        raise ValueError("Select at least one predictor variable.")

    if target_column in feature_columns:
        raise ValueError("The target cannot also be a predictor.")

    selected_columns = [target_column] + feature_columns

    data = df[selected_columns].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    if len(data) < 10:
        raise ValueError("At least 10 complete numeric observations are required.")

    X = data[feature_columns]
    y = data[target_column]

    if X.nunique().min() < 2:
        raise ValueError("Each predictor must contain at least two distinct values.")

    if y.nunique() < 2:
        raise ValueError("The target must contain at least two distinct values.")

    # Split data before fitting to evaluate unseen observations
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # Fit model using training data only
    X_train_sm = sm.add_constant(X_train, has_constant="add")
    model = sm.OLS(y_train, X_train_sm).fit()

    # Predict on held-out test data
    X_test_sm = sm.add_constant(X_test, has_constant="add")
    X_test_sm = X_test_sm.reindex(columns=X_train_sm.columns)

    predictions = model.predict(X_test_sm)

    return {
        "model": model,
        "r_squared": model.rsquared,
        "adjusted_r_squared": model.rsquared_adj,
        "test_mae": mean_absolute_error(y_test, predictions),
        "test_rmse": mean_squared_error(y_test, predictions) ** 0.5,
        "test_r_squared": r2_score(y_test, predictions),
        "predictions": pd.DataFrame({
            "Actual": y_test,
            "Predicted": predictions
        }),
        "coefficients": model.params,
        "p_values": model.pvalues,
    }
