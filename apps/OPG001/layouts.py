######################################################################################################################
"""
layouts.py

stores all layouts excluding hierarchy filter layout
"""
######################################################################################################################

# External Packages
import inspect
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from flask import session
import json
import logging

# Internal Modules
import config
from conn import get_conn
# from apps.OPG001.app import app
from apps.OPG001.data import GRAPH_OPTIONS, CLR, DATA_CONTENT_HIDE, VIEW_CONTENT_SHOW, BAR_X_AXIS_OPTIONS, \
    CUSTOMIZE_CONTENT_HIDE, X_AXIS_OPTIONS, get_label, LAYOUT_CONTENT_HIDE, \
    saved_layouts, saved_dashboards
from apps.OPG001.hierarchy_filter import get_hierarchy_layout
from apps.OPG001.datepicker import get_date_picker
from apps.OPG001.graphs import __update_graph


# Contents:
#   HELPER FUNCTION(S)
#       - change_index()
#       - recursive_to_plotly_json()
#   DATA SIDE MENU
#       - get_data_set_picker()
#       - get_data_menu()
#   LAYOUT
#       - get_layout()
#   TAB LAYOUT
#       - get_default_tab_content()
#   DASHBOARD LAYOUT
#       - get_layout()
#       - get_layout_graph()
#       - get_layout_dashboard()
#   TILE LAYOUT
#       - get_tile()
#       - get_tile_layout()
#   GRAPH MENUS
#       - get_line_graph_menu()
#       - get_bar_graph_menu()
#       - get_scatter_graph_menu()
#       - get_table_graph_menu()
#       - get_sankey_menu()


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


def recursive_to_plotly_json(document):
    document = document.to_plotly_json()
    inspect.getmembers(html, inspect.isclass)
    html_classes = tuple(x[1] for x in inspect.getmembers(html, inspect.isclass))
    dcc_classes = tuple(x[1] for x in inspect.getmembers(dcc, inspect.isclass))

    def _recursive_to_plotly_json(inner_document):
        if isinstance(inner_document, list):
            i = 0
            for list_items in inner_document:
                if isinstance(list_items, (html_classes, dcc_classes)):
                    list_items = list_items.to_plotly_json()
                    inner_document[i] = list_items
                _recursive_to_plotly_json(
                    inner_document=list_items
                )
                i += 1
        elif isinstance(inner_document, dict):
            for dict_key, dict_value in inner_document.items():
                if isinstance(dict_value, (html_classes, dcc_classes)):
                    dict_value = dict_value.to_plotly_json()
                    inner_document[dict_key] = dict_value
                _recursive_to_plotly_json(
                    inner_document=dict_value
                )

        return inner_document

    return _recursive_to_plotly_json(inner_document=document)


# ************************************************DATA SIDE MENU******************************************************


# get Data set picker for data menu
def get_data_set_picker(tile, df_name):
    """
    :param tile: Index of the created data side-menu.
    :return: Drop down of the possible data sets.
    """
    return [
        html.H6(
            "{}:".format(get_label('LBL_Data_Set')),
            style={'color': CLR['text1'], 'margin-top': '25px', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id={'type': 'data-set', 'index': tile},
                options=[{'label': get_label(i,'Data_Set'), 'value': i} for i in session['dataset_list']],
                value=df_name,
                clearable=False,
                style={'flex-grow': '1'}),
            html.Div(
                html.Div([
                    html.I(
                        html.Span(
                            get_label("LBL_Refresh_Data_Set"),
                            className='save-symbols-tooltip'),
                        id={'type': 'confirm-load-data', 'index': tile},
                        className='fa fa-check',
                        style=DATA_CONTENT_HIDE),
                    html.I(
                        html.Span(
                            get_label("LBL_Confirm_Data_Set_Load"),
                            className='save-symbols-tooltip'),
                        id={'type': 'confirm-data-set-refresh', 'index': tile},
                        className='fa fa-refresh',
                        style=DATA_CONTENT_HIDE)],
                    id='dataset-confirmation-symbols'),
                style={'display': 'inline-block', 'height': '35px', 'margin-left': '20px', 'text-align': 'center',
                       'position': 'relative', 'vertical-align': 'top', 'background-color': 'white', 'width': '40px',
                       'border': '1px solid {}'.format(CLR['lightgray']), 'border-radius': '6px'})],
            style={'display': 'flex'})
    ]


# get DATA side-menu
def get_data_menu(tile, df_name=None, mode='Default', hierarchy_toggle='Level Filter', level_value=None,
                  nid_path="root", graph_all_toggle=None, fiscal_toggle='Gregorian', input_method='all-time',
                  num_periods='5', period_type='last-years', df_const=None):
    # if df_name is None:
    #     df_name = session['dataset_list'][0]
    content = [
        html.A(
            className='boxclose',
            style={'position': 'relative', 'left': '3px'},
            id={'type': 'data-menu-close', 'index': tile}),
        dcc.Loading([
        html.Div(get_data_set_picker(tile, df_name)),
        html.Div(
            get_hierarchy_layout(tile, df_name, hierarchy_toggle, level_value, graph_all_toggle, nid_path, df_const)),
        html.Div(get_date_picker(tile, df_name, fiscal_toggle, input_method, num_periods, period_type, df_const))])]

    dashboard_loading_wrapper = html.Div(
        content,
        id={'type': 'data-menu-tile-loading', 'index': tile})

    if mode == 'Default':
        return html.Div(
            dashboard_loading_wrapper,
            id={'type': 'data-menu-dashboard-loading', 'index': tile},
            style={'width': '260px', 'height': '100%', 'margin-left': '20px', 'margin-right': '20px',
                   'padding': '0'})

    elif mode == 'tile-loading':
        return content

    elif mode == 'dashboard-loading':
        return dashboard_loading_wrapper


# ****************************************************TAB LAYOUT******************************************************

# get div body
def get_div_body(num_tiles=1, input_tiles=None, tile_keys=None):
    return [
        # body div
        html.Div(
            get_tile_layout(num_tiles, input_tiles, tile_keys),
            id='div-body',
            style={'overflow-x': 'hidden', 'overflow-y': 'hidden'},
            className='graph-container')]


# default tab layout
def get_default_tab_content():
    return [
        # stores number of tiles for the tab
        html.Div(
            id='num-tiles',
            style={'display': 'none'},
            **{'data-num-tiles': 1}),
        # data side menu divs
        html.Div(get_data_menu(0), id={'type': 'data-tile', 'index': 0}, style=DATA_CONTENT_HIDE),
        html.Div(get_data_menu(1), id={'type': 'data-tile', 'index': 1}, style=DATA_CONTENT_HIDE),
        html.Div(get_data_menu(2), id={'type': 'data-tile', 'index': 2}, style=DATA_CONTENT_HIDE),
        html.Div(get_data_menu(3), id={'type': 'data-tile', 'index': 3}, style=DATA_CONTENT_HIDE),
        html.Div(get_data_menu(4), id={'type': 'data-tile', 'index': 4}, style=DATA_CONTENT_HIDE),
        # div wrapper for body content
        html.Div(
            get_div_body(),
            id='div-body-wrapper',
            className='flex-div-body-wrapper')]


# *************************************************DASHBOARD LAYOUT***************************************************

# Page layout for UI
# https://community.plotly.com/t/dash-on-multi-page-site-app-route-flask-to-dash/4582/11
def get_layout():
    return html.Div([dcc.Location(id='url', refresh=False),
                     html.Div(id='page-content')])


def get_layout_graph(report_name):

    conn = get_conn()
    query = """\
    declare @p_report_layout varchar(max)
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, 'Get', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], report_name)

    cursor = conn.cursor()
    cursor.execute(query)

    clob = cursor.fetchone()
    cursor.nextset()
    results = cursor.fetchone()

    if results.result_status != 'OK':
        cursor.close()
        del cursor
        logging.error(results.result_status)
        return PreventUpdate

    j = json.loads(clob.clob_text)

    graph_title = clob.ref_desc

    cursor.close()
    del cursor

    # generate state_of_display
    # {'props': {'children': 'Los Angeles Department of Water and Power'}}
    # split on ^||^, ignore 'root', append children
    state_of_display = ''
    nid_path = "root^||^Los Angeles Department of Water and Power".split('^||^')  # j['NID Path'].split('^||^') TODO: Find why this is hardcoded
    nid_path.remove('root')
    for x in nid_path:
        if state_of_display:
            state_of_display += ', '
        state_of_display += '"{}"'.format(x)  # "'{}'".format(x)

    if state_of_display:
        state_of_display = '{{"props": {{"children": {}}}}}'.format(
            state_of_display)  # "{{'props': {{'children': {}}}}}".format(state_of_display)

    graph = __update_graph(j['Data Set'],
                           j['Args List'],
                           j['Graph Type'],
                           graph_title,
                           j['Num Periods'],
                           j['Period Type'],
                           j['Hierarchy Toggle'],
                           j['Level Value'],
                           j['Graph All Toggle'],  # [],  # hierarchy_graph_children,
                           json.loads(state_of_display),  # state_of_display,
                           j.get('Date Tab'),  # None,  # secondary_type,
                           j['Timeframe'],
                           j['Fiscal Toggle'],
                           j.get('Start Year'),  # j['Start Year'],
                           j.get('End Year'),  # j['End Year'],
                           j.get('Start Secondary'),  # j['Start Secondary'],
                           j.get('End Secondary'),
                           j.get('df_const'))  # j['End Secondary'])

    if graph is None:
        raise PreventUpdate

    return html.Div(dcc.Loading([graph]))


# get the input box for the dashboard title
def get_dashboard_title_input(title=''):
    return dcc.Input(
        id='dashboard-title',
        placeholder=get_label('LBL_Enter_Dashboard_Title'),
        value=title,
        className='dashboard-title')


# defines entire dashboard layout
def get_layout_dashboard():
    """
    :return: Layout of app's UI.
    """
    return html.Div([
        # flex
        html.Div([
            # tabs
            html.Div([
                html.Div([
                    html.Div([
                        html.Button(
                            get_label("LBL_Tab"),
                            id={'type': 'dashboard-tab', 'index': 0},
                            className='dashboard-tab-button',
                            disabled=True),
                        html.Button(
                            "x",
                            id={'type': 'dashboard-tab-close', 'index': 0},
                            className='dashboard-tab-close-selected')],
                        className='dashboard-tab-selected')],
                    id='tab-header',
                    style={'display': 'inline-block', 'height': '30xp', 'flex-grow': '1'}),
                html.A(
                    className='boxadd',
                    id='tab-add')],
                id='tab-menu-header',
                style={'border-bottom': '1px solid {}'.format(CLR['lightgray']), 'z-index': '99', 'width': '100%',
                       'background-color': CLR['background1'], 'display': 'flex'}),
            # master nav bar
            html.Header([
                html.Div([
                    html.Button(
                        className='master-nav',
                        n_clicks=1,
                        children=get_label('LBL_New'),
                        id='button-new',
                        disabled=False)
                ], style={'display': 'inline-block'},
                    id='button-new-wrapper'),
                html.Button(
                    "Reset",
                    className='master-nav',
                    id='dashboard-reset',
                    style={'width': 'auto'}),
                html.Div(
                    html.Div([
                        html.I(
                            html.Span(
                                get_label("LBL_Reset_Dashboard_All_Unsaved_Changes_will_Be_Lost"),
                                className='save-symbols-tooltip'),
                            id='confirm-dashboard-reset',
                            className='fa fa-undo',
                            style={'padding': '7px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                                   'margin-right': '10px', 'margin-left': '7px', 'vertical-align': 'top'}),
                        html.Span([
                            html.I(
                                [],
                                className='fa fa-undo',
                                style={'position': 'absolute', 'left': '0', 'width': '15px'}),
                            html.I(
                                [],
                                className='fa fa-ban fa-2x',
                                style={'position': 'absolute', 'top': '50%', 'margin-left': '-13px', 'width': '26px',
                                       'margin-top': '-15px', 'color': CLR['background1']}),
                            html.Span(
                                get_label("LBL_Cancel_Reset_Attempt"),
                                className='save-symbols-tooltip')],
                            className='save-overwrite-symbols',
                            style={'padding': '7px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                                   'margin-left': '10px', 'margin-right': '14px', 'display': 'inline-block',
                                   'vertical-align': 'top'})],
                        id='dashboard-reset-symbols',
                        style={'width': '71px', 'border': '1px solid {}'.format(CLR['lightgray']), 'margin': '2px 0',
                               'border-radius': '6px', 'display': 'none'}),
                    style={'display': 'inline-block', 'height': '35px', 'margin-left': '20px', 'text-align': 'center',
                           'position': 'relative', 'vertical-align': 'top'}),
                html.Button(
                    className='master-nav',
                    n_clicks=1,
                    children=get_label('LBL_Confirm_Delete'),
                    style={'display': 'inline-block', 'float': 'right', 'width': 'auto', 'margin-right': '20px'},
                    id='confirm-delete-dashboard'),
                dcc.Dropdown(
                    id='delete-dashboard',
                    options=[{'label': saved_dashboards[key]['Dashboard Title'], 'value': key} for key in
                             saved_dashboards],
                    clearable=False,
                    style={'width': '250px', 'font-size': '13px', 'box-sizing': 'border-box', 'height': '35px',
                           'display': 'inline-block', 'vertical-align': 'bottom', 'float': 'right',
                           'border-radius': '0'},
                    value='',
                    placeholder=get_label('LBL_Delete_A_Saved_Dashboard')),
                dcc.Dropdown(
                    id='select-dashboard-dropdown',
                    options=[{'label': saved_dashboards[key]['Dashboard Title'], 'value': key} for key in
                             saved_dashboards],
                    clearable=False,
                    style={'width': '250px', 'font-size': '13px', 'box-sizing': 'border-box', 'height': '35px',
                           'display': 'inline-block', 'vertical-align': 'bottom', 'float': 'right',
                           'border-radius': '0', 'margin-left': '20px'},
                    value='',
                    placeholder=get_label('LBL_Select_A_Saved_Dashboard')),
                html.Div(
                    [],
                    id='dashboard-save-status-symbols',
                    style={'float': 'right', 'display': 'inline-block', 'height': '35px',
                           'margin-left': '20px', 'text-align': 'center'}),
                html.Button(
                    className='master-nav',
                    n_clicks=1,
                    children=get_label('LBL_Save_Dashboard'),
                    style={'display': 'inline-block', 'float': 'right', 'width': 'auto'},
                    id='button-save-dashboard'),
                html.Div(
                    get_dashboard_title_input(),
                    id='dashboard-title-wrapper',
                    style={'display': 'inline-block', 'float': 'right'})
            ], style={'border-bottom': '1px solid {}'.format(CLR['lightgray']),
                      'z-index': '99', 'width': '100%', 'top': '0',
                      'background-color': CLR['white']},
                id='button-save-dashboard-wrapper'),
            html.Div([
                # tab content
                html.Div([
                    html.Div(
                        get_default_tab_content(),
                        className='flex-container graph-container',
                        id='tab-content')],
                    className='flex-container graph-container',
                    id='tab-content-wrapper',
                    **{'data-active-tab': 0},
                    style={'max-height': 'calc(100vh - 68px)'}
                )
            ], style={'flex-grow': '1'})
            # To show footer: calc(100vh - 15px)
            # To hide footer: calc(100vh)
        ], style={'display': 'flex', 'flex-direction': 'column', 'height': 'calc(100vh - 15px)', 'overflow': 'hidden',
                  'border-bottom': '1px solid {}'.format(CLR['lightgray'])}),
        # dashboard-reset-trigger is used by NEW/DELETE to trigger MANAGE DATA SIDEMENUS to reset the data menus
        html.Div(
            id='dashboard-reset-trigger',
            style={'display': 'none'}),
        # select-range-trigger is used by the load callbacks to load the select range datepicker section
        html.Div(
            id={'type': 'select-range-trigger', 'index': 0},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'select-range-trigger', 'index': 1},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'select-range-trigger', 'index': 2},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'select-range-trigger', 'index': 3},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'select-range-trigger', 'index': 4},
            style={'display': 'none'}),
        # graph-menu-trigger is triggered by manage_sidemenus and triggers update_graph_menu. Represents a change in df.
        html.Div(
            id={'type': 'graph-menu-trigger', 'index': 0},
            **{'data-df_name': session['dataset_list'][0]},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'graph-menu-trigger', 'index': 1},
            **{'data-df_name': session['dataset_list'][0]},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'graph-menu-trigger', 'index': 2},
            **{'data-df_name': session['dataset_list'][0]},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'graph-menu-trigger', 'index': 3},
            **{'data-df_name': session['dataset_list'][0]},
            style={'display': 'none'}),
        # update-graph-trigger is triggered by update_graph_menu and triggers update_graph. Represents a change in df or
        # link state
        html.Div(
            id={'type': 'update-graph-trigger', 'index': 0},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'update-graph-trigger', 'index': 1},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'update-graph-trigger', 'index': 2},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'update-graph-trigger', 'index': 3},
            style={'display': 'none'}),
        # tile-closed-trigger stores index of deleted tile
        html.Div(
            id='tile-closed-trigger',
            style={'display': 'none'}),
        # tile-save-trigger-wrapper conditionally triggers the tile saving callback
        html.Div(
            id='tile-save-trigger-wrapper',
            style={'display': 'none'}),
        # reset-selected-layout-trigger resets the selected layout dropdown value to ''
        html.Div(
            id={'type': 'reset-selected-layout', 'index': 0},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'reset-selected-layout', 'index': 1},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'reset-selected-layout', 'index': 2},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'reset-selected-layout', 'index': 3},
            style={'display': 'none'}),
        # set-dropdown-options-trigger is used to detect when to update all 'select layout' dropdown options
        html.Div(
            id={'type': 'set-dropdown-options-trigger', 'index': 0},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-dropdown-options-trigger', 'index': 1},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-dropdown-options-trigger', 'index': 2},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-dropdown-options-trigger', 'index': 3},
            style={'display': 'none'}),
        # set-tile-title-trigger is used by the tile load callback and dashboard save callbacks to load the tile title
        html.Div(
            id={'type': 'set-tile-title-trigger', 'index': 0},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-tile-title-trigger', 'index': 1},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-tile-title-trigger', 'index': 2},
            style={'display': 'none'}),
        html.Div(
            id={'type': 'set-tile-title-trigger', 'index': 3},
            style={'display': 'none'}),
        # num-tile-2 / 3 / 4 temporarily store the number of tiles before they are inserted into the primary num-tiles
        html.Div(
            id='num-tiles-2',
            style={'display': 'none'},
            **{'data-num-tiles': 1}),
        html.Div(
            id='num-tiles-3',
            style={'display': 'none'},
            **{'data-num-tiles': 1}),
        html.Div(
            id='num-tiles-4',
            style={'display': 'none'},
            **{'data-num-tiles': 1}),
        # memory locations for tabs
        dcc.Store(
            id='tab-storage',
            storage_type='memory',
            data=[{'content': get_default_tab_content(), 'title': ''}]),
        # memory locations for dataframe constants
        dcc.Store(
            id='df-constants-storage',
            storage_type='memory',
            data=None)
    ], style={'background-color': CLR['lightpink']})


# ****************************************************TILE LAYOUT****************************************************

# create customize content
def get_customize_content(tile, graph_type, graph_menu):
    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Type')),
            style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
        html.Div(
            dcc.Dropdown(
                id={'type': 'graph-type-dropdown', 'index': tile},
                clearable=False,
                options=[{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in GRAPH_OPTIONS],
                value=graph_type,
                style={'max-width': '405px', 'width': '100%', 'font-size': '13px'}),
            style={'margin-left': '15px'}),
        html.Div(
            children=graph_menu,
            id={'type': 'div-graph-options', 'index': tile})]


# create default tile
def get_tile(tile, tile_keys=None, df_const=None):
    """
    :param tile: Index of the created tile.
    :return: New tile with index values matching the specified tile index.
    """
    return [html.Div([
        # flex container
        html.Div([
            html.Header([
                dcc.Input(
                    id={'type': 'tile-title', 'index': tile},
                    placeholder=get_label('LBL_Enter_Graph_Title'),
                    value=tile_keys['Tile Title'] if tile_keys else '',
                    className='tile-title'),
                html.Button(
                    [get_label('LBL_View')],
                    id={'type': 'tile-view', 'index': tile},
                    className='tile-nav tile-nav--view tile-nav--selected'),
                dcc.Store(
                    id={'type': 'tile-view-store', 'index': tile}),
                html.Button(
                    [get_label('LBL_Customize')],
                    id={'type': 'tile-customize', 'index': tile},
                    className='tile-nav tile-nav--customize'),
                html.Button(
                    [get_label('LBL_Graphs')],
                    id={'type': 'tile-layouts', 'index': tile},
                    className='tile-nav tile-nav--layout'),
                html.Button(
                    [get_label('LBL_Data')],
                    id={'type': 'tile-data', 'index': tile},
                    className='tile-nav tile-nav--data'),
                html.I(
                    className=tile_keys['Link'] if tile_keys else 'fa fa-link',
                    id={'type': 'tile-link', 'index': tile},
                    style={'position': 'relative'})],
                style={'margin-right': '25px'}),
            html.A(
                className='boxclose',
                id={'type': 'tile-close', 'index': tile},
                style={'position': 'absolute', 'right': '0', 'top': '0'}),
            html.Div(
                style=VIEW_CONTENT_SHOW,
                id={'type': 'tile-view-content', 'index': tile},
                className='fill-container',
                children=[
                    html.Div(
                        children=[],
                        id={'type': 'graph_display', 'index': tile},
                        className='fill-container')]),
            html.Div(
                tile_keys['Customize Content'] if tile_keys else get_customize_content(
                    tile=tile, graph_type='Line', graph_menu=get_line_graph_menu(
                        # tile, X_AXIS_OPTIONS[0], [LOADED_DFS[DATA_SETS[0]].VARIABLE_OPTIONS[0]['value']],
                        # LOADED_DFS[DATA_SETS[0]].MEASURE_TYPE_OPTIONS[0], DATA_SETS[0])),
                        # for now, since options may not exist in the data, just pass in blanks
                        # this will be changed later to be more robust
                        tile, '', '', '', session['dataset_list'][0], df_const=df_const)),
                style=CUSTOMIZE_CONTENT_HIDE,
                id={'type': 'tile-customize-content', 'index': tile},
                className='customize-content'),
            html.Div([  # TODO : style this to match customize menu and get rid of unnecessary divs
                html.P(get_label('LBL_Save_The_Graph'),
                       style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div([
                    html.Button(
                        id={'type': 'save-button', 'index': tile},
                        n_clicks=0,
                        children=get_label('LBL_Save_Graph'),
                        style={'display': 'inline-block'},
                        className='tile-save-button-{}'.format(str(tile))),
                    html.Div(
                        [],
                        id={'type': 'tile-save-status-symbols', 'index': tile},
                        style={'display': 'inline-block', 'height': '38px', 'text-align': 'center',
                               'margin-left': '20px', 'position': 'relative', 'vertical-align': 'top'})]),
                html.P(get_label('LBL_Select_A_Saved_Graph'),
                       style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div(
                    id={'type': 'select-layout-dropdown-div', 'index': tile},
                    children=[
                        dcc.Dropdown(id={'type': 'select-layout-dropdown', 'index': tile},
                                     options=[{'label': saved_layouts[key]['Title'], 'value': key} for key in
                                              saved_layouts],
                                     style={'width': '400px', 'font-size': '13px'},
                                     clearable=True,
                                     value='',
                                     placeholder='{}...'.format(get_label('LBL_Select')))
                    ], style={'width': '400px'}),
                html.P(get_label('LBL_Delete_A_Saved_Graph'),
                       style={'color': CLR['text1'], 'margin-top': '10px', 'font-size': '15px'}),
                html.Div([
                    html.Div(
                        id={'type': 'delete-layout-dropdown-div', 'index': tile},
                        children=[
                            dcc.Dropdown(id={'type': 'delete-layout-dropdown', 'index': tile},
                                         options=[{'label': saved_layouts[key]['Title'], 'value': key} for key in
                                                  saved_layouts],
                                         style={'width': '400px', 'font-size': '13px'},
                                         value='',
                                         placeholder='{}...'.format(get_label('LBL_Select')))
                        ], style={'width': '400px'}),
                    html.Button(
                        id={'type': 'confirm-delete-button', 'index': tile},
                        children=get_label('LBL_Confirm_Delete'),
                        n_clicks=0)
                ], style={'display': 'inline-block'})
            ], style=LAYOUT_CONTENT_HIDE, id={'type': 'tile-layouts-content', 'index': tile},
                className='customize-content')
        ], style={'flex-direction': 'column'},
            className='flex-container fill-container')
    ], className='tile-container',
        id={'type': 'tile', 'index': tile},
        style={'z-index': '{}'.replace("{}", str(tile))})]


# arrange tiles on the page for 1-4 tiles
def get_tile_layout(num_tiles, input_tiles, tile_keys=None, df_const=None):
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
        elif tile_keys:
            tile[0] = get_tile(0, tile_keys[0], df_const=df_const)
        else:
            tile[0] = get_tile(0, df_const=df_const)
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
                tile[i] = get_tile(i, df_const=df_const)
        elif tile_keys:
            for i in range(num_tiles):
                tile[i] = get_tile(i, tile_keys[i], df_const=df_const)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i, df_const=df_const)
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
                tile[i] = get_tile(i, df_const=df_const)
        elif tile_keys:
            for i in range(num_tiles):
                tile[i] = get_tile(i, tile_keys[i], df_const=df_const)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i, df_const=df_const)
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
                tile[i] = get_tile(i, df_const=df_const)
        elif tile_keys:
            for i in range(num_tiles):
                tile[i] = get_tile(i, tile_keys[i], df_const=df_const)
        else:
            for i in range(num_tiles):
                tile[i] = get_tile(i, df_const=df_const)
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
        raise IndexError("The number of displayed tiles cannot exceed 4, " + str(num_tiles) + " tiles were requested")

    return children


# ***************************************************GRAPH MENUS*****************************************************

# line graph menu layout
def get_line_graph_menu(tile, x, y, measure_type, df_name, df_const):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the line graph menu corresponds to.
    :param df_name: Name of the data set being used.
    :return: Menu with options to modify a line graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_X_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in
                                                             X_AXIS_OPTIONS],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        clearable=False,
                        value=measure_type,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})])
        ], style={'margin-left': '15px'})]


# bar graph menu layout
def get_bar_graph_menu(tile, x, y, measure_type, df_name, df_const):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the bar graph menu corresponds to.
    :param df_name: Name of the data set being used.
    :return: Menu with options to modify a bar graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables
    # (args-value: {})[3] = orientation
    # (args-value: {})[4] = animate graph

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Group_By')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in BAR_X_AXIS_OPTIONS],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=measure_type,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graph_Orientation')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                        options=[{'label': get_label('LBL_'+i), 'value': i} for i in ['Vertical', 'Horizontal']],
                        value='Vertical',
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            dcc.Checklist(
                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 4},
                options=[{'label': get_label('LBL_Animate_Over_Time'),
                          'value': 'animate'}],
                value=[],
                style={'color': 'black', 'width': '100%', 'display': 'inline-block'}),

        ], style={'margin-left': '15px'})]


# scatter graph menu layout
def get_scatter_graph_menu(tile, x, y, measure_type, df_name, df_const):
    """
    :param measure_type: the measure type value
    :param y: the y-axis value
    :param x: the x-axis value
    :param tile: Index of the tile the scatter graph menu corresponds to.
    :param df_name: Name of the data set being used.
    :return: Menu with options to modify a scatter graph.
    """
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = y-axis (measure type)
    # (args-value: {})[2] = graphed variables

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_X_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in X_AXIS_OPTIONS],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=measure_type,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=y,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})])
        ], style={'margin-left': '15px'})]


# bubble graph menu layout
def get_bubble_graph_menu(tile, x, x_measure, y, y_measure, size, size_measure, df_name, df_const):
    # (args-value: {})[0] = x-axis
    # (args-value: {})[1] = x-axis measure
    # (args-value: {})[2] = y-axis
    # (args-value: {})[3] = y-axis measure
    # (args-value: {})[4] = size
    # (args-value: {})[5] = size measure

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_X_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_X_Axis_Measure')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=x_measure,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=y,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Y_Axis_Measure')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=y_measure,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Size')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 4},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=size,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Size_Measure')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 5},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=size_measure,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
        ], style={'margin-left': '15px'})]


# box plot menu layout
def get_box_plot_menu(tile, axis_measure, graphed_variables, graph_orientation, df_name, show_data_points, df_const):
    # (args-value: {})[0] = graphed variables
    # (args-value: {})[1] = measure type
    # (args-value: {})[2] = points toggle
    # (args-value: {})[3] = orientation

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Axis_Measure')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else [{'label': i, 'value': i} for i in
                                                             df_const[df_name]['MEASURE_TYPE_OPTIONS']],
                        value=axis_measure,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '5px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=graphed_variables,
                        multi=True,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})]),
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graph_Orientation')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '70px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': get_label('LBL_'+i), 'value': i} for i in ['Vertical', 'Horizontal']],
                        value=graph_orientation,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '350px'})]),
            dcc.Checklist(
                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                options=[{'label': get_label('LBL_Show_Data_Points'), 'value': 'show'}],
                value=show_data_points)
        ], style={'margin-left': '15px'})]


# table menu layout
def get_table_graph_menu(tile, number_of_columns):
    """
    :param number_of_columns: The number of columns to display
    :param tile: Index of the tile the table instructions corresponds to.
    :return: Text instructions for how user can interact with table.
    """
    # (args-value: {})[0] = tile index
    language = session["language"]

    return [
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
                        "{}:".format(get_label('LBL_Num_Of_Rows')),
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
                "{}:".format(get_label('LBL_How_To_Filter_The_Table')),
                style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
            html.Div([
                dcc.Markdown(
                    '''
                     - Type a search term into the '...' row at the top of
                     the data-table to filter for matching entries within that column
                     - Use comparison operators for more precise numerical filtering,
                     for example: > 80, = 2019, < 200
                    ''' if language == 'En' else
                    '''
                    - Tapez un terme de recherche dans la ligne '' ... ''
                    en haut du tableau de données pour filtrer les entrées correspondantes
                    dans cette colonne
                    - Utilisez des opérateurs de comparaison pour un filtrage numérique plus 
                    précis, par exemple:> 80, = 2019, < 200
                    ''')],
                style={'margin-left': '15px'}),
            html.P(
                "{}:".format(get_label('LBL_How_To_Hide_Columns')),
                style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
            html.Div([
                dcc.Markdown(
                    '''
                     - Columns that have no data are not displayed 
                     - To hide a column click on the eye icon beside the column header
                     - To display hidden columns enable them within the 'TOGGLE COLUMNS' menu
                    ''' if language == 'En' else
                    '''
                    - Les colonnes sans données ne sont pas affichées
                    - Pour masquer une colonne, cliquez sur l'icône en forme d'œil à côté de
                    l'en-tête de la colonne
                    - Pour afficher les colonnes cachées, activez-les dans le menu 'BASCULER LES COLONNES'
                    ''')],
                style={'margin-left': '15px'}),
        ], style={'font-size': '13px'})]


# sankey menu layout
def get_sankey_menu(tile, graphed_options, df_name, df_const):
    """
    :param tile: Index of the tile the line graph menu corresponds to.
    :param graphed_options: the variable name
    :param df_name: Name of the data set being used.
    :return: Menu with options to modify a sankey graph.
    """
    # (args-value: {})[0] = graphed variables

    return [
        html.P(
            "{}:".format(get_label('LBL_Graph_Options')),
            style={'margin-top': '10px', 'color': CLR['text1'], 'font-size': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        style={'color': CLR['text1'], 'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '60px', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                html.Div([
                    dcc.Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'],
                        value=graphed_options,
                        multi=False,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '80%', 'max-width': '330px'})])
        ], style={'margin-left': '15px'})]
