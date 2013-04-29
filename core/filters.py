import time
import hashlib


def epoch(value):
    try:
        return int(time.mktime(value.timetuple()))
    except:
        return 0


def sha1(value, pre='', post=''):
    return hashlib.sha1('%s%s%s' % (pre, value, post)).hexdigest()
