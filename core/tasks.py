import heroku

# from flask import render_template, render_template_string
from jinja2 import FileSystemLoader, Environment

from postmark.core import PMMail
from twilio.rest import TwilioRestClient

from flask import Flask

from celery import Celery

from utils import configure_app


app = Flask(__name__)
configure_app(app, 'config.DevelopmentConfig')
# configure_error_handlers(app)
# configure_middleware_handlers(app)
# toolbar = DebugToolbarExtension(app)
env = Environment(loader=FileSystemLoader('./templates/'))

celery = Celery()
celery.add_defaults(app.config)

cloud = heroku.from_key(app.config.get('HEROKU_API_KEY'))


def send_reminder(venue, user, last_checkin, checkin):

    scale_celery(1)

    if user.get('send_on') == 'instantly':

        if user.get('email'):
            print 'Delaying email'
            email_reminder.delay(venue, user, last_checkin, checkin)

        if user.get('phone'):
            print 'Delaying sms'
            sms_reminder.delay(venue, user, last_checkin, checkin)
    else:
        if user.get('email'):
            print 'Async email'
            email_reminder.apply_async((venue, user, last_checkin, checkin), countdown=int(user.get('send_on')))

        if user.get('phone'):
            print 'Async sms'
            sms_reminder.apply_async((venue, user, last_checkin, checkin), countdown=int(user.get('send_on')))


def scale_celery(qty=0):
    cloud._http_resource(method='POST',
        resource=('apps', app.config.get('HEROKU_APP_NAME'), 'ps', 'scale'),
            data={'type': 'celeryd', 'qty': qty})


@celery.task
def email_reminder(venue, user, last_checkin, checkin):
    template = env.get_template('core/email.txt')
    postmark_message = PMMail(api_key=app.config.get('POSTMARK_API_KEY'),
                          subject='You just checked-in @ %s' % venue.get('venue_name'),
                          sender=app.config.get('POSTMARK_SENDER'),
                          to=user.get('email'),
                          text_body=template.render(venue=venue,
                            last_checkin=last_checkin, checkin=checkin))
    postmark_message.send()
    scale_celery(0)


@celery.task
def sms_reminder(venue, user, last_checkin, checkin):
    template = env.get_template('core/sms.txt')
    twilio_client = TwilioRestClient(app.config.get('TWILIO_ACCOUNT_SID'),
        app.config.get('TWILIO_AUTH_TOKEN'))
    twilio_client.sms.messages.create(to=user.get('phone'),
        from_=app.config.get('TWILIO_FROM_NUMBER'),
        body=template.render(venue=venue, last_checkin=last_checkin, checkin=checkin))
    scale_celery(0)


@celery.task
def test():
    print 'here'
    template = env.get_template('core/sms.txt')
    print template
    print template.render()
