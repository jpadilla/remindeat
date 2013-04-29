import datetime
from app import mongo


def import_checkins(client, user):

    food_categories = []
    categories = client.venues.categories()['categories']
    for category in categories:
        if category['name'] == 'Food':
            for _category in category['categories']:
                food_categories.append(_category['id'])

    print '# of food categories %s' % len(food_categories)

    checkins = client.users.checkins()['checkins']
    print '# of checkins %s' % checkins['count']
    print '--------'
    for checkin in checkins['items']:
        _checkin = checkin
        _venue = checkin['venue']
        _categories = _venue['categories']
        for category in _categories:
            if category['primary']:
                if category['id'] in food_categories:
                    print u'We have a food place'
                    venue = mongo.db.venues.find_one({'foursquare_id': _venue.get('id')})
                    if not venue:
                        print 'New Venue!'
                        _v = {
                            'foursquare_id': _venue.get('id'),
                            'venue_name': _venue.get('name'),
                            'categories': _categories,
                            'createdAt': datetime.datetime.utcnow(),
                            'updatedAt': datetime.datetime.utcnow()
                        }
                        mongo.db.venues.insert(_v)
                        venue = mongo.db.venues.find_one({'foursquare_id': _venue.get('id')})

                    checkin = mongo.db.checkins.find_one({'foursquare_id': _checkin.get('id')})
                    if not checkin:
                        print 'New Checkin!'
                        _c = {
                            'venue': venue,
                            'foursquare_id': _checkin.get('id'),
                            'meals': [],
                            'user': user,
                            'createdAt': datetime.datetime.fromtimestamp(_checkin['createdAt']),
                            'updatedAt': datetime.datetime.utcnow()
                        }
                        mongo.db.checkins.insert(_c)
                        checkin = mongo.db.checkins.find_one({'foursquare_id': _checkin.get('id')})
                else:
                    print 'Not a food place'
            else:
                print 'Not primary'
