######################################################################################################################
"""
app.py

initializes the app's: server, metadata and external stylesheets
"""
######################################################################################################################

# External Packages
# import dash
import app
# from apps.OPG001.data import LANGUAGE
from apps.OPG001.layouts import get_layout

# from apps.OPG001.data import DATA_SETS

# ***********************************************APP INITIATION*******************************************************

# external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"]
# external_scripts = ["https://cdn.plot.ly/plotly-locale-fr-latest.js"]

# app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
#                 external_stylesheets=external_stylesheets, external_scripts=external_scripts,
#                 assets_ignore='French Details.css' if LANGUAGE == 'en' else '')
# server = app.server
app = app.get_app('OPG001/')
app.layout = get_layout()

# We import callbacks after setting the layout to avoid callback exception errors w/o suppressing
import apps.OPG001.user_interface_callbacks
import apps.OPG001.functionality_callbacks
import apps.OPG001.saving_loading_callbacks

# ****************************************************CHECKLIST*******************************************************

# TODO list
# 6) make alternative to 'graph all siblings'
# 7) save tabs/create tabs like dashboards
# 9) js for TabContentWrapperResizer does not work if the window is loaded while small
# 11) style 'Graphs' Tab to match customize menu and look good
# 10) compact triggers
# 11) only display graphed variables that have data for them
# 4) datepicker secondary up/down arrows can index years (possible?)
# 5) remove redundant/unnecessary divs, id's, etc.
# 6) table disappear/reappear
# 7) table does not appear if data not specified/not found (add placeholder table with only column names?)
# 7) create tiles with highlighted backgrounds
# 8) deleting an unlinked tile -> highlighting linked tiles only highlights the linked tile beside it at the beginning
# 11) graph menus have wrong parameter names (y and measure value)
# 15) pressing DATA update prevented if menu is already open, and similar preventable updates for modified callbacks
# 17) changing graph type resets selected graphed variables
# x) GENERAL PROOFREAD/CLEAN/DOCUMENTATION AFTER ALL ^^^^
