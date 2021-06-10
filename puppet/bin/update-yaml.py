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


def user_projects_db(yamlusers, session):
    """
        Build list of active projects from cache for users listed in yaml in
        same order as they are listed there.
    """
    projects = list()

    for (key, value) in yamlusers.items():
        user_db = session.query(User).filter(User.username == key).one()
        all_projects = [project.idproj for project in user_db.projects_assign
                        if project.status in [1,2]]
        projects.append(' '.join(all_projects).strip())

    return projects


def user_projects_yaml(yamlusers):
    """
        Build list of active projects for users in yaml in same order as they
        are listed there.
    """
    projects = list()

    for (key, value) in yamlusers.items():
        project = value['comment'].split(',')
        if len(project) > 1:
            projects.append(project[1].strip())
        else:
            projects.append('')

    return projects


def user_projects_changed(yaml, db, logger):
    """
        Find the differencies in same ordered lists of projects for users in
        cache and yaml
    """
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
    ret = None
    try:
        with open(path, 'w') as stream:
            yaml.dump(data, stream, default_flow_style=False)
        ret = True

    except yaml.YAMLError as e:
        logger.error(e)
        ret = False

    except Exception as e:
        logger.error(e)
        ret = False

    return ret


def merge_users(old, new):
    d = dict()
    d.update(old)
    d.update(new)

    return d


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="update Puppet YAML listing all users and projects' assignments in their comment field")
    parser.add_argument('-d', required=False, help='SQLite DB file', dest='sql')
    parser.add_argument('-n', required=False, help='No operation mode', dest='noaction', action='store_true')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
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

    users = session.query(User).all()
    maxuid = session.query(MaxUID).first()
    usersdb = set(user.username for user in users)
    newusers = usersdb.difference(yamlusers)

    yamlprojects = user_projects_yaml(yusers['isabella_users'])
    dbprojects = user_projects_db(yusers['isabella_users'], session)
    projects_changed = user_projects_changed(yamlprojects, dbprojects, logger)

    if args.noaction:
        logger.info("NO EXECUTE mode, just print actions")

    # trigger is new users that exist in the cache db, but are not
    # presented in yaml. since we're merging new users to existing ones
    # and going all over them for the full yaml dump, we'll also report
    # if some new project assignments happened and for whom.
    if newusers:
        uid = maxuid.uid
        newusersd = dict()
        added_projects_users = list()

        for user in newusers:
            uid += 1
            udb = session.query(User).filter(User.username == user).one()
            comment = '{0} {1}, {2}'.format(udb.name, udb.surname, udb.projects)
            newuser = dict(comment='%s' % comment,
                           gid=conf_opts['settings']['gid'],
                           shell=conf_opts['settings']['shell'],
                           home='/home/{0}'.format(udb.username),
                           uid=uid)
            newusersd.update({unidecode(udb.username): newuser})

        allusers = merge_users(yusers['isabella_users'], newusersd)
        for user, metadata in allusers.items():
            try:
                udb = session.query(User).filter(User.username == user).one()
                all_projects = [project.idproj for project in
                                udb.projects_assign if project.status in [1,2]]
                try:
                    prev_projects = metadata['comment'].split(',')[1].strip()
                except IndexError:
                    prev_projects = ''
                if prev_projects != ' '.join(all_projects):
                    added_projects_users.append(udb.username)
                if udb.projects:
                    metadata['comment'] = '{0} {1}, {2}'.format(udb.name,
                                                                udb.surname,
                                                                udb.projects)
                    if metadata['shell'] == conf_opts['settings']['disableshell']:
                        metadata['shell'] = udb.was_shell
                else:
                    metadata['comment'] = '{0} {1},'.format(udb.name,
                                                            udb.surname)

            except NoResultFound as e:
                logger.error('{1} {0}'.format(user, str(e)))
                continue


    # trigger here is only new project assignments. so new users, same set of
    # them in db and yaml, just the associations between projects and users
    # changed.
    elif projects_changed:
        added_projects_users, deleted_projects_users = list(), list()
        try:
            # user is assigned to new project and reflects changes in yaml
            # comment
            projectschanged_db = session.query(Projects).filter(Projects.idproj.in_(projects_changed)).all()
            for project in projectschanged_db:
                users = project.users
                for user in users:
                    yaml_user = yusers['isabella_users'][user.username]
                    try:
                        yaml_projects = yaml_user['comment'].split(',')[1].strip()
                    except IndexError as exc:
                        yaml_projects = ''
                    if yaml_projects != user.projects:
                        diff_project = user_projects_changed([yaml_projects], [user.projects], logger)
                        if len(user.projects.split()) > len(yaml_projects.split()):
                            added_projects_users.append((user.username, ' '.join(diff_project)))
                        elif len(user.projects.split()) < len(yaml_projects.split()):
                            deleted_projects_users.append((user.username, ' '.join(diff_project)))
                        else:
                            added_projects_users.append((user.username, user.projects))
                            deleted_projects_users.append((user.username, yaml_projects))
                        if user.projects:
                            yaml_user['comment'] = '{0} {1}, {2}'.format(user.name,
                                                                         user.surname,
                                                                         user.projects)
                            # if user was previously disabled, he'll have
                            # nologin set. this will ensure working shell
                            # once he's back and active with new project
                            if yaml_user['shell'] == conf_opts['settings']['disableshell']:
                                yaml_user['shell'] = user.was_shell
                        else:
                            yaml_user['comment'] = '{0} {1},'.format(user.name,
                                                                     user.surname)

        except NoResultFound as e:
            logger.error('{1} {0}'.format(user, str(e)))
            pass

    else:
        logger.info("No changes in projects and users associations")

    # disable users whose grace period is over and are therefore inactive
    disabled_users = list()
    for user, data in yusers['isabella_users'].items():
        try:
            udb = session.query(User).filter(User.username == user).one()
            if (conf_opts['settings']['disableuser']
                and udb.status == 0
                and data['shell'] != conf_opts['settings']['disableshell']):
                udb.was_shell = data['shell']
                data['shell'] = conf_opts['settings']['disableshell']
                data['comment'] = '{0} {1},'.format(udb.name, udb.surname)
                udb.date_disabled = datetime.date.today()
                disabled_users.append(udb.username)
                session.commit()
            else:
                if udb.status == 0 and data['shell'] != conf_opts['settings']['disableshell']:
                    disabled_users.append(udb.username)

        except NoResultFound as e:
            logger.error('{1} {0}'.format(user, str(e)))
            continue
    if not disabled_users:
        logger.info("No users that needs to be disabled")


    # yaml changes needs to be written
    yaml_write_content = None
    if newusers or projects_changed or disabled_users:
        if newusers:
            yaml_write_content = {'isabella_users': allusers}

        elif projects_changed or disabled_users:
            yaml_write_content = yusers

        if args.noaction:
            yaml_written = True
        else:
            # backup and write once whatever changes were
            backup_yaml(conf_opts['external']['isabellausersyaml'], logger)
            yaml_written = write_yaml(conf_opts['external']['isabellausersyaml'], yaml_write_content, logger)

        if not yaml_written:
            logger.error("Error saving YAML changes")
            raise SystemExit(1)

        if newusers:
            logger.info("Added %d users: %s" % (len(newusersd), ', '.join(newusersd.keys())))
            if not args.noaction:
                f = session.query(MaxUID).first()
                f.uid = uid
                session.commit()
            if added_projects_users:
                logger.info("Changed projects for %d users: %s" %
                            (len(added_projects_users), ', '.join(added_projects_users)))

        elif projects_changed:
            if added_projects_users:
                logger.info("Update associations of existing users to projects: %s " %
                            ', '.join(['{0} assigned to {1}'.format(t[0], t[1]) for t in added_projects_users]))
            if deleted_projects_users:
                logger.info("Update associations of existing users to projects: %s " %
                            ', '.join(['{0} sign off from {1}'.format(t[0], t[1]) for t in deleted_projects_users]))


        if disabled_users:
            if conf_opts['settings']['disableuser']:
                logger.info("Disabled %s users: %s" % (len(disabled_users), ', '.join(disabled_users)))
            else:
                logger.info("%s users that will be disabled: %s" % (len(disabled_users), ', '.join(disabled_users)))


if __name__ == '__main__':
    main()
