from flask import jsonify
from flask import request, g
from webservice.models import ReceiverSample
from webservice.api.auth import token_auth
from webservice.api.responses import bad_request
from webservice.api import bp
from webservice import db


# def check_fields_exist(fields: (), data: dict):
#     not_existed_fields = []
#     valid_fields = []
#     for field in fields:
#         if field in data:
#             valid_fields.append(field)
#             if type(data[field]) is dict:
#                 not_existed_fields.extend(check_fields_exist([f for f in fields if f not in valid_fields], data[field]))
#         else:
#             not_existed_fields.append(field)
#     return not_existed_fields

def get_dict_keys(data: dict):
    keys = list(data.keys())
    for field in data:
        if type(data[field]) is dict:
            keys.extend(get_dict_keys(data[field]))
    return keys


def get_invalid_fields(fields: (), data: dict) -> tuple:
    keys = set(get_dict_keys(data))
    current_fields = set(fields)
    if current_fields != keys:
        return tuple(current_fields.difference(keys))
    return ()


def __check_fields(response: dict, required: tuple) -> bool:
    states = [field in response for field in set(required)]
    return False if False in states else True


def __parse_satellites_data(response: list) -> dict:
    required_fields = {'gps', 'glonass', 'beidou', 'galileo', 'qzss', 'irnss', 'sbas'}
    fields = set([item['system'] for item in response])
    diff = len(required_fields.symmetric_difference(fields))

    if diff == 0:
        result = {item['system']: item['count'] for item in response}
    else:
        result = None
    return result


@bp.route('samples/receiver', methods=['POST'])
@token_auth.login_required
def add_sample():
    try:
        data = request.get_json()

        if data == {}:
            return bad_request("Empty request")

        if 'pdop' not in data:
            return bad_request("Field `pdop` required")
        if 'mask' not in data:
            return bad_request("Field `mask` required")
        if 'uptime' not in data:
            return bad_request("Field `uptime` required")
        if 'temperature' not in data:
            return bad_request("Field `temperature` required")
        if 'used_satellites' not in data:
            return bad_request("Field `used_satellites` required")

        sat_data = {i['system']: i['count'] for i in data['used_satellites']
                     if __check_fields(i, ('system', 'count'))}

        if 'gps' not in sat_data:
            return bad_request("Gps data invalid")
        if 'glonass' not in sat_data:
            return bad_request("Glonass data invalid")
        if 'beidou' not in sat_data:
            return bad_request("Beidou data invalid")
        if 'galileo' not in sat_data:
            return bad_request("Galileo data invalid")
        if 'qzss' not in sat_data:
            return bad_request("Qzss data invalid")
        if 'irnss' not in sat_data:
            return bad_request("Irnss data invalid")
        if 'sbas' not in sat_data:
            return bad_request("Sbas data invalid")

        sample = ReceiverSample(data['pdop'], data['mask'], data['uptime'], data['temperature'], sat_data['gps'],
                                sat_data['glonass'], sat_data['beidou'], sat_data['galileo'], sat_data['qzss'],
                                sat_data['irnss'], sat_data['sbas'])
        sample.cors = g.current_cors
        db.add(sample)
        db.commit()

        response = jsonify({'status': 'ok'})
        response.status_code = 201
        return response
    except ValueError as e:
        return bad_request(str(e))
    except TypeError as e:
        return bad_request(str(e))

# sample_data = {
#         'pdop': 1,
#         'uptime': 3600,
#         'temperature': 44.3,
#         'used_satellites': {
#             'gps': 2,
#             'glonass': 1,
#             'beidou': 4,
#             'galileo': 0,
#             'qzss': 0,
#             'irnss': 0,
#             'sbas': 0
#         }
#     }
