######################################################################################################################
"""
app.py

initializes the app's: server, metadata and external stylesheets
"""
######################################################################################################################

# External Packages
import app
from apps.dashboard.layouts import get_layout

# ***********************************************APP INITIATION*******************************************************

app = app.get_app('dashboard/')
app.layout = get_layout

# We import callbacks after setting the layout to avoid callback exception errors w/o suppressing
# These are used by Dash so ignore the PyCharm warnings
import apps.dashboard.user_interface_callbacks
import apps.dashboard.functionality_callbacks
import apps.dashboard.saving_loading_callbacks

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
