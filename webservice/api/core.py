from werkzeug import exceptions
from flask import request
from webservice.api.responses import bad_request


def get_data_from_request():
    try:
        data = request.get_json()
    except exceptions.BadRequest as e:
        return bad_request(e.description)
    else:
        return data
