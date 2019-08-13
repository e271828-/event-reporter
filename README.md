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

 - `EVENTREPORTER_QUEUE_NAME` (redis key)
 - `UA_ID` (GA UA ID)
 - `EVENTREPORTER_TTL` (int: controls whether to set expire time for redis keys)
 - `HONEYCOMB_WRITEKEY` (optional)

## Testing
```
export UA_ID='My_UA_ID'

nosetests -s
```

## Dispatch Types

 - `ga`: GA
 - `honey`: honeycomb.io
 - `slack`: slack

### Example slack event: Simple message
`er.store('slack', 'event', '<uuid4>', webhook='<slack_webhook_uri>', message='text')`

### Example slack event: Blocks message
`er.store('slack', 'event', '<uuid4>', webhook='<slack_webhook_uri>', blocks=<list_of_dicts>)`

### Example slack blocks format
```
[
	{
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": "Hello
			}
	}
]
```


.. and check your GA property, honeycomb dash, or slack channel to see the data.
