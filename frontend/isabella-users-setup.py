#!/usr/bin/python

import os
import requests
import shutil
import sqlite3
import subprocess
import sys

from base64 import b64encode

from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger
from isabella_users_frontend.userutils import UserUtils
from isabella_users_frontend.msg import InfoAccOpen

connection_timeout = 120
conf_opts = parse_config()


def gen_password():
    s = os.urandom(64)

    return b64encode(s)[:30]


def fetch_newly_created_users(subscription, logger):
    users = None

    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        projects = response.json()

        for p in projects:
            if p.get('users', None):
                users = [u for u in p['users']]

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

    except Exception as e:
        logger.error(e)

    return users


def gen_username(uid, logger):
    username = None

    try:
        if '@' in uid['uid']:
            username = uid['uid'].split('@')[0]
        else:
            logger.warning('Wrong uid: %s' % uid['uid'])

    except Exception as e:
        logger.error(e)

    return username


def create_shareddir(dir, uid, gid, logger):
    try:
        os.mkdir(dir, 0750)
        os.chown(dir, uid, gid)

        return True

    except Exception as e:
        logger.error(e)

        return False


def create_homedir(dir, uid, gid, logger):
    try:
        os.mkdir(dir, 0750)
        os.chown(dir, uid, gid)

        for root, dirs, files in os.walk(conf_opts['settings']['skeletonpath']):
            for f in files:
                shutil.copy(root + '/' + f, dir)
                os.chown(dir + '/' + f, uid, gid)

        return True

    except Exception as e:
        logger.error(e)

        return False


def subscribe_maillist(token, name, email, username, logger):
    try:
        headers, payload = {}, {}

        headers = requests.utils.default_headers()
        headers.update({'content-type': 'application/x-www-form-urlencoded'})
        headers.update({'x-auth-token': token})
        payload = "list={0}&email={1}".format(name, email)

        response = requests.post(conf_opts['external']['mailinglist'],
                                 headers=headers, data=payload, timeout=180)
        response.raise_for_status()

        return True

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('Failed subscribing user %s on %s: %s' % (username, name,
                                                               str(e)))
        return False


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    usertool = UserUtils(logger)
    users = fetch_newly_created_users(conf_opts['external']['subscription'], logger)

    email_info = dict()

    if users:
        con = sqlite3.connect(conf_opts['settings']['cache'])
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        for u in users:
            password = None
            username = gen_username(u, logger)
            email = u['mail']
            email_info.update({username: dict()})
            email_info[username].update(email=email)
            uobj = usertool.get_user(username)
            if uobj:
                uid = usertool.get_user_id(uobj)
                cur.execute('select * from users where username = ?', (username,))
                r = cur.fetchone()
                if not r:
                    cur.execute('insert into users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                (None, username, 0, 0, 0, None, 0, 0, 0))
                    con.commit()
                    cur.execute('select * from users where username = ?', (username,))
                    r = cur.fetchone()

                userid, username, ishome, isshared, ispass, passval, issge, ismaillist, isemail = r

                if not ishome:
                    home = usertool.get_user_home(uobj)

                    if not os.path.exists(home):
                        if not create_homedir(home, uid, conf_opts['settings']['gid'], logger):
                            logger.error('Failed %s directory creation' % home)
                        else:
                            cur.execute('update users set home = ? where username == ?', (1, username, ))
                            con.commit()
                    else:
                        logger.warning('Skipping %s directory creation, already exists' % home)

                if not isshared:
                    sharedpath = conf_opts['settings']['sharedpath']
                    if not os.path.exists(sharedpath + username):
                        if not create_shareddir(sharedpath + username, uid, conf_opts['settings']['gid'], logger):
                            logger.error('Failed %s directory creation' % (sharedpath + username))
                        else:
                            cur.execute('update users set shared = ? where username == ?', (1, username, ))
                            con.commit()
                    else:
                        logger.warning('Skipping %s directory creation, already exists' % (sharedpath + username))

                if not ispass:
                    if usertool.get_user_pass(uobj) == '!!':
                        password = gen_password()
                        usertool.set_user_pass(uobj, password)
                        email_info[username].update(password=password)
                        cur.execute('update users set pass = ? where username == ?', (1, username, ))
                        cur.execute('update users set passvalue = ? where username == ?', (password, username, ))
                        con.commit()

                if not issge:
                    sgecreateuser_cmd = conf_opts['settings']['sgecreateuser']
                    try:
                        os.chdir(os.path.dirname(sgecreateuser_cmd))
                        subprocess.check_call('{0} {1} {2}'.format(sgecreateuser_cmd, username, 'foo'),
                                            shell=True, bufsize=512)
                        logger.info('User %s added to SGE' % username)
                        cur.execute('update users set sge = ? where username == ?', (1, username, ))
                        con.commit()

                    except Exception as e:
                        logger.error('Failed adding user %s to SGE: %s ' % (username, str(e)))

                if not ismaillist:
                    if subscribe_maillist(conf_opts['external']['mailinglisttoken'],
                                          conf_opts['external']['mailinglistname'],
                                          email, username, logger):
                        cur.execute('update users set maillist = ? where username == ?', (1, username, ))
                        con.commit()

                if not isemail:
                    templatepath = conf_opts['external']['emailtemplate']
                    smtpserver = conf_opts['external']['emailsmtp']
                    emailfrom = conf_opts['external']['emailfrom']
                    cur.execute('select passvalue from users where username = ?', (username,))
                    password = cur.fetchone()

                    e = InfoAccOpen(username, password, templatepath,
                                    smtpserver, emailfrom, email, logger)
                    e.send()

        con.close()

    else:
        raise SystemExit(0)


if __name__ == '__main__':
    main()
