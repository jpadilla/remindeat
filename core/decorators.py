from functools import wraps
from flask import g, request, redirect, url_for, session

from app import mongo


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login_view', next=request.url))
        g.user_id = session.get('user_id')
        g.user = mongo.db.users.find_one({'_id': g.user_id})
        return f(*args, **kwargs)
    return decorated_function
