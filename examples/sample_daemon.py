import time
import json
import logging
import os
from redis import StrictRedis
from event_reporter import EventReporter

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
LOG = logging.getLogger('evrlistener')

LOCALCONN = StrictRedis()
ER = EventReporter(conn=LOCALCONN)

def process_item(item):
    '''called for each new item'''
    return ER.dispatch(item)

def fetch_func():
    item = ER.fetch_oldest(blocking=True, timeout=5)
    if item:
        try:
            process_item(item)
        except Exception as e:
            LOG.error("process_item failed:{}, message: {}".format(
                e, message))
            time.sleep(10)  # sleep for 10 seconds
    time.sleep(0.001)  # be nice to the system :)


def main():
    while True:
        fetch_func()


if __name__ == "__main__":
    main()
