from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Unicode, MetaData, ForeignKey, Date, select
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class Assign(Base):
    __tablename__ = 'assign'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'))
    project_id = Column(ForeignKey('projects.id'))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    feedid = Column(Integer)
    username = Column(Unicode(8))
    name = Column(Unicode(20))
    surname = Column(Unicode(40))
    mail = Column(Unicode(60))
    projects = relationship("Projects", secondary="assign", backref=backref('users', order_by=id))

    def __init__(self, feedid, username, name, surname, mail):
        self.feedid = feedid
        self.username = username
        self.name = name
        self.surname = surname
        self.mail = mail


class Projects(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    idproj = Column(Unicode(40))
    feedid = Column(Integer)
    name = Column(Unicode(180))
    respname = Column(Unicode(20))
    respemail = Column(Unicode(60))
    status = Column(Integer)
    institution = Column(Unicode(180))
    date_created = Column(Date)
    date_from = Column(Date)
    date_to = Column(Date)

    def __init__(self, feedid, idproj, name, respname, respemail, status,
                 institution, date_created, date_from, date_to):
        self.feedid = feedid
        self.idproj = idproj
        self.respname = respname
        self.respemail = respemail
        self.name = name
        self.status = status
        self.institution = institution
        self.date_created = date_created
        self.date_from = date_from
        self.date_to = date_to
