#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

from sqlalchemy import create_engine, and_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from unidecode import unidecode

from isabella_users_puppet.cachedb import Base, User, Projects
from isabella_users_puppet.config import parse_config
from isabella_users_puppet.log import Logger

import argparse
import requests
import sys
import re

connection_timeout = 120
conf_opts = parse_config()


def fetch_feeddata(subscription, logger):
    statuses_users = dict()
    users = dict()

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        return response.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users.values()


def gen_username(name, surname):
    # ASCII convert
    name = name.lower()
    surname = surname.lower()
    # remove " ", "|" and "/"
    name = re.sub('[ \-|]', '', name)
    surname = re.sub('[ \-|]', '', surname)
    # take first char of name and first seven from surname
    username = name[0] + surname[:7]

    return username


def to_unicode(s):
    return unicode(s, 'utf-8')


def concat(s):
    if '-' in s:
        s = s.split('-')
        s = ''.join(s)
    if ' ' in s:
        s = s.split(' ')
        s = ''.join(s)

    return s


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()


    parser = argparse.ArgumentParser(description="isabella-users-puppet sync DB")
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    data = fetch_feeddata(conf_opts['external']['subscription'], logger)

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    for project in data:
        # skip projects that have not been accepted yet
        if int(project['status_id']) > 1:
            continue
        idproj = project['sifra']
        try:
            p = session.query(Projects).filter(Projects.idproj == idproj).one()
        except NoResultFound:
            p = Projects(feedid=project['id'], idproj=idproj,
                         respname='', respemail='', institution='', name='',
                         date_from=datetime.strptime(project['date_from'], '%Y-%m-%d'),
                         date_to=datetime.strptime(project['date_to'], '%Y-%m-%d'),
                         date_created=datetime.now(),
                         status=int(project['status_id']))

        users = project.get('users')
        for user in users:
            feedname = unidecode(user['ime'])
            feedname = concat(feedname)
            feedsurname = unidecode(user['prezime'])
            feedsurname = concat(feedsurname)
            try:
                u = session.query(User).filter(
                    and_(User.name == feedname,
                         User.surname == feedsurname)).one()
            except NoResultFound:
                u = User(feedid=user['id'], username=gen_username(feedname, feedsurname), name=feedname,
                         surname=feedsurname, mail=user['mail'],
                         date_join=datetime.now(),
                         status=int(user['status_id']))
            p.users.extend([u])
        session.add(p)

    session.commit()

if __name__ == '__main__':
    main()
