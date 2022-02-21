import pytest
from unittest import mock
from cors_webservice.api.responses import success, not_found
from cors_webservice.api.checker import make_problem_from_response
from cors_webservice.models import BaseStation, Problem, ProblemSource, ProblemType
from flask import appcontext_pushed, g
from contextlib import contextmanager
import json
from config import Test
from flask import Response
from flask_jwt_extended import create_access_token
from functools import wraps
from cors_webservice import create_app
import jsonschema
from random import randint


@pytest.fixture
def app():
    tester = create_app(Test)
    return tester


@contextmanager
def user_set(app, user):
    def handler(sender, **kwargs):
        g.user_mock = user

    with appcontext_pushed.connected_to(handler, app):
        yield


@pytest.fixture
def problems():
    pass


@contextmanager
def does_not_raise():
    yield


def make_problem(p_src, p_type, p_msg, p_id=None, level=None, timestamp=None):
    p = Problem(p_msg)
    p.source = ProblemSource(p_src)
    p.type = ProblemType(p_type)
    if timestamp is not None:
        p.timestamp = timestamp
    if level is not None:
        p.level = level
    if p_id is not None:
        p.id = p_id
    return p


def make_bs(code, ipaddr=None, bs_id=None, problems=None):
    bs = BaseStation(code, ipaddr)
    if id is not None:
        bs.id = bs_id
    if problems is not None:
        bs.problem_list = problems
    return bs


# def test_success_request():
#     resp_data = {'code': 200, 'message': 'Success operation', 'data': None}
#     response: Response = success(resp_data['message'], resp_data['data'])
#     assert response.status_code == 200
#     assert response.json == {"status": "OK", "message": "Success operation", "data": {}}
#
#
# def test_bad_request(api):
#     resp_data = {'code': 404, 'message': '', 'error': {'reason': 'Resource not found'}}
#     response: Response = not_found(resp_data['error']['reason'], resp_data['message'])
#     assert response.status_code == 404
#     assert response.json == {"status": "Not Found", "message": "", "error": {"reason": "Resource not found"}}


user_mock = mock.Mock()
user_mock.query.filter_by.first.return_value = 'Admin'
user_mock.check_password.return_value = True


@mock.patch('cors_webservice.api.checker.User', user_mock)
def test_login(app):
    with user_set(app, 'admin'):
        with app.test_client() as c:
            rv = c.post('/api/checker/login', content_type='application/json',
                        json={'username': 'Admin', 'password': 'sss'})
            payload = json.loads(rv.data)
            data = payload.get('data', {})
            assert 'access_token' in data


@pytest.mark.parametrize('in_data', [('ROS', 'CONNECTION', 'Cant connect', randint(0, 100), 40, 1611649504),
                                     ('ROS', 'CONNECTION', 'Cant connect', randint(0, 100), 90, 1611649504)])
def test_make_problem_from_resp(in_data):
    field_names = ('source', 'type', 'msg', 'id',  'level', 'timestamp')
    field_values = in_data

    data = dict((x, y) for x, y in zip(field_names, field_values))
    expected = make_problem(*field_values)

    with mock.patch('cors_webservice.api.checker.get_source', return_value=ProblemSource(data['source'])):
        with mock.patch('cors_webservice.api.checker.get_type', return_value=ProblemType(data['type'])):
            result = make_problem_from_response(data)

    assert result.id is None
    assert result.type.type == data['type']
    assert result.source.name == data['source']
    assert result.msg == data['msg']
    assert result.level == data['level']
    assert result.timestamp == data['timestamp']


class TestGetProblems:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Get response",
        "description": "Get problem response data",
        "type": "object",
        "properties": {
            "id": {
                "description": "Basestation code",
                "type": "integer"
            },
            "source": {
                "description": "Source of problem",
                "type": "string"
            },
            "type": {
                "description": "Type of problem",
                "type": "string"
            },
            "msg": {
                "description": "Message for describe problem",
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
            "timestamp": {
                "description": "Timestamp of problem creation",
                "type": "number"
            },
            "level": {
                "description": "Level of importance of problem occurrence",
                "type": "integer",
                "enum": [0, 10, 20, 30, 40, 50]
            }
        },
        "required": ["id", "source", "type", "msg", "timestamp", "level"]
    }

    get_exist_in = ['TST1']

    problems_data = [
        [randint(0, 100), ('ROS', 'CONNECTION', 'Cant connect', randint(0, 100), 40, 1611649504)],
        [randint(0, 100), ('ROS', 'CONNECTION', 'Cant connect', randint(0, 100), 40, 1611649504)],
        [randint(0, 100), None]
    ]

    @pytest.mark.parametrize('in_data', problems_data)
    def test_get_problem(self, in_data, app):
        with app.test_request_context():
            field_names = ('source', 'type', 'msg', 'id',  'level', 'timestamp')
            field_values = in_data[1]

            in_code = in_data[0]

            if field_values is not None:
                bs_rv = make_bs(in_code, '127.0.0.1', 1, [make_problem(*field_values)])
                expected = [dict((x, y) for x, y in zip(field_names, field_values))]
            else:
                bs_rv = make_bs(in_code, '127.0.0.1', 1)
                expected = []

            with app.test_client() as c:
                access_token = create_access_token('admin')
                headers = {'Authorization': 'Bearer {}'.format(access_token)}

                with mock.patch('cors_webservice.api.checker.get_bs', return_value=bs_rv):
                    rv = c.get(f'/api/checker/problems/{in_code}',
                               content_type='application/json',
                               headers=headers)
                    payload = json.loads(rv.data)

                    status = payload.get('status')
                    data = payload.get('data')

                    if len(data) > 0:
                        problem = data[0]
                        jsonschema.validate(problem, self.schema)

                    assert status == 'OK'
                    assert isinstance(data, list)
                    assert data == expected


class TestAddProblem:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Problem",
        "description": "A problem object",
        "type": "object",
        "properties": {
            "code": {
                "description": "Basestation code",
                "type": "string"
            },
            "source": {
                "description": "Source of problem",
                "type": "string"
            },
            "type": {
                "description": "Type of problem",
                "type": "string"
            },
            "msg": {
                "description": "Message for describe problem",
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
            "timestamp": {
                "description": "Timestamp of problem creation",
                "type": "number"
            },
            "level": {
                "description": "Level of importance of problem occurrence",
                "type": "integer",
                "enum": [0, 10, 20, 30, 40, 50]
            }
        },
        "required": ["code", "source", "type", "msg", "timestamp", "level"]
    }

    in_data = [{"code": "TST1", "source": "ROS", "type": "CONNECTION", "msg": "Cant connect", 'level': 40,
                "timestamp": 1611563435},
               {"code": "TST1", "source": "RASP", "type": "DZLOG", "msg": "Dz log error", 'level': 40,
                "timestamp": 1611563425}]
    mock_problems = [make_problem('ROS', 'CONNECTION', 'Cant connect'), make_problem('RASP', 'DZLOG', 'Dz log error')]
    mock_bs = [BaseStation('TST1'), BaseStation('TST1')]
    exp_statuses = ['OK', 'OK']
    exceptions = [does_not_raise(), pytest.raises(jsonschema.ValidationError),
                  pytest.raises(jsonschema.ValidationError)]

    @pytest.mark.parametrize('input_test,mock_problem,mock_bs,expected_status', zip(in_data, mock_problems, mock_bs,
                                                                                    exp_statuses))
    def test_add_valid_problems(self, input_test, mock_problem, mock_bs, expected_status, app):
        data = input_test
        jsonschema.validate(data, self.schema)

        problem = mock_problem
        bs = mock_bs

        with app.test_request_context():
            with app.test_client() as c:
                access_token = create_access_token('admin')
                headers = {'Authorization': 'Bearer {}'.format(access_token)}

                with mock.patch('cors_webservice.api.checker.get_bs') as get_bs_mock:
                    get_bs_mock.return_value = bs
                    with mock.patch('cors_webservice.api.checker.make_problem_from_response', return_value=problem):
                        with mock.patch('cors_webservice.db.session.commit', return_value=True):
                            rv = c.post(f'/api/checker/problems/', content_type='application/json', json=data,
                                        headers=headers)
                            payload = json.loads(rv.data)
                            resp_status_code = rv.status_code
                            data, status = payload['data'], payload['status']

                            assert resp_status_code == 200
                            assert status == 'OK'
