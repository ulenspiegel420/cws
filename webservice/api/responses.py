from flask import jsonify


def success(data=None, status=200):
    payload = {'success': True, 'data': data}
    if data is None or status == 204:
        return None, 204
    res = jsonify(payload)
    return res, status
