from datetime import datetime
from sqlalchemy import or_

from ..extensions import db
from ..models.contract import Contract
from ..models.signature import Signature
from ..models.user import User  # assumes you have User model
from ..models.notification import Notification  # assumes you have Notification model


def _notify(user_id: int, message: str, kind: str = "CONTRACT"):
    n = Notification(user_id=user_id, message=message, kind=kind, is_read=False)
    db.session.add(n)


def create_contract(created_by_id: int, title: str, template_type: str, content: str) -> Contract:
    c = Contract(
        created_by_id=created_by_id,
        title=title,
        template_type=template_type,
        content=content,
        status="DRAFT",
    )
    db.session.add(c)
    db.session.commit()
    return c


def update_contract(contract: Contract, actor_id: int, data: dict) -> Contract:
    if contract.created_by_id != actor_id:
        raise ValueError("Only the creator can edit the contract.")
    if contract.status != "DRAFT":
        raise ValueError("Contract can only be edited while DRAFT.")

    for k in ["title", "template_type", "content"]:
        if k in data and data[k] is not None:
            setattr(contract, k, data[k])

    db.session.commit()
    return contract


def get_my_contracts(user_id: int):
    # contracts I created OR contracts I have a signature record for
    q = (
        db.session.query(Contract)
        .outerjoin(Signature, Signature.contract_id == Contract.id)
        .filter(or_(Contract.created_by_id == user_id, Signature.user_id == user_id))
        .distinct()
        .order_by(Contract.created_at.desc())
    )
    return q.all()


def get_contract_detail(contract_id: int, user_id: int):
    contract = Contract.query.get_or_404(contract_id)

    # authorization: creator or signer only
    signer = Signature.query.filter_by(contract_id=contract_id, user_id=user_id).first()
    if contract.created_by_id != user_id and not signer:
        raise PermissionError("Not allowed to view this contract.")

    signatures = Signature.query.filter_by(contract_id=contract_id).all()
    return contract, signatures


def send_contract(contract: Contract, actor_id: int, party_user_ids: list[int]):
    if contract.created_by_id != actor_id:
        raise ValueError("Only the creator can send the contract.")
    if contract.status != "DRAFT":
        raise ValueError("Contract can only be sent while DRAFT.")

    # ensure unique ids, remove creator if present (creator does not need to 'sign' in this simple version)
    party_user_ids = list({int(x) for x in party_user_ids if int(x) != actor_id})
    if not party_user_ids:
        raise ValueError("You must select at least one other party.")

    # validate users exist
    existing = {u.id for u in User.query.filter(User.id.in_(party_user_ids)).all()}
    missing = [x for x in party_user_ids if x not in existing]
    if missing:
        raise ValueError(f"Some users do not exist: {missing}")

    # create signature rows
    for uid in party_user_ids:
        sig = Signature.query.filter_by(contract_id=contract.id, user_id=uid).first()
        if not sig:
            db.session.add(Signature(contract_id=contract.id, user_id=uid, status="PENDING"))

        _notify(uid, f"Contract '{contract.title}' requires your signature.")

    contract.status = "SENT"
    db.session.commit()
    return contract


def sign_contract(contract: Contract, actor_id: int):
    if contract.status != "SENT":
        raise ValueError("Contract must be SENT before signing.")

    sig = Signature.query.filter_by(contract_id=contract.id, user_id=actor_id).first()
    if not sig:
        raise PermissionError("You are not a party in this contract.")
    if sig.status == "SIGNED":
        return contract  # idempotent

    sig.status = "SIGNED"
    sig.signed_at = datetime.utcnow()

    # if all signatures are SIGNED => contract SIGNED
    all_sigs = Signature.query.filter_by(contract_id=contract.id).all()
    if all_sigs and all(s.status == "SIGNED" for s in all_sigs):
        contract.status = "SIGNED"
        _notify(contract.created_by_id, f"Contract '{contract.title}' is fully signed.")
        for s in all_sigs:
            _notify(s.user_id, f"Contract '{contract.title}' is fully signed.")

    db.session.commit()
    return contract


def reject_contract(contract: Contract, actor_id: int):
    if contract.status != "SENT":
        raise ValueError("Contract must be SENT before rejecting.")

    sig = Signature.query.filter_by(contract_id=contract.id, user_id=actor_id).first()
    if not sig:
        raise PermissionError("You are not a party in this contract.")
    if sig.status == "REJECTED":
        return contract

    sig.status = "REJECTED"
    sig.signed_at = datetime.utcnow()
    contract.status = "CANCELLED"

    _notify(contract.created_by_id, f"Contract '{contract.title}' was rejected and cancelled.")
    db.session.commit()
    return contract