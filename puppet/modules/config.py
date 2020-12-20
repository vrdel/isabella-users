import configparser
import sys
import os

conf = '/etc/isabella-users-puppet/puppet.conf'


def parse_config(logger=None):
    confopts = dict()

    try:
        config = configparser.ConfigParser()
        if config.read(conf):
            for section in config.sections():
                if section.startswith('external'):
                    confopts['external'] = ({'subscription': config.get(section, 'subscription')})
                    confopts['external'].update({'isabellausersyaml': config.get(section, 'isabellausersyaml')})

                if section.startswith('settings'):
                    confopts['settings'] = {'gid': config.getint(section, 'gid')}
                    confopts['settings'].update({'shell': config.get(section, 'shell')})
                    confopts['settings'].update({'disableuser': config.getboolean(section, 'disableuser')})
                    confopts['settings'].update({'excludeuser': config.get(section, 'excludeuser')})
                    confopts['settings'].update({'cache': config.get(section, 'cache')})
                    confopts['settings'].update({'mapuser': config.get(section, 'mapuser')})
                    confopts['settings'].update({'backupdir': config.get(section, 'backupdir')})

            return confopts

        else:
            if logger:
                logger.error('Missing %s' % conf)
            else:
                sys.stderr.write('Missing %s\n' % conf)
            raise SystemExit(1)

    except (configparser.NoOptionError, configparser.NoSectionError) as e:
        if logger:
            logger.error(e)
        else:
            sys.stderr.write('%s\n' % e)
        raise SystemExit(1)

    except (configparser.MissingSectionHeaderError, configparser.ParsingError, SystemExit) as e:
        if getattr(e, 'filename', False):
            if logger:
                logger.error(e.filename + ' is not a valid configuration file')
                logger.error(' '.join(e.args))
            else:
                sys.stderr.write(e.filename + ' is not a valid configuration file\n')
                sys.stderr.write(' '.join(e.args) + '\n')
        raise SystemExit(1)

    return confopts
