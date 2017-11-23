#!/usr/bin/python

import os
import requests
import sys
import libuser
import shutil

from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger

connection_timeout = 120
conf_opts = parse_config()


def fetch_newly_created_users(subscription, logger):
    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        users = list()
        for p in projects:
            if p.get('users', None):
                users = [u for u in p['users']]

        return users

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)
        raise SystemExit(1)

    except Exception as e:
        logger.error(e)
        raise SystemExit(1)

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

def create_homedir(dir, uid, gid):
    try:
        os.mkdir(dir, 0750)
        os.chown(dir, uid, gid)

        for root, dirs, files in os.walk('/etc/skel'):
            for f in files:
                shutil.copy(root + '/' + f, dir)
                os.chown(dir + '/' + f, uid, gid)

        return True

    except Exception:
        return False

def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    usertool = UserUtils(logger)
    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    if users:
        for u in users:
            username = gen_username(u, logger)
            uobj = usertool.get_user(username)
            if uobj:
                home = usertool.get_user_home(uobj)
                if not os.path.exists(home):
                    uid = usertool.get_user_id(uobj)
                    if not create_homedir(home, uid, conf_opts['settings']['gid']):
                        logger.error('Failed %s directory creation' % home)
                else:
                    logger.warning('Skipping %s directory creation, already exists' % home)

if __name__ == '__main__':
    main()
