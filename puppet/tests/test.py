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
            """[{
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
                    }
                ]
            }]"""
        self.yamlusers = {'abaresic': {'comment': 'Anja Baresic, 5467',
                                       'home': '/home/abaresic',
                                       'shell': '/bin/bash',
                                       'uid': 10181,
                                       'gid': 501},
                          'aaleksic': {'comment': 'Arijan Aleksic, 000-0000000-0004',
                                       'home': '/home/aaleksic',
                                       'shell': '/bin/bash',
                                       'uid': 10132,
                                       'gid': 501}}
        self.newyusers = {u'vpaar': {'comment': 'Vladimir Paar, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 10184},
                          u'skala': {'comment': 'Karolj Skala, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                     'uid': 10183},
                          u'hsute': {'comment': 'Hrvoje Sute, project',
                                     'shell': '/bin/bash',
                                     'gid': 501L,
                                    'uid': 10182}}
        self.uidmax = {'uid_maximus': 10181}
        self.newuidmax = {'uid_maximus': 10184}

    @mock.patch('isabella_users_puppet_setup.max_uid')
    @mock.patch('isabella_users_puppet_setup.write_yaml')
    @mock.patch('isabella_users_puppet_setup.avail_users')
    @mock.patch('isabella_users_puppet_setup.backup_yaml')
    @mock.patch('isabella_users_puppet_setup.requests.post')
    @mock.patch('isabella_users_puppet_setup.requests.get')
    def testYamls(self, reqget, reqpost, mockbackyaml, mockavailusers,
                  mockwriteyaml, mockmaxuid):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        co = {'external': dict()}
        co.update({'settings': dict()})
        co['external']['isabellausersyaml'] = 'tests/isabellausers.yaml'
        co['external']['maxuidyaml'] = 'tests/isab_cro_maximus.yaml'
        co['external']['subscription'] = 'https://161.53.254.158:8443/croisab/api/isabella/projects'
        co['settings']['gid'] = 501L
        co['settings']['shell'] = '/bin/bash'
        reqget.return_value = mocresp
        mockmaxuid.side_effect = [10181, 10184, 10183, 10182]
        isabella_users_puppet_setup.main.func_globals['conf_opts'] = co
        isabella_users_puppet_setup.main()
        mockavailusers.assert_called_with(self.yamlusers)
        merged = dict()
        merged.update(self.yamlusers)
        merged.update(self.newyusers)
        self.assertEqual(mockwriteyaml.call_args_list[0][0][1], merged)
        self.assertEqual(mockwriteyaml.call_args_list[1][0][1], self.newuidmax)
        self.assertEqual(mockmaxuid.call_args_list[0][0][0], self.uidmax)


    @mock.patch('isabella_users_puppet_setup.write_yaml')
    @mock.patch('isabella_users_puppet_setup.requests.post')
    @mock.patch('isabella_users_puppet_setup.requests.get')
    def testMain(self, reqget, reqpost, mockwriteyaml):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        reqget.return_value = mocresp
        isabella_users_puppet_setup.main()
