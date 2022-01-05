import marshmallow
from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import jwt_required

from auth_views import roles_required, get_current_user_custom
from extensions import db
from models import User, AccountType
from schemas_rest import users_schema, type_schema, types_schema, user_schema, guide_arrangement_schema, \
    tourist_reservation_schema

users_bp = Blueprint('users', __name__, url_prefix='/users')


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
        requested_type_id = AccountType.query.filter_by(name=requested_type).first_or_404(description="No such role.").id
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

    return jsonify([users_schema.dump(user) for user in raw_users])


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


@users_bp.put('/<int:user_id>')
@jwt_required()
@roles_required("ADMIN")
def update_user(user_id):
    try:
        wanted_user = User.query.filter_by(id=user_id).first_or_404(description="No such user.")

        new_user = user_schema(request.get_json())
        wanted_user.update(new_user)

        User.query.session.commit()

        return {"msg": "User successfully updated."}

    except marshmallow.ValidationError as err:
        return err.messages, 400


@users_bp.get('/<int:user_id>')
@jwt_required()
@roles_required("ADMIN")
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404(description="No such user.")

    User.query.session.delete(user)
    User.query.session.commit()

    return {"msg": "Successfully deleted a user."}


@users_bp.put('/self')
@jwt_required()
def update_own_user():
    try:
        req_user = get_current_user_custom()
        current_user = User.query.filter_by(id=req_user.id).first()

        new_user = user_schema(request.get_json())
        current_user.update(new_user)

        User.query.session.commit()

        return {"msg": "Profile successfully updated."}

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


@users_bp.get('/self')
@jwt_required()
def get_own_user():
    req_user = get_current_user_custom()
    user = User.query.filter_by(id=req_user.id).first()

    return user_schema.dump(user)


@users_bp.get('/types')
@jwt_required()
@roles_required("ADMIN")
def get_all_types():
    acc_types = AccountType.query.all()

    return jsonify(types_schema.dump(acc_types))


@users_bp.get('/types/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def get_type(type_id):
    acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="There's no such type.")

    return type_schema.dump(acc_type)


@users_bp.post('/types')
@jwt_required()
@roles_required("ADMIN")
def create_type():
    try:
        acc_type = type_schema.load(request.get_json())

        AccountType.query.session.add(acc_type)
        AccountType.query.session.commit()

        return {"msg": "Successfully created an account type."}

    except marshmallow.ValidationError as err:
        return err.messages, 400


@users_bp.delete('/types/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def delete_type(type_id):
    acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="No such type.")

    AccountType.query.session.delete(acc_type)
    AccountType.query.session.commit()

    return {"msg": "Successfully deleted a type."}


@users_bp.put('/types/<int:type_id>')
@jwt_required()
@roles_required("ADMIN")
def update_type(type_id):
    try:
        acc_type = AccountType.query.filter_by(id=type_id).first_or_404(description="No such type.")
        req_name = request.get_json()['name']
        acc_type.name = req_name
        AccountType.query.session.commit()

        return {"msg": "Successfully updated account type."}

    except KeyError as err:
        return {"msg": err}, 400