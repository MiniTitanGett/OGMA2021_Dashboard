######################################################################################################################
"""
layouts.py

stores all layouts excluding hierarchy filter layout
"""
######################################################################################################################

# External Packages
import dash_core_components as dcc
import dash_html_components as html

# Internal Modules
from apps.app0003.data import GRAPH_OPTIONS, DATA_OPTIONS, MEASURE_TYPE_OPTIONS, CLR, DATA_CONTENT_HIDE, VIEW_CONTENT_SHOW, \
    CUSTOMIZE_CONTENT_HIDE, X_AXIS_OPTIONS, get_label, LANGUAGE, LAYOUT_CONTENT_HIDE, LAYOUT_CONTENT_SHOW
from apps.app0003.hierarchy_filter import get_hierarchy_layout
from apps.app0003.datepicker import get_date_picker

from apps.app0003.saving_functions import saved_layouts

# Contents:
#   HELPER FUNCTION(S)
#       - change_index()
#   DATA SIDE MENU
#       - get_data_menu()
#   LAYOUT
#       - get_layout()
#   TILE LAYOUT
#       - get_tile()
#       - get_tile_layout()
#   GRAPH MENUS
#       - get_line_graph_menu()
#       - get_bar_graph_menu()
#       - get_scatter_graph_menu()
#       - get_table_graph_menu()


# ********************************************HELPER FUNCTION(S)******************************************************

# change index numbers of all id's within tile or data side-menu
def change_index(document, new_index):
    """
    :param document: An array of an unknown combination of nested lists/dictionaries.
    :param new_index: New index integer to replace the old index integer.
    :return: Pointer to the modified document.
    """

    def _change_index(document, new_index):
        if isinstance(document, list):
            for list_items in document:
                _change_index(
                    document=list_items, new_index=new_index
                )
        elif isinstance(document, dict):
            for dict_key, dict_value in document.items():
                if dict_key == 'index':
                    document['index'] = new_index
                elif dict_key == 'type' and 'args-value: ' in dict_value:
                    document['type'] = 'args-value: {}'.replace("{}", str(new_index))
                    break
                elif dict_key == 'type' and 'button: ' in dict_value:
                    document['type'] = 'button: {}'.replace("{}", str(new_index))
                _change_index(
                    document=dict_value, new_index=new_index
                )
        return document

    return _change_index(document=document, new_index=new_index)


# ************************************************DATA SIDE MENU******************************************************

# get DATA side-menu
def get_data_menu(tile):
    """
    :param tile: Index of the created data side-menu.
    :return: Default layout of a data side-menu with index values matching the specified tile index.
    """
    children = [
        html.Div([
            html.H6(
                "{}:".format('Hierarchy'),
                style={'color': CLR['text1'], 'margin-top': '5px', 'display': 'inline-block'}),
            html.A(
                className='boxclose',
                style={'position': 'relative', 'left': '20px'},
                id={'type': 'data-menu-close', 'index': tile}),
            get_hierarchy_layout(tile),
            get_date_picker(tile)
        ], style={'width': '260px', 'height': '100%', 'margin-left': '20px', 'margin-right': '20px', 'padding': '0'})
    ]
    return children


# ********************************************************LAYOUT*****************************************************

# Page layout for UI
def get_layout():
    """
    :return: Layout of app's UI.
    """
    return html.Div([
        # decorative red header bar at top
        html.Header(
            style={'background-color': CLR['background1'], 'height': '5px', 'position': 'fixed', 'width': '100%',
                   'z-index': '99', 'top': '0'}
        ),
        # grid
        html.Div([
            # master nav bar
            html.Div([
                html.Button(
                    className='master-nav',
                    n_clicks=1,
                    children=get_label('New'),
                    id='button-new',
                    disabled=True)
            ], style={'border-bottom': '1px solid {}'.format(CLR['lightgray']), 'margin-top': '5px',
                      'z-index': '99', 'width': '100%', 'top': '0',
                      'background-color': CLR['white']},
                id='button-new-wrapper'),
            html.Div([
                html.Div([
                    # data side menu divs
                    html.Div(get_data_menu(0), id={'type': 'data-tile', 'index': 0}, style=DATA_CONTENT_HIDE),
                    html.Div(get_data_menu(1), id={'type': 'data-tile', 'index': 1}, style=DATA_CONTENT_HIDE),
                    html.Div(get_data_menu(2), id={'type': 'data-tile', 'index': 2}, style=DATA_CONTENT_HIDE),
                    html.Div(get_data_menu(3), id={'type': 'data-tile', 'index': 3}, style=DATA_CONTENT_HIDE),
                    html.Div(get_data_menu(4), id={'type': 'data-tile', 'index': 4}, style=DATA_CONTENT_HIDE),
                    # div wrapper for body content
                    html.Div([
                        # body div
                        html.Div(
                            [],
                            id='div-body',
                            style={'overflow-x': 'hidden', 'overflow-y': 'hidden'},
                            className='graph-container')],
                        id='div-body-wrapper',
                        className='div-body-wrapper flex-div-body-wrapper')
                ], className='flex-container graph-container',
                    # To show footer: calc(100vh - 56px)
                    # To hide footer: calc(100vh - 41px)
                    style={'max-height': 'calc(100vh - 41px)'})
            ], style={'flex-grow': '1'})
            # To show footer: calc(100vh - 15px)
            # To hide footer: calc(100vh)
        ], style={'display': 'flex', 'flex-direction': 'column', 'height': 'calc(100vh)', 'overflow': 'hidden'}),
        # footer
        html.Footer(
            style={'border-top': '1px solid {}'.format(CLR['lightgray']), 'height': '15px', 'position': 'fixed',
                   'z-index': '99', 'width': '100%', 'background-color': CLR['white']}),
        # hidden components to trigger callbacks:
        # tile-closed-trigger stores index of deleted tile
        html.Div(
            id='tile-closed-trigger',
            style={'display': 'none'}),
    ], style={'background-color': CLR['lightpink']})


# ****************************************************TILE LAYOUT****************************************************

# create default tile
def get_tile(tile):
    """
    :param tile: Index of the created tile.
    :return: New tile with index values matching the specified tile index.
    """
    children = [html.Div([
        # flex
        html.Div([
            html.Header([
                dcc.Input(
                    id={'type': 'tile-title', 'index': tile},
                    placeholder=get_label('Enter Graph Title'),
                    value='',
                    style={'height': '30px', 'display': 'inline-block', 'margin': '0 0 0 10px',
                           'border': '0', 'border-bottom': '1px solid #bbb', 'border-radius': '0', 'font-size': '13px',
                           'text-align': 'center', 'background-color': 'transparent', 'padding': '0'}),
                html.Button(
                    [get_label('View')],
                    id={'type': 'tile-view', 'index': tile},
                    className='tile-nav-selected',
                    n_clicks=0),
                dcc.Store(
                    id={'type': 'tile-view-store', 'index': tile}),
                html.Button(
                    [get_label('Customize')],
                    id={'type': 'tile-customize', 'index': tile},
                    className='tile-nav',
                    n_clicks=0),
                html.Button(
                    [get_label('Layouts')],
                    id={'type': 'tile-layouts', 'index': tile},
                    className='save-nav',
                    style={'width': '80px'}),
                html.Button(
                    [get_label('Data')],
                    id={'type': 'tile-data', 'index': tile},
                    className='static-tile-nav'),
                html.I(
                    className='fa fa-link',
                    id={'type': 'tile-link', 'index': tile},
                    style={'position': 'relative'}),
                html.A(
                    className='boxclose',
                    id={'type': 'tile-close', 'index': tile})
            ], style={'width': '100%', 'display': 'inline-block', 'height': 'auto', 'z-index': '1'}),
            html.Div(
                style=VIEW_CONTENT_SHOW,
                id={'type': 'tile-view-content', 'index': tile},
                className='fill-container',
                children=[
                    html.Div(
                        children=[],
                        id={'type': 'graph_display', 'index': tile},
                        className='fill-container')]),
            html.Div([
                html.P(
                    "{}:".format('Graph Type'),
                    style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'graph-type-dropdown', 'index': tile},
                        clearable=False,
                        options=[{'label': get_label(i), 'value': i} for i in GRAPH_OPTIONS], value=GRAPH_OPTIONS[0],
                        style={'max-width': '400px', 'width': '100%', 'font-size': '13px'})
                ], style={'margin-left': '15px'}),
                html.Div(
                    id={'type': 'div-graph-options', 'index': tile})
            ], style=CUSTOMIZE_CONTENT_HIDE,
                id={'type': 'tile-customize-content', 'index': tile},
                className='customize-content'),
            html.Div([
                html.P(get_label('Save a layout'), style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div(
                    id={'type': 'save-div', 'index': tile},
                    children=[
                        html.Button(id={'type': 'save-button', 'index': tile},
                                    n_clicks=0,
                                    children='Save Selection',
                                    style={'display': 'center'}),

                    ], style={'width': '400px'}),
                # have this so it is always displaying a message, make sure nothing is preventing this in the callback
                html.Div(id={'type': 'save-message', 'index': tile}),
                html.P(get_label('Select a saved layout'),
                       style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div(
                    id={'type': 'select-layout-dropdown-div', 'index': tile},
                    children=[
                        dcc.Dropdown(id={'type': 'select-layout-dropdown', 'index': tile},
                                     options=[{
                                         'label': key, 'value': key} for key in saved_layouts
                                     ],
                                     clearable=False,
                                     style={'width': '400px', 'font-size': '13px'},
                                     value='',
                                     )
                    ], style={'width': '400px'}),
                html.P(get_label('Delete a saved layout'),
                       style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div(
                    id={'type': 'delete-layout-dropdown-div', 'index': tile},
                    children=[
                        dcc.Dropdown(id={'type': 'delete-layout-dropdown', 'index': tile},
                                     options=[{
                                         'label': key, 'value': key} for key in saved_layouts
                                     ],
                                     style={'width': '400px', 'font-size': '13px'},
                                     value='',
                                     )
                    ], style={'width': '400px'}),
            ], style=LAYOUT_CONTENT_HIDE, id={'type': 'tile-layouts-content', 'index': tile},
                className='customize-content')
        ], style={'flex-direction': 'column'},
            className='flex-container fill-container')
    ], className='tile-container',
        id={'type': 'tile', 'index': tile},
        style={'z-index': '{}'.replace("{}", str(tile))})]
    return children


# arrange tiles on the page for 1-4 tiles
def get_tile_layout(num_tiles, input_tiles):
    """
    :param num_tiles: Desired number of tiles to display.
    :param input_tiles: List of children of existing tiles.
    :raise IndexError: If num_tiles < 0 or num_tiles > 4
    :return: Layout of specified number of tiles.
    """

    tile = [None, None, None, None]

    # for each case, prioritize reusing existing input_tiles, otherwise create default tiles where needed
    if num_tiles == 0:
        children = []

    elif num_tiles == 1:
        if input_tiles:
            tile[0] = [
                html.Div(
                    children=input_tiles[0],
                    className='tile-container',
                    id={'type': 'tile', 'index': 0}, style={'z-index': '0'})]
        else:
            tile[0] = get_tile(0)
        children = [
            html.Div([
                html.Div(
                    children=tile[0],
                    style={'grid-row': '1', 'grid-column': '1', '-ms-grid-row': '1', '-ms-grid-column': '1'})],
                className='grid-container fill-container',
                style={'grid-template-rows': '100%', 'grid-template-columns': '100%',
                       '-ms-grid-rows': '100%', '-ms-grid-columns': '100%'})]

    elif num_tiles == 2:
        if input_tiles:
            for i in range(len(input_tiles)):
                tile[i] = [
                    html.Div(
                        children=input_tiles[i],
                        className='tile-container',
                        id={'type': 'tile', 'index': i},
                        style={'z-index': '{}'.replace("{}", str(i))})]
            for i in range(len(input_tiles), num_tiles):
                tile[i] = get_tile(i)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i)
        children = [
            html.Div([
                html.Div(
                    children=tile[0],
                    style={'grid-row': '1', 'grid-column': '1', '-ms-grid-row': '1', '-ms-grid-column': '1'}),
                html.Div(
                    children=tile[1],
                    style={'border-left': '1px solid {}'.format(CLR['lightergray']),
                           'grid-row': '1', 'grid-column': '2', '-ms-grid-row': '1', '-ms-grid-column': '2'})
            ], className='grid-container fill-container',
                style={'grid-template-rows': '100%', 'grid-template-columns': '50% 50%',
                       '-ms-grid-rows': '100%', '-ms-grid-columns': '50% 50%'})]

    elif num_tiles == 3:
        if input_tiles:
            for i in range(len(input_tiles)):
                tile[i] = [
                    html.Div(
                        children=input_tiles[i],
                        className='tile-container',
                        id={'type': 'tile', 'index': i},
                        style={'z-index': '{}'.replace("{}", str(i))})]
            for i in range(len(input_tiles), num_tiles):
                tile[i] = get_tile(i)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i)
        children = [
            html.Div([
                html.Div(
                    children=tile[0],
                    style={'grid-row': '1', 'grid-column': '1', '-ms-grid-row': '1', '-ms-grid-column': '1'}),
                html.Div(
                    children=tile[1],
                    style={'border-left': '1px solid {}'.format(CLR['lightergray']),
                           'grid-row': '1', 'grid-column': '2', '-ms-grid-row': '1', '-ms-grid-column': '2'}),
                html.Div(
                    children=tile[2],
                    style={'border-top': '1px solid {}'.format(CLR['lightergray']), 'grid-row': '2',
                           'grid-column-start': '1', 'grid-column-end': '-1', '-ms-grid-row': '2',
                           '-ms-grid-column': '1', '-ms-grid-column-span': '2'})
            ], className='grid-container fill-container',
                style={'grid-template-rows': '50% 50%', 'grid-template-columns': '50% 50%',
                       '-ms-grid-rows': '50% 50%', '-ms-grid-columns': '50% 50%'})]

    elif num_tiles == 4:
        if input_tiles:
            for i in range(len(input_tiles)):
                tile[i] = [
                    html.Div(
                        children=input_tiles[i],
                        className='tile-container',
                        id={'type': 'tile', 'index': i},
                        style={'z-index': '{}'.replace("{}", str(i))})]
            for i in range(len(input_tiles), num_tiles):
                tile[i] = get_tile(i)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i)
        children = [
            html.Div([
                html.Div(
                    children=tile[0],
                    style={'grid-row': '1', 'grid-column': '1', '-ms-grid-row': '1', '-ms-grid-column': '1'}),
                html.Div(
                    children=tile[1],
                    style={'border-left': '1px solid {}'.format(CLR['lightergray']),
                           'grid-row': '1', 'grid-column': '2', '-ms-grid-row': '1', '-ms-grid-column': '2'}),
                html.Div(
                    children=tile[2],
                    style={'border-top': '1px solid {}'.format(CLR['lightergray']),
                           'grid-row': '2', 'grid-column': '1', '-ms-grid-row': '2', '-ms-grid-column': '1'}),
                html.Div(
                    children=tile[3],
                    style={'border-top': '1px solid {}'.format(CLR['lightergray']),
                           'border-left': '1px solid {}'.format(CLR['lightergray']),
                           'grid-row': '2', 'grid-column': '2', '-ms-grid-row': '2', '-ms-grid-column': '2'})
            ], className='grid-container fill-container',
                style={'grid-template-rows': '50% 50%', 'grid-template-columns': '50% 50%',
                       '-ms-grid-rows': '50% 50%', '-ms-grid-columns': '50% 50%'})]

    else:
        raise IndexError("The number of displayed tiles cannot exceed 4")

    return children


# ***************************************************GRAPH MENUS*****************************************************

# line graph menu layout
def get_line_graph_menu(tile, x, y, measure_type):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the line graph menu corresponds to.
    :return: Menu with options to modify a line graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables

    children = [
        html.P(
            "{}:".format(get_label('Graph Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('X-Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label(i), 'value': i} for i in X_AXIS_OPTIONS],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Y-Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[{'label': i, 'value': i} for i in MEASURE_TYPE_OPTIONS],
                        value=measure_type,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Graphed Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': i, 'value': i} for i in DATA_OPTIONS],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})])
        ], style={'margin-left': '15px'})
    ]
    return children


# bar graph menu layout
def get_bar_graph_menu(tile, x, y, measure_type):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the bar graph menu corresponds to.
    :return: Menu with options to modify a bar graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables

    # BAR_X_AXIS_OPTIONS = X_AXIS_OPTIONS + ['Variable Names']
    bar_group_options = ['Specific Item', 'Variable Names']

    children = [
        html.P(
            "{}:".format(get_label('Graph Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Group By')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label(i), 'value': i} for i in bar_group_options],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Y-Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[{'label': i, 'value': i} for i in MEASURE_TYPE_OPTIONS],
                        value=measure_type,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Graphed Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': i, 'value': i} for i in DATA_OPTIONS],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})])
        ], style={'margin-left': '15px'})
    ]
    return children


# scatter graph menu layout
def get_scatter_graph_menu(tile, x, y, measure_type):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the scatter graph menu corresponds to.
    :return: Menu with options to modify a scatter graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables

    children = [
        html.P(
            "{}:".format(get_label('Graph Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('X-Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label(i), 'value': i} for i in X_AXIS_OPTIONS],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Y-Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[{'label': i, 'value': i} for i in MEASURE_TYPE_OPTIONS],
                        value=measure_type,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Graphed Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': i, 'value': i} for i in DATA_OPTIONS],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})])
        ], style={'margin-left': '15px'})
    ]
    return children


# box plot menu layout
def get_box_plot_menu(tile, axis_measure, graphed_variables, graph_orientation):
    # (args-value: {})[0] = graphed variables
    # (args-value: {})[1] = measure type
    # (args-value: {})[2] = points toggle
    # (args-value: {})[3] = orientation

    children = [
        html.P(
            "{}:".format(get_label('Graph Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Axis Measure')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': i, 'value': i} for i in MEASURE_TYPE_OPTIONS],
                        value=axis_measure,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Graphed Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[{'label': i, 'value': i} for i in DATA_OPTIONS],
                        value=graphed_variables,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('Graph Orientation')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': get_label(i), 'value': i} for i in ['Vertical', 'Horizontal']],
                        value=graph_orientation,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            dcc.Checklist(
                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                options=[{'label': get_label('Show Data Points'), 'value': 'show'}])
        ], style={'margin-left': '15px'})]
    return children


# table menu layout
def get_table_graph_menu(tile, number_of_columns):
    """
    :param number_of_columns: The number of columns to display
    :param tile: Index of the tile the table instructions corresponds to.
    :return: Text instructions for how user can interact with table.
    """
    # (args-value: {})[0] = tile index
    children = [
        html.Div([
            # id is used by create_graph callback to verify that the table menu is created before it activates
            dcc.Dropdown(
                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                options=[{'label': tile, 'value': tile}],
                value=tile,
                clearable=False,
                style={'display': 'none'}),
            # page_size for table
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('# of Rows')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '10px'}),
                html.Div([
                    dcc.Input(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        type="number",
                        value=number_of_columns,
                        min=10,
                        max=100,
                        style={'width': '80%', 'max-width': '350px'})],
                    style={'display': 'inline-block'})]),

            html.P(
                "{}:".format(get_label('How to Filter the Table')),
                style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
            html.Div([
                dcc.Markdown(
                    '''
                     - Type a search term into the '...' row at the top of
                     the data-table to filter for matching entries within that column
                     - Use comparison operators for more precise numerical filtering,
                     for example: > 80, = 2019, < 200
                    ''' if LANGUAGE == 'en' else
                    '''
                    - Tapez un terme de recherche dans la ligne '' ... ''
                    en haut du tableau de données pour filtrer les entrées correspondantes
                    dans cette colonne
                    - Utilisez des opérateurs de comparaison pour un filtrage numérique plus 
                    précis, par exemple:> 80, = 2019, < 200
                    ''')],
                style={'margin-left': '15px'}),
            html.P(
                "{}:".format(get_label('How to Hide Columns')),
                style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
            html.Div([
                dcc.Markdown(
                    '''
                     - Columns that have no data are not displayed 
                     - To hide a column click on the eye icon beside the column header
                     - To display hidden columns enable them within the 'TOGGLE COLUMNS' menu
                    ''' if LANGUAGE == 'en' else
                    '''
                    - Les colonnes sans données ne sont pas affichées
                    - Pour masquer une colonne, cliquez sur l'icône en forme d'œil à côté de
                    l'en-tête de la colonne
                    - Pour afficher les colonnes cachées, activez-les dans le menu 'BASCULER LES COLONNES'
                    ''')],
                style={'margin-left': '15px'}),
        ], style={'font-size': '13px'})
    ]
    return children
