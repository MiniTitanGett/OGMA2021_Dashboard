######################################################################################################################
"""
graphs.py

contains functions to generate graphs
"""
######################################################################################################################

# External Packages
from _datetime import datetime

import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_table
import dash_html_components as html
import dash
import pandas as pd
from re import search

import os
import plotly.graph_objects as go

# Internal Modules
from apps.OPG001.data import get_label, data_filter, LANGUAGE, customize_menu_filter, session


# Contents:
#   HELPER FUNCTIONS
#       - set_partial_periods()
#       - get_empty_graph_subtitle()
#   GRAPH FUNCTIONS
#       - get_blank_figure()
#       - get_line_figure()
#       - get_scatter_figure()
#       - get_bar_figure()
#       - get_box_figure()
#       - get_table_figure()
#       - __update_graph()


# ***********************************************HELPER FUNCTIONS****************************************************

# mark partial periods on graph
def set_partial_periods(fig, dataframe, graph_type):
    # Annotate partial data points
    partial_data_points = dataframe[dataframe[get_label('Partial Period')] == get_label('TRUE')]
    index_vals = list(partial_data_points.index.values)
    partial_pos = {}  # Key: x_val, Value: list of y_vals
    for i in range(len(partial_data_points)):
        # Co-ordinates of marker to be labeled
        x_val = partial_data_points.loc[index_vals[i], get_label('Date of Event')]
        y_val = partial_data_points.loc[index_vals[i], get_label('Measure Value')]
        if x_val in partial_pos:
            # Add y_val to list associated with x_val
            current_y_list = partial_pos[x_val]
            current_y_list.append(y_val)
            partial_pos[x_val] = current_y_list
        else:
            # Create new list of y_vals
            partial_pos[x_val] = [y_val]
        partial_pos[x_val].sort(reverse=True)
    # None on bar graph due to formatting
    if graph_type != 'Bar':
        for i in partial_pos:
            for j in range(len(partial_pos[i])):
                if j == 0:
                    # Data point with highest y val (for each x) is labeled
                    fig.add_annotation(
                        x=i,
                        y=partial_pos[i][j],
                        text=get_label("Partial Period"),
                        showarrow=True,
                        arrowhead=7,
                        ax=0,
                        ay=-40,
                        bgcolor='#ffffff')
                else:
                    # Unlabeled black dots on lower data points
                    fig.add_annotation(
                        x=i,
                        y=partial_pos[i][j],
                        text="",
                        arrowhead=7,
                        ax=0,
                        ay=0)
    return fig


# get subtitle for empty graph
def get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path,
                             hierarchy_graph_children, variable_names):
    # if hierarchy toggle set to "Level Filter"
    if hierarchy_type == 'Level Filter':
        # if df empty because no hierarchy level selected, leave titles blank unless a title is manually set
        if not hierarchy_level_dropdown or len(variable_names) == 0:
            sub_title = "No Data Specified"
        # else, hierarchy level selected but df empty because no data was found
        else:
            sub_title = "No Data Found"
    # else, hierarchy toggle set to "Specific Item"
    else:
        # if a specific selection has been made while "All in Dropdown" is unselected
        if hierarchy_graph_children != ['graph_children']:
            # if a specific selection has been made and variable names are selected then no data was found
            if len(hierarchy_path) != 0 and len(variable_names) > 0:
                sub_title = "No Data Found"
            # else, no specific or variable name selection was made, leave blank unless title is specified
            else:
                sub_title = "No Data Specified"
        # a specific selection has been made while "All in Dropdown" is selected, data was not found
        else:
            sub_title = "No Data Found"
    return sub_title


# ************************************************GRAPH FUNCTIONS**************************************************


# create a blank graph with an appropriate sub-title
def get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                     hierarchy_path, hierarchy_graph_children, variable_names):
    sub_title = get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown,
                                         hierarchy_path, hierarchy_graph_children, variable_names)
    if sub_title == 'No Data Specified' and not tile_title:
        title = '<br><sub>{} </sub>'.format(get_label(sub_title))
    else:
        title += '<br><sub>{} </sub>'.format(get_label(sub_title))
    fig = px.line(
        title=title)
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')
    return fig


# line graph layout
def get_line_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                    hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)

    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Create title
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if hierarchy_type == 'Level Filter':
                # Whole level graph title
                title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1], get_label('Time'))
            elif len(hierarchy_path) != 0:
                # Item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[1], get_label('Time'))
            else:
                # Root's children graph title
                title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Time'))

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Create title
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if hierarchy_specific_dropdown:
                title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1], get_label('Time'))
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1], get_label('Time'))

    # if df is not empty, create graph
    if not filtered_df.empty:

        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            color = hierarchy_level_dropdown if hierarchy_type == 'Level Filter' else \
                df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
            line_group = get_label('Variable Name')
            legend_title_text = get_label(hierarchy_level_dropdown) if hierarchy_type == 'Level Filter' else \
                get_label(df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)])
            filtered_df.rename(columns={color: get_label(color)}, inplace=True)
        else:
            color = 'Variable Name'
            line_group = None
            legend_title_text = get_label('Variable Names')

        hover_data = [get_label('Variable Name'), get_label('Partial Period')]

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Measure Value', 'Variable Name', 'Partial Period']},
                           inplace=True)

        # generate graph
        fig = px.line(
            title=title,
            data_frame=filtered_df,
            x=get_label('Date of Event'),
            y=get_label('Measure Value'),
            color=get_label(color),
            line_group=line_group,
            hover_data=hover_data)
        fig.update_layout(
            yaxis={'title': arg_value[1]},
            legend_title_text=legend_title_text,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Line')
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[2])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


# scatter graph layout
def get_scatter_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                       hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)

    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if hierarchy_type == 'Level Filter':
                # Whole level graph title
                title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1], get_label('Time'))
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[1], get_label('Time'))
            else:
                # Root's children graph title
                title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Time'))

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_specific_dropdown:
                title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1], get_label('Time'))
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1], get_label('Time'))

    # if df is not empty, create graph
    if not filtered_df.empty:

        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            color = hierarchy_level_dropdown if hierarchy_type == 'Level Filter' else \
                df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
            legend_title_text = get_label(hierarchy_level_dropdown) if hierarchy_type == 'Level Filter' else \
                get_label(df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)])
            filtered_df.rename(columns={color: get_label(color)}, inplace=True)
        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            color = 'Variable Name'
            legend_title_text = get_label('Variable Names')

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Measure Value', 'Variable Name', 'Partial Period']},
                           inplace=True)
        hover_data = [get_label('Variable Name'), get_label('Partial Period')]

        # generate graph
        fig = px.scatter(
            title=title,
            data_frame=filtered_df,
            x=get_label('Date of Event'),
            y=get_label('Measure Value'),
            color=get_label(color),
            hover_data=hover_data)
        fig.update_layout(
            yaxis={'title': arg_value[1]},
            legend_title_text=legend_title_text,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Scatter')
    # else, filtered is empty, create default empty graph
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[2])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


# animated bubble layout
def get_bubble_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                      hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = x-axis measure
    # (args-value: {})[2] = y-axis
    # (args-value: {})[3] = y-axis measure
    # (args-value: {})[4] = size
    # (args-value: {})[5] = size measure

    # Specialty filtering
    filtered_df = dff.copy().query(
        "(`Variable Name` == @arg_value[0] and `Measure Type` == @arg_value[1]) or (`Variable Name` == @arg_value[2] "
        "and `Measure Type` == @arg_value[3]) or (`Variable Name` == @arg_value[4] and `Measure Type` == @arg_value["
        "5])")

    if hierarchy_type == 'Level Filter':
        color = hierarchy_level_dropdown
    elif hierarchy_type == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        color = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
    else:
        color = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path) - 1]
    filtered_df[['Date of Event', 'Measure Type', 'Variable Name',
                 'Partial Period', color]] = filtered_df[
        ['Date of Event', 'Measure Type', 'Variable Name',
         'Partial Period', color]].astype(str)
    filtered_df = filtered_df.pivot_table(index=['Date of Event', 'Partial Period', color],
                                          columns=['Variable Name', 'Measure Type'],
                                          values='Measure Value').reset_index()
    filtered_df = filtered_df.dropna()

    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if hierarchy_type == 'Level Filter':
                # Whole level graph title
                title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[2], arg_value[4])
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[2], arg_value[4])
            else:
                # Root's children graph title
                title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[2], arg_value[4])

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_specific_dropdown:
                title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[2], arg_value[4])
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[2], arg_value[4])

    # if df is not empty, create graph
    if not filtered_df.empty:

        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        legend_title_text = get_label(hierarchy_level_dropdown) if hierarchy_type == 'Level Filter' else 'Traces'

        filtered_df.rename(columns={color: get_label(color)}, inplace=True)

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Variable Name', 'Partial Period']},
                           inplace=True)

        # generate graph
        fig = px.scatter(
            title=title,
            x=filtered_df[arg_value[0], arg_value[1]],
            y=filtered_df[arg_value[2], arg_value[3]],
            size=filtered_df[arg_value[4], arg_value[5]],
            animation_frame=filtered_df['Date of Event'],
            color=filtered_df[get_label(color)],
            range_x=[0, filtered_df[arg_value[0], arg_value[1]].max()],
            range_y=[0, filtered_df[arg_value[2], arg_value[3]].max()],
            labels={'animation_frame': 'Date of Event'}
        )
        fig.update_layout(
            xaxis_title='{} ({})'.format(arg_value[0], arg_value[1]),
            yaxis_title='{} ({})'.format(arg_value[2], arg_value[3]),
            legend_title_text='Size: <br> &#9; {} ({})<br> <br>{}'.format(arg_value[4], arg_value[5],
                                                                          legend_title_text),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    # else, filtered is empty, create default empty graph
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[2])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


# bar graph layout
def get_bar_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    # arg_value[3] = orientation
    # arg_value[4] = animation bool

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)

    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_type == 'Level Filter':
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1],
                                                  get_label('Variable Names'))
                else:
                    # Whole level graph title
                    title = '{0}: {1} vs {0}'.format(get_label(hierarchy_level_dropdown), arg_value[1])
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                if arg_value[0] == 'Variable Names':
                    title = title + ': {} vs {}'.format(arg_value[1], get_label('Variable Names'))
                else:
                    title = title + ': {} vs {}'.format(arg_value[1], hierarchy_path[-1])
            else:
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1],
                                                  get_label('Variable Names'))
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Root'))

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if arg_value[0] == 'Variable Names':
                title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                              get_label('Variable Names'))
            else:
                if hierarchy_specific_dropdown:
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1], get_label('Time'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1], get_label('Time'))

    # if df is not empty, create graph
    if not filtered_df.empty:

        group_by_item = arg_value[0] != 'Variable Names'
        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Axis and color logic
            if not group_by_item:
                x_axis = 'Variable Name'
                if hierarchy_type == 'Level Filter':
                    color = hierarchy_level_dropdown
                else:
                    color = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                hover_data = [get_label('Date of Event'), get_label('Partial Period')]
                filtered_df.rename(columns={color: get_label(color)}, inplace=True)
            elif hierarchy_type == 'Level Filter':
                x_axis = hierarchy_level_dropdown
                color = 'Variable Name'
                hover_data = [get_label('Date of Event'), get_label('Variable Name'), get_label('Partial Period')]
                filtered_df.rename(columns={x_axis: get_label(x_axis)}, inplace=True)
            else:
                x_axis = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                color = 'Variable Name'
                hover_data = [get_label('Date of Event'), get_label('Variable Name'), get_label('Partial Period')]
                filtered_df.rename(columns={x_axis: get_label(x_axis)}, inplace=True)

            x = x_axis
            legend_title_text = get_label(color)

            filtered_df['Date of Event'] = \
                filtered_df['Date of Event'].transform(lambda i: i.strftime(format='%Y-%m-%d'))

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            color = 'Variable Name' if group_by_item else 'Partial Period'
            x = 'Date of Event' if group_by_item else 'Variable Name'
            legend_title_text = get_label('Variable Name') if group_by_item else get_label('Partial Period')
            if not group_by_item:
                filtered_df['Date of Event'] = \
                    filtered_df['Date of Event'].transform(lambda i: i.strftime(format='%Y-%m-%d'))
            hover_data = [get_label('Partial Period')] if group_by_item else [get_label('Date of Event')]

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Measure Value', 'Variable Name', 'Partial Period']},
                           inplace=True)

        # generate graph
        fig = px.bar(
            title=title,
            data_frame=filtered_df,
            x=get_label(x) if arg_value[3] == 'Vertical' else get_label('Measure Value'),
            y=get_label('Measure Value') if arg_value[3] == 'Vertical' else get_label(x),
            color=get_label(color),
            barmode='group',
            hover_data=hover_data)
        fig.update_layout(
            yaxis={'title': arg_value[1]} if arg_value[3] == 'Vertical' else {},
            xaxis={} if arg_value[3] == 'Vertical' else {'title': arg_value[1]},
            legend_title_text=legend_title_text,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Bar')
    # else, filtered is empty, create default empty graph
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[2])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


# bar graph layout TODO: VERTICAL TICKS OVERLAPPING WITH THE ANIMATION SLIDER
def get_animated_bar_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                            hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    # arg_value[3] = orientation
    # arg_value[4] = animate bool

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)
    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_type == 'Level Filter':
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1],
                                                  get_label('Variable Names'))
                else:
                    # Whole level graph title
                    title = '{0}: {1} vs {0}'.format(get_label(hierarchy_level_dropdown), arg_value[1])
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                if arg_value[0] == 'Variable Names':
                    title = title + ': {} vs {}'.format(arg_value[1], get_label('Variable Names'))
                else:
                    title = title + ': {} vs {}'.format(arg_value[1], hierarchy_path[-1])
            else:
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1],
                                                  get_label('Variable Names'))
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Root'))

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if arg_value[0] == 'Variable Names':
                title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                              get_label('Variable Names'))
            else:
                if hierarchy_specific_dropdown:
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1], get_label('Time'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1], get_label('Time'))

    # if df is not empty, create graph
    if not filtered_df.empty:

        group_by_item = arg_value[0] != 'Variable Names'
        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Axis and color logic
            if not group_by_item:
                x_axis = 'Variable Name'
                if hierarchy_type == 'Level Filter':
                    color = hierarchy_level_dropdown
                else:
                    color = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                hover_data = [get_label('Date of Event'), get_label('Partial Period')]
                filtered_df.rename(columns={color: get_label(color)}, inplace=True)
            elif hierarchy_type == 'Level Filter':
                x_axis = hierarchy_level_dropdown
                color = 'Variable Name'
                hover_data = [get_label('Date of Event'), get_label('Variable Name'), get_label('Partial Period')]
                filtered_df.rename(columns={x_axis: get_label(x_axis)}, inplace=True)
            else:
                x_axis = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                color = 'Variable Name'
                hover_data = [get_label('Date of Event'), get_label('Variable Name'), get_label('Partial Period')]
                filtered_df.rename(columns={x_axis: get_label(x_axis)}, inplace=True)

            x = x_axis
            legend_title_text = get_label(color)

            filtered_df['Date of Event'] = \
                filtered_df['Date of Event'].transform(lambda i: i.strftime(format='%Y-%m-%d'))

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            color = 'Variable Name' if group_by_item else 'Partial Period'
            x = 'Variable Name'
            legend_title_text = get_label('Variable Name') if group_by_item else get_label('Partial Period')
            if not group_by_item:
                filtered_df['Date of Event'] = \
                    filtered_df['Date of Event'].transform(lambda i: i.strftime(format='%Y-%m-%d'))
            hover_data = [get_label('Partial Period')] if group_by_item else [get_label('Date of Event')]

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Measure Value', 'Variable Name', 'Partial Period']},
                           inplace=True)

        filtered_df['Date of Event'] = filtered_df['Date of Event'].astype(str)

        # TODO: Remove in production when there is a full dataset
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            for i in filtered_df['Date of Event'].unique():
                for j in filtered_df[get_label(x)].unique():
                    for k in filtered_df[get_label(color)].unique():
                        if filtered_df.query("`Date of Event` == @i and `{}` == @j and `{}` == @k".format(get_label(x),
                                                                                                          get_label(
                                                                                                              color))).empty:
                            filtered_df = filtered_df.append(
                                {'Date of Event': i, get_label(x): j, get_label(color): k, 'Measure Value': 0},
                                ignore_index=True)
        # fixes shifting indices
        filtered_df = filtered_df.sort_values(by=[get_label(x)])
        # generate graph
        fig = px.bar(
            title=title,
            data_frame=filtered_df,
            x=get_label(x) if arg_value[3] == 'Vertical' else get_label('Measure Value'),
            y=get_label('Measure Value') if arg_value[3] == 'Vertical' else get_label(x),
            color=get_label(color) if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                                           hierarchy_graph_children == [
                                                                               'graph_children']) else None,
            barmode='group',
            hover_data=hover_data,
            animation_frame=get_label('Date of Event'))
        fig.update_layout(
            yaxis={'title': arg_value[1], 'range': [0, filtered_df['Measure Value'].max()]} if arg_value[
                                                                                                   3] == 'Vertical' else {
                'type': 'category'},
            xaxis={'visible': False, 'type': 'category'} if arg_value[3] == 'Vertical' else {'title': arg_value[1],
                                                                                             'range': [0, filtered_df[
                                                                                                 'Measure Value'].max()]},
            legend_title_text=legend_title_text,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Bar')
    # else, filtered is empty, create default empty graph
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[2])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


def get_box_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = measure type selector
    # arg_value[1] = variable selector
    # arg_value[2] = orientation toggle
    # arg_value[3] = data points toggle

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, arg_value[0], arg_value[1], df_const)

    # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
    if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                            hierarchy_graph_children == ['graph_children']):
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_type == 'Level Filter':
                # Whole level graph title
                title = '{}: {} {}'.format(get_label(hierarchy_level_dropdown), arg_value[0], get_label('Distribution'))
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} {}'.format(arg_value[0], get_label('Distribution'))
            else:
                # Roots children graph title
                title = '{}: {} {}'.format(get_label("Root's Children"), arg_value[0], get_label('Distribution'))

    # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
    else:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if hierarchy_specific_dropdown:
                title = '{}: {} {}'.format(hierarchy_specific_dropdown, arg_value[0], get_label('Distribution'))
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}: {} {}'.format(hierarchy_path[-1], arg_value[0], get_label('Distribution'))

    # if df is not empty, create graph
    if not filtered_df.empty:

        title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            if arg_value[2] == 'Horizontal':
                xaxis = 'Measure Value'
                if hierarchy_type == 'Level Filter':
                    yaxis = hierarchy_level_dropdown
                else:
                    yaxis = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                filtered_df.rename(columns={yaxis: get_label(yaxis)}, inplace=True)
            else:
                if hierarchy_type == 'Level Filter':
                    xaxis = hierarchy_level_dropdown
                else:
                    xaxis = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                filtered_df.rename(columns={xaxis: get_label(xaxis)}, inplace=True)
                yaxis = 'Measure Value'

            x = xaxis
            y = yaxis
            xaxis = {'title': get_label(xaxis)}
            yaxis = {'title': get_label(yaxis)}

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            x = 'Measure Value' if arg_value[2] == 'Horizontal' else None
            y = 'Measure Value' if arg_value[2] == 'Vertical' else None
            xaxis = {'title': get_label('Measure Value')} if arg_value[2] == 'Horizontal' else None
            yaxis = {'title': get_label('Measure Value')} if arg_value[2] == 'Vertical' else None

        filtered_df['Date of Event'] = filtered_df['Date of Event'].transform(lambda i: i.strftime(format='%Y-%m-%d'))

        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        filtered_df.rename(columns={i: get_label(i) for i in
                                    ['Date of Event', 'Measure Value', 'Variable Name', 'Partial Period']},
                           inplace=True)
        hover_data = [get_label('Date of Event'), get_label('Variable Name'), get_label('Partial Period')]

        # generate graph
        fig = px.box(
            title=title,
            data_frame=filtered_df,
            x=get_label(x),
            y=get_label(y),
            color=get_label('Variable Name'),
            points='all' if arg_value[3] else False,
            hover_data=hover_data)
        fig.update_layout(
            xaxis=xaxis,
            yaxis=yaxis,
            legend_title_text=get_label('Variable Names'),
            boxgap=0.1,
            boxgroupgap=0.5,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')

    # else, filtered is empty, create default empty graph
    else:
        fig = get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                               hierarchy_path, hierarchy_graph_children, arg_value[1])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)

    return graph


def get_table_figure(arg_value, dff, tile, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                     hierarchy_type, hierarchy_graph_children, tile_title):
    # arg_value[0] = tile index
    # arg_value[1] = page_size

    # Clean dataframe to display nicely
    dff = dff.dropna(how='all', axis=1)

    # use manual title, if any
    if tile_title:
        title = tile_title
    # if no manual title and filtering based on level, use level selection as title
    elif hierarchy_type == 'Level Filter':
        title = get_label(hierarchy_level_dropdown)
    # else, no manual title and filtering based on specific item
    else:
        # if "graph all in dropdown" is selected
        if hierarchy_graph_children == ['graph_children']:
            # if not roots children
            if len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
            # Roots children graph title
            else:
                title = '{}'.format(get_label("Root's Children"))
        # else, "graph all in dropdown" is unselected
        else:
            if hierarchy_specific_dropdown:
                title = '{}'.format(hierarchy_specific_dropdown)
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}'.format(hierarchy_path[-1])

    # Create table
    if not dff.empty:

        # If dataframe has a link column Links should be displayed in markdown w/ the form (https://www.---------):
        columns_for_dash_table = []
        for i in dff.columns:
            if i == 'Link':
                columns_for_dash_table.append(
                    {"name": i, "id": i, "type": 'text', 'presentation': 'markdown', "hideable": True})
            else:
                columns_for_dash_table.append({"name": get_label(i), "id": i, "hideable": True})

        cond_style = []
        for col in dff.columns:
            name_length = len(get_label(col))
            pixel = 50 + round(name_length * 6)
            pixel = str(pixel) + "px"
            cond_style.append({'if': {'column_id': col}, 'minWidth': pixel})
        cond_style.append({'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'})

        if arg_value[1] is None or type(arg_value[1]) is not int:
            arg_value[1] = 10

        table = html.Div([
            html.Div(style={'height': '28px'}),
            html.Plaintext(title,
                           style={'font-family': 'Open Sans, verdana, arial, sans-serif', 'font-size': '17px',
                                  'white-space': 'pre', 'margin': '0', 'margin-left': 'calc(5% - 9px)',
                                  'cursor': 'default'}),
            html.Sub('{} {}'.format(get_label('Data Accessed on'), datetime.date(datetime.now())),
                     style={'margin-left': 'calc(5% - 9px)', 'cursor': 'default', 'font-size': '12px',
                            'font-family': '"Open Sans", verdana, arial, sans-serif'}),
            dash_table.DataTable(
                id={'type': 'datatable', 'index': tile},
                columns=columns_for_dash_table,

                page_current=0,
                page_size=int(arg_value[1]),
                page_action="custom",

                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='multi',
                sort_by=[],

                cell_selectable=False,

                style_data_conditional=cond_style,

                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},

                style_table={'margin-top': '10px', 'overflow': 'auto'},
            )], style={'height': '90%', 'width': 'auto', 'overflow-y': 'auto', 'overflow-x': 'hidden',
                       'margin-left': '10px', 'margin-right': '10px'})

    # else, create a blank table placeholder with an appropriate subtitle
    else:
        sub_title = get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown,
                                             hierarchy_path, hierarchy_graph_children, ['filler'])
        if sub_title == 'No Data Specified' and not tile_title:
            title = " "
        table = html.Div([
            html.Div(style={'height': '28px'}),
            html.Plaintext(title,
                           style={'font-family': 'Open Sans, verdana, arial, sans-serif', 'font-size': '17px',
                                  'white-space': 'pre', 'margin': '0', 'margin-left': 'calc(5% - 9px)',
                                  'cursor': 'default'}),
            html.Sub(sub_title,
                     style={'margin-left': 'calc(5% - 9px)', 'cursor': 'default', 'font-size': '12px',
                            'font-family': '"Open Sans", verdana, arial, sans-serif'})
        ], style={'height': '90%', 'width': 'auto', 'overflow-y': 'auto', 'overflow-x': 'hidden',
                  'margin-left': '10px', 'margin-right': '10px'})

    return table


# sankey graph layout
def get_sankey_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                      hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    title = tile_title

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, 'Link', arg_value[0], df_const)

    # if df is not empty, create empty sankey graph
    if filtered_df.empty:
        return dcc.Graph(
            id='graph-display',
            className='fill-container',
            responsive=True,
            config=dict(locale=LANGUAGE),
            figure=get_blank_figure(tile_title, title, hierarchy_type, hierarchy_level_dropdown,
                                    hierarchy_path, hierarchy_graph_children, []))

    title += '<br><sub>{} {} </sub>'.format(get_label('Data Accessed on'), datetime.date(datetime.now()))

    dir_name = os.path.dirname(__file__)

    # filename = os.path.join(dir_name, 'test_data/OPG010 Node Metadata.csv')
    # filename = os.path.join(dir_name, 'test_data/OPG010 Node Metadata 2.xlsx')
    filename = os.path.join(dir_name, 'test_data/OPG010 Node Metadata 3.xlsx')
    node_df = pd.read_excel(filename)

    # filename = os.path.join(dir_name, 'test_data/OPG010 SanKey Series.csv')
    # df = pd.read_csv(filename)

    # link_df = df[df['Measure Type'] == 'Link']  # need to further filter!!!
    # link_df = filtered_df[filtered_df['Measure Fcn'] == 'Link']

    label_numpy = []
    custom_numpy = []
    x_numpy = []
    y_numpy = []
    node_colour_numpy = []

    for index, row in node_df.iterrows():
        label_numpy.append(get_label(row['Node']))
        custom_numpy.append(get_label(row['Node'] + '_Long'))
        x_numpy.append(row['X-Coord'])
        y_numpy.append(row['Y-Coord'])
        node_colour_numpy.append(row['Colour'])

    source_numpy = []
    target_numpy = []
    value_numpy = []
    link_colour_numpy = []

    for index, row in filtered_df.iterrows():
        source_numpy.append(row['Measure Id'])
        target_numpy.append(row['MeasQual1'])
        value_numpy.append(row['MeasQual2'])
        link_colour_numpy.append(node_colour_numpy[int(row['Measure Id'])])

    fig = go.Figure(data=[go.Sankey(
        # arrangement
        # valueformat
        # valuesuffix
        node=dict(
            pad=15,
            # thickness=20,
            # line=dict(color="black", width=0.5),
            label=label_numpy,  # label=["A1", "A2", "B1", "B2", "C1", "C2"],
            x=x_numpy,
            y=y_numpy,
            customdata=custom_numpy,
            hovertemplate=get_label('Node ') + ' %{customdata} ' + get_label('has total value ') + ' %{value}',
            color=node_colour_numpy
        ),
        link=dict(
            source=source_numpy,  # source=[0, 1, 0, 2, 3, 3],  # indices correspond to labels, eg A1, A2, A2, B1, ...
            target=target_numpy,  # target=[2, 3, 3, 4, 4, 5],
            value=value_numpy,  # value=[8, 4, 2, 8, 4, 2]
            # customdata
            hovertemplate=get_label('Link from node') + ' %{source.customdata}<br />' +
                          get_label('to node') + ' %{target.customdata}<br />' +
                          get_label('has value') + ' %{value}',
            color=link_colour_numpy
            # label
        )
    )])

    fig.update_layout(
        # hovermode
        # plot_bgcolor
        # paper_bgcolor
        title_text=title,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')  # ,
    # font=dict(size=19, color='white'),
    # font_size=10)

    return dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)


# update graph internal - can be called from callbacks or programatically
def __update_graph(df_name, graph_options, graph_type, graph_title, num_periods, period_type,
                   hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_options,
                   state_of_display, secondary_type, timeframe,
                   fiscal_toggle, start_year, end_year, start_secondary, end_secondary, df_const):
    # Creates a hierarchy trail from the display
    if type(state_of_display) == dict:
        state_of_display = [state_of_display]
    list_of_names = []
    if len(state_of_display) > 0:
        for obj in state_of_display:
            list_of_names.append(obj['props']['children'])

    if hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        # If at a leaf node then display it's parents data
        nid_path = "root"
        for x in list_of_names:
            nid_path += ('^||^{}'.format(x))
        if not hierarchy_options:
            list_of_names.pop()

    # hierarchy specific dropdown selection is last item in list_of_names, otherwise None
    hierarchy_specific_dropdown = list_of_names[-1] if len(list_of_names) > 0 else None

    # If "Last ___ ____" is active and the num_periods is invalid (None), return an empty graph
    if timeframe == 'to-current' and not num_periods:
        filtered_df = pd.DataFrame(columns=df_const[df_name]['COLUMN_NAMES'])
    # else, filter normally
    else:
        filtered_df = data_filter(list_of_names, secondary_type, end_secondary, end_year,
                                  start_secondary, start_year, timeframe, fiscal_toggle, num_periods, period_type,
                                  hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                                  df_name, df_const)

    # line graph creation
    if graph_type == 'Line':
        return get_line_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                               list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                               df_const)
    # scatter graph creation
    elif graph_type == 'Scatter':
        return get_scatter_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                  list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                  df_const)

    # bubble graph creation
    elif graph_type == 'Bubble':
        return get_bubble_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                 list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                 df_const)

    # bar graph creation
    elif graph_type == 'Bar':
        if graph_options[4]:
            return get_animated_bar_figure(graph_options, filtered_df, hierarchy_specific_dropdown,
                                           hierarchy_level_dropdown,
                                           list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title,
                                           df_name, df_const)
        else:
            return get_bar_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                  list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                  df_const)
    # box plot creation
    elif graph_type == 'Box_Plot':
        return get_box_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name, df_const)
    # table creation
    elif graph_type == 'Table':
        # code to fix shifting
        changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]
        changed_index = dash.callback_context.inputs_list[2]['id']['index']
        if search(r'\d+', changed_id) and int(search(r'\d+', changed_id).group()) != 4:
            changed_index = int(search(r'\d+', changed_id).group())
        return get_table_figure(graph_options, filtered_df, changed_index, hierarchy_specific_dropdown,
                                hierarchy_level_dropdown,
                                list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title)

    # sankey creation
    elif graph_type == 'Sankey':
        return get_sankey_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                 list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                 df_const)

    # catch all
    else:
        return None
