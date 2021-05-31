from datetime import timedelta

import flask
from flask import Flask, request, session, g
import pyodbc
from werkzeug.utils import redirect
import config
import logging

from apps.OPG001.data import load_datasets
from flask_session import Session

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


server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_PERMANENT'] = True
server.config['SESSION_USE_SIGNER'] = True
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
server.config['SESSION_FILE_THRESHOLD'] = 100

server_session = Session(server)


def dict_to_string(d):

    if d is None:
        return "None"

    s = ""

    for key in d:

        if s != "":
            s += ", "

        s += "('" + key + "', '" + str(d[key]) + "')"

    return "[" + s + "]"


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
@server.before_first_request
def before_first_request_func():
    logging.debug(request.method + " " + request.url)
    logging.debug("request=" + dict_to_string(request.values))
    logging.debug("cookies=" + dict_to_string(request.cookies))
    logging.debug("session=" + dict_to_string(session))


# WebModuleBeforeDispatch
@server.before_request
def before_request_func():
    logging.debug(request.method + " " + request.url)
    logging.debug("request=" + dict_to_string(request.values))
    logging.debug("cookies=" + dict_to_string(request.cookies))
    logging.debug("session=" + dict_to_string(session))

    if config.SESSIONLESS:
        session["sessionID"] = "0"
        session["externalID"] = "0"
        return None

    conn = get_conn()

    # if the sessionid exists in the request, validate the nonce
    # otherwise validate the sessionid/tokenid out of the cookie

    sessionid = request.args.get("sessionID", type=int)

    if sessionid:  # and (sessionid != session.get("sessionID")):
        session["sessionID"] = "0"
        session["externalID"] = "0"

        nonce_key = request.args.get("a")
        nonce_value = request.args.get("b")

        query = """\
        declare @p_external_id int
        declare @p_result_status varchar(255)
        exec dbo.OPP_Validate_Nonce {}, \'{}\', \'{}\', @p_external_id output, @p_result_status output
        select @p_external_id as external_id, @p_result_status as result_status
        """.format(sessionid, nonce_key, nonce_value)

        # logging.debug("\n" + query)

        cursor = conn.cursor()
        cursor.execute(query)

        results = cursor.fetchone()

        if results.result_status != "OK":
            cursor.close()
            del cursor
            logging.error(results.result_status)
            flask.abort(404)

        session["sessionID"] = sessionid
        session["externalID"] = results.external_id

        cursor.close()
        del cursor

        if session['sessionID'] == 105: # TODO: shows how we can get data specific to a session id
            load_datasets(['OPG001_2016-17_Week_v3.csv'])
            session['dataset_list'] = ['OPG001_2016-17_Week_v3.csv']
        else:
            load_datasets(config.DATA_SETS)
            session['dataset_list'] = config.DATA_SETS

        # redirect without the query params to prevent errors on refresh
        if request.args.get('reportName'):
            return redirect(request.path + '?reportName=' + request.args.get('reportName'))
        else:
            return redirect(request.path)

    # validate session
    sessionid = session["sessionID"]
    externalid = session["externalID"]

    query = """\
    declare @p_external_id int
    declare @p_session_status varchar(64)
    declare @p_result_status varchar(255)
    exec dbo.OPP_Get_Session2 {}, {}, {}, null, null, null, null, null, null, null, null, null, null, null, null, null,
    null, null, null, @p_session_status output, null, null, null, null, null, null, null, null, @p_external_id output,
    @p_result_status output
    select @p_external_id as external_id, @p_session_status as session_status, @p_result_status as result_status
    """.format(sessionid, sessionid, 1)

    # logging.debug("\n" + query)

    cursor = conn.cursor()
    cursor.execute(query)

    results = cursor.fetchone()

    if results.result_status != "OK" or results.external_id != externalid or results.session_status != 'OK':
        cursor.close()
        del cursor
        if results.result_status != "OK":
            logging.error(results.result_status)
        elif results.session_status != "OK":
            logging.error(results.session_status)
        else:
            logging.error("Invalid external_id: {}".format(externalid))
        flask.abort(404)

    cursor.close()
    del cursor


# WebModuleAfterDispatch
@server.after_request
def after_request_func(response):
    logging.debug("request=" + dict_to_string(request.values))
    logging.debug("session=" + dict_to_string(session))
    return response


# WebModuleException?
@server.teardown_request
def teardown_request_func(error=None):
    logging.debug("request=" + dict_to_string(request.values))
    logging.debug("session=" + dict_to_string(session))

    if error:
        logging.error(str(error))


# WebModuleDestroy?
@server.teardown_appcontext
def teardown_appcontext_func(error=None):
    close_conn()

    if error:
        logging.error(str(error))


@server.route('/')
def index():
    return 'Hello world!'  # 404
