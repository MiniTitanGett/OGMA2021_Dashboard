######################################################################################################################
"""
saving_functions.py

stores all functions used for saving graph meta data and dashboard meta data
"""
######################################################################################################################

# External Packages
import os
import json
import pyodbc
from flask import session
from dash.exceptions import PreventUpdate

# Internal Packages
import config
from server import get_conn
from apps.OPG001.layouts import get_line_graph_menu, get_bar_graph_menu, get_scatter_graph_menu, get_table_graph_menu,\
    get_box_plot_menu, get_sankey_menu
from apps.OPG001.data import saved_layouts, saved_dashboards

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
        saved_layouts[name] = attributes


# maps the name of the dashboard to the dashboard attributes you want to store
def save_dashboard_state(name, attributes):
    """
    :param attributes: list of all of the attributes that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    if attributes:
        saved_dashboards[name] = attributes


# loads the saved graphs into a dictionary
def load_saved_graphs():
    """
    loads the saved layouts into the saved_layouts dictionary upon dashboard startup
    """
    if os.stat('apps/OPG001/saved_layouts.json').st_size != 0:
        with open('apps/OPG001/saved_layouts.json') as json_file:
            saved_graphs_temp = json.load(json_file)
            for key in saved_graphs_temp:
                save_layout_state(key, saved_graphs_temp[key])
        json_file.close()


load_saved_graphs()


# loads the saved graphs into a dictionary
def load_saved_dashboards():
    """
    loads the saved dashboards into the saved_dashboards dictionary upon dashboard startup
    """
    if os.stat('apps/OPG001/saved_dashboards.json').st_size != 0:
        with open('apps/OPG001/saved_dashboards.json') as json_file:
            saved_dashboards_temp = json.load(json_file)
            for key in saved_dashboards_temp:
                save_dashboard_state(key, saved_dashboards_temp[key])
        json_file.close()


load_saved_dashboards()


# saves the tiles meta data to the saved layouts file
def save_layout_to_file(layouts):
    """
    saves the layouts to the json file
    :param layouts: the dictionary containing all of the saved layouts
    """
    j = json.dumps(layouts, sort_keys=True)
    if j:
        with open('apps/OPG001/saved_layouts.json', 'w') as file:
            file.write(j)
            file.close()


def save_layout_to_db(graph_title):

    if config.SESSIONLESS:
        return

    conn = get_conn()
    j = json.dumps(saved_layouts[graph_title], sort_keys=True)

    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Add', graph_title, 'Dash', j, 'application/json', 'json')

    cursor = conn.cursor()
    cursor.execute(query)

    # results = cursor.fetchone()

    # ignore result status for now

    cursor.close()
    del cursor


# saves the dashboards meta data to the saved layouts file
def save_dashboard_to_file(dashboard):
    """
    saves the dashboards to the json file
    :param dashboard: the dictionary containing all of the saved dashboards
    """
    j = json.dumps(dashboard, sort_keys=True)
    with open('apps/OPG001/saved_dashboards.json', 'w') as file:
        file.write(j)
        file.close()


#  function for deleting line from text file
def delete_layout(key, layouts):
    """
    removes selected layouts from the json file
    :param key: the title of the graph, this is the key in the dictionary of saved layouts
    :param layouts: the dictionary containing all of the saved layouts
    """
    if os.stat('apps/OPG001/saved_layouts.json').st_size != 0:
        with open('apps/OPG001/saved_layouts.json', 'r') as file:
            saved_graphs_temp = json.load(file)
            del saved_graphs_temp[key]
            del layouts[key]
            file.close()
        with open('apps/OPG001/saved_layouts.json', 'w') as file:
            j = json.dumps(saved_graphs_temp, sort_keys=True)
            file.write(j)
            file.close()


#  function for deleting line from text file
def delete_dashboard(key, dashboards):
    """
    removes selected dashboard from the json file
    :param key: the title of the dashboard, this is the key in the dictionary of saved dashboards
    :param dashboards: the dictionary containing all of the saved dashboards
    """
    if os.stat('apps/OPG001/saved_dashboards.json').st_size != 0:
        with open('apps/OPG001/saved_dashboards.json', 'r') as file:
            saved_dashboards_temp = json.load(file)
            del saved_dashboards_temp[key]
            del dashboards[key]
            file.close()
        with open('apps/OPG001/saved_dashboards.json', 'w') as file:
            j = json.dumps(saved_dashboards_temp, sort_keys=True)
            file.write(j)
            file.close()


def load_graph_menu(graph_type, tile, df_name, args_list):
    if graph_type == 'Line' or graph_type == 'Scatter' or graph_type == 'Bar':
        x = args_list[0]
        measure_type = args_list[1]
        y = args_list[2]
        if graph_type == 'Line':
            graph_menu = get_line_graph_menu(tile=tile, x=x, y=y, measure_type=measure_type, df_name=df_name)
        elif graph_type == 'Scatter':
            graph_menu = get_scatter_graph_menu(tile=tile, x=x, y=y, measure_type=measure_type, df_name=df_name)
        else:
            graph_menu = get_bar_graph_menu(tile=tile, x=x, y=y, measure_type=measure_type, df_name=df_name)
    elif graph_type == 'Table':
        number_of_columns = args_list[1]
        graph_menu = get_table_graph_menu(tile=tile, number_of_columns=number_of_columns)
    elif graph_type == 'Box_Plot':
        axis_measure = args_list[0]
        graphed_variables = args_list[1]
        graph_orientation = args_list[2]
        show_data_points = args_list[3]
        graph_menu = get_box_plot_menu(tile=tile, axis_measure=axis_measure,
                                       graphed_variables=graphed_variables, graph_orientation=graph_orientation,
                                       df_name=df_name, show_data_points=show_data_points)
    elif graph_type == 'Sankey':
        graph_menu = get_sankey_menu(tile=tile, graphed_options=args_list[0], df_name=df_name)
    else:
        raise PreventUpdate

    return graph_menu
