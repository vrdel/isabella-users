from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Unicode, MetaData, ForeignKey, Date, Boolean, select
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(8))
    name = Column(Unicode(20))
    surname = Column(Unicode(40))
    email = Column(Unicode(60))
    shell = Column(Unicode(15))
    homedir = Column(Unicode(15))
    password = Column(Unicode(60))
    uid = Column(Integer)
    gid = Column(Integer)
    issubscribe = Column(Boolean)
    ispasswordset = Column(Boolean)
    ishomecreated = Column(Boolean)
    issgeadded = Column(Boolean)
    issentemail = Column(Boolean)
    date_created = Column(Date)
    status = Column(Integer)
    project = Column(Unicode(40))
    last_project = Column(Unicode(40))

    def __init__(self, username, name, surname, email, shell, homedir, password,
                 uid, gid, issubscribe, ispasswordset, ishomecreated,
                 issgeadded,  issentemail, date_created, status, project,
                 last_project):
        self.username = username
        self.name = name
        self.surname = surname
        self.email = email
        self.shell = shell
        self.homedir = homedir
        self.password = password
        self.uid = uid
        self.gid = gid
        self.issubscribe = issubscribe
        self.issentemail = issentemail
        self.ispasswordset = ispasswordset
        self.ishomecreated = ishomecreated
        self.issgeadded = issgeadded
        self.date_created = date_created
        self.status = status
        self.project = project
        self.last_project = last_project
