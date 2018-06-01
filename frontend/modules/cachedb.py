from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Unicode, MetaData, ForeignKey, Date, select
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(8))
    name = Column(Unicode(20))
    surname = Column(Unicode(40))
    mail = Column(Unicode(60))
    shell = Column(Unicode(15))
    homedir = Column(Unicode(15))
    password = Column(Unicode(60))
    issubscribe = Column(Integer)
    issentmail = Column(Integer)
    ispasswordset = Column(Integer)
    date_created = Column(Date)
    status = Column(Integer)
    last_project = Column(Unicode(40))

    def __init__(self, username, name, surname, mail, shell, homedir,
                    password, issubscribe, issentemail, ispasswordset,
                    date_created, status, last_project):
        self.username = username
        self.name = name
        self.surname = surname
        self.mail = mail
        self.shell = shell
        self.homedir = homedir
        self.password = password
        self.issubscribe = issubscribe
        self.issentemail = issentemail
        self.ispasswordset = ispasswordset
        self.date_created = date_created
        self.status = status
        self.last_project = last_project
