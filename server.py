import logging

from flask import Flask, request, session, g
import flask
import pyodbc
from werkzeug.utils import redirect

import config

########################################################################################################################

from logging.config import dictConfig
from dotenv import load_dotenv
import os

load_dotenv()
# set up logger using logging_config.ini file in venv or .env, else default
if os.path.exists(os.path.dirname(os.path.realpath(__file__))+'\\.env'):
    LOG_PATH = os.getenv('LOG_PATH')+'mylog.log'
else:
    LOG_PATH = 'C:/Temp/mylog.log'
    try:
        os.mkdir('C:/Temp/')
    except FileExistsError as exc:
        pass

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': os.getenv('LOG_LEVEL') if os.path.exists(os.path.dirname(os.path.realpath(__file__))+'\\.env') else 'DEBUG'
        },
        'custom_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': r'{}'.format(LOG_PATH),
            'level': os.getenv('LOG_LEVEL') if os.path.exists(os.path.dirname(os.path.realpath(__file__))+'\\.env') else 'DEBUG'
        }
    },
    'root': {
        'level': os.getenv('LOG_LEVEL') if os.path.exists(os.path.dirname(os.path.realpath(__file__))+'\\.env') else 'DEBUG',
        'handlers': ['wsgi', 'custom_handler']
    }
})

########################################################################################################################

# https://stackoverflow.com/questions/18967441/add-a-prefix-to-all-flask-routes/36033627#36033627
# https://docs.microsoft.com/en-us/visualstudio/python/configure-web-apps-for-iis-windows?view=vs-2019


class PrefixMiddleware(object):

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]


# https://pythonise.com/series/learning-flask/python-before-after-request

server = Flask(__name__)
server.config['SECRET_KEY'] = config.SECRET_KEY
server.debug = config.DEBUG
# ==================
# server.config['SERVER_NAME'] = 'pacman.ogma.local:8080'
# server.config['SESSION_COOKIE_DOMAIN'] = 'pacman.ogma.local:8080'
# ==================
server.wsgi_app = PrefixMiddleware(server.wsgi_app)  # , prefix=config.APPLICATION_ROOT)


def get_conn():

    if 'conn' not in g:
        g.conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)

    return g.conn


def close_conn():
    conn = g.pop('conn', None)

    if conn is not None:
        conn.close()


# def get_cursor():
#
#    if 'cursor' not in g:
#        conn = get_conn()
#        g.cursor = conn.cursor()
#
#    return g.cursor


# def del_cursor():
#    cursor = g.pop('cursor', None)
#
#    if cursor is not None:
#        cursor.close()
#        del cursor


# WebModuleCreate?
# @server.before_first_request
# def before_first_request_func():
    # print('before first request')


# WebModuleBeforeDispatch
@server.before_request
def before_request_func():
    # print('before request')

    if config.CONNECTION_STRING is None:
        return None

    session['sessionID'] = 0
    session['externalID'] = 0

    return None # TODO: Why do we return None and still have a ton of code underneath?

    conn = get_conn()

    # if the sessionid exists in the request, validate the nonce
    # otherwiese validate the sessionid/tokenid out of the cookie

    sessionid = request.args.get('sessionID', type=int)

    if sessionid and (sessionid != session.get('sessionID')):
        nonce_key = request.args.get('a')
        nonce_value = request.args.get('b')

        query = """\
        declare @p_external_id int
        declare @p_result_status varchar(255)
        exec dbo.opp_validate_nonce {}, \'{}\', \'{}\', @p_external_id output, @p_result_status output
        select @p_external_id as external_id, @p_result_status as result_status
        """.format(sessionid, nonce_key, nonce_value)

        cursor = conn.cursor()
        cursor.execute(query)

        results = cursor.fetchone()

        if results.result_status != 'OK':
            cursor.close()
            del cursor
            print(results.result_status)
            flask.abort(404)

        session['sessionID'] = sessionid
        session['externalID'] = results.external_id

        cursor.close()
        del cursor

        # redirect without the query params to prevent errors on refresh
        if request.args.get('reportName'):
            return redirect(request.path + '?reportName=' + request.args.get('reportName'))
        else:
            return redirect(request.path)

    # validate session
    sessionid = session['sessionID']
    externalid = session['externalID']

    query = """\
    declare @p_external_id int
    declare @p_session_status varchar(64)
    declare @p_result_status varchar(255)
    exec dbo.opp_get_session2 {}, {}, {}, null, null, null, null, null, null, null, null, null, null, null, null, null,
    null, null, null, @p_session_status output, null, null, null, null, null, null, null, null, @p_external_id output,
    @p_result_status output
    select @p_external_id as external_id, @p_session_status as session_status, @p_result_status as result_status
    """.format(sessionid, sessionid, 1)

    cursor = conn.cursor()
    cursor.execute(query)

    results = cursor.fetchone()

    if results.result_status != 'OK' or results.external_id != externalid or results.session_status != 'OK':
        cursor.close()
        del cursor
        if results.result_status != 'OK':
            print(results.result_status)
        elif results.session_status != 'OK':
            print(results.session_status)
        else:
            print('Invalid external_id: {}'.format(externalid))
        flask.abort(404)

    cursor.close()
    del cursor


# WebModuleAfterDispatch
@server.after_request
def after_request_func(response):
    # print('after request')
    return response


# WebModuleException?
@server.teardown_request
def teardown_request_func(error=None):
    # print('teardown request')

    if error:
        # log the error
        print(str(error))


# WebModuleDestroy?
@server.teardown_appcontext
def teardown_appcontext_func(error=None):
    # print('teardown appcontext')
    close_conn()

    if error:
        # log the error
        print(str(error))


@server.route('/')
def index():
    return 'Hello world!'  # 404
