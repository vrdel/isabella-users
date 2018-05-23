#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

import argparse
import csv
import yaml

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Date, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

from datetime import datetime


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
    username = Column(String)
    name = Column(String)
    surname = Column(String)
    mail = Column(String)
    projects = relationship("Projects", secondary="assign")

    def __init__(self, feedid, username, name, surname, mail):
        self.feedid = feedid
        self.username = username
        self.name = name
        self.surname = surname
        self.mail = mail

    #def __repr__(self):
    #    return u"<User('%s','%s', '%s')>" % (self.username, self.name,
    #                                        self.surname, self.mail)


class Projects(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    idproj = Column(String)
    feedid = Column(Integer)
    name = Column(String)
    status = Column(Integer)
    institution = Column(String)
    date_created = Column(Date)
    date_from = Column(Date)
    date_to = Column(Date)

    def __init__(self, feedid, idproj, name, status, institution, date_created,
                 date_from, date_to):
        self.feedid = feedid
        self.idproj = idproj
        self.name = name
        self.status = status
        self.institution = institution
        self.date_created = date_created
        self.date_from = date_from
        self.date_to = date_to

    #def __repr__(self):
    #    return u"<Projects('%s','%s','%s','%s','%s','%s')>" % (self.name,
    #                                                          self.status,
    #                                                          self.institution,
    #                                                          self.date_created,
    #                                                          self.date_from,
    #                                                          self.date_to)


def load_yaml(yamlfile):
    stream = file(yamlfile, 'r')

    return yaml.load(stream)


def load_csv(csvfile):
    with open(csvfile, 'r') as cfh:
        lines = list()
        csvread = csv.reader(cfh)
        for l in csvread:
            lines.append(l)

        return lines


def main():
    parser = argparse.ArgumentParser(description="Isabella users Puppet DB tool")
    parser.add_argument('-c', required=True, help='CSV file', dest='csv')
    parser.add_argument('-y', required=True, help='YAML file', dest='yaml')
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    pr2l = dict(id=0, name=1, inst=2, datefrom=9, dateto=10, datecreate=11, status=12)

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)
        Base.metadata.create_all(engine)

    if args.csv:
        csvcontent = load_csv(args.csv)

    if args.yaml:
        yamlcontent = load_yaml(args.yaml)

    connection = engine.connect()
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    for u, d in yamlcontent['isabella_users'].iteritems():
        try:
            per, proj = d['comment'].split(',')
            idproj = proj.strip()
            proj = filter(lambda x: str(x[pr2l['id']]) == idproj, csvcontent)[0]

        except (IndexError, ValueError):
            continue

        u = User(feedid=0, username=u, name=unicode(per.split(' ')[0], 'utf-8'),
                 surname=unicode(per.split(' ')[1], 'utf-8'), mail='')
        p = Projects(feedid=0, idproj=idproj,
                     date_from=datetime.strptime(proj[pr2l['datefrom']], '%Y-%m-%d'),
                     date_to=datetime.strptime(proj[pr2l['dateto']], '%Y-%m-%d'),
                     name=unicode(proj[pr2l['name']], 'utf-8'),
                     date_created=datetime.strptime(proj[pr2l['datecreate']], '%Y-%m-%d'),
                     status=int(proj[pr2l['status']]),
                     institution=unicode(proj[pr2l['inst']], 'utf-8'))
        u.projects.extend([p])
        session.add(u)
        session.commit()


if __name__ == '__main__':
    main()
