import ros_api


def load_modem_info(basestation: str, ipaddr: str):
    with ros_api.Api(ipaddr, 'eft', 'admin-eftcors') as api:
        pass