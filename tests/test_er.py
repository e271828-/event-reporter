import unittest
from event_reporter import EventReporter
from mockredis.noseplugin import WithRedis
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

    def test_store_fetch_dispatch(self):
        """
        Checks to see that the EventReporter stores expected data
        """
        self.er.store('ga', 'event', '20538abc-a8af-46e0-b292-0999d94468e9', category='user', action='action_name', aip='1', uip='1.2.3.4', ds='web')

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

        r = self.er.fetch()

        self.assertTrue(isinstance(r['ts'], int))

        # ts varies
        del expected['ts']

        self.assertDictContainsSubset(expected, r)

        # NOTE: live test.
        self.assertTrue(self.er.dispatch(r))

        print(f'Data has been sent to {self.my_ua}. Please check real-time stats to confirm correctness.')
