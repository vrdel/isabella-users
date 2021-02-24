#!/usr/bin/python3

from sqlalchemy import create_engine, and_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from text_unidecode import unidecode

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
            match = list(filter(lambda u: u.startswith(username), existusers))
        else:
            match = list(filter(lambda u: u.startswith(username[:-1]), existusers))

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

    parser = argparse.ArgumentParser(description="pull latest users, projects and assignments from the API and store it in cache.db")
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

    for projectfeed in data:
        # skip projects that have not been accepted yet or are HTC only
        if int(projectfeed['status_id']) > 1 or int(projectfeed['htc']) > 1:
            continue
        idproj = projectfeed['sifra']
        try:
            projectdb = session.query(Projects).filter(Projects.idproj == idproj).one()
            # update project timeline to most recent one as it is needed if
            # project is prolong
            projectdb.date_from = datetime.strptime(projectfeed['date_from'], '%Y-%m-%d')
            projectdb.date_to = datetime.strptime(projectfeed['date_to'], '%Y-%m-%d')
            projectdb.name = projectfeed['name']
            projectdb.institution = projectfeed['ustanova']
        except NoResultFound:
            # project status is taken from the API only this time when we're
            # registering new one in the cache.db. later on it's controlled and
            # set by the update-flags.py
            projectdb = Projects(feedid=projectfeed['id'], idproj=idproj,
                                 respname='', respemail='',
                                 institution=projectfeed['ustanova'],
                                 name=projectfeed['name'],
                                 date_from=datetime.strptime(projectfeed['date_from'],
                                                             '%Y-%m-%d'),
                                 date_to=datetime.strptime(projectfeed['date_to'],
                                                           '%Y-%m-%d'),
                                 date_created=datetime.now(),
                                 status=int(projectfeed['status_id']))

        usersdb = set([(concat(ue.name), concat(ue.surname)) for ue in projectdb.users])
        usersfeed = list()
        diff = set()
        users = projectfeed.get('users', None)
        if users:
            usersfeed = set([(concat(unidecode(uf['ime'])), concat(unidecode(uf['prezime']))) for uf in users])
            # notice if user is signed off from the project
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
                # this ones always get refreshed with actual data on the API.
                # reasoning is that they may have been changed since last sync.
                u.mail = feedemail
                u.name = feedname
                u.surname = feedsurname
                u.consent_disable = True if user['status_id'] == 5 else False
            except NoResultFound:
                try:
                    # uid not found, lookup by name and surname
                    u = session.query(User).filter(
                        and_(User.name == feedname,
                             User.surname == feedsurname)).one()
                    # if found, but with different uid - we have a duplicate.
                    # these are the cases where Imenko Prezimenovic changes the
                    # institution.
                    if u.feeduid != feeduid:
                        u_dup = User(feedid=user['id'],
                                     username=gen_username(feedname,
                                                           feedsurname,
                                                           allusernames),
                                     name=feedname, surname=feedsurname,
                                     feeduid=feeduid, mail=feedemail,
                                     date_join=datetime.now(),
                                     status=int(user['status_id']),
                                     consent_disable=False,
                                     projects='')
                    else:
                        u.mail = feedemail
                except NoResultFound:
                    # user status is taken from the API only this time when we're
                    # registering new one in the cache.db. later on it's controlled and
                    # set by the update-userdb.py
                    u = User(feedid=user['id'], username=gen_username(feedname, feedsurname, allusernames),
                             name=feedname, surname=feedsurname, feeduid=feeduid, mail=feedemail,
                             date_join=datetime.now(),
                             status=int(user['status_id']),
                             consent_disable=False,
                             projects='')
            if u_dup:
                projectdb.users.extend([u, u_dup])
            else:
                projectdb.users.extend([u])
        if diff:
            for ud in diff:
                u = session.query(User).filter(and_(User.name == ud[0], User.surname == ud[1])).one()
                projectdb.users.remove(u)
        session.add(projectdb)

    session.commit()


if __name__ == '__main__':
    main()
