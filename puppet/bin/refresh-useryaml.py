#!/usr/bin/python

import __main__
__main__.__requires__ = __requires__ = []
__requires__.append('SQLAlchemy >= 0.8.2')
import pkg_resources
pkg_resources.require(__requires__)

import argparse

from isabella_users_puppet.cachedb import Base, User, Projects, MaxUID
from isabella_users_puppet.log import Logger
from isabella_users_puppet.config import parse_config

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from unidecode import unidecode

import sys
import datetime
import yaml
import shutil

conf_opts = parse_config()


def avail_users(stream):
    users = set(stream.keys())

    return users


def is_date(date):
    try:
        _ = datetime.datetime.strptime(date, '%Y-%m-%d')
        t = tuple(int(i) for i in date.split('-'))

        return datetime.date(*t)

    except ValueError:
        print 'Date not in %Y-%m-%d format'

        raise SystemExit(1)


def load_yaml(path, logger):
    try:
        stream = file(path, 'r')
        return yaml.load(stream)

    except yaml.YAMLError as e:
        logger.error(e)


def all_false(cont):
    for e in cont:
        if e:
            return False

    return True


def backup_yaml(path, logger):
    try:
        shutil.copy(path, conf_opts['external']['backupdir'])

    except shutil.Error as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)


def write_yaml(path, data, logger):
    try:
        stream = file(path, 'w')
        yaml.dump(data, stream, default_flow_style=False)
        return True

    except yaml.YAMLError as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)


def merge_users(old, new):
    d = dict()
    d.update(old)
    d.update(new)

    return d


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="isabella-users-puppet refresh user yaml")
    parser.add_argument('-d', required=True, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    parser.add_argument('-n', required=False, default=False,
                        action='store_true', help='No operation, just print changes', dest='nop')
    args = parser.parse_args()

    yusers = load_yaml(conf_opts['external']['isabellausersyaml'], logger)
    ycrongiusers = load_yaml(conf_opts['external']['crongiusersyaml'], logger)
    yamlusers = avail_users(yusers['isabella_users'])
    yamlcrongiusers = avail_users(ycrongiusers['crongi_users'])

    if args.sql:
        engine = create_engine('sqlite:///%s' % args.sql, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    users = session.query(User).all()
    maxuid = session.query(MaxUID).first()
    usersdb = set(u.username for u in users)
    newusers = usersdb.difference(yamlusers)
    newincrongi = newusers.intersection(yamlcrongiusers)

    if args.nop:
        print "Accounts to be opened:"
        print
        print "Diff DB - YAML"
        print newusers
        print
        print "From CRO-NGI"
        print newincrongi

    elif newusers:
        uid = maxuid.uid
        newusersd = dict()

        for u in newincrongi:
            udb = session.query(User).filter(User.username == u).one()
            if udb.last_project:
                comment = '{0} {1}, {2}'.format(udb.name, udb.surname, udb.last_project)
            else:
                comment = '{0} {1}'.format(udb.name, udb.surname)
            newuser = dict(comment=comment,
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           home='/home/{0}'.format(udb.username),
                           uid=ycrongiusers['crongi_users'][u]['uid'])
            newusersd.update({unidecode(udb.username): newuser})

        for u in newusers:
            uid += 1
            udb = session.query(User).filter(User.username == u).one()
            if udb.last_project:
                comment = '{0} {1}, {2}'.format(udb.name, udb.surname, udb.last_project)
            else:
                comment = '{0} {1}'.format(udb.name, udb.surname)
            newuser = dict(comment='%s' % comment,
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           home='/home/{0}'.format(udb.username),
                           uid=uid)
            newusersd.update({unidecode(udb.username): newuser})

        allusers = merge_users(yusers['isabella_users'], newusersd)
        skipusers = conf_opts['settings']['excludeuser']
        skipusers = set([u.strip() for u in skipusers.split(',')])
        for u, d in allusers.iteritems():
            if u in skipusers:
                continue
            try:
                udb = session.query(User).filter(User.username == u).one()
                if conf_opts['settings']['disableuser']:
                    if udb.status == 0:
                        d['shell'] = '/sbin/nologin'
                    elif udb.status == 1:
                        d['shell'] = conf_opts['settings']['shell']
                if udb.last_project:
                    d['comment'] = '{0} {1}, {2}'.format(udb.name, udb.surname, udb.last_project)
                else:
                    d['comment'] = '{0} {1}'.format(udb.name, udb.surname)
            except NoResultFound as e:
                logger.error('{1} {0}'.format(u, str(e)))
                continue
        backup_yaml(conf_opts['external']['isabellausersyaml'], logger)
        r = write_yaml(conf_opts['external']['isabellausersyaml'], {'isabella_users': allusers}, logger)
        if r:
            logger.info("Added %d users: %s" % (len(newusersd), ', '.join(newusersd.keys())))
            f = session.query(MaxUID).first()
            f.uid = uid
            session.commit()


if __name__ == '__main__':
    main()
