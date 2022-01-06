import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

import account_change_request_views
import arrangement_views
import auth_views
import reservation_views
import user_views
from config import BaseConfig
from extensions import ma, db, jwt_man, mi, mail
from models import User


def create_app(config_object=BaseConfig()):
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)

    @app.cli.command("create-admin")
    @click.option("-u", "--username", "username")
    @click.option("-e", "--email", "email")
    @click.option("-f", "--first-name", "first_name")
    @click.option("-l", "--last-name", "last_name")
    @click.option("-p", "--password", "password")
    @with_appcontext
    def create_admin(username, email, first_name, last_name, password):
        admin = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=generate_password_hash(
                password,
                current_app.config.get("PASSWORD_HASH_ALGORITHM"),
                current_app.config.get("PASSWORD_SALT_LENGTH")
            )
        )
        User.query.session.add(admin)
        User.query.session.commit()
        print("Successfully created an admin.")

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
