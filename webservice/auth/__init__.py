from flask import Blueprint

bp = Blueprint('auth', __name__)

from webservice.auth import routes
