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
        homedir = usertool.get_user_home(userobj)
        if homedir.startswith('/home'):
            comment = usertool.get_user_comment(userobj)
            name, surname, project = '', '', ''
            if comment:
                if ',' in comment:
                    fullname, project = map(lambda x: x.strip(), comment.split(','))
                    name, surname = fullname.split(' ')
                else:
                    name, surname = comment.split(' ')

            username = usertool.get_user_name(userobj)
            shell = usertool.get_user_shell(userobj)
            passw = usertool.get_user_pass(userobj)
            userid = int(usertool.get_user_id(userobj))

            u = User(username, name, surname,
                     'set', shell, homedir, 'set',
                     1, 1, 1,
                     datetime.strptime('1970-01-01', '%Y-%m-%d'),
                     1, project)
            session.add(u)

    session.commit()


if __name__ == '__main__':
    main()
