#!/usr/bin/python3

import argparse

from isabella_users_puppet.cachedb import User, MaxUID, Projects
from isabella_users_puppet.log import Logger
from isabella_users_puppet.config import parse_config

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from text_unidecode import unidecode

import sys
import datetime
import yaml
import shutil
import os

conf_opts = parse_config()


def avail_users(stream):
    users = set(stream.keys())

    return users


def user_projects_db(yamlusers, skipusers, session):
    projects = list()

    for (key, value) in yamlusers.items():
        if key in skipusers:
            continue

        user_db = session.query(User).filter(User.username == key).one()
        all_projects = [project.idproj for project in user_db.projects]
        projects.append(' '.join(all_projects).strip())

    return projects


def user_projects_yaml(yamlusers, skipusers):
    projects = list()

    for (key, value) in yamlusers.items():
        if key in skipusers:
            continue

        project = value['comment'].split(',')
        if len(project) > 1:
            projects.append(project[1].strip())
        else:
            projects.append('')

    return projects


def user_projects_changed(yaml, db, logger):
    changed = list()
    diff = set()

    if len(yaml) == len(db):
        for (i, p) in enumerate(db):
            if p != yaml[i]:
                py = yaml[i].split()
                pd = p.split()
                spy = set(py)
                spd = set(pd)
                if len(py) > len(pd):
                    diff.update(spy.difference(spd))
                else:
                    diff.update(spd.difference(spy))
    else:
        logger.error('DB and YAML out of sync')

        raise SystemExit(1)

    changed = [project for project in diff]

    return changed


def is_date(date):
    try:
        _ = datetime.datetime.strptime(date, '%Y-%m-%d')
        t = tuple(int(i) for i in date.split('-'))

        return datetime.date(*t)

    except ValueError:
        print('Date not in %Y-%m-%d format')

        raise SystemExit(1)


def load_yaml(path, logger):
    try:
        with open(path, 'r') as stream:
            return yaml.load(stream)

    except yaml.YAMLError as e:
        logger.error(e)


def all_false(cont):
    for e in cont:
        if e:
            return False

    return True


def backup_yaml(path, logger):
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    try:
        shutil.copy(path, conf_opts['settings']['backupdir'] + \
                    '/' + os.path.basename(path) + '_%s' % date)

    except shutil.Error as e:
        logger.error(e)

    except Exception as e:
        logger.error(e)


def write_yaml(path, data, logger):
    try:
        with open(path, 'w') as stream:
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
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    parser.add_argument('-n', required=False, default=False,
                        action='store_true', help='No operation, just print changes', dest='nop')
    args = parser.parse_args()

    cachedb = conf_opts['settings']['cache']

    yusers = load_yaml(conf_opts['external']['isabellausersyaml'], logger)
    yamlusers = avail_users(yusers['isabella_users'])

    if args.sql:
        cachedb = args.sql

    engine = create_engine('sqlite:///%s' % cachedb, echo=args.verbose)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    skipusers = conf_opts['settings']['excludeuser']
    skipusers = set([u.strip() for u in skipusers.split(',')])

    users = session.query(User).all()
    maxuid = session.query(MaxUID).first()
    usersdb = set(u.username for u in users)
    newusers = usersdb.difference(yamlusers)

    yamlprojects = user_projects_yaml(yusers['isabella_users'], skipusers)
    dbprojects = user_projects_db(yusers['isabella_users'], skipusers, session)
    projects_changed = user_projects_changed(yamlprojects, dbprojects, logger)

    if args.nop:
        print("Accounts to be opened:")
        print("Diff DB - YAML")
        print(newusers)
        print("Changed projects")
        print(projects_changed)

    # trigger is new users that exist in the cache db, but are not
    # presented in yaml. since we're merging new users to existing ones
    # and going all over them for the full yaml dump, we'll also report
    # if some new project assignments happened and for whom.
    elif newusers:
        uid = maxuid.uid
        newusersd = dict()
        changed_users = list()

        for u in newusers:
            uid += 1
            udb = session.query(User).filter(User.username == u).one()
            if udb.last_project:
                all_projects = [project.idproj for project in udb.projects]
                comment = '{0} {1}, {2}, {3}'.format(udb.name, udb.surname,
                                                     ' '.join(all_projects),
                                                     udb.last_project)
            else:
                comment = '{0} {1}'.format(udb.name, udb.surname)
            newuser = dict(comment='%s' % comment,
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           home='/home/{0}'.format(udb.username),
                           uid=uid)
            newusersd.update({unidecode(udb.username): newuser})

        allusers = merge_users(yusers['isabella_users'], newusersd)
        for u, d in allusers.items():
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
                    all_projects = [project.idproj for project in udb.projects]
                    prev_projects =  d['comment'].split(',')[1].strip()
                    if prev_projects != ' '.join(all_projects):
                        changed_users.append(udb.username)
                    d['comment'] = '{0} {1}, {2}, {3}'.format(udb.name,
                                                              udb.surname,
                                                              ' '.join(all_projects),
                                                              udb.last_project)
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
            if changed_users:
                logger.info("Changed projects for %d users: %s" %
                            (len(changed_users), ', '.join(changed_users)))

    # trigger here is only new project assingments. so new users, same set of
    # them in db and yaml, just the associations between projects and users
    # changed.
    elif projects_changed:
        try:
            changed_users = list()

            projectschanged_db = session.query(Projects).filter(Projects.idproj.in_(projects_changed)).all()
            for p in projectschanged_db:
                users = p.users
                for u in users:
                    if u.username in skipusers:
                        continue
                    yaml_user = yusers['isabella_users'][u.username]
                    yaml_projects = yaml_user['comment'].split(',')[1].strip()
                    all_projects = [project.idproj for project in u.projects]
                    str_all_projects = ' '.join(all_projects)
                    if yaml_projects != str_all_projects:
                        diff_project = user_projects_changed([yaml_projects], [str_all_projects], logger)
                        changed_users.append((u.username, ' '.join(diff_project)))
                        yaml_user['comment'] = '{0} {1}, {2}, {3}'.format(u.name, u.surname, str_all_projects, u.last_project)

        except NoResultFound as e:
            logger.error('{1} {0}'.format(u, str(e)))
            pass

        backup_yaml(conf_opts['external']['isabellausersyaml'], logger)
        r = write_yaml(conf_opts['external']['isabellausersyaml'], {'isabella_users': yusers['isabella_users']}, logger)
        if r:
            logger.info("Update associations of existing users to projects: %s " %
                        ', '.join(['{0} assigned to {1}'.format(t[0], t[1]) for t in changed_users]))

    else:
        logger.info("No changes in projects and users")


if __name__ == '__main__':
    main()
