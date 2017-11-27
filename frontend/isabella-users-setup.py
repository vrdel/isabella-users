#!/usr/bin/python

import os
import requests
import shutil
import sys

from base64 import b64encode

from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger
from isabella_users_frontend.userutils import UserUtils

connection_timeout = 120
conf_opts = parse_config()


def gen_password():
    s = os.urandom(64)

    return b64encode(s)[:30]


def fetch_newly_created_users(subscription, logger):
    users = None

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        for p in projects:
            if p.get('users', None):
                users = [u for u in p['users']]

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users


def gen_username(uid, logger):
    username = None

    try:
        if '@' in uid['uid']:
            username = uid['uid'].split('@')[0]
        else:
            logger.warning('Wrong uid: %s' % uid['uid'])

    except Exception as e:
        logger.error(e)

    return username


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


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    usertool = UserUtils(logger)
    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    email_info = dict()

    if users:
        for u in users:
            username = gen_username(u, logger)
            email_info.update({username: dict()})
            email_info[username].update(email=u['mail'])
            uobj = usertool.get_user(username)
            if uobj:
                uid = usertool.get_user_id(uobj)

                home = usertool.get_user_home(uobj)
                if not os.path.exists(home):
                    if not create_homedir(home, uid, conf_opts['settings']['gid'], logger):
                        logger.error('Failed %s directory creation' % home)
                else:
                    logger.warning('Skipping %s directory creation, already exists' % home)

                sharedpath = conf_opts['settings']['sharedpath']
                if not os.path.exists(sharedpath + username):
                    if not create_shareddir(sharedpath + username, uid, conf_opts['settings']['gid'], logger):
                        logger.error('Failed %s directory creation' % (sharedpath + username))
                else:
                    logger.warning('Skipping %s directory creation, already exists' % (sharedpath + username))

                if usertool.get_user_pass(uobj) == '!!':
                    password = gen_password()
                    usertool.set_user_pass(uobj, password)
                    email_info[username].update(password=password)

    else:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
