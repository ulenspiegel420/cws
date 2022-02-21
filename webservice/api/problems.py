from flask import make_response, request, abort
from flask_jwt_extended import jwt_required
import sqlalchemy.exc
from webservice import db
from webservice.models import BaseStation, Problem
import webservice.api.responses
from webservice.api import bp


@bp.route('problems/bs/<code>')
@jwt_required()
def get_problems(code):
    bs = db.session.query(BaseStation).filter_by(code=code).first()
    if bs is None:
        return abort(404, description='Resource {} not found'.format(code))
    if not bs.problems:
        return webservice.api.responses.success([])
    data = []
    problem_code = request.args.get('code')
    problem_source = request.args.get('source')

    if problem_code:
        for p in bs.problems:
            if p.code == request.args['problem_code']:
                data.append(p)
    else:
        data.extend([p.to_dict() for p in bs.problems])
    return webservice.api.responses.success(data)


@bp.route('problems/bs/<bs_code>', methods=['POST'])
@jwt_required()
def add_problem(bs_code: str):
    bs = BaseStation.query.filter_by(code=bs_code).first()
    if bs is None:
        return abort(404, "That resource not found in service", bs_code)

    data: {} = request.get_json()
    validate_errors = []
    try:
        code = data['code']
        if not isinstance(code, int):
            validate_errors.append(['code', 'Invalid type'])
        source = data['source']
        if not isinstance(source, int):
            validate_errors.append(['source', 'Invalid type'])
        lvl = data['level']
        if not isinstance(lvl, int):
            validate_errors.append(['level', 'Invalid type'])
        timestamp = data['timestamp']
        if not isinstance(timestamp, int):
            validate_errors.append(['timestamp', 'Invalid type'])
        if timestamp <= 0:
            validate_errors.append(['timestamp', 'Invalid value'])
        msg = data['message']
        if not isinstance(msg, str):
            validate_errors.append(['message', 'Invalid type'])
        if len(msg) == 0:
            validate_errors.append(['message', 'Empty value'])
    except KeyError as e:
        validate_errors.append([str(e), 'Field required'])

    if len(validate_errors) != 0:
        return abort(422, 'Validate error',  validate_errors)

    new_problem = Problem(code=code, source=source, level=lvl, msg=msg,  timestamp=timestamp)
    try:
        bs.problems.append(new_problem)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        return abort(422, 'MySQL error {} {}'.format(e.orig.args[0], e.orig.args[1]))
    return webservice.api.responses.success({'id': new_problem.id}, status=201)


@bp.route('problems/<id_param>', methods=['DELETE'])
@jwt_required()
def delete_problem(id_param):
    problem_id = int(id_param)
    problem = db.session.query(Problem).filter_by(id=problem_id).first()
    if problem:
        db.session.delete(problem)
        db.session.commit()
        return webservice.api.responses.success()
    return webservice.api.responses.success(204)
