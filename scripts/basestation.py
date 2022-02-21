from flask import current_app
from flask_script import Command, Option, Group
from webservice import db
from webservice.models import BaseStation
import re
import json


class AddBaseStation(Command):
    def __init__(self):
        super(AddBaseStation, self).__init__()

    def get_options(self):
        return [Group(Option('-j', dest='json_string'), Option('-f', dest='file'), exclusive=True)]

    def run(self, json_string=None, file=None):
        if file is not None:
            try:
                with open(file, 'r') as handle:
                    data = json.load(handle)
            except FileNotFoundError:
                print('File not found')
        elif json_string is not None:

        else:
            print('Any parameters are required')
            return 1





class CollectRaspData(Command):
    option_list = (
        Option('--py3v', dest='py3_version', action='store_true'),
        Option('--glibv', dest='glib_version', action='store_true'),
        Option('--updates', dest='updates', action='store_true'),
        Option('--usb_boot', dest='usb_boot', action='store_true')
    )

    def __init__(self):
        super().__init__()
        self.__ssh_client = paramiko.SSHClient()
        self.__ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

    def __exec_cmd(self, cmd: str) -> str:
        stdin, stdout, stderr = self.__ssh_client.exec_command(cmd)
        reply = stderr.read().strip().decode('utf-8') + stdout.read().strip().decode('utf-8')
        return reply

    def get_py3_version(self) -> str:
        cmd = 'python3 --version'
        reply = self.__exec_cmd(cmd)
        result = '-'
        if reply is not None:
            match = re.search(r"(?<=Python )(\d|\.)+", reply)
            if match is not None:
                result = match.group(0)
        return result

    def get_glib_version(self) -> str:
        cmd = 'ldd --version ldd | grep GLIBC'
        reply = self.__exec_cmd(cmd)
        result = '-'
        if reply is not None:
            match = re.search(r"(?<=GLIBC )(\d|\.)+", reply)
            if match is not None:
                result = match.group(0)
        return result

    def is_usb_boot(self) -> bool:
        cmd = 'vcgencmd otp_dump | grep 17:'
        reply = self.__exec_cmd(cmd)
        result = False
        if reply is not None:
            result = True if reply != '17:1020000a' else False
        return result

    def check_updates(self) -> bool:
        cmd = 'test -f /usr/local/sumcheck2 && echo True || echo False'
        reply = self.__exec_cmd(cmd)
        result = False
        if reply is not None:
            if reply.lower() == 'true':
                result = True
        return result

    def run(self, py3_version=None, glib_version=None, updates=None, usb_boot=None):
        current_app.logger.info('Start collecting rasp data command')

        n = 1
        current_app.logger.debug(f"Pass #{str(n)}")
        for bs in db.session.query(BaseStation):
            try:
                self.__ssh_client.connect(bs.ipaddr, 8822, 'pi', 'eftcors' + bs.code)
            except Exception as e:
                current_app.logger.error(f"Cant connect to mpc on  {bs.code}: {str(e)}")
                self.__ssh_client.close()
                continue

            py3_ver = None
            try:
                if py3_version:
                    py3_ver = self.get_py3_version()
            except Exception as e:
                current_app.logger.error(f"Cant get python3 version on  {bs.code}: {str(e)}")
            else:
                if bs.py_version != py3_ver:
                    bs.py_version = py3_ver

            glib_ver = None
            try:
                if glib_version:
                    glib_ver = self.get_glib_version()
            except Exception as e:
                current_app.logger.error(f"Cant get glib version on  {bs.code}: {str(e)}")
            else:
                if bs.glib_version != glib_ver:
                    bs.glib_version = glib_ver

            is_mpc_updated = None
            try:
                if updates:
                    is_mpc_updated = self.check_updates()
            except Exception as e:
                current_app.logger.error(f"Cant check last update on  {bs.code}: {str(e)}")
            else:
                if bs.is_mpc_updated != is_mpc_updated:
                    bs.is_mpc_updated = is_mpc_updated

            is_usb_boot = None
            try:
                if usb_boot:
                    is_usb_boot = self.is_usb_boot()
            except Exception as e:
                current_app.logger.error(f"Cant get usb boot state  {bs.code}: {str(e)}")
            else:
                if bs.is_usb_boot != is_usb_boot:
                    bs.is_usb_boot = is_usb_boot

            self.__ssh_client.close()
            db.session.commit()
            current_app.logger.debug(f'BS {bs.code} data updated')
            n += 1
