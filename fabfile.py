import os
import mimetypes

from fabric.api import *

from boto.s3.key import Key
from boto.s3.connection import S3Connection

# IAM User: remindeat
AWS_ACCESS_KEY = 'AKIAJEENTBAQ7W2IYOBA'
AWS_SECRET_KEY = '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'
AWS_BUCKET_NAME = 'com.remindeat.assets'


# === Environments ===
def development():
    env.remote = 'origin master'


def production():
    env.remote = 'heroku master'


# === Deployment ===
def deploy():
    local('git push {remote}'.format(**env))


# === Static ===
def collectstatic():
    conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
    bucket = conn.create_bucket(AWS_BUCKET_NAME)
    excludes = ['.DS_Store']

    for root, dirs, files in os.walk('static/'):
        print root + '...'
        for f in files:
            _f = '%s/%s' % (root, f)

            mime_type, encoding = mimetypes.guess_type(f)
            mime_type = mime_type or 'application/octet-stream'
            headers = {
                'Content-Type': mime_type
            }

            if f not in excludes:
                k = Key(bucket)
                k.key = _f
                k.set_contents_from_filename(_f, headers)
                k.set_acl('public-read')

            # if f.endswith('.css') or f.endswith('.js'):
            #     p = os.popen('yuicompressor %s' % _f, 'r')
            #     while 1:
            #         line = p.readline()
            #         if not line:
            #             break
            #         k = Key(bucket)
            #         k.key = _f
            #         k.set_contents_from_string(line, headers)
            #         k.set_acl('public-read')
            # elif f not in excludes:
            #     k = Key(bucket)
            #     k.key = _f
            #     k.set_contents_from_filename(_f, headers)
            #     k.set_acl('public-read')
