import config  # MUST BE THE FIRST IMPORT!!!
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from server import server
from apps.OPG001.local_app import app as opg001
# from apps.app0001 import app as app0001
# from apps.app0002 import app as app0002
# from apps.app0004 import app as app0004
# from apps.app0005 import app as app0005


# https://dash.plotly.com/integrating-dash
# https://stackoverflow.com/questions/59627976/integrating-dash-apps-into-flask-minimal-example
# https://medium.com/@rajesh.r6r/deploying-a-python-flask-rest-api-on-iis-d8d9ebf886e9
# https://pypi.org/project/wfastcgi/
# https://stackoverflow.com/questions/30906489/how-to-implement-flask-application-dispatching-by-path-with-wsgi

server.wsgi_app = DispatcherMiddleware(server.wsgi_app, {
    '/OPG001': opg001.server,
    # '/0001': app0001.server,
    # '/0002': app0002.server
    # '/0004': app0004.server,
    # '/0005': app0005.server
})

if __name__ == '__main__':
    # server.run(debug=config.DEBUG)
    run_simple('127.0.0.1',  # 'pacman.ogma.local',  # '192.168.16.62',  # '127.0.0.1',
               8080,
               server.wsgi_app,
               use_debugger=config.DEBUG,
               use_reloader=config.DEBUG)
