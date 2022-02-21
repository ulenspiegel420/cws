import ros_api
from flask_script import Command
from flask import current_app
from cors_webservice import db
from cors_webservice.models import BaseStation
from cors_webservice.utils import load_modem_info


class UpdateModemInfo(Command):
    def __init__(self):
        super().__init__()

    def run(self):
        current_app.logger.info('Start updating modems info')

        for bs in db.session.query(BaseStation).all():
            try:
                with ros_api.Api(bs.ipaddr, 'eft', 'admin-eftcors') as api:
                    modem_info = api.get_usb_device('1-1')
            except Exception as e:
                current_app.logger.error(f'Update modem info: {str(e)}')
            else:
                if bs.has_modem():
                    pass
                else:
                    pass
