from flask import g, request, jsonify, abort, make_response
from webservice import jwt
from webservice.models import User
from flask_jwt_extended import create_access_token
from hmac import compare_digest
from webservice.api import bp


# def authenticate(username, password):
#     user = User.query.filter_by(username=username).first()
#     if user and compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
#         return user
#
#
# def identity(payload):
#     user_id = payload['identity']
#     return User.query.filter_by(id=user_id).first()

@jwt.unauthorized_loader
def unauthorized_callback(err):
    return make_response({"success": False, "reason": "Unauthorized", "data": "Token required"}, 401)


@bp.route('/auth/login', methods=['POST'])
def login():
    if not request.is_json:
        abort(400, 'Missing JSON in request')

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username:
        abort(400, 'Missing username parameter')
    if not password:
        abort(400, 'Missing password parameter')

    user = User.query.filter_by(username=username).first()

    if user is None:
        abort(401, description='Incorrect login or password')

    if not user.check_password(password):
        abort(401, description='Incorrect login or password')

    access_token = create_access_token(identity=username)
    return jsonify({'success': True, 'msg': 'Ok', 'data': {'access_token': access_token}})

