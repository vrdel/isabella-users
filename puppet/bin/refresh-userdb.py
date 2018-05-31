#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

import argparse

from isabella_users_puppet.cachedb import Base, User, Projects

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

import datetime


def is_date(date):
    try:
        _ = datetime.datetime.strptime(date, '%Y-%m-%d')
        t = tuple(int(i) for i in date.split('-'))

        return datetime.date(*t)

    except ValueError:
        print 'Date not in %Y-%m-%d format'

        raise SystemExit(1)


def all_false(cont):
    for e in cont:
        if e:
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description="isabella-users-puppet disable user DB")
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-t', required=True, help='YYY-MM-DD', type=is_date, dest='date')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    for p in session.query(Projects):
        if p.date_to < args.date:
            p.status = 0
        else:
            p.status = 1

    for u in session.query(User):
        proj_statuses = [p.status for p in u.projects]
        if all_false(proj_statuses):
            u.status = 0
        else:
            u.status = 1
        proj_datecreate = [(p.id, p.date_created) for p in u.projects if p.status == 1]
        if proj_datecreate:
            last = max(proj_datecreate)
            plast = session.query(Projects).filter(Projects.id == last[0]).one()
            u.last_project = plast.idproj

    session.commit()


if __name__ == '__main__':
    main()
