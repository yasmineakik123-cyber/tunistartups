from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.contract import Contract
from ..schemas import (
    ContractCreateSchema,
    ContractUpdateSchema,
    ContractSendSchema,
    ContractOutSchema,
)
from ..schemas import SignatureOutSchema
from ..services.contract_service import (
    create_contract,
    update_contract,
    get_my_contracts,
    get_contract_detail,
    send_contract,
    sign_contract,
    reject_contract,
)

blp = Blueprint("contracts", __name__, description="Contract simulation endpoints")


@blp.route("/contracts")
class Contracts(MethodView):
    @jwt_required()
    @blp.response(200, ContractOutSchema(many=True))
    def get(self):
        user_id = int(get_jwt_identity())
        return get_my_contracts(user_id)

    @jwt_required()
    @blp.arguments(ContractCreateSchema)
    @blp.response(201, ContractOutSchema)
    def post(self, data):
        user_id = int(get_jwt_identity())
        try:
            c = create_contract(
                created_by_id=user_id,
                title=data["title"],
                template_type=data["template_type"],
                content=data["content"],
                party_user_ids=data.get("party_user_ids"),
            )
            return c
        except ValueError as e:
            abort(400, message=str(e))


@blp.route("/contracts/<int:contract_id>")
class ContractDetail(MethodView):
    @jwt_required()
    @blp.response(200, ContractOutSchema)
    def get(self, contract_id):
        user_id = int(get_jwt_identity())
        try:
            contract, _signatures = get_contract_detail(contract_id, user_id)
            return contract
        except PermissionError as e:
            abort(403, message=str(e))

    @jwt_required()
    @blp.arguments(ContractUpdateSchema)
    @blp.response(200, ContractOutSchema)
    def patch(self, data, contract_id):
        user_id = int(get_jwt_identity())
        contract = Contract.query.get_or_404(contract_id)
        try:
            return update_contract(contract, user_id, data)
        except ValueError as e:
            abort(400, message=str(e))


@blp.route("/contracts/<int:contract_id>/signatures")
class ContractSignatures(MethodView):
    @jwt_required()
    @blp.response(200, SignatureOutSchema(many=True))
    def get(self, contract_id):
        user_id = int(get_jwt_identity())
        try:
            _, signatures = get_contract_detail(contract_id, user_id)
            return signatures
        except PermissionError as e:
            abort(403, message=str(e))


@blp.route("/contracts/<int:contract_id>/send")
class ContractSend(MethodView):
    @jwt_required()
    @blp.arguments(ContractSendSchema)
    @blp.response(200, ContractOutSchema)
    def post(self, data, contract_id):
        user_id = int(get_jwt_identity())
        contract = Contract.query.get_or_404(contract_id)
        try:
            return send_contract(contract, user_id, data["party_user_ids"])
        except ValueError as e:
            abort(400, message=str(e))


@blp.route("/contracts/<int:contract_id>/sign")
class ContractSign(MethodView):
    @jwt_required()
    @blp.response(200, ContractOutSchema)
    def post(self, contract_id):
        user_id = int(get_jwt_identity())
        contract = Contract.query.get_or_404(contract_id)
        try:
            return sign_contract(contract, user_id)
        except (ValueError, PermissionError) as e:
            abort(400, message=str(e))


@blp.route("/contracts/<int:contract_id>/reject")
class ContractReject(MethodView):
    @jwt_required()
    @blp.response(200, ContractOutSchema)
    def post(self, contract_id):
        user_id = int(get_jwt_identity())
        contract = Contract.query.get_or_404(contract_id)
        try:
            return reject_contract(contract, user_id)
        except (ValueError, PermissionError) as e:
            abort(400, message=str(e))
