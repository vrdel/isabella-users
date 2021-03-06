from distutils.core import setup
import glob

NAME = 'isabella-users-puppet'


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
      description='Scripts for updating Puppet yaml with user accounts',
      url='https://github.com/vrdel/isabella-users/puppet',
      package_dir={'isabella_users_puppet': 'modules/'},
      packages=['isabella_users_puppet'],
      data_files=[('/etc/%s' % NAME, glob.glob('config/*')),
                  ('/etc/logrotate.d', ['logrotate.d/isabella-users-cache-backup']),
                  ('/usr/libexec/%s' % NAME, ['bin/sync-api.py',
                                              'bin/email-expired.py',
                                              'bin/email-grace.py',
                                              'bin/email-test.py',
                                              'bin/update-flags.py',
                                              'bin/update-yaml.py']),
                  ])
