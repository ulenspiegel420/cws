import os
import dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
dotenv.load_dotenv()


class Default(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 2592000
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    SQLALCHEMY_ECHO = False
    CHR_HOST = os.environ.get('CHR_HOST')
    CHR_USER = os.environ.get('CHR_USER')
    CHR_PWD = os.environ.get('CHR_PWD')


class Test(Default):
    TESTING = True
    DEBUG = True
    ENV = 'TESTING'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'Qwerty12345'


class Development(Default):
    DEBUG = True
    ENV = "DEVELOPMENT"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = False
    JWT_COOKIE_SECURE = False


class Production(Default):
    ENV = "PRODUCTION"
