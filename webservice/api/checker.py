from webservice import db
from webservice.api import bp
from flask import request
from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound
from webservice.api.responses import success, bad_request, not_found
from webservice.api.core import get_data_from_request
from webservice.models import User, CheckerResult, Problem, BaseStation, BsCheckResult


def make_problem_from_response(data) -> Problem:
    p_source = get_source(data.get('source', None))
    if p_source is None:
        raise NoResultFound('Such source not found')
    p_type = get_type(data.get('type'))
    if p_type is None:
        raise NoResultFound('Such type not found')

    problem = Problem(data.get('msg', None))
    problem.source = p_source
    problem.type = p_type
    problem.level = data.get('level')
    problem.timestamp = data.get('timestamp')

    return problem


def get_user(username):
    user = User.query.filter_by(username=username).first()
    return user


def get_bs(code) -> BaseStation:
    bs = BaseStation.query.filter_by(code=code).first()
    return bs


def get_all_bs() -> []:
    result = BaseStation.query.all()
    return result


def get_source(source_name):
    result = ProblemSource.query.filter_by(name=source_name).one_or_none()
    return result


def get_type(type_name):
    result = ProblemType.query.filter_by(type=type_name).one_or_none()
    return result


@bp.route('checker/results', methods=['POST'])
def add_total_stats():
    data = request.get_json()

    lead_time = data.get('lead_time')
    if lead_time is None:
        return bad_request("Lead time is required")
    if not isinstance(lead_time, int):
        return bad_request("Lead time must be number")

    start_time = data.get('start_time')
    if start_time is None:
        return bad_request("Start time is required")
    if not isinstance(start_time, str):
        return bad_request("Start time must be str date (mysql timestamp compatibility)")

    try:
        checker_result = CheckerResult(lead_time=lead_time, start_time=start_time)
        db.session.add(checker_result)
        db.session.commit()
        return '', 204
    except Exception as e:
        return str(e), 500


@bp.route('checker/sources')
def get_sources():
    sources = ProblemSource.query.all()
    data = []
    for s in sources:
        data.append({'id': s.id, 'name': s.name})
    return success(data=data)


@bp.route('checker/types')
def get_types():
    types = ProblemType.query.all()
    data = []
    for t in types:
        data.append({'id': t.id, 'name': t.type})
    return success(data=data)


@bp.route('checker/bs/results/add', methods=['POST'])
def add_bs_check_results():
    data = get_data_from_request()
    if 'code' not in data:
        return bad_request("Base station ID required")
    if 'ros_problems' not in data:
        return bad_request("Count ROS problems required")
    if 'rasp_problems' not in data:
        return bad_request("Count raspberry problems required")
    if 'receiver_problems' not in data:
        return bad_request("Count receiver problems required")

    code = data.get('code')
    ros_problems = data.get('ros_problems')
    rasp_problems = data.get('rasp_problems')
    receiver_problems = data.get('receiver_problems')

    if ros_problems < 0 or rasp_problems < 0 or receiver_problems < 0:
        return not_found('Count must be positive number')
    bs = BaseStation.query.filter_by(code=code).first_or_404(description='Base station does not exists')

    try:
        check_result = BsCheckResult(ros_problems, rasp_problems, receiver_problems)
        check_result.id_bs = bs.id

        db.session.add(check_result)
        db.session.commit()
        return success()
    except Exception as e:
        return bad_request(str(e))
