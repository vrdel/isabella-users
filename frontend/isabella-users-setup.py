#!/usr/bin/python

import requests
import sys
import libuser

from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger

connection_timeout = 120
conf_opts = parse_config()


def fetch_newly_created_users(subscription, logger):
    try:
        response = requests.get(subscription, timeout=connection_timeout)
        response.raise_for_status()
        users = response.json()

        return users

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error(e)
        raise SystemExit(1)

    except Exception as e:
        logger.error(e)
        raise SystemExit(1)


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    usertool = UserUtils(conf_opts['settings']['gid'], logger)
    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    if users:
        for u in users:
            uobj = usertool.get_user(u['username'])
            if uobj:
                print uobj.get(libuser.USERNAME)

main()
