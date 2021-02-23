#!/usr/bin/python3

from isabella_users_puppet.cachedb import User, Projects

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from isabella_users_puppet.config import parse_config
from isabella_users_puppet.log import Logger
from isabella_users_puppet.msg import EmailSend

import argparse
import datetime
import sys

conf_opts = parse_config()


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="warn users that they are not active anymore")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    cachedb = conf_opts['settings']['cache']
    gracedays = datetime.timedelta(days=conf_opts['settings']['gracedays'])

    if args.sql:
        cachedb = args.sql

    engine = create_engine('sqlite:///%s' % cachedb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    # take into account only users for which grace period is active
    # send two emails for them - on the date_to of last active project
    # and date_to + gracedays. if user is marked
    grace_users = session.query(User).filter(User.status == 2).all()
    for user in grace_users:
        print(user.username)
        dates = [project.date_to for project in user.projects_assign]
        most_recent = max(dates)
        last_project = [project for project in user.projects_assign
                        if project.date_to == most_recent]
        last_project = last_project[0]
        if last_project.date_to == datetime.date.today():
            print('grace active - i would send an email')
            print(f' {user.username}')
            conf_ext = conf_opts['external']
            email = EmailSend(conf_ext['emailtemplatewarn'],
                              conf_ext['emailhtml'], conf_ext['emailsmtp'],
                              conf_ext['emailfrom'], 'dvrcic@srce.hr',
                              gracedays, logger)
            email.send()
        if last_project.date_to + gracedays == datetime.date.today():
            print('end grace - i would send an email')
            print(f' {user.username}')


if __name__ == '__main__':
    main()
