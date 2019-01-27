event-reporter
===========================

A Python wrapper for backend reporting via a worker/queue system.


[![travis](https://travis-ci.com/e271828-/event-reporter.svg?branch=master)](https://travis-ci.com/e271828-/event-reporter)

[![Codecov](http://codecov.io/github/e271828-/event-reporter/coverage.svg?branch=master)](http://codecov.io/github/e271828-/event-reporter?branch=master)


System flow:

Store event quickly on webserver [e.g. within a flask endpoint]:
```
from event_reporter import EventReporter
from redis import StrictRedis

er = EventReporter(conn=StrictRedis())

er.store('ga', 'event', '<uuid4 clientid>', category='event_category', action='action_name', aip='1', uip='1.2.3.4', ds='web')
```

Fetch event within worker and dispatch to final destination:
```
from event_reporter import EventReporter
from redis import StrictRedis

er = EventReporter(conn=StrictRedis())

r = er.fetch()

er.dispatch(r)
```

## Env vars used
`EVENTREPORTER_QUEUE_NAME` (redis key)
`UA_ID` (GA UA ID)

## Testing
```
export UA_ID='My_UA_ID'

nosetests -s
```

.. and check your GA property to see the data.
