from flask import Flask
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import BaseConfig

app = Flask(__name__)
app.config.from_object(BaseConfig)
db = SQLAlchemy(app)
ma = Marshmallow(app)

from models import *

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
