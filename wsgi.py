import os
from webservice import create_app, db
from webservice.models import User, BaseStation, Problem
import click
import json
import logging.config


try:
    with open('logging.json') as f:
        logging.config.dictConfig(json.load(f))
except FileNotFoundError:
    logging.basicConfig()

cfg = os.getenv('FLASK_CONFIG') or 'default_config'
flask_env = os.getenv('FLASK_ENV') or 'Development'
app = create_app(cfg+'.'+flask_env)
app.logger.info('CORS WebService startup')


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Problem=Problem)


@app.cli.command()
@click.option('--json', 'json_str', help='Add basestation')
def add_basestation(json_str):
    if json_str is None or json_str == '':
        print('JSON string required')
        return -1
    data = json.loads(json_str)
    new_stations = [BaseStation(code=i['code'], ipaddr=i['ipaddr']) for i in data]

    try:
        db.session.add_all(new_stations)
        items_count = len(db.session.new)
        db.session.commit()

        print(f'Successful added {str(items_count)} records')
    except Exception as e:
        print('Error occurred: ' + str(e))


if __name__ == '__main__':
    app.run()
