import requests


# ✅ Put your REAL key here (no env file)
OXR_APP_ID = "3c8796bacac444489db587810b8fc316"


class FxServiceError(Exception):
    pass


def get_latest_rates(symbols: str = "TND,EUR") -> dict:
    """
    Fetch latest FX rates from OpenExchangeRates.
    Free plan base is always USD, so we never set base=...
    """
    url = "https://openexchangerates.org/api/latest.json"
    params = {
        "app_id": OXR_APP_ID,
        "symbols": symbols.replace(" ", ""),  # clean spaces
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.HTTPError as e:
        # Often 401 here means app_id is wrong OR plan limitations
        raise FxServiceError(f"OpenExchangeRates HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FxServiceError(f"Network error calling OpenExchangeRates: {e}") from e

    # Basic validation
    if "rates" not in data or "base" not in data:
        raise FxServiceError(f"Unexpected response format: {data}")

    return {
        "base": data.get("base", "USD"),
        "timestamp": data.get("timestamp", 0),
        "rates": data.get("rates", {}),
    }
