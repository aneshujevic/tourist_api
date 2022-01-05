from flask import Flask

import arrangements
import auth
from config import BaseConfig
from extensions import ma, db, jwt_man, mi


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


def register_blueprints(app):
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(arrangements.arrangements_bp)
