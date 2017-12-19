import sqlite3
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
        self.bogususerfeed = \
            """[{
                "id": 108,
                "sifra": "API-2017",
                "status_id": "1",
                "date_from": "2017-11-10",
                "date_to": "2017-12-31",
                "users": [
                    {
                        "id": 375,
                        "uid": "hsutesrce.hr",
                        "ime": "Hrvoje",
                        "prezime": "Sute",
                        "mail": "Hrvoje.Sute@srce.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "108",
                            "osoba_id": "375"
                        }
                    }
                ]
            }]"""
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
        self.feedemail = \
            """[{
                "id": 108,
                "sifra": "API-2017",
                "status_id": "1",
                "date_from": "2017-11-10",
                "date_to": "2017-12-31",
                "users": [
                    {
                        "id": 375,
                        "uid": "dvrcic@srce.hr",
                        "ime": "Daniel",
                        "prezime": "Vrcic",
                        "mail": "Daniel.Vrcic@srce.hr",
                        "status_id": "1",
                        "pivot": {
                            "project_id": "108",
                            "osoba_id": "375"
                        }
                    }
                ]}
            ]"""

    @unittest.skip('skip this')
    @mock.patch('isabella_users_setup.requests.get')
    def testParseProjectsFeed(self, reqget):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        reqget.return_value = mocresp
        users = isabella_users_setup.fetch_newly_created_users(isabella_users_setup.conf_opts,
                                                               self.log)
        self.assertTrue(reqget.called)
        self.assertEqual(len(users), 3)

    @unittest.skip('skip this')
    @mock.patch('isabella_users_setup.requests.post')
    @mock.patch('isabella_users_setup.requests.get')
    def testMain(self, reqget, reqpost):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        reqget.return_value = mocresp
        isabella_users_setup.main()

    # @unittest.skip('skip this')
    @mock.patch('isabella_users_setup.sqlite3')
    @mock.patch('isabella_users_setup.requests.post')
    @mock.patch('isabella_users_setup.requests.get')
    def testEmail(self, reqget, reqpost, psqlite):
        moccursor = mock.Mock()
        moccursor.fetchone.side_effect= [(0, 'hsute', 1, 1, 1, 'foo', 1, 0, 1),
                                         (1, 'skala', 1, 1, 1, 'foo', 1, 0, 1),
                                         (2, 'vpaar', 1, 1, 1, 'foo', 1, 0, 1)]
        mocconn = mock.Mock()
        mocconn.cursor.return_value = moccursor
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feed)
        reqget.return_value = mocresp
        psqlite.connect.return_value = mocconn
        isabella_users_setup.main()
        if reqpost.mock_calls:
            self.assertEqual(reqpost.call_args_list[0][1]['data'], 'list=Isabella-dezurni&email=Hrvoje.Sute@srce.hr')
            self.assertEqual(reqpost.call_args_list[1][1]['data'], 'list=Isabella-dezurni&email=skala@irb.hr')
            self.assertEqual(reqpost.call_args_list[2][1]['data'], 'list=Isabella-dezurni&email=vpaar@phy.hr')

        moccursor = mock.Mock()
        moccursor.fetchone.side_effect= [(3, 'dvrcic', 1, 1, 1, 'foo', 1, 1, 0)]
        mocconn = mock.Mock()
        mocconn.cursor.return_value = moccursor
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.return_value = json.loads(self.feedemail)
        reqget.return_value = mocresp
        psqlite.connect.return_value = mocconn
        isabella_users_setup.main()

    @unittest.skip('skip this')
    @mock.patch('isabella_users_setup.requests.get')
    def testUsername(self, reqget):
        mocresp = mock.create_autospec(requests.Response)
        mocresp.json.side_effect = [json.loads(self.bogususerfeed), json.loads(self.feed)]
        reqget.return_value = mocresp
        users = isabella_users_setup.fetch_newly_created_users(isabella_users_setup.conf_opts,
                                                               self.log)
        userlist = list()
        for u in users:
            userlist.append(isabella_users_setup.gen_username(u, self.log))

        self.assertEqual(userlist, [None])

        users = isabella_users_setup.fetch_newly_created_users(isabella_users_setup.conf_opts,
                                                               self.log)


        userlist = list()
        for u in users:
            userlist.append(isabella_users_setup.gen_username(u, self.log))
        self.assertEqual(userlist, ['hsute','skala','vpaar'])
