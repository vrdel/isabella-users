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
from isabella_users_frontend.config import parse_config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import datetime
import sys

conf_opts = parse_config()


def diff_projects(db, passwd):
    userdiff = dict()

    for username in passwd.keys():
        rem, add = set([]), set([])
        if db[username] != passwd[username]:
            userdiff[username] = {
                'rem': '',
                'add': '',
                'all': ''
            }
            dbs = set(db[username].split())
            pws = set(passwd[username].split())
            if len(dbs) > len(pws):
                rem = dbs.difference(pws)
            else:
                add = pws.difference(dbs)

            userdiff[username]['rem'] = ' '.join(rem)
            userdiff[username]['add'] = ' '.join(add)
            userdiff[username]['all'] = passwd[username]

    return userdiff


def assign_projectusers(session, pu):
    if len(pu) >= 1:
        for key, value in pu.iteritems():
            user = session.query(User).filter(User.username == key).one()
            user.last_projects = value['all']

        session.commit()

        return True

    else:
        return False


def db_users_projects(session=None):
    all_users_projects_db = dict()

    if session:
        for user in session.query(User).all():
            all_users_projects_db[user.username] = user.last_projects

    return all_users_projects_db


def str_iterable(s):
    return ', '.join(s)


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    cdb = conf_opts['settings']['cache']

    parser = argparse.ArgumentParser(description="isabella-users-frontend update users DB")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    if args.sql:
        cdb = args.sql

    engine = create_engine('sqlite:///%s' % cdb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    usertool = UserUtils(logger)

    # create new users by comparing user entries in /etc/passwd and in
    # cache.db. if user exists in /etc/passwd but not in cache.db, we have a new
    # one.
    # TODO: user exist in cache.db but not in /etc/passwd?
    allusers_passwd = set(usertool.all_users_list())
    allusers_db = set([u[0] for u in session.query(User.username).all()])
    diff = allusers_passwd.difference(allusers_db)

    if diff:
        for username in diff:
            userobj = usertool.get_user(username)

            name, surname, projects = usertool.info_comment(userobj)
            username = usertool.get_user_name(userobj)
            shell = usertool.get_user_shell(userobj)
            userid = usertool.get_user_id(userobj)
            groupid = usertool.get_group_id(userobj)
            home = usertool.get_user_home(userobj)

            # create a new entry in cache.db for new user.
            # initially set his projects and last_projects field the same.
            u = User(username, name, surname, '', shell, home, '', userid,
                     groupid, False, False, False, False, False,
                     datetime.datetime.now(), True, projects, projects)

            session.add(u)

        session.commit()
        logger.info("New users added into DB: %s", str_iterable(diff))

    else:
        logger.info("No new users added in /etc/passwd")

    # report differencies in (user, project) assignments by creating and
    # comparing associations from /etc/passwd and from cache db. set
    # last_projects field in cache.db to match projects in /etc/passwd.
    # projects field will have previous value so that create-accounts.py can
    # notice the difference.
    all_users_projects_password = usertool.all_users_projects()
    all_users_projects_db = db_users_projects(session)

    pjs = diff_projects(all_users_projects_db, all_users_projects_password)
    if assign_projectusers(session, pjs):
        for user, assign in pjs.iteritems():
            if assign['add']:
                logger.info('User %s assigned to projects %s', user, assign['add'])
            if assign['rem']:
                logger.info('User %s sign off projects %s', user, assign['rem'])


if __name__ == '__main__':
    main()
