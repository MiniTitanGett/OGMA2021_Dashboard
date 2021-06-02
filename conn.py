from flask import g
import pyodbc
import config


def get_conn():

    if 'conn' not in g:
        g.conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)

    return g.conn


def close_conn():
    conn = g.pop('conn', None)

    if conn is not None:
        conn.close()
