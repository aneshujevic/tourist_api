from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
ma = Marshmallow()
mi = Migrate()
jwt_man = JWTManager()
mail = Mail()
