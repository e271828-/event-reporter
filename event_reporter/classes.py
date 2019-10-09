import json
import logging
import os
import time
from typing import Dict

import google_measurement_protocol  # event, pageview, report

import beeline
import requests

LOG = logging.getLogger("EventReporter")

TTL = os.getenv('EVENTREPORTER_TTL')  # event reporter TTL set in env

logging.getLogger('urllib3').setLevel(logging.INFO)


class EventReporter(object):
    def __init__(self, conn, UA=None, queue_name=None, honey_writekey=None):
        '''
        Initialize an EventReporter. Responsible for putting events
        and their timestamps into a simple Redis list queue.

        conn: Redis conn obj
        UA: GAMP property ID
        '''

        super(EventReporter, self).__init__()
        self.conn = conn
        default_ua = os.getenv('UA_ID')
        default_honeywritekey = os.getenv("HONEYCOMB_WRITEKEY")
        self.honey_writekey = honey_writekey or default_honeywritekey
        self.UA = UA or default_ua

        # configure honeycomb
        if honey_writekey:
            beeline.init(
                writekey=honey_writekey,
                dataset='event_reporter',
                service_name='event_reporter')

        # default queue name (redis key) to store and fetch events
        default_queue_name = os.getenv('EVENTREPORTER_QUEUE_NAME',
                                       'temp___eventreporterqueue')
        self.queue_name = queue_name or default_queue_name

        logging.basicConfig(
            level='WARNING', format='%(name)s | %(levelname)s | %(message)s')
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
                # hack for fakeredis
                event = self.conn.blpop(self.queue_name)
        else:
            event = self.conn.lpop(self.queue_name)

        if event:
            if type(event) == tuple:
                event = json.loads(event[1])
            else:
                event = json.loads(event)
        return event

    def dispatch(self, data: Dict):
        '''
        Figures out the right handler to use for reporting and calls it
        with event data.

        Returns False if sending any request failed, otherwise True.
        '''
        if data['handler'] == 'ga':

            if not self.UA:
                raise ValueError('missing UA')

            # report offset between now and when we got the event (ms)
            data['args']['qt'] = str(self.get_ts() - data['ts'])

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
            res = google_measurement_protocol.report(
                self.UA,
                data['clientid'],
                payload,
                extra_headers=extra_headers)

            if not res:
                raise ValueError('nothing to send')

            for req in res:
                req.raise_for_status()
        elif data['handler'] == 'honey':
            event = beeline.new_event()
            event.add(data)
            event.send()
        elif data['handler'] == 'slack':
            webhook = data['args'].get('webhook')
            if not webhook:
                raise ValueError('slack handler: missing webhook')
            slack_data = {}
            if data['args'].get('message'):
                slack_data['text'] = data['args'].get('message')
            elif data['args'].get('blocks'):
                # support Block Kit Builder
                slack_data['blocks'] = data['args'].get('blocks')
            else:
                raise ValueError('slack handler: missing both message and blocks')
            response = requests.post(webhook, json=slack_data)
            if response.status_code != 200:
                self.logger.warning(f"could not send slack msg: code {response.status_code} msg {response.text}. tried to send: {json.dumps(slack_data)}")
            else:
                self.logger.debug('sent slack webhook: {response.status_code}')
        else:
            raise ValueError('unknown handler')
        return True

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
