#!/usr/bin/python3

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
import json

connection_timeout = 120
conf_opts = parse_config()


def fetch_feeddata(subscription, logger):
    statuses_users = dict()

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        return response.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)


def gen_username(name, surname, existusers):
    # ASCII convert
    name = name.lower()
    surname = surname.lower()
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

    cachedb = conf_opts['settings']['cache']

    parser = argparse.ArgumentParser(description="isabella-users-puppet sync DB")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()

    data = fetch_feeddata(conf_opts['external']['subscription'], logger)

    logger.info('Fetched %d projects' % len(data))

    with open(conf_opts['settings']['mapuser'], mode='r') as fp:
        mapuser = json.loads(fp.read())

    if args.sql:
        cachedb = args.sql

    engine = create_engine('sqlite:///%s' % cachedb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    for project in data:
        # skip projects that have not been accepted yet or are HTC only
        if int(project['status_id']) > 1 or int(project['htc']) > 1:
            continue
        idproj = project['sifra']
        try:
            p = session.query(Projects).filter(Projects.idproj == idproj).one()
            # update project timeline to most recent one as it is needed if
            # project is prolong
            p.date_from = datetime.strptime(project['date_from'], '%Y-%m-%d')
            p.date_to = datetime.strptime(project['date_to'], '%Y-%m-%d')
        except NoResultFound:
            p = Projects(feedid=project['id'], idproj=idproj,
                         respname='', respemail='', institution='', name='',
                         date_from=datetime.strptime(project['date_from'], '%Y-%m-%d'),
                         date_to=datetime.strptime(project['date_to'], '%Y-%m-%d'),
                         date_created=datetime.now(),
                         status=int(project['status_id']))

        usersdb = set([(concat(ue.name), concat(ue.surname)) for ue in p.users])
        usersfeed = list()
        diff = set()
        users = project.get('users', None)
        if users:
            usersfeed = set([(concat(unidecode(uf['ime'])), concat(unidecode(uf['prezime']))) for uf in users])
            diff = usersdb.difference(usersfeed)

        allusernames = set([username[0] for username in session.query(User.username).all()])
        for user in users:
            u_dup = None
            feedname = concat(unidecode(user['ime']))
            feedsurname = concat(unidecode(user['prezime']))
            feeduid = user['uid']
            feedemail = user['mail']
            for mu in mapuser:
                munc = concat(unidecode(mu['from']['name']))
                musc = concat(unidecode(mu['from']['surname']))
                if feedname == munc and feedsurname == musc:
                    feedname = concat(mu['to']['name'])
                    feedsurname = concat(mu['to']['surname'])

            # lookup first by uid
            try:
                u = session.query(User).filter(User.feeduid == feeduid).one()
                u.mail = feedemail
                u.name = feedname
                u.surname = feedsurname
            except NoResultFound:
                try:
                    # uid not found, lookup by name and surname
                    u = session.query(User).filter(
                        and_(User.name == feedname,
                             User.surname == feedsurname)).one()
                    # if found, but with different uid - we have a duplicate
                    if u.feeduid != feeduid:
                        u_dup = User(feedid=user['id'],
                                     username=gen_username(feedname,
                                                           feedsurname,
                                                           allusernames),
                                     name=feedname, surname=feedsurname,
                                     feeduid=feeduid, mail=feedemail,
                                     date_join=datetime.now(),
                                     status=int(user['status_id']),
                                     last_project='')
                    else:
                        u.mail = feedemail
                except NoResultFound:
                    u = User(feedid=user['id'], username=gen_username(feedname, feedsurname, allusernames),
                             name=feedname, surname=feedsurname, feeduid=feeduid, mail=feedemail,
                             date_join=datetime.now(),
                             status=int(user['status_id']), last_project='')
            if u_dup:
                p.users.extend([u, u_dup])
            else:
                p.users.extend([u])
        if diff:
            for ud in diff:
                u = session.query(User).filter(and_(User.name == ud[0], User.surname == ud[1])).one()
                p.users.remove(u)
        session.add(p)

    session.commit()


if __name__ == '__main__':
    main()
