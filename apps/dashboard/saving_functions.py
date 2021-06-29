######################################################################################################################
"""
saving_functions.py

stores all functions used for saving graph meta data and dashboard meta data
"""
######################################################################################################################

# External Packages
# import os
import json
# import pyodbc
# import logging
# import pymssql
from flask import session
from dash.exceptions import PreventUpdate

# Internal Packages
# import config
from conn import exec_storedproc
from apps.dashboard.layouts import get_line_scatter_graph_menu, get_bar_graph_menu, get_table_graph_menu, \
    get_box_plot_menu, get_sankey_menu, get_bubble_graph_menu


# Contents:
#   SAVING FUNCTIONS
#       - save_layout_state()
#       - save_dashboard_state()
#       - get_dashboard_attributes()
#       - load_saved_graphs()
#       - load_saved_dashboards()
#       - save_layout_to_file()
#       - save_layout_to_db
#       - save_dashboard_to_file()
#       - delete_layout()
#       - delete_dashboard()


# maps the name of the graph to the attributes you want to store
def save_layout_state(name, attributes):
    """
    :param attributes: meta data that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    if attributes:
        session['saved_layouts'][name] = attributes


# maps the name of the dashboard to the dashboard attributes you want to store
def save_dashboard_state(name, attributes):
    """
    :param attributes: list of all of the attributes that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    if attributes:
        session['saved_dashboards'][name] = attributes


def save_layout_to_db(graph_id, graph_title, is_adding):
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, \'{}\', \'{}\', \'{}\', 'Dash', \'{}\', 'application/json',
    'json', @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Add' if is_adding else 'Edit', graph_id, graph_title,
               json.dumps(session['saved_layouts'][graph_id], sort_keys=True))

    exec_storedproc(query)


def save_dashboard_to_db(dashboard_id, dashboard_title):
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboards {}, 'Add', \'{}\', \'{}\', 'Dash', \'{}\', 'application/json',
    'json', @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], dashboard_id, dashboard_title,
               json.dumps(session['saved_dashboards'][dashboard_id], sort_keys=True))

    exec_storedproc(query)


def delete_layout(graph_id):
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, 'Delete', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], graph_id)

    exec_storedproc(query)

    del session['saved_layouts'][graph_id]


def delete_dashboard(dashboard_id):
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboards {}, \'{}\', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Delete', dashboard_id)

    exec_storedproc(query)

    del session['saved_dashboards'][dashboard_id]


def load_graph_menu(graph_type, tile, df_name, args_list, df_const):
    if graph_type == 'Line' or graph_type == 'Scatter':
        graph_menu = get_line_scatter_graph_menu(tile=tile, x=args_list[0], y=args_list[1], measure_type=args_list[2],
                                                 mode=args_list[3],  df_name=df_name, df_const=df_const)
    elif graph_type == 'Bar':
        graph_menu = get_bar_graph_menu(tile=tile, x=args_list[0], y=args_list[1], measure_type=args_list[2],
                                        orientation=args_list[3], animate=args_list[4], df_name=df_name,
                                        df_const=df_const)
    elif graph_type == 'Table':
        graph_menu = get_table_graph_menu(tile=tile, number_of_columns=args_list[1])
    elif graph_type == 'Box_Plot':
        graph_menu = get_box_plot_menu(tile=tile, axis_measure=args_list[0], graphed_variables=args_list[1],
                                       graph_orientation=args_list[2], show_data_points=args_list[3], df_name=df_name,
                                       df_const=df_const)
    elif graph_type == 'Sankey':
        graph_menu = get_sankey_menu(tile=tile, graphed_options=args_list[0], df_name=df_name, df_const=df_const)
    elif graph_type == 'Bubble':
        graph_menu = get_bubble_graph_menu(tile=tile, x=args_list[0], x_measure=args_list[1], y=args_list[2],
                                           y_measure=args_list[3], size=args_list[4], size_measure=args_list[5],
                                           df_name=df_name, df_const=df_const)
    else:
        raise PreventUpdate

    return graph_menu
