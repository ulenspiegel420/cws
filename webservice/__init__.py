from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

metadata = MetaData(naming_convention={
                      "ix": 'ix_%(column_0_label)s',
                      "uq": "uq_%(table_name)s_%(column_0_name)s",
                      "ck": "ck_%(table_name)s_%(column_0_name)s",
                      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                      "pk": "pk_%(table_name)s"
})


db = SQLAlchemy(metadata=metadata)
migrate = Migrate(compare_type=True)
jwt = JWTManager()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Для доступа к сервису необходимо зарегестрироваться'


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    login.init_app(app)

    from webservice.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from webservice.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from webservice.core import bp as core_bp
    app.register_blueprint(core_bp)

    jwt.init_app(app)

    return app
