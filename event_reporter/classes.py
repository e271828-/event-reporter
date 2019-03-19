import logging
import os
import json
from typing import Dict
import time

import keen
import google_measurement_protocol  # event, pageview, report

LOG = logging.getLogger("EventReporter")

TTL = os.getenv('EVENTREPORTER_TTL') # event reporter TTL set in env

class EventReporter(object):
    def __init__(self, conn, UA=None, queue_name=None):
        '''
        Initialize an EventReporter. Responsible for putting events
        and their timestamps into a simple Redis list queue.

        conn: Redis conn obj
        UA: GAMP property ID
        '''

        super(EventReporter, self).__init__()
        self.conn = conn
        default_ua = os.getenv('UA_ID', None)
        self.UA = UA or default_ua
        # default queue name (redis key) to store and fetch events
        default_queue_name = os.getenv('EVENTREPORTER_QUEUE_NAME', 'temp___eventreporterqueue')
        self.queue_name = queue_name or default_queue_name

        logging.basicConfig(level='WARNING', format='%(name)s | %(levelname)s | %(message)s')
        self.logger = logging.getLogger('EventReporter')
        self.logger.setLevel(logging.DEBUG)

    def get_ts(self):
        ''' current timestamp in ms '''
        return int(round(time.time() * 1000))

    def write_event(self, event):
        ''' write event to queue '''
        self.conn.rpush(self.queue_name, json.dumps(event))
        ''' set TTL for key '''
        if TTL:
            self.conn.expire(self.queue_name, int(TTL))

    def fetch(self):
        ''' fetch and remove most recent event from the queue '''
        event = self.conn.rpop(self.queue_name)
        if event:
            return json.loads(event)
        else:
            return None

    def fetch_oldest(self, blocking=True, timeout=None):
        '''
        remove and return oldest event from the queue. 
        blocks until an event is available if blocking is True and timeout is None.
        '''
        if blocking:
            if timeout:
                event = self.conn.blpop(self.queue_name, timeout=timeout)
            else:
                # hack for mockredis
                event = self.conn.blpop(self.queue_name)                
        else:
            event = self.conn.lpop(self.queue_name)

        if event:
            if type(event) == tuple:
                event = json.loads(event[1])
            else:
                event = json.loads(event)
        return event


    def _dispatch_ga(self, ua, data):
        if data['etype'] == 'event':
            payload = google_measurement_protocol.event(**data['args'])

        elif data['etype'] == 'pageview':
            payload = google_measurement_protocol.pageview(**data['args'])
        else:
            raise ValueError('unknown etype')
        # GA appears to ignore its own 'ua' override.
        # this is silly, but is the recommended solution.
        user_agent = data['args'].get('ua')
        if user_agent:
            extra_headers = {'user-agent': user_agent}
        else:
            extra_headers = {}

        # LOG.debug('payload: {}'.format(list(payload)))
        # send data (res is list of requests objs)
        res = google_measurement_protocol.report(ua, data['clientid'], payload, extra_headers=extra_headers)

        if not res:
            raise ValueError('nothing to send')

        for req in res:
           req.raise_for_status() 
        return True

    def _dispatch_keen(self, event, data):
        keen.add_event(event, data)
        return True


    def dispatch(self, data: Dict):
        '''
        Figures out the right handler to use for reporting and calls it
        with event data.

        Returns False if sending any request failed, otherwise True.
        '''

        # report offset between now and when we got the event (ms)
        data['args']['qt'] = str(self.get_ts() - data['ts'])

        if data['handler'] == 'ga':
            if not self.UA:
                LOG.error("No self UA defined skipping")
                return True
            else:
                return self._dispatch_ga(ua=self.UA, data=data)
        if data['handler'] == 'keen':
            event = data['etype']
            if not event:
                LOG.error("You need to specific an event (etype) if you dispatch to keen")
                return False
            else:
                try:
                    return self._dispatch_keen(event, data=data)
                except keen.exceptions.InvalidEnvironmentError as e:
                    LOG.warn("You are sending to keen but you need to specify some envvars{}".format(e))
                    return False
        else:
            raise ValueError('unknown handler')


    def safe_store(self, handler, etype, clientid, **data: Dict):
        '''
        Like store, but never throws an exception.
        '''
        r = False

        try:
            r = self.store(handler, etype, clientid, **data)
        except Exception as e:
            LOG.error(f'safe_store: store failed with: {e}')

        return r


    def store(self, handler: str, etype: str, clientid: str, **data: Dict):
        '''
        Stores an event dict with its timestamp in ms onto a simple queue.

        Arguments:
            handler: 
                A string defining what handler the receiving worker should use.
            etype: 
                A string defining what event type the handler will see.
            clientid: 
                A string of valid UUID4 format for a unique clientid.

            the other args: 
                Any simple dict matching that handler's expectations.

        Called by e.g. API endpoints that need to return quickly.
        Returns value of queue op action.
        '''
        assert handler and etype and clientid

        final_data = {
            "handler": handler,
            "etype": etype,
            "clientid": clientid,
            "ts": self.get_ts(),
            "args": data
        }

        # store event data
        r = self.write_event(final_data)

        debug_json = {"message": "new_eventreporter_report_json", **final_data}

        self.logger.debug(json.dumps(debug_json))

        return r
