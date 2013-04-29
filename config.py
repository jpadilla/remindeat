import os
import sys
from pymongo.uri_parser import parse_uri

project_name = 'remindeat'


class Config(object):
    DEBUG = False
    TESTING = False

    DEBUG_TB_INTERCEPT_REDIRECTS = False

    POSTMARK_API_KEY = os.environ['POSTMARK_API_KEY']
    POSTMARK_SENDER = os.environ['POSTMARK_SENDER']

    TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
    TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
    TWILIO_FROM_NUMBER = os.environ['TWILIO_FROM_NUMBER']

    HEROKU_API_KEY = os.environ['HEROKU_API_KEY']
    HEROKU_APP_NAME = os.environ['HEROKU_APP_NAME']

    FOURSQUARE_CLIENT_ID = os.environ['FOURSQUARE_CLIENT_ID']
    FOURSQUARE_CLIENT_SECRET = os.environ['FOURSQUARE_CLIENT_SECRET']
    FOURSQUARE_REDIRECT_URI = os.environ['FOURSQUARE_REDIRECT_URI']
    FOURSQUARE_PUSH_SECRET = os.environ['FOURSQUARE_PUSH_SECRET']

    SECRET_KEY = os.environ['SECRET_KEY']


class DevelopmentConfig(Config):
    DEBUG = True

    # Database Settings
    DB_URI = 'mongodb://localhost:27017/remindeat'
    MONGO_DBNAME = parse_uri(DB_URI)['database']

    # Celery Settings
    BROKER_URL = DB_URI

    STATIC_URL = '/static/'


class ProductionConfig(Config):
    try:
        SENTRY_DSN = os.environ['SENTRY_DSN']

        if 'MONGOHQ_URL' in os.environ:
            DB_URI = os.environ['MONGOHQ_URL']
            PARSED_DB_URI = parse_uri(DB_URI)
            MONGO_DBNAME = PARSED_DB_URI['database']
            MONGO_HOST = PARSED_DB_URI['nodelist'][0][0]
            MONGO_PORT = PARSED_DB_URI['nodelist'][0][1]
            MONGO_USERNAME = PARSED_DB_URI['username']
            MONGO_PASSWORD = PARSED_DB_URI['password']

            # Celery Settings
            BROKER_URL = DB_URI
    except:
        print "Unexpected error:", sys.exc_info()

    STATIC_URL = 'https://s3.amazonaws.com/com.remindeat.assets/static/'
