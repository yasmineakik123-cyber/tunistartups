import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


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


_MODEL_CACHE = {"clf": None, "reg": None}


def load_models(model_dir: str | Path):
    model_dir = Path(model_dir)
    if _MODEL_CACHE["clf"] is None:
        _MODEL_CACHE["clf"] = joblib.load(model_dir / "reach100k_clf.joblib")
    if _MODEL_CACHE["reg"] is None:
        _MODEL_CACHE["reg"] = joblib.load(model_dir / "months100k_reg.joblib")
    return _MODEL_CACHE["clf"], _MODEL_CACHE["reg"]


def _band_for_probability(p: float):
    if p >= 0.80:
        return "High", {"min": 1.5, "max": 2.5}
    if 0.60 <= p <= 0.79:
        return "Medium-High", {"min": 2.0, "max": 3.5}
    if 0.40 <= p <= 0.59:
        return "Medium", {"min": 3.0, "max": 5.0}
    if 0.25 <= p <= 0.39:
        return "Low-Medium", {"min": 5.0, "max": 7.0}
    return "Low", None


def _format_feature_name(name: str) -> str:
    if "_" in name and any(name.startswith(c + "_") for c in CATEGORICAL_COLS):
        base, value = name.split("_", 1)
        return f"{base}={value}"
    return name


def explain_logreg(pipeline, payload_dict: dict, top_n: int = 5):
    preprocessor = pipeline.named_steps["preprocess"]
    clf = pipeline.named_steps["clf"]

    df = pd.DataFrame([payload_dict])
    X_trans = preprocessor.transform(df)
    feature_names = preprocessor.get_feature_names_out()

    coef = clf.coef_.ravel()
    impacts = coef * X_trans.ravel()
    idx_sorted = np.argsort(impacts)

    top_negative_idx = idx_sorted[:top_n]
    top_positive_idx = idx_sorted[-top_n:][::-1]

    def _pack(indices):
        items = []
        for i in indices:
            items.append(
                {
                    "feature": _format_feature_name(feature_names[i]),
                    "impact": float(round(impacts[i], 4)),
                }
            )
        return items

    return {
        "top_positive": _pack(top_positive_idx),
        "top_negative": _pack(top_negative_idx),
    }


def predict(payload_dict: dict, model_dir: str | Path):
    clf, reg = load_models(model_dir)

    df = pd.DataFrame([payload_dict])
    p_reach = float(clf.predict_proba(df)[0][1])

    band, years_range = _band_for_probability(p_reach)

    years_model_estimate = None
    if p_reach >= 0.35:
        months = float(reg.predict(df)[0])
        years_model_estimate = round(months / 12.0, 2)

    return {
        "p_reach_100k": round(p_reach, 4),
        "band": band,
        "years_range": years_range,
        "years_model_estimate": years_model_estimate,
    }
