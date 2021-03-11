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
from isabella_users_frontend.msg import InfoAccOpen
from isabella_users_frontend.helpers import fetch_projects, fetch_users, extract_email

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from urllib import urlencode

import sys
import os
import shutil
import subprocess
import json
import requests

connection_timeout = 120

conf_opts = parse_config()


def unsubscribe_maillist(server, credentials, name, email, username, logger):
    try:
        headers = dict()

        headers = requests.utils.default_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        auth = tuple(credentials.split(':'))
        response = requests.get('{}/lists/{}'.format(server, name), auth=auth, headers=headers)
        list_id = json.loads(response.content)['list_id']
        response = requests.delete('{}/lists/{}/member/{}'.format(server,
                                                                  list_id,
                                                                  email),
                                   headers=headers, auth=auth,
                                   timeout=connection_timeout)
        response.raise_for_status()

        return True

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        excp_msg = getattr(e.response, 'content', False)
        if excp_msg:
            errormsg = ('{} {}').format(str(e), excp_msg)
        else:
            errormsg = ('{}').format(str(e))

        logger.error('Failed unsubscribing user %s from %s: %s' % (username,
                                                                   name,
                                                                   errormsg))
        return False


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

    allusers_passwd = set(usertool.all_users_list())
    allusers_db = set([u[0] for u in session.query(User.username).all()])

    projects = fetch_projects(conf_opts['external']['subscription'], logger)
    noemail = session.query(User).filter(User.email == '').all()
    for u in noemail:
        if u.name and u.surname:
            emailto = extract_email(projects, u.name, u.surname, u.projects, logger)
            if emailto:
                u.email = emailto
    session.commit()

    for upw in allusers_passwd:
        # unsubscribe opened user account from mailing list
        userobj = usertool.get_user(upw)
        shell = usertool.get_user_shell(userobj)
        if shell == '/sbin/nologin':
            u = session.query(User).filter(User.username == upw)[0]
            if u.shell != '/sbin/nologin':
                credentials = conf_opts['external']['mailinglistcredentials']
                listname = conf_opts['external']['mailinglistname']
                listserver = conf_opts['external']['mailinglistserver']
                if u.email:
                    r = unsubscribe_maillist(listserver, credentials, listname, u.email, u.username, logger)
                    if r:
                        u.issubscribe = False
                        u.shell = '/sbin/nologin'
                        logger.info('User %s unsubscribed from %s' % (u.username, listname))
                else:
                    logger.error('Email for user %s unknown, not trying to unsubscribe to mailinglist' % u.username)

                session.commit()


if __name__ == '__main__':
    main()
