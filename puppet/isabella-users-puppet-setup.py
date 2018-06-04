#!/usr/bin/python

import re
import requests
import shutil
import sys
import yaml

from unidecode import unidecode
from isabella_users_puppet.config import parse_config
from isabella_users_puppet.log import Logger

connection_timeout = 120
conf_opts = parse_config()


def find_inactive_users(statuses):
    inactive = list()

    for u, s in statuses.iteritems():
        bools = map(lambda t: t == 1, s)
        if not all(bools):
            inactive.append(u)

    return inactive


def fetch_newly_created_users(subscription, logger):
    statuses_users = dict()
    users = dict()

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        for p in projects:
            if p.get('users', None):
                for u in p['users']:
                    if u['id'] not in users:
                        users[u['id']] = u
                    if u['id'] in statuses_users:
                        statuses_users[u['id']].append(int(u['status_id']))
                    else:
                        statuses_users[u['id']] = list()
                        statuses_users[u['id']].append(int(u['status_id']))

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users.values(), find_inactive_users(statuses_users)


def avail_users(stream):
    users = set(stream.keys())

    return users


def gen_username(name, surname, existusers, logger):
    # ASCII convert
    name = unidecode(name.lower())
    surname = unidecode(surname.lower())
    # take first char of name and first seven from surname
    username = name[0] + surname[:7]

    if username not in existusers:
        return username

    elif username in existusers:
        match = list()
        if len(username) < 8:
            match = filter(lambda u: u.startswith(username), existusers)
        else:
            match = filter(lambda u: u.startswith(username[:-1]), existusers)

        return username + str(len(match))


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

    users, inactive = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    yusers = load_yaml(conf_opts['external']['isabellausersyaml'], logger)
    ycrongiusers = load_yaml(conf_opts['external']['crongiusersyaml'], logger)
    ymaxuid = load_yaml(conf_opts['external']['maxuidyaml'], logger)
    maxuid = max_uid(ymaxuid)
    yamlusers = avail_users(yusers['isabella_users'])
    yamlcrongiusers = avail_users(ycrongiusers['crongi_users'])

    uid = maxuid
    newyusers = dict()
    for u in users:
        username = gen_username(u['ime'], u['prezime'], yamlusers.keys() + \
                                yamlcrongiusers.keys(), logger)
        import pdb; pdb.set_trace()  # XXX BREAKPOINT
        if username in yamlusers:
            if username in inactive:
                yamlusers[username]['shell'] = '/sbin/nologin'
                logger.info("Disabled user: %s"  % username)
            continue
        elif username in yamlcrongiusers:
            newuser = dict(comment=u'{0} {1}, project'.format(u['ime'], u['prezime']),
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           uid=ycrongiusers['crongi_users'][username]['uid'])
            newyusers.update({username: newuser})
        else:
            uid += 1
            shell = conf_opts['settings']['shell'] if username not in inactive else '/sbin/nologin'
            newuser = dict(comment=u'{0} {1}, project'.format(u['ime'], u['prezime']),
                           gid=conf_opts['settings']['gid'],
                           shell=shell,
                           uid=uid)
            newyusers.update({unidecode(username): newuser})

    if uid != maxuid:
        backup_yaml(conf_opts['external']['isabellausersyaml'], logger)
        backup_yaml(conf_opts['external']['maxuidyaml'], logger)
        write_yaml(conf_opts['external']['isabellausersyaml'],
                   merge_users(yusers['isabella_users'], newyusers), logger)
        newymaxuid = dict(uid_maximus=uid)
        write_yaml(conf_opts['external']['isabellausersyaml'], newymaxuid, logger)
        addedusers = ', '.join(newyusers.keys())
        logger.info("Added users: %s" % addedusers)


if __name__ == '__main__':
    main()
