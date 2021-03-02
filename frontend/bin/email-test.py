#!/usr/bin/python

from isabella_users_frontend.config import parse_config
from isabella_users_frontend.log import Logger
from isabella_users_frontend.msg import InfoAccOpen

import argparse
import datetime
import sys

conf_opts = parse_config()


def main():
    lobj = Logger(sys.argv[0])
    logger = lobj.get()

    parser = argparse.ArgumentParser(description="warn users that they are not active anymore")
    parser.add_argument('-f', required=True, help='Email FROM', dest='emailfrom')
    parser.add_argument('-t', required=True, help='Email TO', dest='emailto')
    parser.add_argument('-u', required=True, help='Username', dest='username')
    parser.add_argument('-p', required=True, help='Password', dest='password')
    parser.add_argument('-v', required=False, default=False,
                        action='store_true', help='Verbose', dest='verbose')
    args = parser.parse_args()
    templatepath = conf_opts['external']['emailtemplate']
    templatehtml = conf_opts['external']['emailhtml']
    smtpserver = conf_opts['external']['emailsmtp']
    emailfrom = conf_opts['external']['emailfrom']

    email_obj = InfoAccOpen(templatepath, templatehtml, smtpserver,
                            args.emailfrom, args.emailto, args.username,
                            args.password, logger)

    ret = email_obj.send()


if __name__ == '__main__':
    main()
