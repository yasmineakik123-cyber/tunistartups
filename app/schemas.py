from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=120))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True)
    location = fields.Str(required=False, allow_none=True)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class TokenSchema(Schema):
    access_token = fields.Str(required=True)

class StartupCreateSchema(Schema):
    name = fields.Str(required=True)
    industry = fields.Str(required=False, allow_none=True)
    stage = fields.Str(required=False, allow_none=True)
    pitch = fields.Str(required=False, allow_none=True)

class StartupSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    industry = fields.Str(allow_none=True)
    stage = fields.Str(allow_none=True)
    pitch = fields.Str(allow_none=True)
    score_total = fields.Int()
    owner_id = fields.Int()
    

class PostCreateSchema(Schema):
    title = fields.Str(required=True)
    content = fields.Str(required=True)
    post_type = fields.Str(required=False, allow_none=True)
    startup_id = fields.Int(required=False, allow_none=True)
    community_id = fields.Int(required=False, allow_none=True)

class PostSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    content = fields.Str()
    post_type = fields.Str(allow_none=True)
    author_id = fields.Int()
    startup_id = fields.Int(allow_none=True)
    community_id = fields.Int(allow_none=True)

class CommentCreateSchema(Schema):
    content = fields.Str(required=True)

class ReactionCreateSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["LIKE", "SAVE"]))

class NotificationSchema(Schema):
    id = fields.Int()
    message = fields.Str()
    kind = fields.Str(allow_none=True)
    is_read = fields.Bool()
    created_at = fields.DateTime()

from marshmallow import Schema, fields, validate

# ... keep your existing schemas above ...


class BankSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    created_at = fields.DateTime()


class LoanRateSchema(Schema):
    id = fields.Int()
    bank_id = fields.Int()
    product_name = fields.Str()
    rate_value = fields.Float()
    valid_from = fields.Date(allow_none=True)
    valid_to = fields.Date(allow_none=True)
    source_note = fields.Str(allow_none=True)
    created_at = fields.DateTime()

    # optional convenience field (filled in route output)
    bank_name = fields.Str(dump_only=True)


class LegalResourceSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    category = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    last_updated = fields.Date(allow_none=True)
    created_at = fields.DateTime()



class ContractCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    template_type = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    content = fields.Str(required=True, validate=validate.Length(min=10))

    # parties to request signatures from (users on the platform)
    party_user_ids = fields.List(fields.Int(), required=False)  # for SEND step (optional at create)


class ContractUpdateSchema(Schema):
    title = fields.Str(required=False, validate=validate.Length(min=2, max=200))
    template_type = fields.Str(required=False, validate=validate.Length(min=2, max=80))
    content = fields.Str(required=False, validate=validate.Length(min=10))


class ContractSendSchema(Schema):
    party_user_ids = fields.List(fields.Int(), required=True, validate=validate.Length(min=1))


class ContractOutSchema(Schema):
    id = fields.Int()
    created_by_id = fields.Int()
    title = fields.Str()
    template_type = fields.Str()
    content = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()



class SignatureOutSchema(Schema):
    id = fields.Int()
    contract_id = fields.Int()
    user_id = fields.Int()
    status = fields.Str()
    signed_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()

class FxLatestQuerySchema(Schema):
    # Optional: defaults are USD-based, because free plan is USD base.
    symbols = fields.String(load_default="TND,EUR")  # comma-separated


class FxRateItemSchema(Schema):
    symbol = fields.String(required=True)
    rate = fields.Float(required=True)


class FxLatestResponseSchema(Schema):
    base = fields.String(required=True)
    timestamp = fields.Integer(required=True)
    rates = fields.Dict(keys=fields.String(), values=fields.Float())
    
    


class TaskCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=False, allow_none=True)

    priority = fields.Str(required=False, allow_none=True, validate=validate.OneOf(["LOW", "MEDIUM", "HIGH"]))
    due_date = fields.Date(required=False, allow_none=True)

    # allocation
    assigned_to_id = fields.Int(required=False, allow_none=True)

class TaskUpdateSchema(Schema):
    title = fields.Str(required=False, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=False, allow_none=True)

    status = fields.Str(required=False, validate=validate.OneOf(["TODO", "IN_PROGRESS", "DONE"]))
    priority = fields.Str(required=False, validate=validate.OneOf(["LOW", "MEDIUM", "HIGH"]))
    due_date = fields.Date(required=False, allow_none=True)

    assigned_to_id = fields.Int(required=False, allow_none=True)

class TaskOutSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str(allow_none=True)
    status = fields.Str()
    priority = fields.Str()
    due_date = fields.Date(allow_none=True)

    startup_id = fields.Int()
    created_by_id = fields.Int()
    assigned_to_id = fields.Int(allow_none=True)

    created_at = fields.DateTime()

class StartupMemberAddSchema(Schema):
    username = fields.Str(required=True)
    
# app/schemas/startup_membership.py


class JoinCodeResponseSchema(Schema):
    join_code = fields.String(required=True)

class JoinStartupSchema(Schema):
    code = fields.String(required=True)
    
