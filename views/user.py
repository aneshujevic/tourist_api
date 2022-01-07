import datetime

import jwt
import marshmallow
import sqlalchemy.exc
from flask import current_app, request, jsonify, Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash

from views.auth import roles_required, get_current_user_custom
from views.auth import auth_bp
from config.extensions import db
from utils.mail_service import send_successful_registration, send_password_reset_email, send_password_changed_email
from models.models import User, AccountType, AccountTypeChangeRequest, Arrangement
from schemas.schemas_rest import users_schema, type_schema, types_schema, user_schema, guide_arrangement_schema, \
    tourist_reservation_schema

types_bp = Blueprint('types', __name__, url_prefix='/types')
users_bp = Blueprint('users', __name__, url_prefix='/users')
users_bp.register_blueprint(types_bp)


@users_bp.get('/page/<int:page>')
@jwt_required()
@roles_required("ADMIN")
def get_all_users(page=1):
    if page <= 0:
        return {"msg": "Invalid page number."}, 400

    results_per_page = current_app.config.get('RESULTS_PER_PAGE')
    sorts = {
        "id-a": User.id.asc(),
        "id-d": User.id.desc(),
        "email-a": User.email.asc(),
        "email-d": User.email.desc(),
        "username-a": User.username.asc(),
        "username-d": User.username.desc(),
        "first-name-a": User.first_name.asc(),
        "first-name-d": User.first_name.desc(),
        "last-name-a": User.last_name.asc(),
        "last-name-d": User.last_name.desc(),
    }

    req_sort_param = request.args.get('sort', None)

    if (requested_type := request.args.get('type', None)) and requested_type is not None:
        requested_type_id = AccountType.query.filter_by(name=requested_type).first_or_404(
            description="No such role.").id
        select_statement = User.query.join(User.account_type).filter_by(id=requested_type_id)
    else:
        select_statement = User.query

    if req_sort_param is None or sorts.get(req_sort_param, None) is None:
        raw_users = db.session.execute(
            select_statement
                .order_by(User.id.asc())
                .limit(results_per_page)
                .offset((page - 1) * results_per_page)
        ).all()
    else:
        sorting_param = sorts[req_sort_param]
        raw_users = db.session.execute(
            select_statement
                .order_by(sorting_param)
                .limit(results_per_page)
                .offset((page - 1) * results_per_page)
        ).all()

    return jsonify([user_schema.dump(user[0]) for user in raw_users])


@users_bp.get('/<int:user_id>')
@jwt_required()
@roles_required("ADMIN")
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404(description="No such user.")

    for acc_type in user.account_type:
        if "GUIDE" in acc_type.name:
            return guide_arrangement_schema.dump(user)
        elif "TOURIST" in acc_type.name:
            return tourist_reservation_schema.dump(user)
        else:
            return user_schema.dump(user)


@auth_bp.post('/register')
def register_user():
    try:
        wanted_type = None
        if request.get_json().get('wanted_type'):
            wanted_type = request.json.pop('wanted_type')

        user = user_schema.load(request.get_json())

        tourist_acc_type = AccountType.query.filter_by(name="TOURIST").first_or_404(description="Role does not exist.")
        user.account_type.append(tourist_acc_type)
        user.password = generate_password_hash(
            user.password,
            current_app.config.get("PASSWORD_HASH_ALGORITHM"),
            current_app.config.get("PASSWORD_SALT_LENGTH")
        )

        User.query.session.add(user)

        if wanted_type is not None:
            acc_type = AccountType.query.filter_by(name=wanted_type) \
                .first_or_404(description="No such account type found.")

            change_request = AccountTypeChangeRequest(
                user_id=user.id,
                filing_date=datetime.datetime.now(),
                wanted_type_id=acc_type.id
            )

            AccountTypeChangeRequest.query.session.add(change_request)

        User.query.session.commit()

        send_successful_registration(user.username, user.email, user.first_name, user.last_name)

        return {
            "msg": "Successfully registered.",
            "account": user_schema.dump(user)
        }

    except marshmallow.ValidationError as err:
        return err.messages, 400

    except sqlalchemy.exc.SQLAlchemyError as err:
        return {"msg": "Database operational error."}, 400


@auth_bp.post('/forgot-password')
def get_reset_token():
    try:
        email = request.get_json().get('email', None)

        if email is None:
            return {"msg": "Malformed request."}, 400

        user = User.query.filter_by(email=email).first_or_404(description="No such user found.")
        token = user.get_reset_token()

        send_password_reset_email(email, token)

        return {"msg": "Email with further instructions has been sent to you."}

    except KeyError:
        return {"msg": "Malformed request."}, 400


@auth_bp.post('/reset-password/<string:token>')
def change_password(token):
    try:
        jwt_decoded = jwt.decode(token, algorithms="HS256", key=current_app.config.get("JWT_SECRET_KEY"))
        username = jwt_decoded['reset_password']
        password = request.get_json()['password']
        password1 = request.get_json()['password1']

        if len(password) < 8 or password != password1:
            return {"msg": "Passwords must be the same"}, 400

        user = User.query.filter_by(username=username) \
            .first_or_404(description="No such user exists.")

        user.password = generate_password_hash(
            password,
            current_app.config.get("PASSWORD_HASH_ALGORITHM"),
            current_app.config.get("PASSWORD_SALT_LENGTH")
        )

        User.query.session.commit()

        send_password_changed_email(user)

        return {"msg": "Password updated successfully."}

    except KeyError:
        return {"msg": "Invalid request."}, 400

    except jwt.DecodeError as decode_err:
        print(decode_err)
        return {"msg": "Invalid token."}, 400


@users_bp.put('/<int:user_id>')
@jwt_required()
@roles_required("ADMIN")
def update_user(user_id):
    try:
        wanted_user = User.query.filter_by(id=user_id).first_or_404(description="No such user.")

        new_user = user_schema.load(request.get_json())
        wanted_user.update(new_user)

        User.query.session.commit()

        return {
            "msg": "User successfully updated.",
            "account": user_schema.dump(wanted_user)
        }

    except marshmallow.ValidationError as err:
        return err.messages, 400


@users_bp.delete('/<int:user_id>')
@jwt_required()
@roles_required("ADMIN")
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404(description="No such user.")

    User.query.session.delete(user)
    User.query.session.commit()

    return {"msg": "Successfully deleted a user."}


@users_bp.get('/guides/free')
@jwt_required()
@roles_required("ADMIN")
def get_free_guides():
    try:
        guide = AccountType.query.filter_by(name="GUIDE").first()
        req_start_date = request.args.get('start_date')
        req_end_date = request.args.get('end_date')

        start_date = datetime.date.fromisoformat(req_start_date)
        end_date = datetime.date.fromisoformat(req_end_date)

        if end_date < start_date:
            return {"msg": "Malformed dates."}, 400

        users = db.session.query(User) \
            .outerjoin(Arrangement, Arrangement.guide_id == User.id) \
            .where(
            User.account_type.any(id=guide.id),
            or_(
                and_(end_date <= Arrangement.start_date, start_date >= Arrangement.end_date),
                Arrangement.id == None,
            )
        ).all()

        return {"guides": users_schema.dump(users)}

    except KeyError:
        return {"msg": "Start date and end date needed."}, 400


@users_bp.get('/self')
@jwt_required()
def get_own_user():
    req_user = get_current_user_custom()
    user = User.query.filter_by(id=req_user.id).first()

    return user_schema.dump(user)


@users_bp.put('/self')
@jwt_required()
def update_own_user():
    try:
        req_user = get_current_user_custom()
        current_user = User.query.filter_by(id=req_user.id).first()

        new_user = user_schema.load(request.get_json())
        new_user.password = generate_password_hash(
            new_user.password,
            current_app.config.get("PASSWORD_HASH_ALGORITHM"),
            current_app.config.get("PASSWORD_SALT_LENGTH")
        )
        current_user.update(new_user)

        User.query.session.commit()

        return {
            "msg": "Profile successfully updated.",
            "account": user_schema.dump(current_user)
        }

    except marshmallow.ValidationError as err:
        return err.messages, 400


@users_bp.delete('/self')
@jwt_required()
def delete_own_user():
    req_user = get_current_user_custom()
    user = User.query.filter_by(id=req_user.id).first()
    User.query.session.delete(user)
    User.query.session.commit()

    return {"msg": "Profile successfully deleted."}


@types_bp.get('')
@jwt_required()
@roles_required("ADMIN")
def get_all_types():
    acc_types = AccountType.query.all()

    return jsonify(types_schema.dump(acc_types))


@types_bp.get('/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def get_type(type_id):
    acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="There's no such type.")

    return type_schema.dump(acc_type)


@types_bp.post('')
@jwt_required()
@roles_required("ADMIN")
def create_type():
    try:
        acc_type = type_schema.load(request.get_json())

        AccountType.query.session.add(acc_type)
        AccountType.query.session.commit()

        return {
            "msg": "Successfully created an account type.",
            "type": type_schema.dump(acc_type)
        }

    except marshmallow.ValidationError as err:
        return err.messages, 400


@types_bp.delete('/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def delete_type(type_id):
    acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="No such type.")

    AccountType.query.session.delete(acc_type)
    AccountType.query.session.commit()

    return {"msg": "Successfully deleted a type."}


@types_bp.put('/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def update_type(type_id):
    try:
        acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="No such type.")
        req_name = request.get_json()['name']
        acc_type.name = req_name
        AccountType.query.session.commit()

        return {
            "msg": "Successfully updated account type.",
            "type": type_schema.dump(acc_type)
        }

    except KeyError as err:
        return {"msg": err}, 400
