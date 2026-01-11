from flask.views import MethodView
from flask_smorest import Blueprint

from ..models.hub import Bank, LoanRate, LegalResource
from ..schemas import BankSchema, LoanRateSchema, LegalResourceSchema

blp = Blueprint("Hub", "hub", description="Finance & Legal Hub (mock/simulation)")


@blp.route("/hub/banks")
class HubBanks(MethodView):
    @blp.response(200, BankSchema(many=True))
    def get(self):
        return Bank.query.order_by(Bank.name.asc()).all()


@blp.route("/hub/loan-rates")
class HubLoanRates(MethodView):
    @blp.response(200, LoanRateSchema(many=True))
    def get(self):
        # We enrich output with bank_name to make the UI simpler
        rates = (
            LoanRate.query.join(Bank, LoanRate.bank_id == Bank.id)
            .order_by(Bank.name.asc(), LoanRate.rate_value.asc())
            .all()
        )

        result = []
        for r in rates:
            result.append(
                {
                    "id": r.id,
                    "bank_id": r.bank_id,
                    "bank_name": r.bank.name if r.bank else None,
                    "product_name": r.product_name,
                    "rate_value": r.rate_value,
                    "valid_from": r.valid_from,
                    "valid_to": r.valid_to,
                    "source_note": r.source_note,
                    "created_at": r.created_at,
                }
            )
        return result


@blp.route("/hub/legal-resources")
class HubLegalResources(MethodView):
    @blp.response(200, LegalResourceSchema(many=True))
    def get(self):
        return LegalResource.query.order_by(LegalResource.id.desc()).all()
