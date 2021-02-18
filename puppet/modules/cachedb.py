from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Unicode, MetaData, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship, backref

import datetime

Base = declarative_base()


class Assign(Base):
    __tablename__ = 'assign'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'))
    project_id = Column(ForeignKey('projects.id'))
    when = Column(DateTime, default=datetime.datetime.now)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    feedid = Column(Integer)
    username = Column(Unicode(8))
    name = Column(Unicode(20))
    surname = Column(Unicode(40))
    feeduid = Column(Unicode(60))
    mail = Column(Unicode(60))
    status = Column(Integer)
    date_join = Column(Date)
    consent_disable = Column(Boolean)
    projects = Column(Unicode(40))
    projects_assign = relationship("Projects", secondary="assign", backref=backref('users', order_by=id))

    def __init__(self, feedid, username, name, surname, feeduid, mail,
                 date_join, status, consent_disable, projects):
        self.feedid = feedid
        self.username = username
        self.name = name
        self.surname = surname
        self.feeduid = feeduid
        self.mail = mail
        self.date_join = date_join
        self.status = status
        self.consent_disable = consent_disable
        self.projects = projects


class Projects(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    idproj = Column(Unicode(40))
    feedid = Column(Integer)
    name = Column(Unicode(180))
    respname = Column(Unicode(20))
    respemail = Column(Unicode(60))
    status = Column(Integer)
    grace_status = Column(Boolean)
    institution = Column(Unicode(180))
    date_created = Column(Date)
    date_from = Column(Date)
    date_to = Column(Date)

    def __init__(self, feedid, idproj, name, respname, respemail, status,
                 grace_status, institution, date_created, date_from, date_to):
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
        self.grace_status = grace_status


class MaxUID(Base):
    __tablename__ = 'maxuid'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer)

    def __init__(self, uid):
        self.uid = uid
