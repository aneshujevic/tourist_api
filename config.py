from datetime import timedelta


class BaseConfig(object):
    DEBUG = True
    SECRET_KEY = 'change me'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres_secret_user:postgres_secret_passwd@localhost:5432/tourist_api_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False,

    # JWT config
    JWT_SECRET_KEY = 'SUPER-SUPER-SECRET-KEY',
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15),
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=3)
