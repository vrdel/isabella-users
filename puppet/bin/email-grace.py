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


def is_date(date):
    """
        Enforce specific date format on argument
    """
    try:
        _ = datetime.datetime.strptime(date, '%Y-%m-%d')
        t = tuple(int(i) for i in date.split('-'))

        return datetime.date(*t)

    except ValueError:
        print('Date not in %Y-%m-%d format')

        raise SystemExit(1)


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="warn users that they are not active anymore")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-n', required=False, help='No operation mode', dest='noaction', action='store_true')
    parser.add_argument('-t', required=False, help='YYYY-MM-DD', type=is_date, dest='date')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    cachedb = conf_opts['settings']['cache']
    gracedays = datetime.timedelta(days=conf_opts['settings']['gracedays'])

    if args.sql:
        cachedb = args.sql

    if args.date:
        datenow = args.date
    else:
        datenow = datetime.date.today()

    engine = create_engine('sqlite:///%s' % cachedb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    if args.noaction:
        logger.info("NO EXECUTE mode, just print actions")

    # take into account only users for which grace period is active
    # send two emails for them - on the date_to of last active project
    # and date_to + gracedays.
    grace_users = session.query(User).filter(User.status == 2).all()
    grace_stat, expire_stat = list(), list()
    for user in grace_users:
        if user.grace_email:
            continue

        dates = [project.date_to for project in user.projects_assign]
        most_recent = max(dates)
        last_project = [project for project in user.projects_assign
                        if project.date_to == most_recent]
        last_project = last_project[0]

        if last_project.date_to == datenow:
            conf_ext = conf_opts['external']
            email = EmailSend(conf_ext['emailtemplatewarn'],
                              conf_ext['emailhtml'], conf_ext['emailsmtp'],
                              conf_ext['emailfrom'], user.mail,
                              last_project, gracedays, logger)
            msg = f'Sent grace email for {user.username} {last_project.idproj} @ {user.mail}'
            if args.noaction:
                logger.info(msg)
            elif email.send():
                logger.info(msg)
                user.grace_email = True
                grace_stat.append(user)
                session.commit()

    for user in grace_users:
        # ensure that user firstly received grace_email before
        # expire_mail will be sent to him
        if user.grace_email and not user.expire_email:
            dates = [project.date_to for project in user.projects_assign]
            most_recent = max(dates)
            last_project = [project for project in user.projects_assign
                            if project.date_to == most_recent]
            last_project = last_project[0]

            if last_project.date_to + gracedays == datenow:
                conf_ext = conf_opts['external']
                email = EmailSend(conf_ext['emailtemplatedelete'],
                                  conf_ext['emailhtml'], conf_ext['emailsmtp'],
                                  conf_ext['emailfrom'], user.mail,
                                  last_project, gracedays, logger)
                msg = f'Sent expire email for {user.username} {last_project.idproj} @ {user.mail}'
                if args.noaction:
                    logger.info(msg)
                elif email.send():
                    logger.info(msg)
                    user.expire_email = True
                    expire_stat.append(user)
                    session.commit()

    if not grace_stat and not expire_stat:
        logger.info('No grace and expired users')
    else:
        if grace_stat:
            logger.info(f'Sent emails for {len(grace_stat)} grace users')
        if expire_stat:
            logger.info(f'Sent emails for {len(expire_stat)} expired users')


if __name__ == '__main__':
    main()
