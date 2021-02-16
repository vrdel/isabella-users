#!/usr/bin/python3

from isabella_users_puppet.cachedb import User, Projects

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from isabella_users_puppet.config import parse_config
from isabella_users_puppet.log import Logger

import argparse
import datetime
import sys


conf_opts = parse_config()


def is_date(date):
    try:
        _ = datetime.datetime.strptime(date, '%Y-%m-%d')
        t = tuple(int(i) for i in date.split('-'))

        return datetime.date(*t)

    except ValueError:
        print('Date not in %Y-%m-%d format')

        raise SystemExit(1)


def all_false(cont):
    for e in cont:
        if e:
            return False

    return True


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="isabella-users-puppet disable user DB")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-t', required=False, help='YYY-MM-DD', type=is_date, dest='date')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    cachedb = conf_opts['settings']['cache']
    gracedays = datetime.timedelta(days=conf_opts['settings']['gracedays'])

    if args.sql:
        cachedb = args.sql

    if args.date:
        date = args.date
    else:
        date = datetime.date.today()

    engine = create_engine('sqlite:///%s' % cachedb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    logger.info("Update projects and users expired on %s" % date)

    # is project expired or not. allow some graceperiod and treat it as active
    # in such.
    for p in session.query(Projects):
        if p.date_to + gracedays < date:
            p.status = 0
        else:
            p.status = 1

    # conclude if user is active or not. user is active only if he's assigned
    # to at least one active project (set previously).
    for u in session.query(User):
        proj_statuses = [p.status for p in u.projects]
        if all_false(proj_statuses):
            u.status = 0
        else:
            u.status = 1

    session.commit()


if __name__ == '__main__':
    main()
