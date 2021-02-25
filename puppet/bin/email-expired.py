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
    parser.add_argument('-n', required=False, help='No operation mode', dest='noaction', action='store_true')
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

    if args.noaction:
        logger.info("NO EXECUTE mode, just print actions")

    disabled_users = session.query(User).filter(User.status == 0).all()
    disabled_stat = list()
    for user in disabled_users:
        if user.expire_email:
            continue
        dates = [project.date_to for project in user.projects_assign]
        if dates:
            most_recent = max(dates)
            last_project = [project for project in user.projects_assign
                            if project.date_to == most_recent]
            last_project = last_project[0]
            conf_ext = conf_opts['external']
            email = EmailSend(conf_ext['emailtemplatewarn'],
                              conf_ext['emailhtml'], conf_ext['emailsmtp'],
                              conf_ext['emailfrom'], user.mail,
                              last_project, gracedays, logger)
            msg = f'Sent expire email for {user.username} {last_project.idproj} @ {user.mail}'
            if args.noaction:
                logger.info(msg)
                disabled_stat.append(user)
            elif email.send():
                logger.info(msg)
                user.expire_email = True
                disabled_stat.append(user)
                session.commit()

    if not disabled_stat:
        logger.info('No expired users')
    else:
        logger.info(f'Sent emails for {len(disabled_stat)} expired users')


if __name__ == '__main__':
    main()
