import os
from dotenv import load_dotenv

# https://pypi.org/project/dotenv-config/
# https://hackersandslackers.com/configure-flask-applications/
# https://github.com/theskumar/python-dotenv
# https://dev.to/nicolaerario/comment/fe1e

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
BASE_PATHNAME = os.getenv("BASE_PATHNAME")
DEBUG = (os.getenv("DEBUG") == 'true')

if BASE_PATHNAME is None:
    BASE_PATHNAME = '/python/'


