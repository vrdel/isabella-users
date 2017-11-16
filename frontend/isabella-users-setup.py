#!/usr/bin/python

import requests
import sys

from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger

conf_opts = parse_config()

def fetch_newly_created_users(subscription, logger):
    try:
        response = requests.get(subscription, timeout=120)
        response.raise_for_status()
        users = response.json()

        return users

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)

def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

main()
