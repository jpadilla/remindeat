web: newrelic-admin run-program gunicorn app:app -b 0.0.0.0:$PORT -w 3 --log-level=DEBUG
celeryd: newrelic-admin run-program celery -A core.tasks worker --loglevel=info
