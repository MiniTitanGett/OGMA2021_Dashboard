######################################################################################################################
"""
app.py

initializes the app's: server, metadata and external stylesheets
"""
######################################################################################################################

# External Packages
# import dash
import app
# from apps.app0003.data import LANGUAGE
from apps.app0003.layouts import get_layout

# ***********************************************APP INITIATION*******************************************************

external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"]
external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js"]

# app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
#                 external_stylesheets=external_stylesheets, external_scripts=external_scripts,
#                 assets_ignore='French Details.css' if LANGUAGE == 'en' else '')
# server = app.server
app = app.get_app('0003/')
app.layout = get_layout()

# We import callbacks after setting the layout to avoid callback exception errors w/o suppressing
import apps.app0003.user_interface_callbacks
import apps.app0003.functionality_callbacks

# ****************************************************CHECKLIST*******************************************************

# TODO 3: implement new hierarchy
# TODO 4: implement missing functionality to new hierarchy
# TODO 5A: clean, comment, reformat and compress code
# TODO 5B: document all spotless functions/modules
# TODO 6: test UI callbacks for unhandled cases, double firing, unneeded inputs, excess outputs, improvable efficiency..
# TODO 7: begin work on data filtering functionality and additional graph types - back end development begins
# TODO ...: clean all functionality callbacks once functionality components (functions/behaviour/capabilities)
#  are developed further

# Questions for Terry:
# 1) Fiscal dates on x-axis
# 2) Datepicker behaviour changing between fiscal <--> gregorian


# Terry's Objectives:
# - saving (dashboard wide and specific graph tile)
# - updated datepicker with: last (amount) (time type)
# - bilingualism
# - tabular dashboard
# - graph titling
# - x-axis options
# - sankey diagram
# - modified box plot diagram
