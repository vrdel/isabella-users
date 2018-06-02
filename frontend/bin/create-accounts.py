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

from unidecode import unidecode

from base64 import b64encode

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

import datetime
import sys
import requests
import os
import shutil

connection_timeout = 120
conf_opts = parse_config()


def fetch_projects(subscription, logger):
    users = None

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        users = dict()
        projects = response.json()

        return projects

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users.values()


def concat(s):
    if '-' in s:
        s = s.split('-')
        s = ''.join(s)
    if ' ' in s:
        s = s.split(' ')
        s = ''.join(s)

    return s


def gen_password():
    s = os.urandom(64)

    return b64encode(s)[:30]


def create_shareddir(dir, uid, gid, logger):
    try:
        os.mkdir(dir, 0750)
        os.chown(dir, uid, gid)

        return True

    except Exception as e:
        logger.error(e)

        return False


def create_homedir(dir, uid, gid, logger):
    try:
        os.mkdir(dir, 0750)
        os.chown(dir, uid, gid)

        for root, dirs, files in os.walk(conf_opts['settings']['skeletonpath']):
            for f in files:
                shutil.copy(root + '/' + f, dir)
                os.chown(dir + '/' + f, uid, gid)

        return True

    except Exception as e:
        logger.error(e)

        return False


def subscribe_maillist(token, name, email, username, logger):
    try:
        headers, payload = dict(), dict()

        headers = requests.utils.default_headers()
        headers.update({'content-type': 'application/x-www-form-urlencoded'})
        headers.update({'x-auth-token': token})
        payload = "list={0}&email={1}".format(name, email)

        response = requests.post(conf_opts['external']['mailinglist'],
                                 headers=headers, data=payload, timeout=180)
        response.raise_for_status()

        return True

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('Failed subscribing user %s on %s: %s' % (username, name,
                                                               str(e)))
        return False


def extract_email(projects, name, surname, last_project):
    for p in projects:
        if last_project == p['sifra']:
            users = p['users']
            for u in users:
                if (name == concat(unidecode(u['ime'])) and
                    surname == concat(unidecode(u['prezime']))):
                    return u['mail']


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

    projects = fetch_projects(conf_opts['external']['subscription'], logger)

    not_created = session.query(User).filter(User.ishomecreated == False).all()
    for u in not_created:
        u.mail = extract_email(projects, u.name, u.surname, u.last_project)
        u.password = gen_password()

    session.commit()


if __name__ == '__main__':
    main()
