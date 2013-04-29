from os import environ

from pymongo import Connection

from flask import render_template, g

from core.filters import epoch, sha1


def configure_app(app, config):
    app.config.from_object(config)
    if environ.get('APP_CONFIG'):
        app.config.from_object(environ.get('APP_CONFIG'))


# DB Connection
def connect_db(app):
    connection = Connection(app.config['DB_URI'])
    return connection[app.config['DB_NAME']]


def configure_template_filters(app):
    app.jinja_env.filters['epoch'] = epoch
    app.jinja_env.filters['sha1'] = sha1


# Middleware
def configure_middleware_handlers(app):

    @app.before_request
    def before_request():
        g.db = connect_db(app)

    @app.teardown_request
    def teardown_request(exception):
        g.db.connection.close()


def configure_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_page(error):
        """
        The server understood the request, but is refusing to fulfill it.
        Authorization will not help and the request SHOULD NOT be repeated.
        If the request method was not HEAD and the server wishes to make public
        why the request has not been fulfilled, it SHOULD describe the reason for
        the refusal in the entity. If the server does not wish to make this
        information available to the client, the status code 404 (Not Found)
        can be used instead.
        """
        return render_template("access_forbidden.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        """
        The server has not found anything matching the Request-URI. No indication
        is given of whether the condition is temporary or permanent. The 410 (Gone)
        status code SHOULD be used if the server knows, through some internally
        configurable mechanism, that an old resource is permanently unavailable
        and has no forwarding address. This status code is commonly used when the
        server does not wish to reveal exactly why the request has been refused,
        or when no other response is applicable.
        """
        return render_template("page_not_found.html"), 404

    @app.errorhandler(405)
    def method_not_allowed_page(error):
        """
        The method specified in the Request-Line is not allowed for the resource
        identified by the Request-URI. The response MUST include an Allow header
        containing a list of valid methods for the requested resource.
        """
        return render_template("method_not_allowed.html"), 405

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("server_error.html"), 500
