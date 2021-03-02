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

from urllib import urlencode

import sys
import requests
import os
import shutil
import subprocess
import json

connection_timeout = 120
conf_opts = parse_config()


def subscribe_maillist(server, credentials, name, email, username, logger):
    try:
        headers = dict()

        headers = requests.utils.default_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        auth = tuple(credentials.split(':'))
        response = requests.get('{}/lists/{}'.format(server, name), auth=auth, headers=headers)
        list_id = json.loads(response.content)['list_id']
        subscribe_payload = dict(list_id=list_id, subscriber=email,
                                 pre_verified=True, pre_confirmed=True)
        data = urlencode(subscribe_payload, doseq=True)

        response = requests.post('{}/members'.format(server),
                                 headers=headers, auth=auth, data=data, timeout=connection_timeout)
        response.raise_for_status()

        return True

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        excp_msg = getattr(e.response, 'content', False)
        if excp_msg:
            errormsg = ('{} {}').format(str(e), excp_msg)
        else:
            errormsg = ('{}').format(str(e))

        logger.error('Failed subscribing user %s on %s: %s' % (username, name,
                                                               errormsg))
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


def extract_email(projects, name, surname, last_project, logger):
    email = None

    # last_project is multi project field now. pick last one, but any will
    # actually play as we're just grabbing email from the API feed.
    if projects:
        try:
            target_project = last_project.split()[-1]

            for p in projects:
                if target_project == p['sifra']:
                    users = p['users']
                    for u in users:
                        if (name == concat(unidecode(u['ime'])) and
                            surname == concat(unidecode(u['prezime']))):
                            email = u['mail']
            if email:
                return email

            else:
                logger.error('Failed grabbing an email for %s %s from the API' % (name, surname))

        except IndexError as exc:
            logger.error('Failed grabbing an project for %s %s from the API' % (name, surname))

    else:
        logger.error('Failed grabbing an email for %s %s from the API as project is unknown' % (name, surname))

    return None


def diff_projects(old, new):
    projects_old = set(old.split())
    projects_new = set(new.split())
    if projects_new:
        diff = dict(add='', rem='', last=new.split()[-1])
    else:
        diff = dict(add='', rem='', last='')

    if len(projects_new) > len(projects_old):
        tmp = projects_new.difference(projects_old)
        diff['add'] = ' '.join(tmp)
    elif len(projects_new) < len(projects_old):
        tmp = projects_old.difference(projects_new)
        diff['rem'] = ' '.join(tmp)
    else:
        diff['add'] = ' '.join(projects_new)
        diff['rem'] = ' '.join(projects_old)

    return diff


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

    # fetch projects feed data as it is needed for email extraction
    projects = fetch_projects(conf_opts['external']['subscription'], logger)

    if not projects:
        logger.error('Could not fetch projects and users')
        raise SystemExit(1)

    # create /home and /shared directories for user
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

    # add users to SGE projects
    # for new users projects and last_projects field are the same so we pick
    # values from any of them.
    not_sge = session.query(User).filter(User.issgeadded == False).all()
    for u in not_sge:
        for project in u.last_projects.split():
            sgecreateuser_cmd = conf_opts['settings']['sgecreateuser']
            try:
                os.chdir(os.path.dirname(sgecreateuser_cmd))
                subprocess.check_call('{0} {1} {2}'.format(sgecreateuser_cmd, u.username, project.strip()),
                                    shell=True, bufsize=512)
                u.issgeadded = True
                logger.info('User %s added in SGE project %s' % (u.username, project.strip()))

            except Exception as e:
                logger.error('Failed adding user %s to SGE: %s' % (u.username, str(e)))
    session.commit()

    # update SGE projects for users
    # for existing user that is assigned to new project or signed off the
    # existing project, projects and last_projects field differ. based on their
    # values, it will be concluded what needs to be done and projects field
    # will be updated to match last_projects field afterward.
    update_sge = session.query(User).filter(User.projects != User.last_projects).all()
    for u in update_sge:
        diff = diff_projects(u.projects, u.last_projects)

        if diff['rem']:
            for project in diff['rem'].split():
                logger.info('User %s sign off from SGE project %s' % (u.username, project.strip()))
                sgeremoveuser_cmd = conf_opts['settings']['sgeremoveuser']
                try:
                    os.chdir(os.path.dirname(sgeremoveuser_cmd))
                    subprocess.check_call('{0} {1} {2}'.format(sgeremoveuser_cmd, u.username, project.strip()),
                                          shell=True, bufsize=512)
                    logger.info('User %s removed from SGE project ACL %s' % (u.username, project.strip()))

                except Exception as e:
                    logger.error('Failed removing of user %s from SGE: %s' % (u.username, str(e)))

        if diff['add']:
            for project in diff['add'].split():
                sgecreateuser_cmd = conf_opts['settings']['sgecreateuser']
                try:
                    os.chdir(os.path.dirname(sgecreateuser_cmd))
                    subprocess.check_call('{0} {1} {2}'.format(sgecreateuser_cmd, u.username, project.strip()),
                                        shell=True, bufsize=512)
                    logger.info('User %s updated to SGE project %s' % (u.username, project.strip()))

                except Exception as e:
                    logger.error('Failed updating user %s to SGE: %s' % (u.username, str(e)))

        # this one is called to explicitly set SGE default_project to user's
        # last_project assigned
        if diff['last'] not in diff['add']:
            sgecreateuser_cmd = conf_opts['settings']['sgecreateuser']
            try:
                os.chdir(os.path.dirname(sgecreateuser_cmd))
                subprocess.check_call('{0} {1} {2}'.format(sgecreateuser_cmd, u.username, diff['last'].strip()),
                                    shell=True, bufsize=512)
                logger.info('User %s SGE default_project explicitly set to %s' % (u.username, diff['last'].strip()))

            except Exception as e:
                logger.error('Failed setting SGE default_project for %s to %s' % (u.username, str(e)))

        u.projects = u.last_projects
    session.commit()

    # set password for opened user accounts
    not_password = session.query(User).filter(User.ispasswordset == False).all()
    for u in not_password:
        password = gen_password()
        u.password = password
        usertool.set_user_pass(usertool.get_user(u.username), password)
        u.ispasswordset = True
    session.commit()

    # send email to user whose account is opened
    not_email = session.query(User).filter(User.issentemail == False).all()
    for u in not_email:
        templatepath = conf_opts['external']['emailtemplate']
        templatehtml = conf_opts['external']['emailhtml']
        smtpserver = conf_opts['external']['emailsmtp']
        emailfrom = conf_opts['external']['emailfrom']
        emailto = extract_email(projects, u.name, u.surname, u.last_projects, logger)
        u.email = emailto

        e = InfoAccOpen(templatepath, templatehtml, smtpserver, emailfrom,
                        emailto, u.username, u.password, logger)
        r = e.send()
        if r:
            u.issentemail = True
            logger.info('Mail sent for %s' % u.username)
    session.commit()

    # subscribe opened user account to mailing list
    not_subscribed = session.query(User).filter(User.issubscribe == False).all()
    for u in not_subscribed:
        credentials = conf_opts['external']['mailinglistcredentials']
        listname = conf_opts['external']['mailinglistname']
        listserver = conf_opts['external']['mailinglistserver']
        if u.email:
            r = subscribe_maillist(listserver, credentials, listname, u.email, u.username, logger)
            if r:
                u.issubscribe = True
                logger.info('User %s subscribed to %s' % (u.username, listname))
        else:
            logger.error('Email for user %s unknown, not trying to subscribe to mailinglist' % u.username)

    session.commit()


if __name__ == '__main__':
    main()
