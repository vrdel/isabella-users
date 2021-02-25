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
    parser.add_argument('-f', required=True, help='Email FROM', dest='emailfrom')
    parser.add_argument('-t', required=True, help='Email TO', dest='emailto')
    parser.add_argument('-y', required=False, help='Type of email template (warn, delete)', dest='emailtype', default='warn')
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

    # pick any expired project
    last_expired_user = session.query(User).filter(User.status == 0).all()
    last_expired_user = last_expired_user[-1]
    disabled_stat = list()
    dates = [project.date_to for project in last_expired_user.projects_assign]
    if dates:
        most_recent = max(dates)
        last_project = [project for project in last_expired_user.projects_assign
                        if project.date_to == most_recent]
        last_project = last_project[0]
        conf_ext = conf_opts['external']

        if args.emailtype == 'warn':
            email_template = conf_ext['emailtemplatewarn']
        else:
            email_template = conf_ext['emailtemplatedelete']

        email = EmailSend(email_template, conf_ext['emailhtml'],
                            conf_ext['emailsmtp'], args.emailfrom,
                            args.emailto, last_project, gracedays, logger)
        msg = f'Sent expire email for {last_expired_user.username} {last_project.idproj} @ {args.emailto}'
        if args.noaction:
            logger.info(msg)
        elif email.send():
            logger.info(msg)
            disabled_stat.append(last_expired_user)

    if not disabled_stat:
        logger.info('No expired user')
    else:
        logger.info(f'Sent email for {len(disabled_stat)} expired user')


if __name__ == '__main__':
    main()
