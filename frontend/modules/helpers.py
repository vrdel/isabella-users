from unidecode import unidecode
from base64 import b64encode
import requests

connection_timeout = 120


def extract_email(projects, name, surname, last_project, logger):
    email = None

    # last_project is multi project field now. pick last one, but any will
    # actually play as we're just grabbing email from the API feed.
    if projects:
        try:
            target_project = last_project.split()[-1]

            for p in projects:
                if target_project == p['sifra']:
                    users = p['users']
                    for u in users:
                        if (name == concat(unidecode(u['ime'])) and
                            surname == concat(unidecode(u['prezime']))):
                            email = u['mail']
            if email:
                return email

            else:
                logger.error('Failed grabbing an email for %s %s from the API' % (name, surname))

        except IndexError as exc:
            logger.error('Failed grabbing an project for %s %s from the API' % (name, surname))

    else:
        logger.error('Failed grabbing an email for %s %s from the API as project is unknown' % (name, surname))

    return None


def concat(s):
    if '-' in s:
        s = s.split('-')
        s = ''.join(s)
    if ' ' in s:
        s = s.split(' ')
        s = ''.join(s)

    return s


def fetch_projects(subscription, logger):
    try:
        response = requests.get(subscription, timeout=connection_timeout, verify=False)
        response.raise_for_status()
        users = dict()
        projects = response.json()

        return projects

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        logger.error('requests error: %s' % e)

        return False
