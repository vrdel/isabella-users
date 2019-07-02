import ConfigParser
import sys
import os

conf = '/etc/isabella-users-frontend/frontend.conf'

def parse_config(logger=None):
    confopts = dict()

    try:
        config = ConfigParser.ConfigParser()
        if config.read(conf):
            for section in config.sections():
                if section.startswith('external'):
                    confopts['external'] = ({'subscription': config.get(section, 'subscription')})
                    confopts['external'].update({'projects': config.get(section, 'projects')})
                    confopts['external'].update({'mailinglist': config.get(section, 'mailinglist')})
                    confopts['external'].update({'mailinglisttoken': config.get(section, 'mailinglisttoken')})
                    confopts['external'].update({'mailinglistname': config.get(section, 'mailinglistname')})
                    confopts['external'].update({'emailfrom': config.get(section, 'emailfrom')})
                    confopts['external'].update({'emailsubject': config.get(section, 'emailsubject')})
                    confopts['external'].update({'emailsmtp': config.get(section, 'emailsmtp')})
                    confopts['external'].update({'emailtemplate': config.get(section, 'emailtemplate')})
                    if not os.path.exists(confopts['external']['emailtemplate']):
                        if logger:
                            logger.error('%s does not exist' % confopts['external']['emailtemplate'])
                        else:
                            sys.stderr.write('%s does not exist\n' % confopts['external']['emailtemplate'])
                        raise SystemExit(1)


                if section.startswith('settings'):
                    confopts['settings'] = {'gid': long(config.get(section, 'gid'))}

                    sharedpath = config.get(section, 'sharedpath')
                    if not sharedpath.endswith('/'):
                        sharedpath = sharedpath + '/'
                    confopts['settings'].update({'sharedpath': sharedpath})

                    skeletonpath = config.get(section, 'skeletonpath')
                    if not skeletonpath.endswith('/'):
                        skeletonpath = skeletonpath + '/'
                    confopts['settings'].update({'skeletonpath': skeletonpath})
                    if not os.path.exists(confopts['settings']['skeletonpath']):
                        if logger:
                            logger.error('%s does not exist' % confopts['settings']['skeletonpath'])
                        else:
                            sys.stderr.write('%s does not exist\n' % confopts['settings']['skeletonpath'])
                        raise SystemExit(1)

                    sgecreateuser = config.get(section, 'sgecreateuser')
                    confopts['settings'].update({'sgecreateuser': sgecreateuser})
                    if not os.path.exists(confopts['settings']['skeletonpath']):
                        if logger:
                            logger.error('%s does not exist' % confopts['settings']['sgecreateuser'])
                        else:
                            sys.stderr.write('%s does not exist\n' % confopts['settings']['sgecreateuser'])
                        raise SystemExit(1)

                    cache = config.get(section, 'cache')
                    confopts['settings'].update({'cache': cache})
                    if not os.path.exists(confopts['settings']['cache']):
                        if logger:
                            logger.error('%s does not exist' % confopts['settings']['cache'])
                        else:
                            sys.stderr.write('%s does not exist\n' % confopts['settings']['cache'])
                        raise SystemExit(1)

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
