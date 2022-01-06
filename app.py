from flask import Flask

import account_change_request_views
import arrangement_views
import auth_views
import reservation_views
import user_views
from config import BaseConfig
from extensions import ma, db, jwt_man, mi, mail
from mail_service import send_successful_registration


def create_app(config_object=BaseConfig()):
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    mi.init_app(app, db)
    jwt_man.init_app(app)
    mail.init_app(app)


def register_blueprints(app):
    app.register_blueprint(auth_views.auth_bp)
    app.register_blueprint(arrangement_views.arrangements_bp)
    app.register_blueprint(user_views.users_bp)
    app.register_blueprint(reservation_views.reservation_bp)
    app.register_blueprint(account_change_request_views.acc_type_change_bp)
