import requests
import mock
import json
import unittest2 as unittest

from modules.log import Logger
import isabella_users_setup

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

    @mock.patch('isabella_users_setup.requests.get')
    def testParseProjectsFeed(self, reqget):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        reqget.return_value = mocresp
        users = isabella_users_setup.fetch_newly_created_users(isabella_users_setup.conf_opts,
                                                               self.log)
        self.assertTrue(reqget.called)
        self.assertEqual(len(users), 3)
