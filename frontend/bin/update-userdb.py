#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

import argparse

from isabella_users_frontend.cachedb import User
from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.log import Logger

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

import datetime
import sys


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="isabella-users-frontend update users DB")
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    usertool = UserUtils(logger)

    allusers_passwd = set(usertool.all_users_list())
    allusers_db = set([u[0] for u in session.query(User.username).all()])
    diff = allusers_passwd.difference(allusers_db)

    if diff:
        for username in diff:
            userobj = usertool.get_user(username)

            name, surname, project = usertool.info_comment(userobj)
            username = usertool.get_user_name(userobj)
            shell = usertool.get_user_shell(userobj)
            passw = usertool.get_user_pass(userobj)
            userid = usertool.get_user_id(userobj)
            groupid = usertool.get_group_id(userobj)
            home = usertool.get_user_home(userobj)

            u = User(username, name, surname, '', shell, home, '', userid,
                     groupid, False, False, False, False, False,
                     datetime.datetime.now(), True, project, project)

            session.add(u)

        session.commit()
        logger.info("New users added into DB: %s" % diff)

    else:
        logger.info("No new users added in /etc/passwd")



if __name__ == '__main__':
    main()
