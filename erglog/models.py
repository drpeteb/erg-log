from pyramid.security import (
    Allow,
    Everyone,
    )

from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    Boolean,
    ForeignKey
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )

from zope.sqlalchemy import ZopeTransactionExtension

# Database session
class DBInterface(object):

    def add_to_db(self, thing):
        try:
            DBSession.add(thing)
            DBSession.flush()
        except DBAPIError:
            raise

    def list_all(self, thing):
        try:
            thing_list = DBSession.query(thing).all()
        except DBAPIError:
            thing_list = []
        return thing_list

    def get_rower_by_username(self, username):
        try:
            rower = DBSession.query(Rower).filter_by(username=username).one()
            return rower
        except DBAPIError:
            raise
        

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DBI = DBInterface()

# Security
class RootFactory(object):
    __acl__ = [ (Allow, 'group:members', 'standard'),
                (Allow, 'group:admins', 'admin') ]
    def __init__(self, request):
        pass

# SQLAlchemy ORM classes
Base = declarative_base()

class Rower(Base):
    __tablename__ = 'rowers'
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True)
    password = Column(Text)
    name = Column(Text, unique=True)
    admin = Column(Boolean)

    def __init__(self, username, password, name, admin=False):
        self.username = username
        self.password = password
        self.name = name
        self.admin = admin

class ErgTypeTime(Base):
    __tablename__ = 'fixed_times'
    id = Column(Integer, primary_key=True)
    time = Column(Integer, unique=True)

    def __init__(self, time):
        self.time = time

class ErgTypeDistance(Base):
    __tablename__ = 'fixed_distances'
    id = Column(Integer, primary_key=True)
    distance = Column(Integer, unique=True)

    def __init__(self, distance):
        self.distance = distance

class ErgRecordTime(Base):
    __tablename__ = 'time_erg_records'
    id = Column(Integer, primary_key=True)
    rower_id = Column(Integer, ForeignKey('rowers.id'))
    rower = relationship("Rower", backref=backref('time_erg_records', order_by=id))
    date = Column(Date, unique=True)
    time = Column(Integer, ForeignKey('fixed_times.time'))
    distance = Column(Integer)

    def __init__(self, rower_id, date, time, distance):
        self.rower_id = rower_id
        self.date = date
        self.distance = distance
        self.time = time

class ErgRecordDistance(Base):
    __tablename__ = 'distance_erg_records'
    id = Column(Integer, primary_key=True)
    rower_id = Column(Integer, ForeignKey('rowers.id'))
    rower = relationship("Rower", backref=backref('distance_erg_records', order_by=id))
    date = Column(Date, unique=True)
    time = Column(Integer)
    distance = Column(Integer, ForeignKey('fixed_distances.distance'))

    def __init__(self, rower_id, date, time, distance):
        self.rower_id = rower_id
        self.date = date
        self.distance = distance
        self.time = time
