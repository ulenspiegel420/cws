import json
import os
import logging.config
from webservice import create_app, models, db
import scripts.basestation
from dotenv import load_dotenv

load_dotenv('.env')

basedir = os.path.abspath(os.path.dirname(__file__))

with open(os.environ.get('LOGGING_CONFIG')) as handler:
    cfg = json.load(handler)
    cfg['loggers']['root']['handlers'].append('manager_hndl')
logging.config.dictConfig(cfg)

app = create_app(os.environ.get('APP_CONFIG'))
app.logger.info("Manager startup")
manager = Manager(app)


def _make_context():
    return dict(app=app, db=db, models=models)


manager.add_command("runserver", Server())
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("add_basestations", scripts.basestation.AddBaseStation())
manager.add_command('collect_rasp_data', scripts.basestation.CollectRaspData())


if __name__ == "__main__":
    manager.run()
