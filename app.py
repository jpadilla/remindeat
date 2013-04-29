from flask import Flask
from flask.ext.pymongo import PyMongo

from flask_debugtoolbar import DebugToolbarExtension
from raven.contrib.flask import Sentry
from celery import Celery

from utils import (configure_error_handlers, configure_app,
    configure_template_filters)


app = Flask(__name__)
configure_app(app, 'config.DevelopmentConfig')
configure_error_handlers(app)
# configure_middleware_handlers(app)
configure_template_filters(app)
toolbar = DebugToolbarExtension(app)
mongo = PyMongo(app)


if not app.config.get('DEBUG'):
    sentry = Sentry(app)

celery = Celery()
celery.add_defaults(app.config)

from core.views import *

if __name__ == '__main__':
    app.run()
