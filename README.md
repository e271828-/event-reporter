event-reporter
===========================

A Python wrapper for backend reporting via a worker/queue system.




<div align="center">
  <a href="https://travis-ci.org/e271828-/event-reporter">
    <img src="https://travis-ci.org/e271828-/event-reporter.svg?branch=master" alt="Build status" />
  </a>
  <a href="http://codecov.io/github/e271828-/event-reporter?branch=master">
    <img src="http://codecov.io/github/e271828-/event-reporter/coverage.svg?branch=master" alt="Codecov" />
  </a>
</div>


System flow:

Store event quickly on webserver [e.g. within a flask endpoint]:
```
from event_reporter import EventReporter
from redis import StrictRedis

er = EventReporter(conn=StrictRedis())

er.store('ga', 'event', '<uuid4 clientid>', aip='1', uip='1.2.3.4', ds='web')
```

Fetch event within worker and dispatch to final destination:
```
from event_reporter import EventReporter
from redis import StrictRedis

er = EventReporter(conn=StrictRedis())

r = er.fetch()

er.dispatch(r)
```

## Testing
```
export UA_ID='My_UA_ID'

nosetests -s
```

.. and check your GA property to see the data.
