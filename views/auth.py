from datetime import timedelta
from functools import wraps

import flask_jwt_extended
from flask import request, Blueprint
from flask_jwt_extended import verify_jwt_in_request, create_access_token, create_refresh_token, jwt_required, \
    get_jwt_identity
from werkzeug.security import check_password_hash

from models.models import User
from schemas.schemas_rest import user_schema


def roles_required(*required_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user_custom()
            if user.account_type.name in required_roles:
                return fn(*args, **kwargs)
            else:
                return {"msg": "Forbidden method."}, 403

        return decorator

    return wrapper


def login_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            return fn(*args, **kwargs)

        return decorator

    return wrapper


def get_current_user_custom():
    jwt_user = flask_jwt_extended.get_jwt_identity()
    return user_schema.get_user_from_jwt_claims(jwt_user)


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.post('/login')
def login():
    json_req = request.get_json()
    username = json_req.get("username", None)
    password = json_req.get("password", None)

    if username is None or password is None:
        return {"message": "Username or password missing."}, 400

    user = User.query.filter_by(username=username).first_or_404(description="No such user found.")

    if not check_password_hash(user.password, password):
        return {"message": "Wrong login credentials."}, 403

    user = user_schema.dump(user)
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return {"access_token": access_token, "refresh_token": refresh_token}


@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, expires_delta=timedelta(hours=3))
    return {"access_token": access_token}
