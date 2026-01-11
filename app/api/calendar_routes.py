# app/api/calendar_routes.py
from datetime import date as dt_date
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app
from marshmallow import Schema, fields
import requests

blp = Blueprint("calendar", __name__, description="Calendar greeting endpoints")

class GreetingQuerySchema(Schema):
    date = fields.Date(required=False)      # optional: ?date=2026-01-10
    country = fields.Str(required=False)    # optional: ?country=TN


@blp.route("/calendar/greeting")
class CalendarGreeting(MethodView):
    @blp.arguments(GreetingQuerySchema, location="query")
    def get(self, args):
        """
        Returns a greeting based on:
        - weekend (Sat/Sun)
        - public holiday (via Calendarific)
        Priority: Holiday > Weekend > Normal day
        """
        api_key = current_app.config.get("CALENDARIFIC_API_KEY", "")
        base_url = current_app.config.get("CALENDARIFIC_BASE_URL", "https://calendarific.com/api/v2")
        default_country = current_app.config.get("CALENDARIFIC_COUNTRY", "TN")

        if not api_key:
            abort(500, message="CALENDARIFIC_API_KEY is not set in environment.")

        d = args.get("date") or dt_date.today()
        country = (args.get("country") or default_country).upper()

        # Weekend check (Sat=5, Sun=6 in Python weekday())
        is_weekend = d.weekday() in (5, 6)

        # Calendarific call
        # Calendarific requires api_key, country, year. month/day are optional filters. :contentReference[oaicite:1]{index=1}
        params = {
            "api_key": api_key,
            "country": country,
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "type": "national",
        }

        try:
            r = requests.get(f"{base_url}/holidays", params=params, timeout=10)
            r.raise_for_status()
            payload = r.json()
        except requests.RequestException:
            abort(502, message="Holiday provider error (Calendarific request failed).")

        holidays = payload.get("response", {}).get("holidays", []) or []
        is_holiday = len(holidays) > 0
        holiday_names = [h.get("name") for h in holidays if h.get("name")]

        if is_holiday:
            # You can customize the message format
            return {
                "date": str(d),
                "country": country,
                "type": "HOLIDAY",
                "holidays": holiday_names,
                "message": f"Happy holidays! Today is: {', '.join(holiday_names)}."
            }, 200

        if is_weekend:
            return {
                "date": str(d),
                "country": country,
                "type": "WEEKEND",
                "holidays": [],
                "message": "Happy weekend!"
            }, 200

        return {
            "date": str(d),
            "country": country,
            "type": "WORKDAY",
            "holidays": [],
            "message": "Have a productive day!"
        }, 200
