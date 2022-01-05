from datetime import timedelta
from functools import wraps

import flask_jwt_extended
import marshmallow
import sqlalchemy.exc
from flask import request, Blueprint
from flask_jwt_extended import verify_jwt_in_request, create_access_token, create_refresh_token, jwt_required, \
    get_jwt_identity

from models import User, AccountType
from schemas_rest import user_schema

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


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


@auth_bp.post('/login')
def login():
    json_req = request.get_json()
    username = json_req.get("username", None)
    password = json_req.get("password", None)

    if username is None or password is None:
        return {"message": "Username or password missing."}, 400

    user = User.query.filter_by(username=username).first_or_404(description="No such user found.")

    # TODO: don't check plain text passwords
    if user.password != password:
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


@auth_bp.post('/register')
def register():
    try:
        request_json = request.get_json()
        user = user_schema.load(request_json)

        if wanted_type := request_json.get('account_type', None) is not None:
            # TODO: create account type change request
            pass

        user.account_type = AccountType.query.filter_by(name="TOURIST").first_or_404(description="Role does not exist.")
        User.query.session.add(user)
        User.query.session.commit()

        return {"msg": "Successfully registered."}

    except marshmallow.ValidationError as err:
        return err.messages, 400

    except sqlalchemy.exc.SQLAlchemyError as err:
        return {"msg": err}, 400
