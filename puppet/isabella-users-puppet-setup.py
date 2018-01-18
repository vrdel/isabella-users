#!/usr/bin/python

import os
import requests
import shutil
import sqlite3
import subprocess
import sys
import yaml
import shutil

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


def avail_users(stream):
    users = set(stream.keys())

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


def backup_yaml(path, logger):
    try:
        shutil.copy(path, conf_opts['external']['backupdir'])

    except shutil.Error as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)


def load_yaml(path, logger):
    try:
        stream = file(path, 'r')
        return yaml.load(stream)

    except yaml.YAMLError as e:
        logger.error(e)


def merge_users(old, new):
    d = dict()
    d.update(old)
    d.update(new)

    return d


def write_yaml(path, data, logger):
    try:
        stream = file(path, 'r')
        return yaml.dump(data, stream)

    except yaml.YAMLError as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)


def max_uid(stream):
    return stream['uid_maximus']


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    yusers = load_yaml(conf_opts['external']['isabellausersyaml'], logger)
    ycrongiusers = load_yaml(conf_opts['external']['crongiusersyaml'], logger)
    ymaxuid = load_yaml(conf_opts['external']['maxuidyaml'], logger)
    maxuid = max_uid(ymaxuid)
    yamlusers = avail_users(yusers['isabella_users'])
    yamlcrongiusers = avail_users(ycrongiusers['crongi_users'])

    uid = maxuid
    newyusers = dict()
    for u in users:
        username = gen_username(u, logger)
        if username in yamlusers:
            continue
        elif username in yamlcrongiusers:
            pass
        else:
            uid += 1
            newuser = dict(comment='{0} {1}, project'.format(u['ime'], u['prezime']),
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           uid=uid)
            newyusers.update({username: newuser})

    if uid != maxuid:
        backup_yaml(conf_opts['external']['isabellausersyaml'], logger)
        backup_yaml(conf_opts['external']['maxuidyaml'], logger)
        write_yaml(conf_opts['external']['isabellausersyaml'],
                   merge_users(yusers['isabella_users'], newyusers), logger)
        newymaxuid = dict(uid_maximus=uid)
        write_yaml(conf_opts['external']['isabellausersyaml'], newymaxuid, logger)


if __name__ == '__main__':
    main()
