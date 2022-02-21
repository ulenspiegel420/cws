from flask import render_template, redirect, url_for, flash, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func
from webservice.core import bp
from webservice import db
from webservice.models import BaseStation, Problem, CheckerResult
import ros


def timestamp_to_datestr(ts, format='%Y-%d-%m'):
    dt = datetime.fromtimestamp(ts)
    result = dt.strftime(format)
    return result


def load_active_secrets():
    result = []
    if ros.connect('185.91.52.137:8728'):
        response = {}
        if ros.login('ros_api', 'n0Tx5KQ8$=*3Bg#q'):
            response = ros.get('/ppp/active')
            ros.close()
        result = [i['comment'] for i in response if i.get('comment') is not None]
    return result


def load_secret(bs_code: str):
    result = {}
    if ros.connect('185.91.52.137:8728'):
        secret_data = {}
        active_data = {}
        if ros.login('ros_api', 'n0Tx5KQ8$=*3Bg#q'):
            secret_data = ros.get('/ppp/secret', comment=bs_code)
            active_data = ros.get('/ppp/active', comment=bs_code)
            ros.close()

        if len(secret_data) == 1:
            result['secret'] = secret_data[0]
        if len(active_data) == 1:
            result['active'] = active_data[0]
    return result


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('core.active'))


@bp.route('/bs/<bs_id>')
@login_required
def basestation(bs_id):
    bs: BaseStation = db.session.query(BaseStation).filter_by(id=bs_id).first()
    secret_data = load_secret(bs.code)

    problems_data = []
    for p in bs.problems:
        problems_data.append({'id': p.id, 'source': p.source, 'msg': p.msg, 'lvl': p.level,
                              'ts': timestamp_to_datestr(p.timestamp)})
    view_data = {
        'id': bs.id,
        'ip': bs.ipaddr,
        'code': bs.code,
        'is_disabled': True if secret_data['secret']['disabled'] == 'true' else False,
        'last_logout': secret_data['secret']['last-logged-out'],
        'is_active': True if 'active' in secret_data else False,
        'cors_id': secret_data['secret']['name'],
        'service': secret_data['secret'].get('service'),
        'uptime': secret_data.get('active', {}).get('uptime'),
        'encoding': secret_data.get('active', {}).get('encoding'),
        'problems': problems_data
    }
    return render_template('basestation.html', title=f'БС {bs.code}', view_data=view_data)


@bp.route('/bs/active')
@login_required
def active():
    q = db.session.query(BaseStation.id,
                         BaseStation.code,
                         BaseStation.ipaddr,
                         func.count(Problem.id).label('count'))\
        .outerjoin(Problem).group_by(BaseStation.id)

    active_codes = load_active_secrets()
    view_data = []
    for data in q.all():
        bs_code = data.code
        ip = data.ipaddr
        is_active = True if bs_code in active_codes else False
        problems_count = data.count

        item = {'id': data.id, 'code': bs_code, 'ip': ip, 'is_active': is_active, 'problems_count': problems_count}
        view_data.append(item)
    return render_template('active.html', title='Список БС', view_data=view_data)


@bp.route('/bs/problems')
@login_required
def problems():
    q = db.session.query(BaseStation.id,
                         Problem.id,
                         BaseStation.code,
                         Problem.msg,
                         Problem.level,
                         Problem.source,
                         Problem.timestamp).join(Problem)
    danger = {}
    warning = {}
    for bs_id, problem_id, code, msg, level, problem_src, timestamp in tuple(q.all()):
        ts = datetime.fromtimestamp(timestamp).strftime('%Y-%d-%m %H:%H')
        p = {'id': problem_id, 'msg': msg, 'source': problem_src, 'lvl': level, 'ts': ts}

        if level == 40:
            if bs_id in danger:
                danger[bs_id]['problems'].append(p)
            else:
                danger[bs_id] = {'code': code, 'problems': [p]}
        else:
            if bs_id in warning:
                warning[bs_id]['problems'].append(p)
            else:
                warning[bs_id] = {'code': code, 'problems': [p]}
    danger_count = 0
    for v in danger.values():
        tmp = len(v['problems'])
        danger_count += tmp
    warning_count = 0
    for v in warning.values():
        tmp = len(v['problems'])
        warning_count += tmp

    chk_res = db.session.query(CheckerResult.start_time, CheckerResult.lead_time).\
        order_by(CheckerResult.id.desc()).first()
    start_time = ''
    end_time = ''
    if chk_res:
        start_time = (chk_res[0] + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (start_time + timedelta(seconds=chk_res[1])).strftime('%Y-%m-%d %H:%M:%S')

    view_data = {'danger': danger,
                 'warning': warning,
                 'danger_count': danger_count,
                 'warning_count': warning_count,
                 'start_time': start_time,
                 'end_time': end_time}

    return render_template('problems.html', title='Problems', view_data=view_data)


@bp.route('/bs/mpc/info')
@login_required
def mpc_data():
    view_data = {}
    q = db.session.query(BaseStation.code,
                         BaseStation.id,
                         BaseStation.py_version,
                         BaseStation.glib_version,
                         BaseStation.is_mpc_updated,
                         BaseStation.is_usb_boot)
    py_stat, glib_stat, update_stat, data = {}, {}, {}, {}
    for code, bs_id, py_ver, glib_ver, is_mpc_updated, is_usb_boot in q:
        py_ver_value = '-' if py_ver is None else py_ver
        if py_ver_value in py_stat:
            py_stat[py_ver_value] += 1
        else:
            py_stat[py_ver_value] = 1

        glib_ver_value = '-' if glib_ver is None else glib_ver
        if glib_ver_value in glib_stat:
            glib_stat[glib_ver_value] += 1
        else:
            glib_stat[glib_ver_value] = 1

        update_value = 'Да' if is_mpc_updated else 'Нет'
        if update_value in update_stat:
            update_stat[update_value] += 1
        else:
            update_stat[update_value] = 1

        data[bs_id] = {'code': code,
                       'py_ver': py_ver_value,
                       'glib_ver': glib_ver_value,
                       'is_mpc_updated': update_value,
                       'is_usb_boot': is_usb_boot
                       }
    view_data['py3_stat'] = py_stat
    view_data['glib_stat'] = glib_stat
    view_data['update_stat'] = update_stat
    view_data['data'] = data

    return render_template('mpc_data.html', view_data=view_data)


def get_str_source(source_id):
    if source_id == 1:
        return 'BS'
    elif source_id == 2:
        return 'RASP'
    elif source_id == 3:
        return 'ROUTER'
    elif source_id == 4:
        return 'RECEIVER'
    else:
        return 'UNKNOWN'


@bp.route('/ros/secrets/active')
@login_required
def active_secrets():
    return jsonify(load_active_secrets())
