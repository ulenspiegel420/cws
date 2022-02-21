from webservice import login, db, jwt
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    pwd_hash = Column(String(128))
    token = Column(String(32), index=True, unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def set_password(self, pwd):
        self.pwd_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.pwd_hash, pwd)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class BaseStation(db.Model):
    __tablename__ = 'base_stations'
    id = Column(Integer, primary_key=True)
    code = Column(String(4), unique=True, nullable=False)
    ipaddr = Column(String(15), unique=True)
    _problems = relationship('Problem', back_populates='bs')
    receiver_updated_pwd = Column(Boolean)
    py_version = Column(String(10))
    glib_version = Column(String(20))
    _is_mpc_updated = Column('is_mpc_updated', Boolean)
    _is_usb_boot = Column('is_usb_boot', Boolean)

    def __init__(self, code: str, ipaddr=None):
        self.code = code
        if ipaddr:
            self.ipaddr = ipaddr

    def has_problem(self, p_src: str, p_type: str) -> bool:
        for p in self._problems:
            if p.source.name == p_src and p.type.type == p_type:
                return True
        return False

    @property
    def problems_count(self):
        return len(self._problems)

    @property
    def has_problems(self):
        if self.problems_count > 0:
            return True
        return False

    @hybrid_property
    def problems(self):
        return self._problems

    @problems.setter
    def problems(self, value):
        if not isinstance(value, list):
            raise TypeError('Value is not list type')
        self.query.exist()
        self._problems = value

    @hybrid_property
    def is_mpc_updated(self):
        return self._is_mpc_updated

    @is_mpc_updated.setter
    def is_mpc_updated(self, value):
        self._is_mpc_updated = value

    @hybrid_property
    def is_usb_boot(self):
        return self._is_usb_boot

    @is_usb_boot.setter
    def is_usb_boot(self, value):
        self._is_usb_boot = value


class Problem(db.Model):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    bs_id = Column(Integer, ForeignKey('base_stations.id'))
    code = Column(Integer)
    source = Column(Integer)
    timestamp = Column('timestamp', Float, nullable=False)
    msg = Column('msg', String(250))
    level = Column('level', Integer, nullable=False)
    bs = relationship('BaseStation', back_populates='_problems')

    __table_args__ = (UniqueConstraint('code', 'source'),)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'source': self.source,
            'msg': self.msg,
            'level': self.level,
            'timestamp': self.timestamp
        }


class BsCheckResult(db.Model):
    __tablename__ = 'bs_check_results'
    id = Column(Integer, primary_key=True)
    bs_id = Column(Integer, ForeignKey('base_stations.id'), nullable=False)
    count_ros_problems = Column(Integer)
    count_rasp_problems = Column(Integer)
    count_receiver_problems = Column(Integer)
    start_time = Column(DateTime)

    def __init__(self, ros_count, rasp_count, receiver_count):
        self.count_ros_problems = ros_count
        self.count_rasp_problems = rasp_count
        self.count_receiver_problems = receiver_count


class CheckerResult(db.Model):
    __tablename__ = 'checker_results'
    id = Column(Integer, primary_key=True)
    start_time = Column(TIMESTAMP, nullable=False)
    lead_time = Column(Integer)
