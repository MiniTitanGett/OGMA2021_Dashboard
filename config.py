import os
from dotenv import load_dotenv
import json

# https://pypi.org/project/dotenv-config/
# https://hackersandslackers.com/configure-flask-applications/
# https://github.com/theskumar/python-dotenv
# https://dev.to/nicolaerario/comment/fe1e

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
BASE_PATHNAME = os.getenv("BASE_PATHNAME")

if BASE_PATHNAME is None:
    BASE_PATHNAME = "/python/"

DATA_SETS = json.loads(os.environ['DATA_SETS'])  # os.getenv("DATA_SETS")

if DATA_SETS is None:
    DATA_SETS = ["OPG001_2016-17_Week_v3.csv", "OPG010 Sankey Data.xlsx"]

LOG_FILE = os.getenv("LOG_FILE")

if LOG_FILE is None:
    LOG_FILE = os.path.dirname(os.path.realpath(__file__)) + "\\log\\python.log"

LOG_LEVEL = os.getenv("LOG_LEVEL")  # DEBUG, INFO, WARNING, ERROR, CRITICAL, or NOTSET

if LOG_LEVEL is None:
    LOG_LEVEL = "ERROR"

DEBUG = (LOG_LEVEL == "DEBUG")


