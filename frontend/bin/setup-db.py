#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

from unidecode import unidecode

from isabella_users_frontend.cachedb import Base, User
from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger
from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.msg import InfoAccOpen

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import sessionmaker

from datetime import datetime

import argparse
import csv
import sys
import yaml


def gen_password():
    s = os.urandom(64)

    return b64encode(s)[:30]


def fetch_users(subscription, logger):
    users = None

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        users = dict()
        projects = response.json()

        for p in projects:
            if p.get('users', None):
                for e in [u for u in p['users']]:
                    if e['id'] not in users:
                        users[e['id']] = e

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users.values()


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()
    lusers = list()

    parser = argparse.ArgumentParser(description="Isabella users frontend DB tool")
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)
        Base.metadata.create_all(engine)

    connection = engine.connect()
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    usertool = UserUtils(logger)

    for userobj in usertool.all_users():
        name, surname, project = usertool.info_comment(userobj)
        username = usertool.get_user_name(userobj)
        shell = usertool.get_user_shell(userobj)
        passw = usertool.get_user_pass(userobj)
        userid = usertool.get_user_id(userobj)
        groupid = usertool.get_group_id(userobj)
        home = usertool.get_user_home(userobj)

        lusers.append(username)

        u = User(username, name, surname, 'set', shell,
                 home, 'set', userid, groupid,
                 True, True, True, True, True,
                 datetime.strptime('1970-01-01', '%Y-%m-%d'),
                 True, project, project)
        session.add(u)

    session.commit()

    if lusers:
        logger.info("Users added into DB: %s" % lusers)
    else:
        logger.info("DB and /etc/passwd synced")


if __name__ == '__main__':
    main()
