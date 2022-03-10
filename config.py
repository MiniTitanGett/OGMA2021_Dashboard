import os
from dotenv import load_dotenv
# import json
import regex
import sys
import logging
from logging.config import dictConfig
from logging import FileHandler

# https://pypi.org/project/dotenv-config/
# https://hackersandslackers.com/configure-flask-applications/
# https://github.com/theskumar/python-dotenv
# https://dev.to/nicolaerario/comment/fe1e

load_dotenv()

# required env setting #################################################################################################

SECRET_KEY = os.getenv("SECRET_KEY")
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

# optional (defaulted) env settings ####################################################################################
css_directory = os.getcwd()

client_css = os.getenv("CLIENT")

BASE_PATHNAME = os.getenv("BASE_PATHNAME")

if BASE_PATHNAME is None:
    BASE_PATHNAME = "/python/"

LOG_FILE = os.getenv("LOG_FILE")

if LOG_FILE is None:
    LOG_FILE = os.path.dirname(os.path.realpath(__file__)) + "\\log\\python.log"

if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.mkdir(os.path.dirname(LOG_FILE))  # let the error propagate since we can't log anyway

LOG_LEVEL = os.getenv("LOG_LEVEL")  # DEBUG, INFO, WARNING, ERROR, CRITICAL, or NOTSET

if LOG_LEVEL is None:
    LOG_LEVEL = "ERROR"

DEBUG = (LOG_LEVEL.upper() == "DEBUG")

LOG_REQUEST = os.getenv("LOG_REQUEST")

if LOG_REQUEST is None:
    LOG_REQUEST = False
else:
    LOG_REQUEST = (LOG_REQUEST.lower() == 'true')

UPDATING_MSG = os.getenv("UPDATING_MSG")

if UPDATING_MSG is None:
    UPDATING_MSG = "Updating..."

# logging setup ########################################################################################################

LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(filename)s (fn:%(funcName)s ln:%(lineno)d): %(message)s"


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    https://stackoverflow.com/a/39215961
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class CustomFileHandler(FileHandler):

    def __init__(self, filename):
        FileHandler.__init__(self, filename)

    def emit(self, record):
        # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
        record.msg = regex.sub(r'\p{C}\[[0-9;]*m', '', record.msg)  # ex. [37m
        FileHandler.emit(self, record)


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': LOG_FORMAT
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': LOG_LEVEL
        }
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['wsgi']
    }
})

cfh = CustomFileHandler(r'{}'.format(LOG_FILE))
cfh.setFormatter(logging.Formatter(LOG_FORMAT))
cfh.setLevel(LOG_LEVEL)
log = logging.getLogger("root")
log.addHandler(cfh)

sys.stdout = StreamToLogger(log, logging.INFO)
sys.stderr = StreamToLogger(log, logging.ERROR)

logging.debug("Configuration complete.")
