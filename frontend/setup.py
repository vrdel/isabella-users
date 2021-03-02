from distutils.core import setup
import glob


NAME = 'isabella-users-frontend'


def get_ver():
    try:
        for line in open(NAME + '.spec'):
            if "Version:" in line:
                return line.split()[1]
    except IOError:
        print("Make sure that %s is in directory" % (NAME + '.spec'))
        raise SystemExit(1)


setup(name=NAME,
      version=get_ver(),
      author='SRCE',
      author_email='dvrcic@srce.hr',
      description='Scripts for opening user accounts on SRCE Isabella cluster',
      url='https://github.com/vrdel/isabella-users/frontend',
      package_dir={'isabella_users_frontend': 'modules/'},
      packages=['isabella_users_frontend'],
      data_files=[('/etc/%s' % NAME, glob.glob('config/*')),
                  ('/usr/libexec/%s' % NAME, ['bin/open-accounts.py',
                                              'bin/update-cache.py',
                                              'bin/email-test.py'
                                              ]),
                  ('/usr/libexec/%s/sgetools/' % NAME, glob.glob('helpers/sgetools/*')),
                  ])
