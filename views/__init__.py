from flask import Blueprint

arrangements_bp = Blueprint('arrangements', __name__, url_prefix='/arrangements')
acc_type_change_bp = Blueprint('account_change_request', __name__, url_prefix='/acc-type-change')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
reservation_bp = Blueprint('reservations', __name__, url_prefix='/reservations')
users_bp = Blueprint('users', __name__, url_prefix='/users')
types_bp = Blueprint('types', __name__, url_prefix='/types')