#!/usr/bin/python

import requests

from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.config import parse_config

conf_opts = parse_config()

def fetch_newly_created_users(subscription):
    try:
        response = requests.get(subscription, timeout=120)
        response.raise_for_status()
        users = response.json()

        return users

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        pass

def main():
    users = fetch_newly_created_users(conf_opts['external']['subscription'])

main()
