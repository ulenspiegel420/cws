from flask import Blueprint
from flask_jwt_extended import jwt_required
import webservice.api.responses


bp = Blueprint('api', __name__)
from webservice.api import auth, basestation, problems, routes


@bp.errorhandler(404)
def http_404_handler(error):
    return {'success': False, 'reason': error.description, 'data': error.response}, 404


@bp.errorhandler(405)
def http_405_handler(error):
    return {'success': False, 'reason': 'Not allowed'}, 405


@bp.errorhandler(422)
def http_422_handler(error):
    return {'success': False, 'reason': error.description, 'data': error.response}, 422


@bp.errorhandler(500)
def http_500_handler(error):
    return {'success': False, 'reason': 'Internal server error'}, 500


@bp.errorhandler(ValueError)
def http_400_handler(error):
    return {'success': False, 'reason': 'Bad request', 'data': str(error)}, 400


@bp.errorhandler(400)
def http_400_handler(error):
    return {'success': False, 'reason': 'Bad request', 'data': {'description': error.description}}, 400


@bp.errorhandler(401)
def http_401_handler(error):
    return {'success': False, 'reason': 'Unauthorized', 'data': error.description}, 401
