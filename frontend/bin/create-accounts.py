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

from unidecode import unidecode

from base64 import b64encode

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import requests
import os
import shutil
import subprocess

connection_timeout = 120
conf_opts = parse_config()


def subscribe_maillist(token, name, email, username, logger):
    try:
        headers, payload = dict(), dict()

        headers = requests.utils.default_headers()
        headers.update({'content-type': 'application/x-www-form-urlencoded'})
        headers.update({'x-auth-token': token})
        payload = "list={0}&email={1}".format(name, email)

        response = requests.post(conf_opts['external']['mailinglist'],
                                 headers=headers, data=payload, timeout=connection_timeout)
        response.raise_for_status()

        return True

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('Failed subscribing user %s on %s: %s' % (username, name,
                                                               str(e)))
        return False


def fetch_projects(subscription, logger):
    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        users = dict()
        projects = response.json()

        return projects

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

        return False


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

    projects = fetch_projects(conf_opts['external']['subscription'], logger)

    if not projects:
        logger.error('Could not fetch projects and users')
        raise SystemExit(1)

    not_home = session.query(User).filter(User.ishomecreated == False).all()
    for u in not_home:
        if (os.path.exists(u.homedir) and
            os.path.exists(conf_opts['settings']['sharedpath'])):
            rh, rs = True, True
        else:
            rh = create_homedir(u.homedir, u.uid, u.gid, logger)
            sharedpath = conf_opts['settings']['sharedpath']
            rs = create_shareddir(sharedpath + u.username, u.uid, u.gid, logger)
        if all([rh, rs]):
            u.ishomecreated = True
            logger.info('Created directories for %s' % u.username)
    session.commit()

    not_sge = session.query(User).filter(User.issgeadded == False).all()
    for u in not_sge:
        sgecreateuser_cmd = conf_opts['settings']['sgecreateuser']
        try:
            os.chdir(os.path.dirname(sgecreateuser_cmd))
            subprocess.check_call('{0} {1} {2}'.format(sgecreateuser_cmd, u.username, u.last_project),
                                  shell=True, bufsize=512)
            u.issgeadded = True
            logger.info('User added in SGE %s' % u.username)

        except Exception as e:
            logger.error('Failed adding user %s to SGE: %s' % (u.username, str(e)))
    session.commit()

    not_password = session.query(User).filter(User.ispasswordset == False).all()
    for u in not_password:
        password = gen_password()
        u.password = password
        usertool.set_user_pass(usertool.get_user(u.username), password)
        u.ispasswordset = True
    session.commit()

    not_email = session.query(User).filter(User.issentemail == False).all()
    for u in not_email:
        templatepath = conf_opts['external']['emailtemplate']
        smtpserver = conf_opts['external']['emailsmtp']
        emailfrom = conf_opts['external']['emailfrom']
        email = extract_email(projects, u.name, u.surname, u.last_project)
        u.email = email

        e = InfoAccOpen(u.username, u.password, templatepath, smtpserver,
                        emailfrom, email, logger)
        r = e.send()
        if r:
            u.issentemail = True
            logger.info('Mail sent for %s' % u.username)
    session.commit()

    not_subscribed = session.query(User).filter(User.issubscribe == False).all()
    for u in not_subscribed:
        token = conf_opts['external']['mailinglisttoken']
        listname = conf_opts['external']['mailinglistname']
        r = subscribe_maillist(token, listname, u.email, u.username, logger)
        if r:
            u.issubscribe = True
            logger.info('User %s subscribed to %s' % (u.username, listname))
    session.commit()


if __name__ == '__main__':
    main()
