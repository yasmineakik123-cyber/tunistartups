# app/api/fx_routes.py
import os
import requests
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort

blp = Blueprint("fx", __name__, description="FX (exchange rates) endpoints")

# Tunisia-relevant defaults (you can edit this list anytime)
DEFAULT_SYMBOLS = [
    "TND",
    "USD", "EUR", "GBP", "JPY", "CNY", "TRY",
    "CHF", "CAD",
    "SAR", "AED",
    "DZD", "MAD", "EGP",
]

@blp.route("/fx/latest")
class FxLatest(MethodView):
    def get(self):
        """
        GET /api/fx/latest
        Optional: /api/fx/latest?symbols=USD,EUR,JPY,CNY

        Returns:
        {
          "base": "TND",
          "timestamp": <unix>,
          "rates": { "TND": 1.0, "USD": ..., "EUR": ..., ... }
        }
        """

        app_id = os.getenv("OXR_APP_ID")
        if not app_id:
            abort(500, message="Missing OXR_APP_ID environment variable")

        # Optional symbols override from query
        symbols_param = request.args.get("symbols", "").strip()
        if symbols_param:
            symbols_list = [s.strip().upper() for s in symbols_param.split(",") if s.strip()]
        else:
            symbols_list = list(DEFAULT_SYMBOLS)

        # Ensure TND always present (pivot)
        if "TND" not in symbols_list:
            symbols_list.append("TND")

        # If you want USD always included too, uncomment:
        # if "USD" not in symbols_list:
        #     symbols_list.append("USD")

        url = "https://openexchangerates.org/api/latest.json"
        params = {
            "app_id": app_id,
            "symbols": ",".join(sorted(set(symbols_list))),
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError as e:
            abort(502, message=f"OXR HTTP error: {str(e)}")
        except requests.exceptions.RequestException as e:
            abort(502, message=f"OXR request failed: {str(e)}")

        rates_usd = data.get("rates", {})
        usd_to_tnd = rates_usd.get("TND")
        if not usd_to_tnd:
            abort(502, message="TND rate missing from OXR response")

        # Convert all requested currencies to BASE=TND
        # Formula: (USD->CCY) / (USD->TND) = (TND->CCY)
        rates_tnd = {"TND": 1.0}

        for ccy in symbols_list:
            if ccy == "TND":
                continue
            usd_to_ccy = rates_usd.get(ccy)
            if usd_to_ccy is None:
                continue
            rates_tnd[ccy] = round(usd_to_ccy / usd_to_tnd, 6)

        return {
            "base": "TND",
            "timestamp": data.get("timestamp"),
            "rates": dict(sorted(rates_tnd.items())),
        }
