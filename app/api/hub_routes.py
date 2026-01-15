import json
import os
from flask.views import MethodView
from flask_smorest import Blueprint, abort

blp = Blueprint("hub", __name__, description="Loans hub")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _seed_data_dir():
    # app/api -> app
    api_dir = os.path.dirname(__file__)
    app_dir = os.path.dirname(api_dir)
    return os.path.join(app_dir, "seed", "data")


def _read_json(filename):
    path = os.path.join(_seed_data_dir(), filename)
    if not os.path.exists(path):
        abort(500, message=f"File not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        abort(500, message=str(e))


# -------------------------------------------------
# Routes
# -------------------------------------------------
@blp.route("/hub/loans")
class HubLoans(MethodView):
    def get(self):
        banks = _read_json("banks.json")
        rates = _read_json("loan_rates.json")

        return {
            "banks": banks,
            "rates": rates
        }