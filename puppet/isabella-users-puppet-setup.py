#!/usr/bin/python

import os
import requests
import shutil
import sqlite3
import subprocess
import sys

from base64 import b64encode

from isabella_users_puppet.config import parse_config
from isabella_users_puppet.log import Logger

connection_timeout = 120
conf_opts = parse_config()


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


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()
    import pdb; pdb.set_trace()  # XXX BREAKPOINT

    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

if __name__ == '__main__':
    main()
