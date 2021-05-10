######################################################################################################################
"""
graphs.py

contains functions to generate graphs
"""
######################################################################################################################

# External Packages
import plotly.express as px
import dash_core_components as dcc
import dash_table
import dash_html_components as html

# Internal Modules
from apps.app0003.data import HIERARCHY_LEVELS, get_label, LANGUAGE, customize_menu_filter


# helper functions
def make_hover_template(text_keys, data_list):
    hover_template = ''
    for i in range(len(text_keys)):
        hover_template = hover_template + '{}: %{{{}}}<br>'.format(get_label(text_keys[i]), data_list[i])
    return hover_template


def set_partial_periods(fig, dataframe, graph_type):
    # Annotate partial data points
    partial_data_points = dataframe[dataframe['Partial Period']]
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


# line graph layout
def get_line_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                    hierarchy_type, hierarchy_graph_children, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    if not hierarchy_type or (hierarchy_type and hierarchy_graph_children == ['graph_children']):
        return get_line_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type,
                                     tile_title)
    else:
        return get_line_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title)


def get_line_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                          get_label('Time')) if hierarchy_specific_dropdown else '{}: {} vs {}'.format(
                hierarchy_path[-1], arg_value[1], get_label('Time'))

        fig = px.line(
            title=title,
            data_frame=filtered_df,
            x='Date of Event',
            y='Measure Value',
            color='Variable Name')
        fig.update_layout(
            xaxis={'title': get_label('Time')},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label('Variable Names'),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        fig = set_partial_periods(fig, filtered_df, 'Line')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Date', 'Measure Value', 'Partial Period']
        data_list = ['x', 'y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        # Empty graph
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_line_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if not hierarchy_type:
                # Whole level graph title
                title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1], get_label('Time'))
            elif len(hierarchy_path) != 0:
                # Item's children graph title
                if LANGUAGE == 'en':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[1], get_label('Time'))
            else:
                # Root's children graph title
                title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Time'))

        fig = px.line(
            title=title,
            data_frame=filtered_df,
            x='Date of Event',
            y='Measure Value',
            color=filtered_df[hierarchy_level_dropdown] if not hierarchy_type else
            filtered_df[HIERARCHY_LEVELS[len(hierarchy_path)]],
            line_group='Variable Name',
            hover_name='Variable Name')
        fig.update_layout(
            xaxis={'title': get_label('Time')},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label(hierarchy_level_dropdown) if not hierarchy_type else
            get_label(HIERARCHY_LEVELS[len(hierarchy_path)]),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Line')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Date', 'Measure Value', 'Partial Period']
        data_list = ['x', 'y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        # Empty graph
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


# scatter graph layout
def get_scatter_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                       hierarchy_type, hierarchy_graph_children, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    if not hierarchy_type or (hierarchy_type and hierarchy_graph_children == ['graph_children']):
        return get_scatter_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type,
                                        tile_title)
    else:
        return get_scatter_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title)


def get_scatter_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                          get_label('Time')) if hierarchy_specific_dropdown else '{}: {} vs {}'.format(
                hierarchy_path[-1], arg_value[1], get_label('Time'))

        fig = px.scatter(
            title=title,
            data_frame=filtered_df,
            x='Date of Event',
            y='Measure Value',
            color='Variable Name')
        fig.update_layout(
            xaxis={'title': get_label('Time')},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label('Variable Names'),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        fig = set_partial_periods(fig, filtered_df, 'Scatter')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Date', 'Measure Value', 'Partial Period']
        data_list = ['x', 'y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        # Empty graph
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_scatter_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title):
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            if not hierarchy_type:
                # Whole level graph title
                title = '{}: {} vs {}'.format(get_label(hierarchy_level_dropdown), arg_value[1], get_label('Time'))
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'en':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[1], get_label('Time'))
            else:
                # Root's children graph title
                title = '{}\'s {}: {} vs {}'.format(get_label('Root'), get_label('Children'), arg_value[1],
                                                    get_label('Time'))

        fig = px.scatter(
            title=title,
            data_frame=filtered_df,
            x='Date of Event',
            y='Measure Value',
            color=filtered_df[hierarchy_level_dropdown] if not hierarchy_type else
            filtered_df[HIERARCHY_LEVELS[len(hierarchy_path)]],
            hover_name='Variable Name')
        fig.update_layout(
            xaxis={'title': get_label('Time')},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label(hierarchy_level_dropdown) if not hierarchy_type else
            get_label(HIERARCHY_LEVELS[len(hierarchy_path)]),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        fig = set_partial_periods(fig, filtered_df, 'Scatter')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Setup custom hover text
        text_keys = ['Date', 'Measure Value', 'Partial Period']
        data_list = ['x', 'y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


# bar graph layout
def get_bar_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    if not hierarchy_type or (hierarchy_type and hierarchy_graph_children == ['graph_children']):
        return get_bar_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type,
                                    tile_title)
    else:
        return get_bar_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title)


def get_bar_figure_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            # Generate title if there is no user entered title
            title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[1],
                                          get_label('Time')) if hierarchy_specific_dropdown else '{}: {} vs {}'.format(
                hierarchy_path[-1], arg_value[1], get_label('Time'))

        group_by_item = arg_value[0] != 'Variable Names'

        fig = px.bar(
            title=title,
            data_frame=filtered_df,
            x='Date of Event' if group_by_item else 'Variable Name',
            y='Measure Value',
            color='Variable Name' if group_by_item else 'Partial Period',
            barmode='group')
        fig.update_layout(
            xaxis={'title': get_label('Time') if group_by_item else get_label('Variable Name')},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label('Variable Name') if group_by_item else get_label('Partial Period'),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Bar')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Setup custom hover text
        text_keys = ['Date', 'Measure Value', 'Partial Period']
        data_list = ['x', 'y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_bar_figure_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title):
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[1], arg_value[2])

    group_by_item = arg_value[0] != 'Variable Names'

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if not hierarchy_type:
                # Whole level graph title
                title = '{0}: {1} vs {0}'.format(get_label(hierarchy_level_dropdown), arg_value[1])
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'en':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} vs {}'.format(arg_value[1], hierarchy_path[-1])
            else:
                # Root's children graph title
                title = '{}: {} vs {}'.format(get_label("Root's Children"), arg_value[1], get_label('Root'))

        # Axis and color logic
        if not group_by_item:
            x_axis = 'Variable Name'
            if not hierarchy_type:
                color = hierarchy_level_dropdown
            else:
                color = HIERARCHY_LEVELS[len(hierarchy_path)]
        elif not hierarchy_type:
            x_axis = hierarchy_level_dropdown
            color = 'Variable Name'
        else:
            x_axis = HIERARCHY_LEVELS[len(hierarchy_path)]
            color = 'Variable Name'

        fig = px.bar(
            title=title,
            data_frame=filtered_df,
            x=filtered_df[x_axis],
            y='Measure Value',
            color=color,
            barmode='group')
        fig.update_layout(
            xaxis={'title': get_label(x_axis)},
            yaxis={'title': arg_value[1]},
            legend_title_text=get_label(color),
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        fig = set_partial_periods(fig, filtered_df, 'Bar')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Measure Value', 'Partial Period']
        data_list = ['y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_box_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_type, hierarchy_graph_children, tile_title):
    # arg_value[0] = measure type selector
    # arg_value[1] = variable selector
    # arg_value[2] = orientation toggle
    # arg_value[3] = data points toggle
    if not hierarchy_type or (hierarchy_type and hierarchy_graph_children == ['graph_children']):
        return get_box_plot_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title)
    else:
        return get_box_plot_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title)


def get_box_plot_specific(arg_value, dff, hierarchy_specific_dropdown, hierarchy_path, tile_title):
    # arg_value[0] = measure type selector
    # arg_value[1] = variable selector
    # arg_value[2] = orientation toggle
    # arg_value[3] = data points toggle

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[0], arg_value[1])

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            title = '{}: {} {}'.format(hierarchy_specific_dropdown, arg_value[0], get_label('Distribution')) \
                if hierarchy_specific_dropdown else '{}: {} {}'.format(
                hierarchy_path[-1], arg_value[0], get_label('Distribution'))

        fig = px.box(
            title=title,
            data_frame=filtered_df,
            x='Measure Value' if arg_value[2] == 'Horizontal' else None,
            y='Measure Value' if arg_value[2] == 'Vertical' else None,
            color='Variable Name',
            points='all' if arg_value[3] else False)
        fig.update_layout(
            xaxis={'title': get_label('Measure Value')} if arg_value[2] == 'Horizontal' else None,
            yaxis={'title': get_label('Measure Value')} if arg_value[2] == 'Vertical' else None,
            legend_title_text=get_label('Variable Names'),
            boxgap=0.1,
            boxgroupgap=0.5,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Measure Value', 'Partial Period']
        data_list = ['x', 'customdata'] if arg_value[2] == 'Horizontal' else ['y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_box_plot_multi(arg_value, dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_type, tile_title):
    # arg_value[0] = measure type selector
    # arg_value[1] = variable selector
    # arg_value[2] = orientation toggle
    # arg_value[3] = data points toggle

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, arg_value[0], arg_value[1])

    if arg_value[2] == 'Horizontal':
        x_axis = 'Measure Value'
        if not hierarchy_type:
            y_axis = hierarchy_level_dropdown
        else:
            y_axis = HIERARCHY_LEVELS[len(hierarchy_path)]
    else:
        if not hierarchy_type:
            x_axis = hierarchy_level_dropdown
        else:
            x_axis = HIERARCHY_LEVELS[len(hierarchy_path)]
        y_axis = 'Measure Value'

    if not filtered_df.empty:
        # Title setup
        if tile_title:
            title = tile_title
        else:
            if not hierarchy_type:
                # Whole level graph title
                title = '{}: {} {}'.format(get_label(hierarchy_level_dropdown), arg_value[0], get_label('Distribution'))
            elif len(hierarchy_path) != 0:
                # Specific item's children graph title
                if LANGUAGE == 'en':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('Children'))
                else:
                    title = '{} {}'.format(get_label('Children of'), hierarchy_path[-1])
                title = title + ': {} {}'.format(arg_value[0], get_label('Distribution'))
            else:
                # Roots children graph title
                title = '{}: {} {}'.format(get_label("Root's Children"), arg_value[0], get_label('Distribution'))

        fig = px.box(
            title=title,
            data_frame=filtered_df,
            x=x_axis,
            y=y_axis,
            color='Variable Name',
            points='all' if arg_value[3] else False)
        fig.update_layout(
            xaxis={'title': get_label(x_axis)},
            yaxis={'title': get_label(y_axis)},
            legend_title_text=get_label('Variable Names'),
            boxgap=0.1,
            boxgroupgap=0.5,
            overwrite=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
        filtered_df['Partial Period'] = filtered_df['Partial Period'].transform(
            lambda j: get_label('TRUE') if j else get_label('FALSE'))

        # Set custom hover text
        text_keys = ['Measure Value', 'Partial Period']
        data_list = ['x', 'customdata'] if arg_value[2] == 'Horizontal' else ['y', 'customdata']
        fig.update_traces(
            customdata=filtered_df['Partial Period'],
            hovertemplate=make_hover_template(text_keys, data_list)
        )
    else:
        fig = px.line().update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')
    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=LANGUAGE),
        figure=fig)
    return graph


def get_table_figure(arg_value, df, tile, tile_title):
    # arg_value[0] = tile index
    # arg_value[1] = page_size

    table = {}

    # Clean dataframe to display nicely
    df = df.dropna(how='all', axis=1)

    # If dataframe has a link column Links should be displayed in markdown w/ the form (https://www.---------):
    columns_for_dash_table = []
    for i in df.columns:
        if i == 'Link':
            columns_for_dash_table.append(
                {"name": i, "id": i, "type": 'text', 'presentation': 'markdown', "hideable": True})
        else:
            columns_for_dash_table.append({"name": get_label(i), "id": i, "hideable": True})

    cond_style = []
    for col in df.columns:
        name_length = len(get_label(col))
        pixel = 50 + round(name_length * 6)
        pixel = str(pixel) + "px"
        cond_style.append({'if': {'column_id': col}, 'minWidth': pixel})
    cond_style.append({'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'})

    if arg_value[1] is None:
        arg_value[1] = 10

    # Create table
    if not df.empty:
        table = html.Div([
            html.Plaintext(tile_title,
                           style={'font-family': 'Open Sans, verdana, arial, sans-serif', 'font-size': '17px',
                                  'fill': 'rgb(42, 63, 95)', 'opacity': '1', 'font-weight': 'normal',
                                  'white-space': 'pre', 'position': 'relative', 'left': '20px'}),
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

                style_table={'margin-top': '10px', 'overflow-y': 'auto', 'overflow-x': 'auto'},
            )], style={'margin': '10px', 'overflow-x': 'hidden', 'overflow-y': 'auto', 'height': '90%', 'width': '99%'})
    return table
