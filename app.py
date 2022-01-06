import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from views import auth, account_change_request, reservation, user, arrangement

from config.config import BaseConfig
from config.extensions import ma, db, jwt_man, mi, mail
from models import User, AccountType


def create_app(config_object=BaseConfig()):
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)

    @app.cli.command("create-profile")
    @click.option("-u", "--username", "username")
    @click.option("-e", "--email", "email")
    @click.option("-f", "--first-name", "first_name")
    @click.option("-l", "--last-name", "last_name")
    @click.option("-p", "--password", "password")
    @click.option("-t", "--account-type", "acc_type")
    @with_appcontext
    def create_profile(username, email, first_name, last_name, password, acc_type):
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
        acc_type = AccountType.query.filter_by(name=acc_type).first()
        admin.account_type.append(acc_type)

        User.query.session.add(admin)
        User.query.session.commit()

        print("Successfully created an admin.")

    @app.cli.command("create-type")
    @click.argument("new_type")
    def create_type(new_type):
        new_type = AccountType(
            name=new_type
        )
        AccountType.query.session.add(new_type)
        AccountType.query.session.commit()
        print(f"Successfully created type {new_type}")

    return app


def register_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    mi.init_app(app, db)
    jwt_man.init_app(app)
    mail.init_app(app)


def register_blueprints(app):
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(arrangement.arrangements_bp)
    app.register_blueprint(user.users_bp)
    app.register_blueprint(user.types_bp)
    app.register_blueprint(reservation.reservation_bp)
    app.register_blueprint(account_change_request.acc_type_change_bp)
