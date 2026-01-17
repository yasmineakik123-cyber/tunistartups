import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


CATEGORICAL_COLS = [
    "industry",
    "business_model",
    "market_size",
    "competition_level",
    "customer_traction",
]

NUMERIC_COLS = [
    "team_size",
    "founder_experience_years",
    "has_technical_cofounder",
    "mvp_ready",
    "months_since_start",
    "monthly_growth_rate_pct",
    "initial_capital_tnd",
    "monthly_burn_tnd",
    "revenue_tnd_current_month",
    "has_investor",
]

TARGET_CLASS = "reached_100k_proxy"
TARGET_MONTHS = "months_to_100k_proxy"


def _build_preprocessor():
    cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        transformers=[
            ("cat", cat, CATEGORICAL_COLS),
            ("num", "passthrough", NUMERIC_COLS),
        ]
    )


def _build_classifier(preprocessor):
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def _build_regressor(preprocessor):
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "reg",
                RandomForestRegressor(
                    n_estimators=300,
                    min_samples_leaf=2,
                    random_state=42,
                ),
            ),
        ]
    )


def main():
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "app" / "seed" / "data" / "tunistartups_plausible_200.csv"
    model_dir = base_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    features = CATEGORICAL_COLS + NUMERIC_COLS

    X = df[features]
    y = df[TARGET_CLASS]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = _build_classifier(_build_preprocessor())
    clf.fit(X_train, y_train)
    y_prob = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    df_pos = df[df[TARGET_CLASS] == 1].copy()
    X_pos = df_pos[features]
    y_pos = df_pos[TARGET_MONTHS]
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_pos, y_pos, test_size=0.2, random_state=42
    )

    reg = _build_regressor(_build_preprocessor())
    reg.fit(X_train_r, y_train_r)
    y_pred_r = reg.predict(X_test_r)
    mae = mean_absolute_error(y_test_r, y_pred_r)

    joblib.dump(clf, model_dir / "reach100k_clf.joblib")
    joblib.dump(reg, model_dir / "months100k_reg.joblib")

    print(f"AUC (reach 100k classifier): {auc:.3f}")
    print(f"MAE (months to 100k regressor): {mae:.2f}")


if __name__ == "__main__":
    main()
