######################################################################################################################
"""
graphs.py

contains functions to generate graphs
"""
######################################################################################################################

# External Packages
# import re
from _datetime import datetime
from flask import session
# import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_table
import dash_html_components as html
import dash
import pandas as pd

# import os
import plotly.graph_objects as go

# Internal Modules
from apps.dashboard.data import get_label, data_filter, customize_menu_filter, linear_regression, polynomial_regression


# ***********************************************HELPER FUNCTIONS****************************************************

# mark partial periods on graph
def set_partial_periods(fig, dataframe, graph_type):
    # Annotate partial data points
    partial_data_points = dataframe[dataframe['Partial Period'] == get_label('LBL_TRUE')]
    index_vals = list(partial_data_points.index.values)
    partial_pos = {}  # Key: x_val, Value: list of y_vals
    for i in range(len(partial_data_points)):
        # Co-ordinates of marker to be labeled
        x_val = partial_data_points.loc[index_vals[i], 'Date of Event']
        y_val = partial_data_points.loc[index_vals[i], 'Measure Value']
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
                        text=get_label("LBL_Partial_Period"),
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
def get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, variable_names, df_name,
                             df_const):
    sub_title = ''
    if df_name is None or df_name not in df_const:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_No_Data_Found'))
    elif hierarchy_type == 'Level Filter' and hierarchy_level_dropdown is None \
            or hierarchy_type == 'Specific Item' and not hierarchy_path:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_Make_A_Hierarchy_Selection'))
    elif not variable_names:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_Make_A_Variable_Selection'))
    return sub_title


def get_hierarchy_col(hierarchy_type, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_path, df_name,
                      df_const):
    if hierarchy_type == 'Level Filter':
        hierarchy_col = hierarchy_level_dropdown
    elif hierarchy_type == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        hierarchy_col = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
    else:
        hierarchy_col = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path) - 1]
    return hierarchy_col


# ************************************************GRAPH FUNCTIONS**************************************************
# line graph layout
def get_line_scatter_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                            hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const,
                            _xaxis_title, _yaxis_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    # arg_value[3] = mode
    # arg_value[4] = fit
    # arg_value[5] = degree
    # arg_value[6] = confidence interval
    # arg_value[7] = grid lines
    # arg_value[8] = legend

    language = session["language"]

    # Check on whether we have enough information to attempt to get data for a graph
    if hierarchy_type == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_type,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_type == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_type,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)
        hierarchy_col = get_hierarchy_col(hierarchy_type, hierarchy_level_dropdown, hierarchy_graph_children,
                                          hierarchy_path, df_name, df_const)
        # Create title
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if hierarchy_type == 'Level Filter':
                    # Whole level graph title
                    title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, df_name), arg_value[1],
                                                  get_label('LBL_Time'))  # hierarchy_level_dropdown
                elif len(hierarchy_path) != 0:
                    # Item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} vs {}'.format(arg_value[1], get_label('LBL_Time'))
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"), arg_value[1], get_label('LBL_Time'))
        else:
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if hierarchy_specific_dropdown:
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1], get_label('LBL_Time'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1], get_label('LBL_Time'))

        # if df is not empty, create graph
        if not filtered_df.empty:

            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

            # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
            if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                    hierarchy_graph_children == ['graph_children']):
                color = hierarchy_col
                line_group = 'Variable Name'
                legend_title_text = get_label('LBL_' + hierarchy_col, df_name)
            else:
                color = 'Variable Name'
                line_group = None
                legend_title_text = get_label('LBL_Variable_Names')

            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j != 'nan' else get_label('LBL_FALSE'))
            filtered_df.sort_values(by=[color, 'Date of Event'], inplace=True)

            # generate graph
            fig = px.line(
                title=title,
                data_frame=filtered_df,
                x='Date of Event',
                y='Measure Value',
                color=color,
                line_group=line_group,
                custom_data=[hierarchy_col, 'Variable Name'])
            fig.update_layout(legend_title_text=legend_title_text)

            if arg_value[3] == 'Line':
                fig.update_traces(mode='lines')
            elif arg_value[3] == 'Scatter':
                fig.update_traces(mode='markers')
            else:
                fig.update_traces(mode='lines+markers')

            hovertemplate = get_label('LBL_Gen_Hover_Data', df_name)
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-A%', get_label('LBL_Date_Of_Event', df_name)).replace(
                '%AXIS-A%', '%{x}')
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-B%', arg_value[1]).replace('%AXIS-B%', '%{y}')
            fig.update_traces(hovertemplate=hovertemplate)
            fig = set_partial_periods(fig, filtered_df, 'Line')

            if arg_value[4] == 'linear-fit':
                ci = True if arg_value[6] == ['ci'] else False
                best_fit_data = linear_regression(filtered_df, 'Date of Event', 'Measure Value', ci)
                filtered_df["Best Fit"] = best_fit_data["Best Fit"]
                fig2 = px.line(
                    data_frame=filtered_df,
                    x='Date of Event',
                    y='Best Fit',
                )
                fig2.update_traces(line_color='#A9A9A9')
                fig2.data[0].name = 'Best fit'
                fig2.data[0].showlegend = True
                fig.add_trace(fig2.data[0])

                if arg_value[6] == ['ci']:
                    filtered_df["Upper Interval"] = best_fit_data["Upper Interval"]
                    filtered_df["Lower Interval"] = best_fit_data["Lower Interval"]
                    fig3 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Upper Interval',
                    )
                    fig4 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Lower Interval',
                    )
                    fig3.update_traces(line_color='#000000')
                    fig3.data[0].showlegend = True
                    fig3.data[0].name = 'Upper Interval'
                    fig.add_trace(fig3.data[0])
                    fig4.update_traces(line_color='#000000')
                    fig4.data[0].showlegend = True
                    fig4.data[0].name = 'Lower Interval'
                    fig.add_trace(fig4.data[0])
            if arg_value[4] == 'curve-fit':
                ci = True if arg_value[6] == ['ci'] else False
                best_fit_data = polynomial_regression(filtered_df, 'Date of Event', 'Measure Value', arg_value[5], ci)
                filtered_df["Best Fit"] = best_fit_data["Best Fit"]
                fig2 = px.line(
                    data_frame=filtered_df,
                    x='Date of Event',
                    y='Best Fit',
                )
                fig2.update_traces(line_color='#A9A9A9')
                fig2.data[0].showlegend = True
                fig2.data[0].name = 'Best Fit'
                fig.add_trace(fig2.data[0])

                if arg_value[6] == ['ci']:  # ci
                    filtered_df["Upper Interval"] = best_fit_data["Upper Interval"]
                    filtered_df["Lower Interval"] = best_fit_data["Lower Interval"]
                    fig3 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Upper Interval',
                    )
                    fig4 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Lower Interval',
                    )
                    fig3.update_traces(line_color='#000000')
                    fig3.data[0].showlegend = True
                    fig3.data[0].name = 'Upper Interval'
                    fig.add_trace(fig3.data[0])
                    fig4.update_traces(line_color='#000000')
                    fig4.data[0].showlegend = True
                    fig4.data[0].name = 'Lower Interval'
                    fig.add_trace(fig4.data[0])
        else:
            fig = px.line(
                title=title + get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path,
                                                       arg_value[2], df_name, df_const))
    else:
        fig = px.line(
            title=get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, arg_value[2],
                                           df_name, df_const))

    # if arg_value[9]:
    #     xaxis = {'title': arg_value[9]}
    if _xaxis_title:
        xaxis = {'title': _xaxis_title}
    else:
        xaxis = {'title': 'Date of Event', 'type': 'date'}
    # if arg_value[10]:
    #     yaxis = {'title': arg_value[10]}
    if _yaxis_title:
        yaxis = {'title': _yaxis_title}
    else:
        yaxis = {'title': arg_value[1]}

    fig.update_layout(
        yaxis=yaxis,
        xaxis=xaxis,
        showlegend=False if arg_value[8] else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')
    # if the checkbox for line and scatter is select or not show gird lines
    if arg_value[7]:
        fig.update_xaxes(showgrid=True, zeroline=True)
        fig.update_yaxes(showgrid=True, zeroline=True)
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


# animated bubble layout
def get_bubble_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                      hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const,
                      _xaxis_title, _yaxis_title):
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = x-axis measure
    # (args-value: {})[2] = y-axis
    # (args-value: {})[3] = y-axis measure
    # (args-value: {})[4] = size
    # (args-value: {})[5] = size measure
    language = session["language"]

    # Check whether we have enough information to attempt getting data for a graph
    if hierarchy_type == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_type,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_type == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_type,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = dff.copy().query(
            "(`Variable Name` == @arg_value[0] and `Measure Type` == @arg_value[1]) or "
            "(`Variable Name` == @arg_value[2] and `Measure Type` == @arg_value[3]) or "
            "(`Variable Name` == @arg_value[4] and `Measure Type` == @arg_value[5])")
        color = get_hierarchy_col(hierarchy_type, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_path,
                                  df_name, df_const)

        filtered_df[['Date of Event', 'Measure Type', 'Variable Name', 'Partial Period', color]] = filtered_df[
            ['Date of Event', 'Measure Type', 'Variable Name', 'Partial Period', color]].astype(str)
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
                    title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, df_name), arg_value[2],
                                                  arg_value[4])
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} vs {}'.format(arg_value[2], arg_value[4])
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"), arg_value[2], arg_value[4])

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

            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))
            legend_title_text = get_label(
                'LBL_' + hierarchy_level_dropdown, df_name) if hierarchy_type == 'Level Filter' else 'Traces'

            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j != 'nan' else get_label('LBL_FALSE'))
            filtered_df.sort_values(by=['Date of Event', color], inplace=True)

            filtered_df['Date of Event'] = filtered_df['Date of Event'].astype(str)

            # generate graph
            fig = px.scatter(
                title=title,
                x=filtered_df[arg_value[0], arg_value[1]],
                y=filtered_df[arg_value[2], arg_value[3]],
                size=filtered_df[arg_value[4], arg_value[5]],
                animation_frame=filtered_df['Date of Event'],
                color=filtered_df[color],
                range_x=[0, filtered_df[arg_value[0], arg_value[1]].max()],
                range_y=[0, filtered_df[arg_value[2], arg_value[3]].max()],
                labels={'animation_frame': 'Date of Event'},
                custom_data=[filtered_df[color], filtered_df['Date of Event'], filtered_df[arg_value[4], arg_value[5]]]
            )
            fig.update_layout(
                legend_title_text='Size: <br> &#9; {} ({})<br> <br>{}'.format(arg_value[4], arg_value[5],
                                                                              legend_title_text))
            hovertemplate = get_label('LBL_Bubble_Hover_Data', df_name)
            hovertemplate = hovertemplate.replace('%AXIS-X-A%', arg_value[0]).replace('%AXIS-X-B%',
                                                                                      arg_value[1]).replace(
                '%X-AXIS%', '%{x}')
            hovertemplate = hovertemplate.replace('%AXIS-Y-A%', arg_value[2]).replace('%AXIS-Y-B%',
                                                                                      arg_value[3]).replace(
                '%Y-AXIS%', '%{y}')
            hovertemplate = hovertemplate.replace('%AXIS-Z-A%', arg_value[4]).replace('%AXIS-Z-B%',
                                                                                      arg_value[5]).replace(
                '%Z-AXIS%', '%{customdata[2]}')
            fig.update_traces(hovertemplate=hovertemplate)
        # else, filtered is empty, create default empty graph
        else:
            fig = px.scatter(
                title=title + get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path,
                                                       arg_value[2], df_name, df_const))
    else:
        fig = px.scatter(
            title=get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, arg_value[2],
                                           df_name, df_const))

    # if arg_value[8]:
    #     xaxis = arg_value[8]
    # else:
    xaxis = '{} ({})'.format(arg_value[0], arg_value[1])
    # if arg_value[9]:
    #     yaxis = arg_value[9]
    # else:
    yaxis = '{} ({})'.format(arg_value[2], arg_value[3])

    fig.update_layout(
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        showlegend=False if arg_value[7] else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    if arg_value[6]:
        fig.update_xaxes(showgrid=True, zeroline=True)
        fig.update_yaxes(showgrid=True, zeroline=True)
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


# bar graph layout TODO: VERTICAL TICKS OVERLAPPING WITH THE ANIMATION SLIDER
def get_bar_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const, _xaxis_title, _yaxis_title):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    # arg_value[3] = orientation
    # arg_value[4] = animation bool
    language = session["language"]
    xaxis = {'type': 'category'}

    # Check whether we have enough information to attempt getting data for a graph
    if hierarchy_type == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_type,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_type == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_type,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = customize_menu_filter(dff, df_name, arg_value[1], arg_value[2], df_const)
        hierarchy_col = get_hierarchy_col(hierarchy_type, hierarchy_level_dropdown, hierarchy_graph_children,
                                          hierarchy_path, df_name, df_const)

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_type == 'Level Filter':

                    if arg_value[0] == 'Variable Names':
                        title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, df_name),
                                                      arg_value[1], get_label('LBL_Variable_Names'))
                    else:
                        # Whole level graph title
                        title = '{0}: {1} vs {0}'.format(get_label('LBL_' + hierarchy_level_dropdown, df_name),
                                                         arg_value[1])
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    if arg_value[0] == 'Variable Names':
                        title = title + ': {} vs {}'.format(arg_value[1], get_label('LBL_Variable_Names'))
                    else:
                        title = title + ': {} vs {}'.format(arg_value[1], hierarchy_path[-1])
                else:
                    if arg_value[0] == 'Variable Names':
                        title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"), arg_value[1],
                                                      get_label('LBL_Variable_Names'))
                    else:
                        # Root's children graph title
                        title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"), arg_value[1],
                                                      get_label('LBL_Root'))

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            # Title setup
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                                  get_label('LBL_Variable_Names'))
                else:
                    if hierarchy_specific_dropdown:
                        title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                                      get_label('LBL_Time'))
                    else:
                        if len(hierarchy_path) == 0:
                            title = ""
                        else:
                            title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[1],
                                                          get_label('LBL_Time'))

        group_by_item = arg_value[0] != 'Variable Names'
        title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

        # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Axis and color logic
            if not group_by_item:
                x = 'Variable Name'
                if hierarchy_type == 'Level Filter':
                    color = hierarchy_level_dropdown
                else:
                    color = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
            elif hierarchy_type == 'Level Filter':
                x = hierarchy_level_dropdown
                color = 'Variable Name'
            else:
                x = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                color = 'Variable Name'

            legend_title_text = get_label('LBL_' + color.replace(' ', '_'), df_name)

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            color = 'Variable Name' if group_by_item else 'Partial Period'
            x = 'Date of Event' if group_by_item and not arg_value[4] else 'Variable Name'
            legend_title_text = get_label('LBL_Variable_Name', df_name) if group_by_item else get_label(
                'LBL_Partial_Period', df_name)
            if group_by_item and not arg_value[4]:
                xaxis = {'type': 'date'}

        # if df is not empty, create graph
        if not filtered_df.empty:

            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda y: get_label('LBL_TRUE') if y != 'nan' else get_label('LBL_FALSE'))
            filtered_df['Date of Event'] = \
                filtered_df['Date of Event'].transform(lambda y: y.strftime(format='%Y-%m-%d'))

            if arg_value[4]:
                # TODO: Remove in production when there is a full dataset
                if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                        hierarchy_graph_children == ['graph_children']):
                    for i in filtered_df['Date of Event'].unique():
                        for j in filtered_df[hierarchy_col].unique():
                            for k in filtered_df[color].unique():
                                if filtered_df.query(
                                        "`Date of Event` == @i and `{}` == @j and `{}` == @k".format(x,
                                                                                                     color)).empty:
                                    filtered_df = filtered_df.append(
                                        {'Date of Event': i, hierarchy_col: j, color: k, 'Measure Value': 0},
                                        ignore_index=True)
            filtered_df.sort_values(by=['Date of Event', hierarchy_col, color], inplace=True)

            # generate graph
            fig = px.bar(
                title=title,
                data_frame=filtered_df,
                x=x if arg_value[3] == 'Vertical' else 'Measure Value',
                y='Measure Value' if arg_value[3] == 'Vertical' else x,
                color=color,
                barmode='group',
                animation_frame='Date of Event' if arg_value[4] else None,
                custom_data=[hierarchy_col, 'Variable Name', 'Date of Event'])
            fig.update_layout(legend_title_text=legend_title_text)

            hovertemplate = get_label('LBL_Gen_Hover_Data', df_name)
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-A%', get_label('LBL_Date_Of_Event', df_name))
            hovertemplate = hovertemplate.replace('%AXIS-A%', '%{customdata[2]}').replace('%AXIS-TITLE-B%',
                                                                                          arg_value[1])
            if arg_value[3] == 'Vertical':
                hovertemplate = hovertemplate.replace('%AXIS-B%', '%{y}')
            else:
                hovertemplate = hovertemplate.replace('%AXIS-B%', '%{x}')
            fig.update_traces(hovertemplate=hovertemplate)

            fig = set_partial_periods(fig, filtered_df, 'Bar')

        # else, filtered is empty, create default empty graph
        else:
            fig = px.bar(
                title=title + get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path,
                                                       arg_value[2], df_name, df_const))
    else:
        fig = px.bar(
            title=get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, arg_value[2],
                                           df_name, df_const))

    # if arg_value[7]:
    #     xaxis = {'title': arg_value[7]}
    if _xaxis_title:
        xaxis = {'title': _xaxis_title}
    # if arg_value[8]:
    #     yaxis = {'title': arg_value[8]}
    if _yaxis_title:
        yaxis = {'title': _yaxis_title}
    else:
        yaxis = {'title': arg_value[1]}

    fig.update_layout(
        xaxis=xaxis if arg_value[3] == 'Vertical' else yaxis,
        yaxis=yaxis if arg_value[3] == 'Vertical' else xaxis,
        showlegend=False if arg_value[6] else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    if arg_value[5]:
        fig.update_xaxes(showgrid=True, zeroline=True)
        fig.update_yaxes(showgrid=True, zeroline=True)
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


def get_box_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title, df_name, df_const, _xaxis_title, _yaxis_title):
    # arg_value[0] = measure type selector
    # arg_value[1] = variable selector
    # arg_value[2] = orientation toggle
    # arg_value[3] = data points toggle
    language = session["language"]
    xaxis = {'title': arg_value[0]}
    yaxis = {'type': 'category'}

    # Check on whether we have enough information to attempt to get data for a graph
    if hierarchy_type == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_type,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_type == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_type,
                                                                  hierarchy_graph_children, df_name, df_const]:
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
                    title = '{}: {} {}'.format(get_label('LBL_' + hierarchy_level_dropdown, df_name), arg_value[0],
                                               get_label('LBL_Distribution'))
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} {}'.format(arg_value[0], get_label('LBL_Distribution'))
                else:
                    # Roots children graph title
                    title = '{}: {} {}'.format(get_label("LBL_Roots_Children"), arg_value[0],
                                               get_label('LBL_Distribution'))

        # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_specific_dropdown:
                    title = '{}: {} {}'.format(hierarchy_specific_dropdown, arg_value[0], get_label('LBL_Distribution'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} {}'.format(hierarchy_path[-1], arg_value[0], get_label('LBL_Distribution'))

        # if df is not empty, create graph
        if not filtered_df.empty:

            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

            # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
            if hierarchy_type == 'Level Filter' or (hierarchy_type == 'Specific Item' and
                                                    hierarchy_graph_children == ['graph_children']):
                x = 'Measure Value'
                if hierarchy_type == 'Level Filter':
                    y = hierarchy_level_dropdown
                else:
                    y = df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                filtered_df.sort_values(by=['Variable Name', y, x], inplace=True)

            # else, hierarchy type is specific item while "Graph all in Dropdown" is unselected
            else:
                x = 'Measure Value'
                y = None
                xaxis = {'title': arg_value[0]}
                yaxis = None
                filtered_df.sort_values(by=['Variable Name', 'Measure Value'])

            filtered_df['Date of Event'] = filtered_df['Date of Event'].transform(
                lambda i: i.strftime(format='%Y-%m-%d'))

            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j != 'nan' else get_label('LBL_FALSE'))

            # generate graph
            fig = px.box(
                title=title,
                data_frame=filtered_df,
                x=x if arg_value[2] == 'Horizontal' else y,
                y=y if arg_value[2] == 'Horizontal' else x,
                color='Variable Name',
                points='all' if arg_value[3] else False)
            fig.update_layout(legend_title_text=get_label('LBL_Variable_Names'))

        # else, filtered is empty, create default empty graph
        else:
            fig = px.box(
                title=title + get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path,
                                                       arg_value[2], df_name, df_const))
    else:
        fig = px.box(
            title=get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, arg_value[2],
                                           df_name, df_const))

    # if arg_value[6]:
    #     xaxis = {'title': arg_value[6]}
    # if arg_value[7]:
    #     yaxis = {'title': arg_value[7]}

    fig.update_layout(
        xaxis=xaxis if arg_value[2] == 'Horizontal' else yaxis,
        yaxis=yaxis if arg_value[2] == 'Horizontal' else xaxis,
        legend_title_text=get_label('LBL_Variable_Names'),
        showlegend=False if arg_value[5] else True,
        boxgap=0.1,
        boxgroupgap=0.5,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    if arg_value[4]:
        fig.update_xaxes(showgrid=True, zeroline=True)
        fig.update_yaxes(showgrid=True, zeroline=True)
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


def get_table_figure(arg_value, dff, tile, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                     hierarchy_type, hierarchy_graph_children, tile_title, df_name):
    # arg_value[0] = tile index
    # arg_value[1] = page_size
    language = session["language"]
    title = ''

    # Clean dataframe to display nicely
    dff = dff.dropna(how='all', axis=1)

    # use special data title if no data
    if hierarchy_type == 'Level Filter' and None in [arg_value, hierarchy_level_dropdown, hierarchy_type,
                                                     hierarchy_graph_children, df_name] \
            or hierarchy_type == 'Specific Item' and None in [arg_value, hierarchy_path, hierarchy_type,
                                                              hierarchy_graph_children, df_name]:
        if df_name is None:
            title = '{}'.format(get_label('LBL_No_Data_Found'))
        elif hierarchy_type == 'Level Filter' and hierarchy_level_dropdown is None \
                or hierarchy_type == 'Specific Item' and not hierarchy_path:
            title = '{}'.format(get_label('LBL_Make_A_Hierarchy_Selection'))
    # use manual title, if any
    elif tile_title:
        title = tile_title
    # if no manual title and filtering based on level, use level selection as title
    elif hierarchy_type == 'Level Filter':
        title = get_label('LBL_' + hierarchy_level_dropdown, df_name)
    # else, no manual title and filtering based on specific item
    else:
        # if "graph all in dropdown" is selected
        if hierarchy_graph_children == ['graph_children']:
            # if not roots children
            if len(hierarchy_path) != 0:
                # Specific item's children graph title
                if language == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                else:
                    title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
            # Roots children graph title
            else:
                title = '{}'.format(get_label("LBL_Roots_Children"))
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
    # If dataframe has a link column Links should be displayed in markdown w/ the form (https://www.---------):
    columns_for_dash_table = []
    for i in dff.columns:
        if i == "Link":
            columns_for_dash_table.append(
                {"name": get_label("LBL_Link", df_name), "id": i, "type": "text", "presentation": "markdown",
                 "hideable": True})
        else:
            columns_for_dash_table.append(
                {"name": get_label('LBL_' + i.replace(' ', '_'), df_name), "id": i, "hideable": True})
    cond_style = []
    for col in dff.columns:
        name_length = len(get_label('LBL_' + col.replace(' ', '_')))
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
        html.Sub('{} {}'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now())),
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

    return table


# sankey graph layout
def get_sankey_figure(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title, df_name,
                      df_const):
    # arg_value[0] = variable selector
    language = session["language"]
    title = tile_title

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, df_name, 'Link', arg_value[0], df_const)

    # if df is not empty, create empty sankey graph
    if filtered_df.empty:
        title += get_empty_graph_subtitle(hierarchy_type, hierarchy_level_dropdown, hierarchy_path, arg_value[0],
                                          df_name, df_const)
        return dcc.Graph(
            id='graph-display',
            className='fill-container',
            responsive=True,
            config=dict(locale=language.lower()),
            figure=go.Figure(
                layout={'title_text': title, 'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)'},
                data=[go.Sankey()]))

    title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

    node_df = session[df_name + "_NodeData"]

    label_numpy = []
    custom_numpy = []
    x_numpy = []
    y_numpy = []
    node_colour_numpy = []

    for index, row in node_df.iterrows():
        label_numpy.append(get_label("LBL_" + row['node_id'], df_name))
        custom_numpy.append(get_label("LBL_" + row['node_id'] + '_Long', df_name))
        x_numpy.append(row['x_coord'])
        y_numpy.append(row['y_coord'])
        node_colour_numpy.append(row['colour'])

    source_numpy = []
    target_numpy = []
    value_numpy = []
    link_colour_numpy = []

    for index, row in filtered_df.iterrows():
        source_numpy.append(row['Measure Id'])
        target_numpy.append(row['MeasQual1'])
        value_numpy.append(row['MeasQual2'])
        link_colour_numpy.append(node_colour_numpy[int(row['Measure Id'])])

    node_hover_template = get_label('LBL_Node_HoverTemplate', df_name)
    node_hover_template = node_hover_template.replace("%VALUE%", "%{value}")
    node_hover_template = node_hover_template.replace("%NODE%", "%{customdata}")

    link_hover_template = get_label("LBL_Link_HoverTemplate", df_name)
    link_hover_template = link_hover_template.replace("%VALUE%", "%{value}")
    link_hover_template = link_hover_template.replace("%SOURCE-NODE%", "%{source.customdata}")
    link_hover_template = link_hover_template.replace("%TARGET-NODE%", "%{target.customdata}")

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
            hovertemplate=node_hover_template,
            color=node_colour_numpy
        ),
        link=dict(
            source=source_numpy,  # source=[0, 1, 0, 2, 3, 3],  # indices correspond to labels, eg A1, A2, A2, B1, ...
            target=target_numpy,  # target=[2, 3, 3, 4, 4, 5],
            value=value_numpy,  # value=[8, 4, 2, 8, 4, 2]
            # customdata
            hovertemplate=link_hover_template,
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
        config=dict(locale=language.lower()),
        figure=fig)


# update graph internal - can be called from callbacks or programatically
def __update_graph(df_name, graph_options, graph_type, graph_title, num_periods, period_type,
                   hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_options,
                   state_of_display, secondary_type, timeframe,
                   fiscal_toggle, start_year, end_year, start_secondary, end_secondary, df_const, xtitle, ytitle):
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

    # line and scatter graph creation
    if graph_type == 'Line' or graph_type == 'Scatter':
        return get_line_scatter_figure(graph_options, filtered_df, hierarchy_specific_dropdown,
                                       hierarchy_level_dropdown, list_of_names, hierarchy_toggle,
                                       hierarchy_graph_children, graph_title, df_name, df_const, xtitle, ytitle)

    # bubble graph creation
    elif graph_type == 'Bubble':
        return get_bubble_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                 list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                 df_const, xtitle, ytitle)

    # bar graph creation
    elif graph_type == 'Bar':
        return get_bar_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                              df_const, xtitle, ytitle)
    # box plot creation
    elif graph_type == 'Box_Plot':
        return get_box_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                              df_const, xtitle, ytitle)
    # table creation
    elif graph_type == 'Table':
        changed_index = dash.callback_context.inputs_list[2]['id']['index']
        return get_table_figure(graph_options, filtered_df, changed_index, hierarchy_specific_dropdown,
                                hierarchy_level_dropdown, list_of_names, hierarchy_toggle, hierarchy_graph_children,
                                graph_title, df_name)

    # sankey creation
    elif graph_type == 'Sankey':
        return get_sankey_figure(graph_options, filtered_df, hierarchy_level_dropdown, list_of_names, hierarchy_toggle,
                                 graph_title, df_name, df_const)

    # catch all
    else:
        return None
