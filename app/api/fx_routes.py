# app/api/fx_routes.py
import os
import requests
from flask.views import MethodView
from flask_smorest import Blueprint, abort

blp = Blueprint("fx", __name__, description="FX (exchange rates) endpoints")


@blp.route("/fx/latest")
class FxLatest(MethodView):
    def get(self):
        """
        GET /api/fx/latest?base=USD&symbols=TND,EUR
        """

        base = "USD"
        symbols = "TND,EUR"

        app_id = os.getenv("OXR_APP_ID")
        if not app_id:
            abort(500, message="Missing OXR_APP_ID environment variable")

        url = "https://openexchangerates.org/api/latest.json"
        params = {"app_id": app_id, "base": base, "symbols": symbols}

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError as e:
            abort(502, message=f"OXR HTTP error: {str(e)}")
        except requests.exceptions.RequestException as e:
            abort(502, message=f"OXR request failed: {str(e)}")

        return {
            "base": data.get("base"),
            "timestamp": data.get("timestamp"),
            "rates": data.get("rates", {}),
        }
