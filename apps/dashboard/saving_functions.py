######################################################################################################################
"""
saving_functions.py

Stores all functions used for saving graph meta data and dashboard meta data.
"""
######################################################################################################################

# External Packages
import json
from flask import session
from dash.exceptions import PreventUpdate

# Internal Modules
from conn import exec_storedproc
from apps.dashboard.layouts import get_line_scatter_graph_menu, get_bar_graph_menu, get_table_graph_menu, \
    get_box_plot_menu, get_sankey_menu, get_bubble_graph_menu

# **********************************************SAVING FUNCTIONS********************************************************


def save_layout_state(name, attributes):
    """
    Maps the name of the graph to the attributes you want to store.
    :param attributes: meta data that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    if attributes:
        session['saved_layouts'][name] = attributes


def save_dashboard_state(name, attributes):
    """
    Maps the name of the dashboard to the dashboard attributes you want to store.
    :param attributes: list of all of the attributes that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    if attributes:
        session['saved_dashboards'][name] = attributes


def save_layout_to_db(graph_id, graph_title, is_adding):
    """Saves a specific graph layout to the database."""
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, \'{}\', \'{}\', \'{}\', 'Dash', \'{}\', 
    'application/json', 'json', @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Add' if is_adding else 'Edit', graph_id, graph_title,
               json.dumps(session['saved_layouts'][graph_id], sort_keys=True))

    exec_storedproc(query)


def save_dashboard_to_db(dashboard_id, dashboard_title, is_adding):
    """Saves a specific dashboard configuration to the database."""
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboards {}, \'{}\', \'{}\', \'{}\', 'Dash', \'{}\', 'application/json',
    'json', @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Add' if is_adding else 'Edit', dashboard_id, dashboard_title,
               json.dumps(session['saved_dashboards'][dashboard_id], sort_keys=True))

    exec_storedproc(query)


def delete_layout(graph_id):
    """Deletes a specific graph layout from the database."""
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, 'Delete', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], graph_id)

    exec_storedproc(query)

    del session['saved_layouts'][graph_id]


def delete_dashboard(dashboard_id):
    """Deletes a specific dashboard configuration from the database."""
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboards {}, \'{}\', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], 'Delete', dashboard_id)

    exec_storedproc(query)

    del session['saved_dashboards'][dashboard_id]


def load_graph_menu(graph_type, tile, df_name, args_list, graph_options, graph_variable, df_const):
    """Retuns the graph menu dependent on the graph type."""
    if graph_type == 'Line' or graph_type == 'Scatter':
        graph_menu = get_line_scatter_graph_menu(tile=tile, x=args_list[0], y=args_list[2], measure_type=args_list[1],
                                                 mode=args_list[3], data_fit=args_list[4], degree=args_list[5],
                                                 ci=args_list[6], gridline=graph_options[6], legend=graph_options[7],
                                                 xaxis=graph_options[0], yaxis=graph_options[1], data_fitting=True,
                                                 xpos=graph_options[2], ypos=graph_options[3],
                                                 xmodified=graph_options[0], ymodified=graph_options[1],
                                                 df_name=df_name, df_const=df_const,
                                                 level_value=graph_variable[0],
                                                 nid_path=graph_variable[1],
                                                 hierarchy_toggle=graph_variable[2],
                                                 graph_all_toggle=graph_variable[3])
    elif graph_type == 'Bar':
        graph_menu = get_bar_graph_menu(tile=tile, x=args_list[0], y=args_list[2], measure_type=args_list[1],
                                        orientation=args_list[3], animate=args_list[4], gridline=graph_options[6],
                                        legend=graph_options[7], xaxis=graph_options[0], yaxis=graph_options[1],
                                        df_name=df_name, xmodified=graph_options[4], ymodified=graph_options[5],
                                        xpos=graph_options[2], ypos=graph_options[3], df_const=df_const,
                                        level_value=graph_variable[0],
                                        nid_path=graph_variable[1],
                                        hierarchy_toggle=graph_variable[2],
                                        graph_all_toggle=graph_variable[3])
    elif graph_type == 'Table':
        graph_menu = get_table_graph_menu(tile=tile, number_of_columns=args_list[1], xaxis=graph_options[0],
                                          yaxis=graph_options[1], xpos=graph_options[2], ypos=graph_options[3],
                                          xmodified=graph_options[4], ymodified=graph_options[5], df_name=df_name,
                                          df_const=df_const)
    elif graph_type == 'Box_Plot':
        graph_menu = get_box_plot_menu(tile=tile, axis_measure=args_list[0], graphed_variables=args_list[1],
                                       graph_orientation=args_list[2], show_data_points=args_list[3],
                                       gridline=graph_options[6], legend=graph_options[7], xaxis=graph_options[0],
                                       yaxis=graph_options[1], df_name=df_name, df_const=df_const,
                                       xmodified=graph_options[4], ymodified=graph_options[5],
                                       xpos=graph_options[2], ypos=graph_options[3],
                                       level_value=graph_variable[0],
                                       nid_path=graph_variable[1],
                                       hierarchy_toggle=graph_variable[2],
                                       graph_all_toggle=graph_variable[3])
    elif graph_type == 'Sankey':
        graph_menu = get_sankey_menu(tile=tile, graphed_options=args_list[0], df_name=df_name, df_const=df_const,
                                     xaxis=graph_options[0], yaxis=graph_options[1], xpos=graph_options[2],
                                     ypos=graph_options[3], xmodified=graph_options[4], ymodified=graph_options[5],
                                     )
    elif graph_type == 'Bubble':
        graph_menu = get_bubble_graph_menu(tile=tile, x=args_list[0], x_measure=args_list[1], y=args_list[2],
                                           y_measure=args_list[3], size=args_list[4], size_measure=args_list[5],
                                           gridline=graph_options[6], legend=graph_options[7], xaxis=graph_options[0],
                                           yaxis=graph_options[1],  df_name=df_name, df_const=df_const,
                                           xpos=graph_options[2], ypos=graph_options[3], xmodified=graph_options[4],
                                           ymodified=graph_options[5])
    else:
        raise PreventUpdate

    return graph_menu
