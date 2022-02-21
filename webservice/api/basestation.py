from flask import current_app, request, jsonify
from webservice import db
from flask_jwt_extended import jwt_required
from webservice.models import BaseStation, Problem
from webservice.api.responses import success
from webservice.core.routes import load_active_secrets
from webservice.api import bp


@bp.route('bs')
@jwt_required()
def get_all_bs():
    q = db.session.query(BaseStation.code,
                         BaseStation.id,
                         BsProblems.problem_id,
                         BsProblems.level,
                         BaseStation.ipaddr,
                         BaseStation.receiver_updated_pwd,
                         ProblemSource.name,
                         ProblemType.type)
    q = q.outerjoin(BaseStation.problems).outerjoin(BsProblems.problem)
    q = q.outerjoin(ProblemSource, ProblemSource.id == Problem.src_id)
    q = q.outerjoin(ProblemType, ProblemType.id == Problem.type_id)

    active_codes = load_active_secrets()

    data = {}
    for row in q.all():
        if row.problem_id is None:
            problem = None
        else:
            problem = {'id': row.problem_id, 'source': row.name, 'type': row.type, 'level': row.level}

        if row.code not in data:
            data[row.code] = {'id': row.id,
                              'ipaddr': row.ipaddr,
                              'is_active': True if row.code in active_codes else False,
                              'receiver_updated_pwd': row.receiver_updated_pwd}
            if problem is not None:
                data[row.code]['problems'] = [problem]
        else:
            if problem is not None:
                data[row.code]['problems'].append(problem)

    return jsonify({'success': True, 'data': data}), 200



@bp.route('bs/<code>')
def get_bs_by_code(code):
    bs: BaseStation = BaseStation.query.filter_by(code=code).first()

    if bs is None:
        return jsonify({'data': {'resource': code}}), 404

    data = {
        'id': bs.id,
        'ipaddr': bs.ipaddr,
        'is_active': True if code in load_active_secrets() else False,
        'receiver_updated_pwd': bs.receiver_updated_pwd
        }

    q = db.session.query(Problem.id, ProblemSource.name.label('source'), ProblemType.type, BsProblems.level)
    q = q.join(BsProblems, ProblemSource, ProblemType).join(BaseStation).filter_by(code=bs.code)

    problems = []
    for row in q.all():
        problems.append(row._asdict())
    if len(problems) > 0:
        data['problems'] = problems

    return jsonify({'success': True, 'data': data})


@bp.route('bs/ipaddr')
def get_all_ipaddr():
    try:
        basestations = BaseStation.query.all()
    except Exception as e:
        return error_response(503, str(e))
    if basestations is not None:
        codes = {s.code: s.ipaddr for s in basestations}
        return success(data=codes)
    return success(data=[])
