import json
import os
from datetime import date
from flask import current_app

from app.extensions import db
from app.models.hub import Bank, LoanRate, LegalResource


def _parse_date(s):
    if not s:
        return None
    # expected: YYYY-MM-DD
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def seed_hub_data():
    """
    Idempotent seeding:
    - banks are created if missing
    - loan rates are inserted if the (bank_id, product_name, rate_value, valid_from, valid_to) combo is missing
    - legal resources are inserted if title missing
    """
    base_dir = os.path.join(os.path.dirname(__file__), "data")

    banks_path = os.path.join(base_dir, "banks.json")
    rates_path = os.path.join(base_dir, "loan_rates.json")
    legal_path = os.path.join(base_dir, "legal_resources.json")

    with open(banks_path, "r", encoding="utf-8") as f:
        banks_data = json.load(f)

    with open(rates_path, "r", encoding="utf-8") as f:
        rates_data = json.load(f)

    with open(legal_path, "r", encoding="utf-8") as f:
        legal_data = json.load(f)

    # ---- Banks
    name_to_bank = {}
    for b in banks_data:
        name = b["name"].strip()
        bank = Bank.query.filter_by(name=name).first()
        if not bank:
            bank = Bank(name=name)
            db.session.add(bank)
            db.session.flush()
        name_to_bank[name] = bank

    db.session.commit()

    # ---- Loan Rates
    for r in rates_data:
        bank_name = r["bank_name"].strip()
        bank = name_to_bank.get(bank_name) or Bank.query.filter_by(name=bank_name).first()
        if not bank:
            bank = Bank(name=bank_name)
            db.session.add(bank)
            db.session.flush()

        valid_from = _parse_date(r.get("valid_from"))
        valid_to = _parse_date(r.get("valid_to"))

        exists = (
            LoanRate.query.filter_by(
                bank_id=bank.id,
                product_name=r["product_name"].strip(),
                rate_value=float(r["rate_value"]),
                valid_from=valid_from,
                valid_to=valid_to,
            ).first()
        )

        if not exists:
            db.session.add(
                LoanRate(
                    bank_id=bank.id,
                    product_name=r["product_name"].strip(),
                    rate_value=float(r["rate_value"]),
                    valid_from=valid_from,
                    valid_to=valid_to,
                    source_note=r.get("source_note"),
                )
            )

    db.session.commit()

    # ---- Legal Resources
    for item in legal_data:
        title = item["title"].strip()
        exists = LegalResource.query.filter_by(title=title).first()
        if not exists:
            db.session.add(
                LegalResource(
                    title=title,
                    category=item.get("category"),
                    summary=item.get("summary"),
                    last_updated=_parse_date(item.get("last_updated")),
                )
            )

    db.session.commit()


def main():
    # Run using: python -m app.seed.seed_hub_data
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_hub_data()
        print("Hub seed completed.")


if __name__ == "__main__":
    main()
