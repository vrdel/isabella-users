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

    parser = argparse.ArgumentParser(description="set user's and project's status flags based on the interested date and state in cache.db . reflect user's project assignments in appropriate field.")
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

    logger.info("Set status flags for projects and users expired on %s, after period of grace %s days" % (date, gracedays.days))

    # set status for projects. project is dead if status is 0. it's expired
    # (status = 0) but in mercy grace period if grace_status = 2. otherwise
    # project is active - status = 1.
    for project in session.query(Projects):
        if project.date_to + gracedays < date:
            project.status = 0
        elif project.date_to + gracedays > date and project.date_to < date:
            project.status = 2
        else:
            project.status = 1

    # conclude if user is active or not. user is active only if he's assigned
    # to at least one active project (set previously).
    # set also all current project assignments in the field projects as it will
    # be checked on update-useryaml.py
    for user in session.query(User):
        proj_statuses = [project.status for project in user.projects_assign]
        if all_false(proj_statuses):
            user.status = 0
        else:
            user.status = 1
        all_projects = [project.idproj for project in user.projects_assign]
        user.projects = ' '.join(all_projects)

    session.commit()


if __name__ == '__main__':
    main()
