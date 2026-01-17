from pathlib import Path

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

from ..ml.inference import CATEGORICAL_COLS, NUMERIC_COLS, explain_logreg, predict, load_models


blp = Blueprint("scoring", __name__, description="Startup 100k scoring")


def _model_dir():
    return Path(__file__).resolve().parents[2] / "models"


@blp.route("/predict")
class ScoringPredict(MethodView):
    def post(self):
        payload = request.get_json(silent=True) or {}

        required = CATEGORICAL_COLS + NUMERIC_COLS
        missing = [k for k in required if k not in payload or payload[k] in ("", None)]
        if missing:
            return {"message": "Missing fields", "missing": missing}, 400

        for key in NUMERIC_COLS:
            try:
                if key in payload:
                    payload[key] = float(payload[key])
            except (TypeError, ValueError):
                return {"message": f"Invalid numeric value for {key}."}, 400

        payload["customer_traction"] = str(payload["customer_traction"])

        clf, _reg = load_models(_model_dir())
        result = predict(payload, _model_dir())
        drivers = explain_logreg(clf, payload)

        return {"input": payload, "result": result, "drivers": drivers}, 200
