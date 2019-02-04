import unittest
from event_reporter import EventReporter
from mockredis.noseplugin import WithRedis
from mockredis.exceptions import ResponseError

import os

class EventReporterTest(unittest.TestCase):
    def setUp(self):
        self.conn = WithRedis.StrictRedis()
        self.conn.flushdb()
        # override with your own UA to verify test results in GA
        self.my_ua = os.getenv('UA_ID', 'UA-116198943-3')
        self.er = EventReporter(UA=self.my_ua, conn=self.conn)

    def test_base(self):
        """
        Checks to see that the base EventReporter class loads
        """
        pass

    @unittest.skip('will fail if env var overrides UA_ID')
    def test_args(self):
        """
        Checks to see that EventReporter stores UA
        """
        self.assertTrue(self.er.UA == 'UA-116198943-3')

    def test_store_fetch_dispatch(self):
        """
        Checks to see that the EventReporter stores expected data
        """
        ar = self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web', ua='my-useragent-test')

        self.assertTrue(ar == None)

        expected = {
            'handler': 'ga',
            'etype': 'event',
            'clientid': '20538abc-a8af-46e0-b292-0999d94468e9',
            'ts': 1548546584914,
            'args': {
                'category': 'user',
                'action': 'action_name',
                'aip': '1',
                'uip': '1.2.3.4',
                'ds': 'web',
                'ua': 'my-useragent-test'
            }
        }

        r = self.er.fetch()

        self.assertTrue(isinstance(r['ts'], int))

        # ts varies
        del expected['ts']

        self.assertDictContainsSubset(expected, r)

        # NOTE: live test.
        self.assertTrue(self.er.dispatch(r))

        # print(f'Data has been sent to {self.my_ua}. Please check real-time stats to confirm correctness.')


    def test_store_fetch_oldest_double(self):
        """
        Checks to see that the EventReporter fetch_oldest gets expected data
        """
        ar = self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web')
        ar2 = self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name_2', aip='1', uip='1.2.3.4', ds='web')

        self.assertTrue(ar == None)

        expected = {
            'handler': 'ga',
            'etype': 'event',
            'clientid': '20538abc-a8af-46e0-b292-0999d94468e9',
            'ts': 1548546584914,
            'args': {
                'category': 'user',
                'action': 'action_name',
                'aip': '1',
                'uip': '1.2.3.4',
                'ds': 'web'
            }
        }

        r = self.er.fetch_oldest()

        self.assertTrue(isinstance(r['ts'], int))

        # ts varies
        del expected['ts']

        self.assertDictContainsSubset(expected, r)


    def test_store_fetch_oldest_single(self):
        """
        Checks to see that the EventReporter fetch_oldest gets expected data
        """
        ar = self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web')

        self.assertTrue(ar == None)

        expected = {
            'handler': 'ga',
            'etype': 'event',
            'clientid': '20538abc-a8af-46e0-b292-0999d94468e9',
            'ts': 1548546584914,
            'args': {
                'category': 'user',
                'action': 'action_name',
                'aip': '1',
                'uip': '1.2.3.4',
                'ds': 'web'
            }
        }

        r = self.er.fetch_oldest()

        self.assertTrue(isinstance(r['ts'], int))

        # ts varies
        del expected['ts']

        self.assertDictContainsSubset(expected, r)


    def test_unsafe_store(self):
        '''
        Verify that e.g. a redis or argument failure throws an exception.
        '''
        with self.assertRaises(TypeError):
            self.er.store(category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web')

    def test_safe_store_fail(self):
        '''
        Verify that e.g. a redis or argument failure does not throw an exception.
        '''
        r = self.er.safe_store(None, None, None, action='action_name', aip='1', uip='1.2.3.4', ds='web')
        self.assertTrue(r == False)

    def test_safe_store_success(self):
        '''
        Verify that e.g. a redis or argument failure does not throw an exception.
        '''
        r = self.er.safe_store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web')
        self.assertTrue(r == None)


    def test_store_fetch_dispatch_referrer(self):
        """
        Checks to see that the EventReporter stores expected data with referrer.
        Looks like it's unnecessary to urlencode prior to handing it off.
        """
        ar = self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web', dr='http://www.test.com')

        self.assertTrue(ar == None)

        expected = {
            'handler': 'ga',
            'etype': 'event',
            'clientid': '20538abc-a8af-46e0-b292-0999d94468e9',
            'ts': 1548546584914,
            'args': {
                'category': 'user',
                'action': 'action_name',
                'aip': '1',
                'uip': '1.2.3.4',
                'ds': 'web',
                'dr': 'http://www.test.com'
            }
        }

        r = self.er.fetch()

        self.assertTrue(isinstance(r['ts'], int))

        # ts varies
        del expected['ts']

        self.assertDictContainsSubset(expected, r)

        # NOTE: live test.
        self.assertTrue(self.er.dispatch(r))
