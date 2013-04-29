import datetime
import json

import foursquare

from flask import (render_template, request, redirect,
                   session, flash, url_for, escape, g)

from pymongo.errors import OperationFailure
from bson.objectid import ObjectId

from app import app, mongo
from core.decorators import login_required
from tasks import send_reminder
from core.helpers import import_checkins

# Construct the client object
client = foursquare.Foursquare(
    client_id=app.config.get('FOURSQUARE_CLIENT_ID'),
    client_secret=app.config.get('FOURSQUARE_CLIENT_SECRET'),
    redirect_uri=app.config.get('FOURSQUARE_REDIRECT_URI')
)


@app.route('/')
def index_view():
    if session.get('user_id'):
        return redirect(url_for('venues_view'))
    data = {}
    data['hide_navbar'] = True
    return render_template('core/index.html', data=data)


@app.route('/login')
def login_view():
    session['next'] = request.args.get('next')
    return redirect(client.oauth.auth_url())


@app.route('/logout')
def logout_view():
    session.pop('next', None)
    session.pop('user_id', None)
    return redirect('/')


@app.route('/oauth/authorize')
def authorize_view():
    access_token = client.oauth.get_token(request.args['code'])

    client.set_access_token(access_token)

    foursquare_user = client.users()['user']
    foursquare_user_contact = foursquare_user.get('contact')

    user = mongo.db.users.find_one({'foursquare_id': foursquare_user.get('id')})
    is_new = False

    if not user:
        is_new = True
        _user = {
            'email': foursquare_user_contact.get('email'),
            'phone': foursquare_user_contact.get('phone'),
            'foursquare_id': foursquare_user.get('id'),
            'send_on': 'instantly',
            'access_token': access_token,
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }
        mongo.db.users.insert(_user)
        user = mongo.db.users.find_one({'foursquare_id': foursquare_user.get('id')})
        import_checkins(client, user)

    if user.get('_id'):
        session['user_id'] = user.get('_id')
        flash('You were succesfully authorized!', 'success')
    else:
        flash('There was an error :(', 'error')
    if is_new:
        return redirect(url_for('settings_view'))
    else:
        next = session.pop('next', None)
        if next:
            return redirect(escape(next))
        return redirect(url_for('venues_view'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    if request.method == 'POST':
        user_id = session.get('user_id')
        email = request.form.get('email')
        phone = request.form.get('phone')
        send_on = request.form.get('send_on')
        if not email and not phone:
            flash('You need to enter at least one option so we can notify you', 'error')
            return redirect(url_for('settings_view'))
        if user_id:
            try:
                mongo.db.users.update({'_id': ObjectId(user_id)}, {
                    '$set': {
                        'email': email,
                        'phone': phone,
                        'send_on': send_on,
                        'updatedAt': datetime.datetime.utcnow()
                    }
                }, safe=True)

                if send_on == 'never':
                    flash('You wont be notified, but you can still keep track of where you ate.', 'success')
                elif email and not phone:
                    flash('You will be notified via email everytime you checkin at a restaurant.', 'success')
                elif not email and phone:
                    flash('You will be notified via SMS everytime you checkin at a restaurant.', 'success')
                else:
                    flash('You will be notified via email and SMS everytime you checkin at a restaurant.', 'success')

            except OperationFailure:
                flash('There was an error saving your settings :(', 'error')

            return redirect(url_for('settings_view'))
    else:
        return render_template('core/settings.html')


@app.route('/venues', methods=['GET'])
@login_required
def venues_view():
    checkins = mongo.db.checkins.find({'user._id': g.user.get('_id')}).sort('createdAt', -1)
    _venues = []
    for checkin in checkins:
        if checkin.get('venue') not in _venues:
            _venues.append(checkin.get('venue'))
    data = {
        'venues': _venues
    }
    return render_template('core/venues.html', data=data)


@app.route('/venue/<ObjectId:venue_id>', methods=['GET'])
@login_required
def venue_meals_view(venue_id):
    venue = mongo.db.venues.find_one_or_404({'_id': venue_id})

    checkins = mongo.db.checkins.find({
        'venue._id': venue.get('_id'),
        'user._id': g.user.get('_id')
    })

    data = {
        'venue': venue,
        'checkins': checkins
    }
    return render_template('core/venue.html', data=data)


@app.route('/c/<ObjectId:checkin_id>', methods=['GET', 'POST'])
@app.route('/checkin/<ObjectId:checkin_id>', methods=['GET', 'POST'])
@login_required
def add_meal_view(checkin_id):
    checkin = mongo.db.checkins.find_one_or_404({'_id': checkin_id})

    # if not checkin:
    #     return 'Not Found', 404

    user = checkin.get('user')
    if user.get('_id') != session.get('user_id'):
        return 'Forbidden', 403

    if request.method == 'POST':
        meals = filter(None, request.form.getlist('meal'))
        # checkin_meals = checkin.get('meals')
        # checkin_meals.extend(meals)
        print 'Meals: %s' % meals
        try:
            mongo.db.checkins.update({'_id': checkin_id}, {
                '$set': {
                    'meals': meals,
                    'updatedAt': datetime.datetime.utcnow()
                }
            }, safe=True)

            flash('Your meals were succesfully saved!', 'success')

        except OperationFailure as e:
            print e
            flash('There was an error saving your meals :(', 'error')

        return redirect(url_for('add_meal_view', checkin_id=checkin_id))
    else:
        data = {
            'checkin': checkin
        }
        return render_template('core/checkin.html', data=data)


@app.route('/push', methods=['POST', 'GET'])
def push_view():

    if request.method != 'POST':
        return 'Nothing to do'

    if request.form.get('secret') != app.config.get('FOURSQUARE_PUSH_SECRET'):
        return 'Invalid secret', 401

    _checkin = json.loads(request.form.get('checkin'))
    _venue = _checkin.get('venue')
    _categories = _venue.get('categories')

    for category in _categories:
        if category.get('primary'):
            if 'Food' in category.get('parents'):
                _user = _checkin.get('user')

                user = mongo.db.users.find_one({'foursquare_id': _user.get('id')})
                if user:
                    venue = mongo.db.venues.find_one({'foursquare_id': _venue.get('id')})
                    if not venue:
                        _v = {
                            'foursquare_id': _venue.get('id'),
                            'venue_name': _venue.get('name'),
                            'categories': _categories,
                            'createdAt': datetime.datetime.utcnow(),
                            'updatedAt': datetime.datetime.utcnow()
                        }
                        mongo.db.venues.insert(_v)
                        venue = mongo.db.venues.find_one({'foursquare_id': _venue.get('id')})

                    last_checkin = mongo.db.checkins.find({
                        'venue._id': venue.get('_id'),
                        'user._id': user.get('_id'),
                        'meals.1': {'$exists': 1}
                    }).sort('_id', -1).limit(1)

                    _c = {
                        'venue': venue,
                        'foursquare_id': _checkin.get('id'),
                        'meals': [],
                        'user': user,
                        'createdAt': datetime.datetime.utcnow(),
                        'updatedAt': datetime.datetime.utcnow()
                    }
                    mongo.db.checkins.insert(_c)
                    checkin = mongo.db.checkins.find_one({'foursquare_id': _checkin.get('id')})

                    if user.get('send_on') != 'never':
                        print 'Send Reminder!'
                        if last_checkin.count(with_limit_and_skip=True) == 1:
                            send_reminder(venue, user, last_checkin[0], checkin)
                        else:
                            send_reminder(venue, user, None, checkin)

                    return 'ok'
                else:
                    return 'User not created', 401
    return 'No Food category found'
