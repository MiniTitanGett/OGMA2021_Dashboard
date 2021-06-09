from flask import g, session
import flask
import logging
import pyodbc
import pandas
import config


# https://kadler.io/2018/01/08/fetching-python-database-cursors-by-column-name.html
class CursorByName:
    def __init__(self, cursor):
        self._cursor = cursor

    def __iter__(self):
        return self

    def __next__(self):
        row = self._cursor.__next__()

        return {description[0]: row[col] for col, description in enumerate(self._cursor.description)}


def get_conn():

    if 'conn' not in g:
        g.conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)

    return g.conn


def close_conn():
    conn = g.pop('conn', None)

    if conn is not None:
        conn.close()


def exec_storedproc(query):
    """
    This will execute the query, check the result_status, and return the output parameters if result_status is 'OK'
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(query)

    # there should only be the output params as a result set
    results = cursor.fetchone()

    cursor.close()
    del cursor

    if results.result_status != "OK":
        logging.error(results.result_status)
        raise Exception(results.result_status)

    return results


def exec_storedproc_results(query):
    """
    This will execute the query, check the result_status, and return the result set if result_status is 'OK'
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(query)

    # this is expecting only 1 or 2 result sets
    results = pandas.DataFrame(CursorByName(cursor))

    if cursor.nextset():
        output = pandas.DataFrame(CursorByName(cursor))
    else:
        output = results
        results = None

    cursor.close()
    del cursor

    result_status = output["result_status"].iloc[0]

    if result_status != "OK":
        logging.error(result_status)
        raise Exception(result_status)

    # this will return None for a stored proc that only returns output params
    return results


def get_ref(ref_table, language):
    """
    gets a table from OP_Ref
    """
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_get_ref_values {}, \'{}\', \'{}\', null, 'Desc', @p_result_status output
    select @p_result_status as result_status 
    """.format(session["sessionID"], ref_table, language)

    return exec_storedproc_results(query)
