from datetime import timedelta


class BaseConfig(object):
    SECRET_KEY = 'change me'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres_secret_user:postgres_secret_passwd@localhost:5432/tourist_api_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_RECORD_QUERIES = True

    # JWT config
    JWT_SECRET_KEY = 'SUPER-SUPER-SECRET-KEY'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=3)

    RESULTS_PER_PAGE = 10

    PASSWORD_HASH_ALGORITHM = 'pbkdf2:sha512:80000'
    PASSWORD_SALT_LENGTH = 32

    CURRENT_DOMAIN = 'http://127.0.0.1:5000'

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'tourist.adm1@gmail.com'
    MAIL_PASSWORD = 'tourist.adm1password'
    DEFAULT_MAIL_SENDER = 'tourist.adm1@gmail.com'
