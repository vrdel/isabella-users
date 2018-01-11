import ConfigParser
import sys
import os

conf = '/etc/isabella-users-puppet/puppet.conf'

def parse_config(logger=None):
    confopts = dict()

    try:
        config = ConfigParser.ConfigParser()
        if config.read(conf):
            for section in config.sections():
                if section.startswith('external'):
                    confopts['external'] = ({'isabellausersyaml': config.get(section, 'isabellausersyaml')})
                    confopts['external'].update({'crongiusersyaml': config.get(section, 'crongiusersyaml')})
                    confopts['external'].update({'maxuidyaml': config.get(section, 'maxuidyaml')})
                    confopts['external'].update({'backupdir': config.get(section, 'backupdir')})

                if section.startswith('settings'):
                    confopts['settings'] = {'gid': long(config.get(section, 'gid'))}
                    confopts['settings'].update({'shell': config.get(section, 'shell')})

            return confopts

        else:
            if logger:
                logger.error('Missing %s' % conf)
            else:
                sys.stderr.write('Missing %s\n' % conf)
            raise SystemExit(1)

    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
        if logger:
            logger.error(e)
        else:
            sys.stderr.write('%s\n' % e)
        raise SystemExit(1)

    except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError, SystemExit) as e:
        if getattr(e, 'filename', False):
            if logger:
                logger.error(e.filename + ' is not a valid configuration file')
                logger.error(' '.join(e.args))
            else:
                sys.stderr.write(e.filename + ' is not a valid configuration file\n')
                sys.stderr.write(' '.join(e.args) + '\n')
        raise SystemExit(1)

    return confopts
