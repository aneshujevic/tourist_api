import datetime

import marshmallow
from flask import jsonify, current_app, request, Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import select

from views.auth import roles_required, get_current_user_custom
from config.extensions import db
from utils.mail_service import send_account_change_request_notification
from models.models import AccountTypeChangeRequest, AccountType, User
from schemas.schemas_rest import account_type_change_requests_schema, account_type_change_request_schema, \
    base_account_type_change_request_schema

acc_type_change_bp = Blueprint('account_change_request', __name__, url_prefix='/acc-type-change')


@acc_type_change_bp.get('/page/<int:page_id>')
@jwt_required()
@roles_required("ADMIN")
def get_all_type_change_requests(page_id):
    if page_id <= 0:
        return {"msg": "Invalid page number."}, 400

    sorts = {
        "filing-date-a": AccountTypeChangeRequest.filing_date.asc(),
        "filing-date-d": AccountTypeChangeRequest.filing_date.desc(),
        "confirmation-date-a": AccountTypeChangeRequest.confirmation_date.asc(),
        "confirmation-date-d": AccountTypeChangeRequest.confirmation_date.desc(),
    }
    wanted_sort = sorts.get("filing-date-a")

    if (sort := request.args.get('sort', None)) and sort:
        if sorts.get(sort, None) is not None:
            wanted_sort = sorts.get(sort)

    raw_requests = db.session.execute(
        select(AccountTypeChangeRequest)
            .order_by(wanted_sort)
            .limit(current_app.config['RESULTS_PER_PAGE'])
            .offset((page_id - 1) * current_app.config['RESULTS_PER_PAGE'])
    ).all()

    return jsonify([account_type_change_request_schema.dump(req[0]) for req in raw_requests])


@acc_type_change_bp.get('/own')
@jwt_required()
def get_own_type_change_requests():
    user = get_current_user_custom()

    requests = AccountTypeChangeRequest.query.filter_by(user_id=user.id).all()

    return jsonify(account_type_change_requests_schema.dump(requests))


@acc_type_change_bp.get('/<int:request_id>')
@jwt_required()
def get_type_change_request(request_id):
    user = get_current_user_custom()

    if user.account_type.name == "ADMIN":
        change_request = AccountTypeChangeRequest.query.filter_by(id=request_id) \
            .first_or_404(description="No such account type change request.")
    else:
        change_request = AccountTypeChangeRequest.query.filter_by(id=request_id, user_id=user.id) \
            .first_or_404(description="There is no such account type change request.")

    return account_type_change_request_schema.dump(change_request)


@acc_type_change_bp.post('')
@jwt_required()
def submit_type_change_request():
    try:
        user = get_current_user_custom()

        wanted_type = request.get_json().pop("wanted_type")
        if (
                user.account_type.name == "GUIDE" and
                wanted_type != "ADMIN"
        ) or (
                user.account_type.name == "TOURIST" and
                (
                        wanted_type != "ADMIN" and
                        wanted_type != "GUIDE"
                )
        ):
            return {"msg": "Invalid account wanted type"}, 400

        acc_type = AccountType.query.filter_by(name=wanted_type) \
            .first_or_404(description="No such account type found.")

        change_request = base_account_type_change_request_schema.load(request.get_json())

        change_request.user_id = user.id
        change_request.filing_date = datetime.datetime.now()
        change_request.wanted_type_id = acc_type.id

        AccountTypeChangeRequest.query.session.add(change_request)
        AccountTypeChangeRequest.query.session.commit()

        return {"msg": "Successfully submitted an account type change request."}

    except KeyError:
        return {"msg": "Wanted type field missing."}, 400

    except marshmallow.ValidationError as err:
        return err.messages, 400


@acc_type_change_bp.put('/<int:request_id>')
@jwt_required()
@roles_required("ADMIN")
def verify_type_change_request(request_id):
    try:
        admin = get_current_user_custom()

        change_request = AccountTypeChangeRequest.query.filter_by(id=request_id) \
            .first_or_404(description="There is no such account type change request.")

        req_change_request = account_type_change_request_schema.load(request.get_json())

        change_request.comment = req_change_request.comment
        change_request.granted = req_change_request.granted
        change_request.confirmation_date = datetime.datetime.now()
        change_request.admin_confirmed_id = admin.id

        AccountTypeChangeRequest.query.session.commit()

        user = User.query.filter_by(change_request.user_id).first_or_404(description="No such user found.")

        send_account_change_request_notification(user, change_request)

        return {"msg": "Successfully verified account change request."}

    except marshmallow.ValidationError as err:
        return err.messages, 400
