from webservice.api import bp
from flask_jwt_extended import jwt_required
import webservice.api.responses


@bp.route('/ping')
@jwt_required()
def ping():
    pass
    return webservice.api.responses.success('pong')