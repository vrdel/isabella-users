import sqlite3
import requests
import mock
import json
import unittest2 as unittest

from modules.log import Logger
import isabella_users_puppet_setup

class ProjectsFeed(unittest.TestCase):
    def setUp(self):
        log = Logger('test')
        self.log = log.get()
        self.feed = \
            """[
                {
                "id": 109,
                "sifra": "Foo-2018",
                "status_id": "1",
                "date_from": "2018-01-01",
                "date_to": "2018-05-15",
                "users": [
                    {
                        "id": 375,
                        "uid": "abaresic@mef.hr",
                        "ime": "Anja",
                        "prezime": "Baresic",
                        "mail": "Anja.Baresic@mef.hr",
                        "status_id": "4",
                        "pivot": {
                            "project_id": "109",
                            "osoba_id": "375"
                        }
                    },
                    {
                        "id": 376,
                        "uid": "tstilino@srce.hr",
                        "ime": "Tomislav",
                        "prezime": "Stilinovic",
                        "mail": "Tomislav.Stilinovic@srce.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "109",
                            "osoba_id": "376"
                        }
                    },
                    {
                        "id": 377,
                        "uid": "eimamagi@srce.hr",
                        "ime": "Emir",
                        "prezime": "Imamagic",
                        "mail": "Emir.Imamagic@srce.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "109",
                            "osoba_id": "377"
                        }
                    },
                    {
                        "id": 378,
                        "uid": "tdomazet@irb.hr",
                        "ime": "Tomislav",
                        "prezime": "Domazet",
                        "mail": "tdomazet@irb.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "109",
                            "osoba_id": "378"
                        }
                    },
                    {
                        "id": 12,
                        "uid": "vpaar@phy.hr",
                        "ime": "Vladimir",
                        "prezime": "Paar",
                        "mail": "vpaar@phy.hr",
                        "status_id": "4",
                        "pivot": {
                            "project_id": "109",
                            "osoba_id": "12"
                        }
                    }]
                },
                {
                "id": 108,
                "sifra": "API-2017",
                "status_id": "1",
                "date_from": "2017-11-10",
                "date_to": "2017-12-31",
                "users": [
                    {
                        "id": 375,
                        "uid": "hsute@srce.hr",
                        "ime": "Hrvoje",
                        "prezime": "Sute",
                        "mail": "Hrvoje.Sute@srce.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "108",
                            "osoba_id": "375"
                        }
                    },
                    {
                        "id": 30,
                        "uid": "skala@irb.hr",
                        "ime": "Karolj",
                        "prezime": "Skala",
                        "mail": "skala@irb.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "108",
                            "osoba_id": "30"
                        }
                    },
                    {
                        "id": 12,
                        "uid": "vpaar@phy.hr",
                        "ime": "Vladimir",
                        "prezime": "Paar",
                        "mail": "vpaar@phy.hr",
                        "status_id": "2",
                        "pivot": {
                            "project_id": "108",
                            "osoba_id": "12"
                        }
                    }]
                }
               ]"""
        self.yamlusers = {'abaresic': {'comment': 'Anja Baresic, 5467',
                                       'home': '/home/abaresic',
                                       'shell': '/bin/bash',
                                       'uid': 634,
                                       'gid': 501},
                          'aaleksic': {'comment': 'Arijan Aleksic, 000-0000000-0004',
                                       'home': '/home/aaleksic',
                                       'shell': '/bin/bash',
                                       'uid': 10132,
                                       'gid': 501}}
        self.newyusers = {u'eimamagi': {'comment': 'Emir Imamagic, project',
                                        'shell': '/bin/bash',
                                        'gid': 501L,
                                        'uid': 10183},
                          u'hsute': {'comment': 'Hrvoje Sute, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 502},
                          u'skala': {'comment': 'Karolj Skala, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 10186},
                          u'tdomazet': {'comment': 'Tomislav Domazet, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 10184},
                          u'tstilino': {'comment': 'Tomislav Stilinovic, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 10182},
                          u'vpaar': {'comment': 'Vladimir Paar, project',
                                     'shell': '/sbin/nologin',
                                     'gid': 501L,
                                     'uid': 10185}}
        self.crongiusers = {'ababic': {'comment': 'Ana Babic',
                                       'gid': 501,
                                       'home': '/home/ababic',
                                       'shell': '/bin/bash',
                                       'uid': 633},
                            'abaresic': {'comment': 'Anja Baresic',
                                         'gid': 501,
                                         'home': '/home/abaresic',
                                         'shell': '/bin/bash',
                                         'uid': 634},
                            'agudyma': {'comment': 'Andrii Gudyma',
                                        'gid': 501,
                                        'home': '/home/agudyma',
                                        'shell': '/bin/bash',
                                        'uid': 10207},
                            'hsute': {'comment': 'Hrvoje Sute',
                                      'gid': 501,
                                      'home': '/home/hsute',
                                      'shell': '/bin/bash',
                                      'uid': 502}}
        self.uidmax = {'uid_maximus': 10181}
        self.newuidmax = {'uid_maximus': 10186}


    def testInactiveUsers(self):
        statuses_users = {u'abaresic': [4],
                          u'eimamagi': [1],
                          u'hsute': [1],
                          u'skala': [1],
                          u'tdomazet': [1],
                          u'tstilino': [1],
                          u'vpaar': [4, 2]}
        inactive = isabella_users_puppet_setup.find_inactive_users(dict(statuses_users))
        self.assertEqual(inactive, ['abaresic', 'vpaar'])


    def testParseYaml(self):
        parsed_isabella = isabella_users_puppet_setup.load_yaml('tests/isabellausers.yaml', self.log)
        self.assertTrue('isabella_users' in parsed_isabella)
        self.assertEqual(parsed_isabella['isabella_users'], self.yamlusers)

        parsed_crongi = isabella_users_puppet_setup.load_yaml('tests/crongiusers.yaml', self.log)
        self.assertTrue('crongi_users' in parsed_crongi)
        self.assertEqual(parsed_crongi['crongi_users'], self.crongiusers)


    @mock.patch('isabella_users_puppet_setup.max_uid')
    @mock.patch('isabella_users_puppet_setup.write_yaml')
    @mock.patch('isabella_users_puppet_setup.avail_users')
    @mock.patch('isabella_users_puppet_setup.backup_yaml')
    @mock.patch('isabella_users_puppet_setup.requests.post')
    @mock.patch('isabella_users_puppet_setup.requests.get')
    def testMainLogic(self, reqget, reqpost, mockbackyaml, mockavailusers,
                  mockwriteyaml, mockmaxuid):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        co = {'external': dict()}
        co.update({'settings': dict()})
        co['external']['isabellausersyaml'] = 'tests/isabellausers.yaml'
        co['external']['crongiusersyaml'] = 'tests/crongiusers.yaml'
        co['external']['maxuidyaml'] = 'tests/isab_cro_maximus.yaml'
        co['external']['subscription'] = 'https://161.53.254.158:8443/croisab/api/isabella/projects'
        co['settings']['gid'] = 501L
        co['settings']['shell'] = '/bin/bash'
        reqget.return_value = mocresp
        mockmaxuid.return_value = 10181
        yamlusers = isabella_users_puppet_setup.load_yaml(co['external']['isabellausersyaml'], self.log)['isabella_users']
        crongiusers = isabella_users_puppet_setup.load_yaml(co['external']['crongiusersyaml'], self.log)['crongi_users']
        mockavailusers.side_effect = [yamlusers, crongiusers]
        isabella_users_puppet_setup.main.func_globals['conf_opts'] = co
        isabella_users_puppet_setup.main()
        merged = dict()
        merged.update(yamlusers)
        merged.update(self.newyusers)
        self.assertEqual(mockwriteyaml.call_args_list[0][0][1], merged)
        self.assertEqual(mockwriteyaml.call_args_list[1][0][1], self.newuidmax)
        self.assertEqual(mockmaxuid.call_args_list[0][0][0], self.uidmax)
