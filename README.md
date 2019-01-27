event-reporter
===========================

A Python wrapper for backend reporting via a worker/queue system.

System flow:

Store event quickly on webserver [e.g. flask]:
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
