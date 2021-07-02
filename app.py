from server import server
import config
import dash
import dash_bootstrap_components as dbc

external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"]
external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js",
                    "https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"]


def get_app(prefix=''):
    return dash.Dash(
        __name__,
        # meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
        external_stylesheets=external_stylesheets,
        external_scripts=external_scripts,
        # assets_ignore='BBB - french stylesheet1.css' if LANGUAGE == 'En' else '',
        server=server,
        url_base_pathname=config.BASE_PATHNAME + prefix,
        suppress_callback_exceptions=True,  # Used to avoid init errors
        update_title=config.UPDATING_MSG
    )
