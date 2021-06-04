from datetime import timedelta
import flask
from flask import Flask, request, session, g
import pyodbc
# import pymssql
from werkzeug.utils import redirect
import config
import logging
# from pandas import DataFrame
import pandas
import json

from conn import get_conn, close_conn
from apps.OPG001.data import saved_layouts, saved_dashboards
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


# https://kadler.io/2018/01/08/fetching-python-database-cursors-by-column-name.html
class CursorByName:
    def __init__(self, cursor):
        self._cursor = cursor

    def __iter__(self):
        return self

    def __next__(self):
        row = self._cursor.__next__()

        return {description[0]: row[col] for col, description in enumerate(self._cursor.description)}


# https://pythonise.com/series/learning-flask/python-before-after-request

server = Flask(__name__)

server.debug = config.DEBUG
server.wsgi_app = PrefixMiddleware(server.wsgi_app)  # , prefix=config.APPLICATION_ROOT)
server.config['SECRET_KEY'] = config.SECRET_KEY
server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_PERMANENT'] = False  # delete the session when the user closes the browser; use to be set to True
server.config['SESSION_USE_SIGNER'] = True
# server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
server.config['SESSION_FILE_THRESHOLD'] = 100
# ==================
# server.config['SERVER_NAME'] = 'pacman.ogma.local:8080'
# server.config['SESSION_COOKIE_DOMAIN'] = 'pacman.ogma.local:8080'
# ==================

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


def get_ref(ref_table, language):
    """
    gets a table from OP_Ref
    """
    conn = get_conn()
    # cursor = conn.cursor()
    # query = "exec dbo.spopref_getoprefdata \'{}\', \'{}\'".format(ref_table, language)

    # cursor.execute(query)

    # results = DataFrame(cursor.fetchall())

    # cursor.close()
    # del cursor

    query = pandas.read_sql("exec dbo.spopref_getoprefdata \'{}\', \'{}\'".format(ref_table, language), conn)
    results = pandas.DataFrame(query, columns=["ref_value", "ref_desc"])

    return results


def load_labels(language="En"):
    session["labels"] = get_ref("Labels", language)


def load_saved_graphs_from_db():
    """
    loads the saved layouts into the saved_layouts dictionary from the database
    """
    conn = get_conn()
    cursor = conn.cursor()
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, 'Find', null, null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session["sessionID"])

    cursor.execute(query)

    results = CursorByName(cursor)  # cursor.fetchall()

    # for now, don't worry about @p_result_status

    for row in results:
        saved_layouts[row["ref_value"]] = json.loads(row["clob_text"])

    cursor.close()
    del cursor


def load_saved_dashboards_from_db():
    """
    loads the saved dashboards into the saved_dashboards dictionary from the database
    """
    conn = get_conn()
    cursor = conn.cursor()
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboards {}, 'Find', null, null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session["sessionID"])

    cursor.execute(query)

    results = CursorByName(cursor)  # cursor.fetchall()

    # for now, don't worry about @p_result_status

    for row in results:
        saved_dashboards[row["ref_value"]] = json.loads(row["clob_text"])

    cursor.close()
    del cursor


def validate_session(sessionid, externalid):
    conn = get_conn()
    cursor = conn.cursor()
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


def load_dataset_list():
    df = get_ref("Data_set", session["language"])
    return df["ref_value"].tolist()


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

    if config.LOG_REQUEST:
        logging.debug(request.method + " " + request.url)
        logging.debug("request=" + dict_to_string(request.values))
        logging.debug("cookies=" + dict_to_string(request.cookies))
        # logging.debug("session=" + dict_to_string(session))

    return


# WebModuleBeforeDispatch
@server.before_request
def before_request_func():

    if config.LOG_REQUEST:
        logging.debug(request.method + " " + request.url)
        logging.debug("request=" + dict_to_string(request.values))
        logging.debug("cookies=" + dict_to_string(request.cookies))
        # logging.debug("session=" + dict_to_string(session))

    conn = get_conn()

    # if the sessionid exists in the request, validate the nonce
    # otherwise validate the sessionid/tokenid out of the cookie

    sessionid = request.args.get("sessionID", type=int)

    if sessionid:  # and (sessionid != session.get("sessionID")):
        session["sessionID"] = 0
        session["externalID"] = 0
        session["language"] = "En"

        nonce_key = request.args.get("a")
        nonce_value = request.args.get("b")

        query = """\
        declare @p_external_id int
        declare @p_result_status varchar(255)
        exec dbo.OPP_Validate_Nonce {}, \'{}\', \'{}\', @p_external_id output, @p_result_status output
        select @p_external_id as external_id, @p_result_status as result_status
        """.format(sessionid, nonce_key, nonce_value)

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

        # validate the session on the first request
        validate_session(sessionid, results.external_id)

        # set the user's language
        language = request.args.get("language")

        if language:
            session["language"] = language

        # load the labels
        load_labels(session["language"])

        # load the available datasets
        session["dataset_list"] = load_dataset_list()  # get_ref("Data_set", session["language"])

        # load the available graphs/layouts
        load_saved_graphs_from_db()

        # load the available dashboards
        load_saved_dashboards_from_db()

        # redirect without the query params to prevent errors on refresh
        if request.args.get('reportName'):
            return redirect(request.path + '?reportName=' + request.args.get('reportName'))
        else:
            return redirect(request.path)

    # validate session from the cookie
    validate_session(int(request.cookies.get("sessionID")), int(request.cookies.get("externalID")))


# WebModuleAfterDispatch
@server.after_request
def after_request_func(response):

    if config.LOG_REQUEST:
        logging.debug("request=" + dict_to_string(request.values))
        logging.debug("cookies=" + dict_to_string(request.cookies))
        # logging.debug("session=" + dict_to_string(session))

    # store sessionID and externalID in the cookie instead of the session
    if not request.cookies.get("sessionID") or request.cookies.get("sessionID") != str(session["sessionID"]):
        logging.debug("setting cookies.")
        response.set_cookie(key="sessionID", value=str(session["sessionID"]))
        response.set_cookie(key="externalID", value=str(session["externalID"]))

    return response


# WebModuleException?
@server.teardown_request
def teardown_request_func(error=None):

    if config.LOG_REQUEST:
        logging.debug("request=" + dict_to_string(request.values))
        logging.debug("cookies=" + dict_to_string(request.cookies))
        # logging.debug("session=" + dict_to_string(session))

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
