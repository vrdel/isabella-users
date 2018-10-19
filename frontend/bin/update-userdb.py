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


def diff_users(session, db, passwd):
    upd = dict()

    for k, v in passwd.iteritems():
        if k:
            users_db = set(u[0] for u in session.query(User.username).filter(User.last_project == k).all())
            users_passwd = set(passwd[k])
            if len(users_db) != len(users_passwd):
                users_add = users_passwd.difference(users_db)
                users_del = users_db.difference(users_passwd)
                upd[k] = {'add': users_add,
                          'del': users_del}

    return upd


def diff_projects(db, passwd):
    psd = dict()
    dbk = set(db.keys())
    pwdk = set(passwd.keys())
    diff = pwdk.difference(dbk)

    for p in diff:
        psd.update({p: passwd[p]})

    return psd


def unsign_projectusers(session, pu):
    if len(pu) >= 1:
        for k, v in pu.iteritems():
            users = session.query(User).filter(User.username.in_(v)).all()
            for u in users:
                u.last_project = ''

        session.commit()

        return True

    else:
        return False


def assign_projectusers(session, pu):
    if len(pu) >= 1:
        for k, v in pu.iteritems():
            users = session.query(User).filter(User.username.in_(v)).all()
            for u in users:
                u.last_project = k

        session.commit()

        return True

    else:
        return False


def db_projects_users(session=None):
    all_projects_user_db = dict()

    if session:
        for u in session.query(User).all():
            p = u.last_project
            if p in all_projects_user_db:
                all_projects_user_db[p].append(u.username)
            else:
                all_projects_user_db[p] = list()
                all_projects_user_db[p].append(u.username)

    return all_projects_user_db


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
        logger.info("New users added into DB: %s" % str_iterable(diff))

    else:
        logger.info("No new users added in /etc/passwd")

    # update (project, user) assignments by creating associations from
    # /etc/passwd and from cache.db. if they differ, there's new project and
    # update last_project field for user assigned to new project.
    all_projects_users_passwd = usertool.all_projects_users()
    all_projects_users_db = db_projects_users(session)

    pjs = diff_projects(all_projects_users_db, all_projects_users_passwd)
    if assign_projectusers(session, pjs):
        for k, v in pjs.iteritems():
            if k:
                logger.info('Users %s assigned to project %s' % (str_iterable(v), k))
            else:
                logger.info('Users %s signoff from last project' % str_iterable(v))

    # update user assignments to existing projects changing his last_project
    # field
    all_projects_users_db = db_projects_users(session)
    upjs = diff_users(session, all_projects_users_db, all_projects_users_passwd)
    if upjs:
        for k, v in upjs.iteritems():
            ptmp = dict()
            ptmp[k] = v['add']
            if ptmp[k] and assign_projectusers(session, ptmp):
                logger.info('Users %s reassigned to project %s' % (str_iterable(v['add']), k))

            ptmp = dict()
            ptmp[k] = v['del']
            if ptmp[k] and unsign_projectusers(session, ptmp):
                logger.info('Users %s signoff from project %s' % (str_iterable(v['del']), k))


if __name__ == '__main__':
    main()
