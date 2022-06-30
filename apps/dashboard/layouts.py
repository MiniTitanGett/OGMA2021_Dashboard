######################################################################################################################
"""
layouts.py

Stores all layouts excluding hierarchy filter layout.
"""
######################################################################################################################

# External Packages
import inspect
import dash_core_components as dcc
from dash_core_components import Store, Dropdown, RadioItems, Location, Markdown, Checklist
import dash_html_components as html
from dash_html_components import Div, Button, P, Header, H6, I, Span, A, Img
import visdcc as visdcc
from dash.exceptions import PreventUpdate
from flask import session
import json
import dash_bootstrap_components as dbc
import dash_responsive_grid_layout as drgl

# Internal Modules
from conn import exec_storedproc_results
from apps.dashboard.data import GRAPH_OPTIONS, DATA_CONTENT_SHOW, DATA_CONTENT_HIDE, VIEW_CONTENT_SHOW, \
    BAR_X_AXIS_OPTIONS, CUSTOMIZE_CONTENT_HIDE, X_AXIS_OPTIONS, get_label, LAYOUT_CONTENT_HIDE, LAYOUTS, \
    dataset_to_df, generate_constants, COLOR_PALETTE
from apps.dashboard.hierarchy_filter import get_hierarchy_layout
from apps.dashboard.secondary_hierarchy_filter import get_secondary_hierarchy_layout
from apps.dashboard.datepicker import get_date_picker
from apps.dashboard.graphs import __update_graph


# ********************************************HELPER FUNCTION(S)******************************************************


def change_index(doc, index):
    """Change index numbers of all id's within tile or data side-menu."""

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

    return _change_index(document=doc, new_index=index)


# TODO: No usages
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


def get_data_set_picker(tile, df_name, confirm_parent, prev_selection, time_period="last-month",  prev_time=None,
                        session_key=None):
    """Returns data set picker for data menu."""
    return [
        Div(
            children=[
                H6(
                    "{}:".format(get_label('LBL_Data_Set')),
                    className='data-set'),
                I(
                    Span(
                        get_label("LBL_Data_Set_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'data-set-info', 'index': tile},
                    style={'position': 'relative'})],
            id={'type': 'data-set-info-wrapper', 'index': tile}),
        Div([
            dcc.Input(
                id={'type': 'data-set-parent', 'index': tile},
                type="text",
                value=confirm_parent,
                style={'display': 'None'},
                debounce=True)],
            style={'display': 'None'}),
        Div([
            Dropdown(
                id={'type': 'data-set', 'index': tile},
                options=[{'label': get_label(i, 'Data_Set'), 'value': i} for i in session['dataset_list']],
                optionHeight=30,
                value=df_name,
                clearable=False,
                style={'flex-grow': '1'}),
            Store(
                data=prev_selection,
                id={'type': 'data-set-prev-selected', 'index': tile}),
            Store(
                data=prev_time,
                id={'type': 'prev-time-period', 'index': tile}),
            Div(
                Div([
                    I(
                        Span(
                            get_label("LBL_Confirm_Data_Set_Load"),
                            className='save-symbols-tooltip'),
                        id={'type': 'confirm-load-data', 'index': tile},
                        className='fa fa-check',
                        style=DATA_CONTENT_HIDE if df_name is None or session_key in session else
                        {'padding': '10px 0', 'cursor': 'pointer', 'width': '15px', 'height': '15px',
                         'position': 'relative', 'margin-right': '10px', 'margin-left': '10px',
                         'vertical-align': 'top'}),
                    I(
                        Span(
                            get_label("LBL_Refresh_Data_Set"),
                            className='save-symbols-tooltip'),
                        id={'type': 'confirm-data-set-refresh', 'index': tile},
                        className='fa fa-refresh',
                        style={'padding': '10px 0', 'cursor': 'pointer', 'width': '15px', 'height': '15px',
                               'position': 'relative', 'margin-right': '10px', 'margin-left': '10px',
                               'vertical-align': 'top'} if df_name is not None and session_key in session else
                        DATA_CONTENT_HIDE)],
                    id='dataset-confirmation-symbols'),
                className='data-set-load-box'),
        ],
            style={'display': 'flex'}),
        Div([
            P("Time Slice: ",
              style={'display': 'inline-block', 'position': 'relative', 'padding-top': '15px'}),
            Div([
                Dropdown(
                    id={'type': 'time-period', 'index': tile},
                    options=[
                        {'label': get_label('LBL_Currently_Active'),
                         'value': 'current-Active'},
                        {'label': get_label('LBL_Last_Month'),
                         'value': 'last-month'},
                        {'label': get_label('LBL_Last_Quarter'),
                         'value': 'last-quarter'},
                        {'label': get_label('LBL_Last_Year'),
                         'value': 'last-year'},
                        {'label': get_label('LBL_All_Time_Monthly'),
                         'value': 'all-time'}
                    ],
                    value=time_period,
                    clearable=False,
                    style={'width': '140px', 'height': '26px', 'margin': '0', 'padding': '0px', 'font-size': '15px',
                           'text-align': 'left', 'border-radius': '5px', 'color': '#333', 'max-height': '26px'}),
            ], style={"display": "inline-block", 'padding': '10px', 'position': 'absolute'}),
        ], style={"display": "inline-block"} if df_name is not None else
            DATA_CONTENT_HIDE, id={'type': 'time-slice-controls', 'index': tile}),
        Div([
            P("No Data Available",
              style={'display': 'inline-block', 'align' 'position': 'relative', 'padding-top': '15px',
                     'font-weight': 'bold'}),
        ], style={'display': 'inline-block', 'text-align': 'center', 'min-width': '260px'} if session_key not in session
                                                                                              and df_name is not None
        else DATA_CONTENT_HIDE, id={'type': 'no-data-info', 'index': tile}),
    ]


def get_data_menu(tile, df_name=None, mode='Default', hierarchy_toggle='Level Filter', level_value='H0',
                  nid_path="root", graph_all_toggle=None, fiscal_toggle='Gregorian', input_method='all-time',
                  num_periods='5', period_type='last-years', prev_selection=None, time_period='last-month',
                  prev_time=None, confirm_parent=None, df_const=None, session_key=None):
    """Returns the data side-menu."""
    content = [
        A(
            className='boxclose',
            style={'position': 'relative', 'left': '3px'},
            id={'type': 'data-menu-close', 'index': tile}),
        Div(get_data_set_picker(tile, df_name, confirm_parent, prev_selection, time_period, prev_time, session_key)),
        Div([
            Div(
                get_hierarchy_layout(tile, df_name, hierarchy_toggle, level_value, graph_all_toggle, nid_path,
                                     df_const, session_key)),
            Div(get_date_picker(tile, df_name, fiscal_toggle, input_method, num_periods, period_type, df_const,
                                session_key))],
            style=DATA_CONTENT_HIDE,
            id={'type': 'data-menu-controls', 'index': tile})]

    dashboard_loading_wrapper = Div(
        content,
        id={'type': 'data-menu-tile-loading', 'index': tile})

    if mode == 'Default':
        return Div(
            dashboard_loading_wrapper,
            id={'type': 'data-menu-dashboard-loading', 'index': tile},
            style={'width': '260px', 'height': '100%', 'margin-left': '20px', 'margin-right': '20px',
                   'padding': '0'})
    elif mode == 'tile-loading':
        return content
    elif mode == 'dashboard-loading':
        return dashboard_loading_wrapper


# ****************************************************TAB LAYOUT******************************************************


def get_div_body(num_tiles=1, tile_keys=None, layout=LAYOUTS[0]):
    """Returns the div body."""
    cols = {'lg': 24}
    breakpoints = {'lg': 1200}
    if num_tiles == 1 and tile_keys is None:
        children = get_tile(0, df_name=None)
    else:
        children = get_tile_layout(num_tiles, tile_keys)
    return [
        # body div
        drgl.ResponsiveGridLayout(
            children=children,
            useCSSTransforms=True,
            id='div-body',
            cols=cols,
            rowHeight=40,
            layouts=layout,
            breakpoints=breakpoints,
            draggableHandle='.dragbar')
    ]


def get_default_tab_content():
    """Returns the default tab layout."""
    return [
        # stores number of tiles for the tab
        Div(
            id='num-tiles',
            style={'display': 'none'},
            **{'data-num-tiles': 1}),
        # data side menu divs
        Div(get_data_menu(0), id={'type': 'data-tile', 'index': 0}, style=DATA_CONTENT_HIDE),
        Div(get_data_menu(1), id={'type': 'data-tile', 'index': 1}, style=DATA_CONTENT_HIDE),
        Div(get_data_menu(2), id={'type': 'data-tile', 'index': 2}, style=DATA_CONTENT_HIDE),
        Div(get_data_menu(3), id={'type': 'data-tile', 'index': 3}, style=DATA_CONTENT_HIDE),
        Div(get_data_menu(4), id={'type': 'data-tile', 'index': 4}, style=DATA_CONTENT_SHOW),
        # div wrapper for body content
        Div(
            get_div_body(),
            id='div-body-wrapper',
            className='flex-div-body-wrapper')]


# *************************************************DASHBOARD LAYOUT***************************************************


# https://community.plotly.com/t/dash-on-multi-page-site-app-route-flask-to-dash/4582/11
def get_layout():
    """Page layout for UI."""
    return Div([Location(id='url', refresh=False),
                     Div(id='page-content')])


def get_layout_graph(report_name):
    """Returns the graph loaded from database."""
    query = """\
    declare @p_report_layout varchar(max)
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_extdashboardreports {}, 'Get', \'{}\', null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(session['sessionID'], report_name)

    results = exec_storedproc_results(query)

    j = json.loads(results["clob_text"].iloc[0])

    graph_title = results["ref_desc"].iloc[0]
    """
    conn = get_conn()
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
    """
    # generate state_of_display
    # {'props': {'children': 'Los Angeles Department of Water and Power'}}
    state_of_display = ''
    # split on ^||^, ignore 'root', append children
    nid_path = j['NID Path'].split('^||^')

    nid_path.remove('root')  # remove root from nid path list
    # create a json array containing dictionarys
    for x in nid_path:
        if state_of_display:
            state_of_display += ', '
        state_of_display += '{{"props": {{"children": "{}"}}}}'.format(
            x)  # "{{'props': {{'children': {}}}}}".format(state_of_display)

    state_of_display = "[{}]".format(state_of_display)

    secondary_state_of_display = ''
    # split on ^||^, ignore 'root', append children
    secondary_nid_path = j.get('Graph Variable')[1].split('^||^')

    secondary_nid_path.remove('root')  # remove root from nid path list
    # create a json array containing dictionarys
    for x in secondary_nid_path:
        if secondary_state_of_display:
            secondary_state_of_display += ', '
        secondary_state_of_display += '{{"props": {{"children": "{}"}}}}'.format(
            x)  # "{{'props': {{'children': {}}}}}".format(secondary_state_of_display)
    secondary_state_of_display = "[{}]".format(secondary_state_of_display)

    # load data (added for external access)
    session[j['Data Set']] = dataset_to_df(j['Data Set'])
    df_const = {j['Data Set']: generate_constants(j['Data Set'])}

    graph = __update_graph(j['Data Set'],
                           j['Args List'],
                           j['Graph Type'],
                           graph_title,
                           j['Num Periods'],
                           j['Period Type'],
                           j['Hierarchy Toggle'],
                           j['Level Value'],
                           j['Graph All Toggle'],  # [],  # hierarchy_graph_children,
                           True,  # hierarchy_options - just pass a non-None value
                           json.loads(state_of_display),  # state_of_display,
                           j.get('Date Tab'),  # None,  # secondary_type,
                           j['Timeframe'],
                           j['Fiscal Toggle'],
                           j.get('Start Year'),  # j['Start Year'],
                           j.get('End Year'),  # j['End Year'],
                           j.get('Start Secondary'),  # j['Start Secondary'],
                           j.get('End Secondary'),  # j['End Secondary']
                           df_const,
                           j.get('Graph Options')[0],  # xtitle
                           j.get('Graph Options')[1],  # ytitle
                           j.get('Graph Options')[2],  # xlegpos
                           j.get('Graph Options')[3],  # ylegpos
                           j.get('Graph Options')[6],  # gridline
                           j.get('Graph Options')[7],  # legend
                           j.get('Graph Variable')[0],  # secondary_hierarchy_level
                           json.loads(secondary_state_of_display),  # secondary_hierarchy_nid_path
                           j.get('Graph Variable')[2],  # secondary_hierarchy_toggle
                           j.get('Graph Variable')[3],  # secondary_hierarchy_graph_all
                           j.get('Graph Variable')[4])  # secondary_hierarchy_option

    if graph is None:
        raise PreventUpdate

    return graph


def get_dashboard_title_input(title=''):
    """Returns the input box for the dashboard title."""
    return dcc.Input(
        id='dashboard-title',
        placeholder=get_label('LBL_Enter_Dashboard_Title'),
        value=title,
        className='dashboard-title',
        debounce=True)


def get_layout_dashboard():
    """Returns layout of app's UI."""
    return Div([
        # flex
        Div([
            # tabs
            Div([
                Div([
                    Div([
                        Button(
                            get_label("LBL_Tab"),
                            id={'type': 'dashboard-tab', 'index': 0},
                            className='dashboard-tab-button',
                            disabled=True),
                        Button(
                            "x",
                            id={'type': 'dashboard-tab-close', 'index': 0},
                            className='dashboard-tab-close-selected')],
                        className='dashboard-tab-selected')],
                    id='tab-header',
                    style={'display': 'inline-block', 'height': '30xp', 'flex-grow': '1'}),
                A(
                    className='boxadd',
                    id='tab-add')],
                id='tab-menu-header',
                className='dashboard-header'),
            # parent nav bar
            Header([
                Div([
                    Button(
                        className='parent-nav',
                        n_clicks=1,
                        children=get_label('LBL_Add_Tile'),
                        id='button-new',
                        disabled=False)
                ], style={'display': 'inline-block'},
                    id='button-new-wrapper'),
                Button(
                    get_label("LBL_Reset"),
                    className='parent-nav',
                    id='dashboard-reset',
                    style={'width': 'auto'}),
                Button(
                    className='parent-nav',
                    n_clicks=1,
                    children=get_label('LBL_Delete'),
                    style={'display': 'inline-block', 'float': 'right', 'width': 'auto', 'margin-right': '20px'},
                    id='delete-dashboard'),
                Button(
                    className='parent-nav',
                    n_clicks=1,
                    children=get_label('LBL_Load_Dashboard'),
                    style={'display': 'inline-block', 'float': 'right', 'width': 'auto', 'margin-right': '20px'},
                    id='load-dashboard'),
                Button(
                    className='parent-nav',
                    n_clicks=1,
                    children=get_label('LBL_Save_Dashboard'),
                    style={'display': 'inline-block', 'float': 'right', 'width': 'auto'},
                    id='save-dashboard'),
                Div(
                    get_dashboard_title_input(),
                    id='dashboard-title-wrapper',
                    style={'display': 'inline-block', 'float': 'right'}),
                Div([
                    P(get_label('LBL_Load_A_Saved_Dashboard'),
                           className='.prompt-title'),
                    Div(
                        children=[
                            Dropdown(
                                id='select-dashboard-dropdown',
                                options=[{'label': session['saved_dashboards'][key]['Dashboard Title'], 'value': key}
                                         for key in
                                         session['saved_dashboards']],
                                clearable=False,
                                style={'width': '400px', 'font-size': '13px'},
                                value='',
                                placeholder='{}...'.format(get_label('LBL_Select'))),
                        ], style={'width': '400px'}),
                    P(get_label('LBL_Load_Dashboard_Prompt'),
                           id={'type': 'tile-layouts-warning', 'index': 4},
                           className='prompt-title')],
                    id='load-dashboard-menu',
                    style={'display': 'none'}
                    )], className='dashboard-parent-nav-bar',
                id='button-save-dashboard-wrapper'),
            Div([
                # tab content
                Div([
                    Div(
                        get_default_tab_content(),
                        className='flex-container graph-container',
                        id='tab-content')],
                    className='flex-container graph-container',
                    id='tab-content-wrapper',
                    **{'data-active-tab': 0},
                    style={'max-height': 'calc(100vh - 68px)'},),

                Div([
                    Store(id={'type': 'tab-swap-flag',  'index': 0}, data=False),
                    Store(id={'type': 'tab-swap-flag',  'index': 1}, data=False),
                    Store(id={'type': 'tab-swap-flag',  'index': 2}, data=False),
                    Store(id={'type': 'tab-swap-flag',  'index': 3}, data=False)],
                    id='tab-swap-flag-wrapper'),

            ], style={'flex-grow': '1'})
            # To show footer: calc(100vh - 15px)
            # To hide footer: calc(100vh)
        ], className='dashboard-layout'),
        # Prompt
        Div(
            Div([
                Div([
                    H6(
                        'Empty Title',
                        id='prompt-title'
                    ),
                    A(
                        className='boxclose',
                        id='prompt-close',
                        style={'position': 'absolute', 'right': '16px', 'top': '8px'})],
                    className='prompt-header'),
                Div([
                    Div('Empty Text', id='prompt-body'),
                    Div([
                        Button(
                            get_label('LBL_Cancel'),
                            id='prompt-cancel',
                            style={'margin-right': '16px', 'width': '80px'}),
                        Button(
                            get_label('LBL_OK'),
                            id='prompt-ok',
                            style={'width': '80px'})],
                        className='prompt-button-wrapper',
                        id='prompt-button-wrapper-duo'),
                    Div([
                        Button(
                            get_label('LBL_Cancel'),
                            id='prompt-option-1',
                            style={'margin-bottom': '16px'}),
                        Button(
                            get_label('LBL_Continue_And_Unlink_My_Graphs'),
                            id='prompt-option-2',
                            style={'margin-bottom': '16px'}),
                        Button(
                            get_label('LBL_Continue_And_Modify_My_Graphs_As_Necessary'),
                            id='prompt-option-3',
                            style={})],
                        className='prompt-button-wrapper-vertical',
                        id='prompt-button-wrapper-trip',
                        style={'display': 'none'})],
                    style={'padding': '24px'})],
                id='prompt-box',
                className='prompt-box'),
            style=DATA_CONTENT_HIDE,
            id='prompt-obscure',
            className='prompt-obscure'
        ),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 0}),  # tile 0
            id={'type': 'prompt-trigger-wrapper', 'index': 0}),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 1}),  # tile 1
            id={'type': 'prompt-trigger-wrapper', 'index': 1}),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 2}),  # tile 2
            id={'type': 'prompt-trigger-wrapper', 'index': 2}),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 3}),  # tile 3
            id={'type': 'prompt-trigger-wrapper', 'index': 3}),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 4}),  # dashboard
            id={'type': 'prompt-trigger-wrapper', 'index': 4}),
        Div(
            Store(id={'type': 'prompt-trigger', 'index': 5}),  # sidemenus
            id={'type': 'prompt-trigger-wrapper', 'index': 5}),
        # separated result stores for specific callback chains
        Store(id={'type': 'prompt-result', 'index': 0}),  # _manage_tile_save_load_trigger() callback
        Store(id={'type': 'prompt-result', 'index': 1}),  # _manage_dashboard_saves_and_reset() callback
        Store(id={'type': 'prompt-result', 'index': 2}),  # _manage_data_sidemenus() callback
        # Floating Menu
        Div(
            Div([
                Div([
                    H6(
                        'Empty Title',
                        id='float-menu-title'
                    ),
                    A(
                        className='boxclose',
                        id='float-menu-close',
                        style={'position': 'absolute', 'right': '16px', 'top': '8px'})],
                    className='prompt-header'),
                Div([
                    Div(id='float-menu-body', style={'display': 'flex', 'min-height': '200px'}),
                    Div([
                        Button(
                            get_label('LBL_Cancel'),
                            id='float-menu-cancel',
                            style={'margin-right': '16px', 'width': '80px'}),
                        Button(
                            get_label('LBL_OK'),
                            id='float-menu-ok',
                            style={'width': '80px'})],
                        className='prompt-button-wrapper')],
                    style={'padding': '24px'})],
                id='float-menu-box',
                className='float-menu-box'),
            style=DATA_CONTENT_HIDE,
            id='float-menu-obscure',
            className='prompt-obscure'),
        Div(
            Store(id={'type': 'float-menu-trigger', 'index': 0}),  # tile 0
            id={'type': 'float-menu-trigger-wrapper', 'index': 0}),
        Div(
            Store(id={'type': 'float-menu-trigger', 'index': 1}),  # tile 1
            id={'type': 'float-menu-trigger-wrapper', 'index': 1}),
        Div(
            Store(id={'type': 'float-menu-trigger', 'index': 2}),  # tile 2
            id={'type': 'float-menu-trigger-wrapper', 'index': 2}),
        Div(
            Store(id={'type': 'float-menu-trigger', 'index': 3}),  # tile 3
            id={'type': 'float-menu-trigger-wrapper', 'index': 3}),
        Div(
            Store(id={'type': 'float-menu-trigger', 'index': 4}),  # linked tiles
            id={'type': 'float-menu-trigger-wrapper', 'index': 4}),
        # separated result stores for specific callback chains
        Store(id={'type': 'float-menu-result', 'index': 0}),  # _manage_tile_save_load_trigger() callback
        Store(id={'type': 'float-menu-result', 'index': 1}),  # _manage_dashboard_saves_and_reset() callback
        Store(id={'type': 'float-menu-result', 'index': 2}),  # _serve_float_menu_and_take_result() callback
        # Popups
        dbc.Alert(
            'Your Tile Has Been Saved',
            id={'type': 'minor-popup', 'index': 0},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '50%', 'top': '80%', 'margin-right': '-100px', 'z-index': '500'},
            duration=4000),
        dbc.Alert(
            'Your Tile Has Been Saved',
            id={'type': 'minor-popup', 'index': 1},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '50%', 'top': '80%', 'margin-right': '-100px', 'z-index': '500'},
            duration=4000),
        dbc.Alert(
            'Your Tile Has Been Saved',
            id={'type': 'minor-popup', 'index': 2},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '50%', 'top': '80%', 'margin-right': '-100px', 'z-index': '500'},
            duration=4000),
        dbc.Alert(
            'Your Tile Has Been Saved',
            id={'type': 'minor-popup', 'index': 3},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '50%', 'top': '80%', 'margin-right': '-100px', 'z-index': '500'},
            duration=4000),
        dbc.Alert(
            'Your Tile Has Been Saved',
            id={'type': 'minor-popup', 'index': 4},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '50%', 'top': '80%', 'margin-right': '-100px', 'z-index': '500'},
            duration=4000),
        dbc.Alert(
            'Your Axes Label May Not Reflect The Graphs',
            id={'type': 'axes-popup', 'index': 0},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Your Axes Label May Not Reflect The Graphs',
            id={'type': 'axes-popup', 'index': 1},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Your Axes Label May Not Reflect The Graphs',
            id={'type': 'axes-popup', 'index': 2},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Your Axes Labels May Not Reflect The Graphs',
            id={'type': 'axes-popup', 'index': 3},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),

        Store(id={'type': 'data-fitting-trigger', 'index': 0}),  # tile 0


        Store(id={'type': 'data-fitting-trigger', 'index': 1}),  # tile 1


        Store(id={'type': 'data-fitting-trigger', 'index': 2}),  # tile 2


        Store(id={'type': 'data-fitting-trigger', 'index': 3}),  # tile 3

        dbc.Alert(
            'Auto Un-Checking Data Fitting Options',
            id={'type': 'fitting-popup', 'index': 0},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Auto Un-Checking Data Fitting Options',
            id={'type': 'fitting-popup', 'index': 1},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Auto Un-Checking Data Fitting Options',
            id={'type': 'fitting-popup', 'index': 2},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Auto Un-Checking Data Fitting Options',
            id={'type': 'fitting-popup', 'index': 3},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'Auto Un-Checking Data Fitting Options',
            id={'type': 'parent-fitting-popup', 'index': 4},
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '47%', 'top': '80%', 'margin-right': '-100px', 'z-index': '1070'},
            duration=4000),
        dbc.Alert(
            'No data available',
            id='no-data-popup',
            is_open=False,
            color='dark',
            style={'position': 'absolute', 'right': '48%', 'top': '80%', 'z-index': '500'},
            duration=4000),


        Div([
            Store(id={'type': 'data-set-result', 'index': 0}, data=False),
            Store(id={'type': 'data-set-result', 'index': 1}, data=False),
            Store(id={'type': 'data-set-result', 'index': 2}, data=False),
            Store(id={'type': 'data-set-result', 'index': 3}, data=False)],
            id='data-set-result-wrapper'),

        # dashboard-reset-confirmation is used by the prompts to reset the viewport
        Store(id='dashboard-reset-confirmation'),
        # javascript visdcc object for running the javascript required to handle plotly_relayout events
        visdcc.Run_js(id={'type': 'javascript', 'index': 0}),
        visdcc.Run_js(id={'type': 'javascript', 'index': 1}),
        visdcc.Run_js(id={'type': 'javascript', 'index': 2}),
        visdcc.Run_js(id={'type': 'javascript', 'index': 3}),
        # select-range-trigger is used by the load callbacks to load the select range datepicker section
        Store(id={'type': 'select-range-trigger', 'index': 0}),
        Store(id={'type': 'select-range-trigger', 'index': 1}),
        Store(id={'type': 'select-range-trigger', 'index': 2}),
        Store(id={'type': 'select-range-trigger', 'index': 3}),
        Store(id={'type': 'select-range-trigger', 'index': 4}),
        # graph-menu-trigger is triggered by manage_sidemenus and triggers update_graph_menu. Represents a change in df.
        Store(
            id={'type': 'graph-menu-trigger', 'index': 0},
            data={'df_name': session['dataset_list'][0]}),
        Store(
            id={'type': 'graph-menu-trigger', 'index': 1},
            data={'df_name': session['dataset_list'][0]}),
        Store(
            id={'type': 'graph-menu-trigger', 'index': 2},
            data={'df_name': session['dataset_list'][0]}),
        Store(
            id={'type': 'graph-menu-trigger', 'index': 3},
            data={'df_name': session['dataset_list'][0]}),
        # update-graph-trigger is triggered by update_graph_menu and triggers update_graph. Represents a change in df or
        # link state
        Store(id={'type': 'update-graph-trigger', 'index': 0}),
        Store(id={'type': 'update-graph-trigger', 'index': 1}),
        Store(id={'type': 'update-graph-trigger', 'index': 2}),
        Store(id={'type': 'update-graph-trigger', 'index': 3}),
        # tile-closed-trigger stores index of deleted tile
        Store(id='tile-closed-trigger'),
        Store(id='tile-closed-input-trigger'),
        # tile-save-trigger conditionally triggers the tile saving callback, wrapper is used to reduce load times
        Div(
            [Store(id={'type': 'tile-save-trigger', 'index': 0}),
             Store(id={'type': 'tile-save-trigger', 'index': 1}),
             Store(id={'type': 'tile-save-trigger', 'index': 2}),
             Store(id={'type': 'tile-save-trigger', 'index': 3})],
            style={'display': 'none'},
            id='tile-save-trigger-wrapper'
        ),
        # reset-selected-layout-trigger resets the selected layout dropdown value to ''
        Store(id={'type': 'reset-selected-layout', 'index': 0}),
        Store(id={'type': 'reset-selected-layout', 'index': 1}),
        Store(id={'type': 'reset-selected-layout', 'index': 2}),
        Store(id={'type': 'reset-selected-layout', 'index': 3}),
        # set-graph-options-trigger is used by the _manage_data_sidemenus callback to load graph options based on
        # the selected dataset
        Store(id={'type': 'set-graph-options-trigger', 'index': 0}),
        Store(id={'type': 'set-graph-options-trigger', 'index': 1}),
        Store(id={'type': 'set-graph-options-trigger', 'index': 2}),
        Store(id={'type': 'set-graph-options-trigger', 'index': 3}),
        # set-dropdown-options-trigger is used to detect when to update all 'select layout' dropdown options
        Store(id={'type': 'set-dropdown-options-trigger', 'index': 0}),
        Store(id={'type': 'set-dropdown-options-trigger', 'index': 1}),
        Store(id={'type': 'set-dropdown-options-trigger', 'index': 2}),
        Store(id={'type': 'set-dropdown-options-trigger', 'index': 3}),
        # set-tile-title-trigger is used by the tile load callback and dashboard save callbacks to load the tile title
        Store(id={'type': 'set-tile-title-trigger', 'index': 0}),
        Store(id={'type': 'set-tile-title-trigger', 'index': 1}),
        Store(id={'type': 'set-tile-title-trigger', 'index': 2}),
        Store(id={'type': 'set-tile-title-trigger', 'index': 3}),
        # set-tile-link-trigger is used by the update graph options callback to trigger the link update callback
        Store(id={'type': 'set-tile-link-trigger', 'index': 0}),
        Store(id={'type': 'set-tile-link-trigger', 'index': 1}),
        Store(id={'type': 'set-tile-link-trigger', 'index': 2}),
        Store(id={'type': 'set-tile-link-trigger', 'index': 3}),
        # num-tile-2 / 3 / 4 temporarily store the number of tiles before they are inserted into the primary num-tiles
        Store(
            id='num-tiles-2',
            data={'num-tiles': 1}),
        Store(
            id='num-tiles-3',
            data={'num-tiles': 1}),
        Store(
            id='num-tiles-4',
            data={'num-tiles': 1}),
        # memory locations for tabs
        Store(
            id='tab-storage',
            storage_type='memory',
            data=[{'content': get_default_tab_content(), 'title': ''}]),
        # memory locations for dataframe constants and its triggers
        Div(
            Div(
                Div(
                    Div(
                        Div(
                            Store(
                                id='df-constants-storage',
                                storage_type='memory',
                                data=None),
                            id={'type': 'df-constants-storage-tile-wrapper', 'index': 0}),
                        id={'type': 'df-constants-storage-tile-wrapper', 'index': 1}),
                    id={'type': 'df-constants-storage-tile-wrapper', 'index': 2}),
                id={'type': 'df-constants-storage-tile-wrapper', 'index': 3}),
            id='df-constants-storage-dashboard-wrapper')
    ], className='dashboard-layout-color')

# ****************************************************TILE LAYOUT****************************************************


# create a new edit menu when a new tile is added
def get_customize_content(tile, graph_type, graph_menu, df_name):
    """Returns customize content."""
    graphs = []
    # check if keyword is in df_name
    if df_name is not None:
        if 'OPG010' in df_name:
            graphs = GRAPH_OPTIONS['OPG010']
        elif 'OPG011' in df_name:
            graphs = GRAPH_OPTIONS['OPG011']
    graphs.sort()
    options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graphs]

    return [
        Div(
            id={'type': 'div-customize-warning-message', 'index': tile},
            children=[
                Markdown(
                    get_label("LBL_Please_Select_A_Data_Set_To_View_Customization_Options")
                )],
            style={'margin-left': '15px'} if df_name is None else
            DATA_CONTENT_HIDE),
        Div(
            id={'type': 'div-graph-type', 'index': tile},
            children=[
                Div(
                    children=[
                        P(
                            "{}:".format(get_label('LBL_Graph_Type')),
                            className='graph-type'),
                        I(
                            Span(
                                get_label("LBL_Graph_Type_Info"),
                                className='save-symbols-tooltip'),
                            className='fa fa-question-circle-o',
                            id={'type': 'graph-type-info', 'index': tile},
                            style={'position': 'relative'})],
                    id={'type': 'graph-type-info-wrapper', 'index': tile}),
                Div(
                    Dropdown(
                        id={'type': 'graph-type-dropdown', 'index': tile},
                        clearable=False,
                        optionHeight=30,
                        options=[{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graphs],
                        value=graph_type if graph_type is not None else options[0]['value'] if len(options) != 0 else
                        None,  # graph_type,
                        style={'max-width': '405px', 'width': '100%', 'font-size': '13px'}),
                    style={'margin-left': '15px'},
                ),
                Div(
                    dcc.Input(
                        id={'type': 'previous-graph-type', 'index': tile},
                        type="text",
                        value=None,
                        style={'display': 'None'},
                        debounce=True),),
            ],
            style=DATA_CONTENT_HIDE if df_name is None else
            {}),
        Div(
            children=graph_menu if df_name else empty_graph_menu(tile),
            id={'type': 'div-graph-options', 'index': tile})]


# adds a tile to the dashboard
def get_tile(tile, tile_keys=None, df_name=None):
    """
    :param tile: Index of the created tile
    :param tile_keys: Holds information regarding tile values
    :param df_name: Name of the data set being used.
    :return: New default tile with index values matching the specified tile index
    """
    return Div(
        Div([
            # flex container
            Div([
                Div([
                    dcc.Input(
                        id={'type': 'tile-title', 'index': tile},
                        placeholder=get_label('LBL_Enter_Graph_Title'),
                        value=tile_keys['Tile Title'] if tile_keys else '',
                        className='tile-title',
                        debounce=True),
                    Header([
                        Button(
                            [get_label('LBL_Graph')],
                            id={'type': 'tile-view', 'index': tile},
                            className='tile-nav tile-nav--view tile-nav--selected'),
                        Store(
                            id={'type': 'tile-view-store', 'index': tile}),
                        Button(
                            [get_label('LBL_Edit')],
                            id={'type': 'tile-customize', 'index': tile},
                            className='tile-nav tile-nav--customize'),
                        Button(
                            [get_label('LBL_Save')],
                            id={'type': 'save-button', 'index': tile},
                            n_clicks=0,
                            className='tile-nav tile-nav--save'),
                        Button(
                            [get_label('LBL_Load')],
                            id={'type': 'tile-layouts', 'index': tile},
                            className='tile-nav tile-nav--layout'),
                        Button(
                            [get_label('LBL_Delete')],
                            id={'type': 'delete-button', 'index': tile},
                            className='tile-nav tile-nav--delete'),
                        Button(
                            [get_label('LBL_Data')],
                            id={'type': 'tile-data', 'index': tile},
                            className='tile-nav tile-nav--data')],
                        className='dragbar',
                        id={'type': 'tile-menu-header', 'index': tile},
                        style={'margin-right': '25px', 'flex-grow': '1'}),
                ], style={'display': 'flex'}),
                Div(
                    I(
                        className=tile_keys['Link'] if tile_keys else 'fa fa-link',
                        id={'type': 'tile-link', 'index': tile},
                        style={'position': 'relative'}),
                    className='dragbar',
                    id={'type': 'tile-link-wrapper', 'index': tile}),
                A(
                    className='boxclose',
                    id={'type': 'tile-close', 'index': tile},
                    style={'position': 'absolute', 'right': '0', 'top': '0'}),
                Div(
                    style=VIEW_CONTENT_SHOW,
                    id={'type': 'tile-view-content', 'index': tile},
                    className='fill-container',
                    children=[
                        Div(
                            children=[],
                            id={'type': 'graph_display', 'index': tile},
                            className='fill-container')]),
                Div(
                    Div(
                        tile_keys['Customize Content'] if tile_keys
                        else get_customize_content(tile=tile, graph_type=None, graph_menu=None, df_name=df_name),
                        style=CUSTOMIZE_CONTENT_HIDE,
                        id={'type': 'tile-customize-content', 'index': tile},
                        className='customize-content'),
                    id={'type': 'tile-customize-content-wrapper', 'index': tile},
                    className='customize-content'),
                Div([
                    P(get_label('LBL_Load_A_Saved_Graph'),
                           className='prompt-title'),
                    Div(
                        id={'type': 'select-layout-dropdown-div', 'index': tile},
                        children=[
                            Dropdown(id={'type': 'select-layout-dropdown', 'index': tile},
                                         options=[{'label': session['saved_layouts'][key]['Title'], 'value': key} for
                                                  key in
                                                  session['saved_layouts']],
                                         optionHeight=30,
                                         style={'width': '400px', 'font-size': '13px'},
                                         clearable=False,
                                         value='',
                                         placeholder='{}...'.format(get_label('LBL_Select'))),
                        ], style={'width': '400px'}),
                    P(get_label('LBL_Load_Graph_Prompt'),
                           id={'type': 'tile-layouts-warning', 'index': tile},
                           className='prompt-title'),
                ], style=LAYOUT_CONTENT_HIDE,
                    id={'type': 'tile-layouts-content', 'index': tile},
                    className='customize-content')
            ], style={'flex-direction': 'column'},
                id={'type': 'tile-body', 'index': tile},
                className='flex-container fill-container'),
            # used to prevent graph menu rebuilds on key built components
            # (Rebuild menu if set to True, Do not rebuild menu if False)
            Store(id={'type': 'tile-rebuild-menu-flag', 'index': tile},
                      data=tile_keys['Rebuild Menu'] if tile_keys else True),
        ], className='tile-container',
            id={'type': 'tile', 'index': tile}),
        className='fill-container',
        style={'border': '1px solid #c7c7c7'},
        id="tile-wrapper: " + str(tile))  # added to remove errors on responsive grid layout


# arrange tiles on the page for 1-4 tiles
def get_tile_layout(num_tiles, tile_keys=None, parent_df=None):
    """
    :param num_tiles: Desired number of tiles to display
    :param tile_keys: key info for building a tile
    :param parent_df: Name of the parent data set being used
    :raise IndexError: If num_tiles < 0 or num_tiles > 4
    :return: Layout of specified number of tiles.
    """
    # for each case, prioritize reusing existing input_tiles, otherwise create default tiles where needed
    if num_tiles == 0:
        children = []
    elif 5 > num_tiles:
        if tile_keys:
            # for i in range(num_tiles):
            #     tile.append(get_tile(i, tile_keys[i], df_name=parent_df))
            tile = [get_tile(i, tile_keys[i], df_name=parent_df) for i in range(num_tiles)]
        else:
            # for i in range(num_tiles):
            #     tile.append(get_tile(i, df_name=parent_df))
            tile = [get_tile(i, df_name=parent_df) for i in range(num_tiles)]
        children = tile

    else:
        raise IndexError("The number of displayed tiles cannot exceed 4, " + str(num_tiles) + " tiles were requested")
    return children


# ***************************************************GRAPH MENUS*****************************************************


def get_line_scatter_graph_menu(tile, x, mode, measure_type, df_name, gridline, legend, df_const, data_fitting, ci,
                                data_fit, degree, xaxis, yaxis, xpos, ypos, xmodified, ymodified, secondary_level_value,
                                secondary_nid_path, secondary_hierarchy_toggle, secondary_graph_all_toggle, color,
                                session_key):
    """
    :param data_fitting: boolean to determine whether to show data fitting options
    :param ci: show confidence interval or not
    :param measure_type: the measure type value
    :param x: the x-axis value
    :param mode: the mode for the graph
    :param tile: Index of the tile the line graph menu corresponds to
    :param df_name: Name of the data set being used
    :param gridline: Show gridline or not
    :param legend: Show legend or not
    :param df_const: Dataframe constants
    :param data_fit: data_fit value
    :param degree: degree value
    :param xaxis: the title of the xaxis
    :param yaxis: the title of the yaxis
    :param xpos: the x position of the legend
    :param ypos: the y position of the legend
    :param xmodified: the x title of the xaxis has been modified
    :param ymodified: the y of the yaxis title has been modified
    :param secondary_hierarchy_toggle: second hierarchy filter either specific or level
    :param secondary_level_value: level of secondary hierarchy
    :param secondary_graph_all_toggle: graph all option of hierarchy item
    :param secondary_nid_path: the path of secondary specific hierarchy
    :param color: the color palette of the graph
    :return: Menu with options to modify a line graph
    """
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = mode
    # arg_value[3] = fit
    # arg_value[4] = degree
    # arg_value[5] = confidence interval
    # arg_value[6] = color

    return [
        Div(
            children=[
                P(
                    "{}:".format(get_label('LBL_Graph_Options')),
                    className='graph-type'),
                I(
                    Span(
                        get_label("LBL_Graph_Options_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'graph-options-info', 'index': tile},
                    style={'position': 'relative'})
            ],
            id={'type': 'graph-options-info-wrapper', 'index': tile}
        ),
        Div([
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_X_Axis')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'margin-right': '102px', 'width': '80%', 'max-width': '50px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else [{'label': get_label('LBL_' + i.replace(' ', '_')),
                                                              'value': i} for i in X_AXIS_OPTIONS],
                        value=x,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px', 'display': 'inline-block', 'width': '50px', 'position': 'relative',
                               'top': '-15px',
                               'margin-right': '5px'})
                ], style={'display': 'inline-block', 'max-width': '350px'}
                   if len(X_AXIS_OPTIONS) > 1 else {'display': 'None'}),
                Div([
                    P(
                        "{}".format(X_AXIS_OPTIONS[0]),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'max-width': '350px'}
                    if len(X_AXIS_OPTIONS) == 1 else {'display': 'None'}),
                Div([
                    Div([
                        P(
                            "{}:".format(get_label('LBL_Y_Axis')),
                            className='graph-option-title')],
                        style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                               'margin-right': '102px'}),
                    Div([
                        Dropdown(
                            id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                            options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"),
                                                                  'value': i} for i in df_const[session_key]
                            ['MEASURE_TYPE_OPTIONS']],
                            clearable=False,
                            optionHeight=30,
                            value=measure_type,
                            style={'font-size': '13px'})],
                        style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
                Div([
                    Div([
                        P(
                            "{}:".format(get_label('LBL_Display')),
                            className='graph-option-title')
                    ], style={'display': 'inline-block', 'width': '40px', 'position': 'relative', 'top': '-3px',
                              'margin-right': '107px'}),
                    Div([
                        RadioItems(
                            id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                            options=[{'label': get_label('LBL_Lines'), 'value': 'Line'},
                                     {'label': get_label('LBL_Points'), 'value': 'Scatter'},
                                     {'label': get_label('LBL_Lines_And_Points'), 'value': 'Lines and Points'}],
                            labelStyle={'display': 'inline-block'},
                            value=mode if mode else 'Lines',
                            style={'font-size': '13px'})],
                        style={'display': 'inline-block'})]),
                Div([
                    Div([
                        P(
                            "{}:".format(get_label('LBL_Data_Fitting')),
                            className='graph-option-title')
                    ], style={'display': 'inline-block', 'position': 'relative', 'vertical-align': 'top'}),
                    I(
                        Span(
                            children=get_label("LBL_Data_Fitting_Shown_Info") if data_fitting else
                            get_label("LBL_Data_Fitting_Hidden_Info"),
                            className='save-symbols-tooltip'
                        ),
                        className='fa fa-question-circle-o',
                        id={'type': 'data-fitting-info', 'index': tile},
                        style={'position': 'relative', 'vertical-align': 'top', 'padding-top': '4px'}),

                    Div(
                        id={'type': 'data-fitting-wrapper', 'index': tile},
                        children=[
                            RadioItems(
                                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                                options=[{'label': get_label('LBL_No_Fit'), 'value': 'no-fit'},
                                         {'label': get_label('LBL_Linear_Fit'), 'value': 'linear-fit'},
                                         {'label': get_label('LBL_Curve_Fit'), 'value': 'curve-fit'}],
                                labelStyle={'display': "inline-block"},
                                value=data_fit if data_fit else 'no-fit',
                                style={'display': 'inline-block', 'font-size': '13px'}),
                            Div([
                                P(["Degree: "], style={'padding-left': '5px', 'display': 'inline-block',
                                                                                                'font-size': '13px'}),
                                Div(
                                    children=Div([
                                        dcc.Input(
                                            id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 4},
                                            value=degree if degree else 3,
                                            type='number',
                                            required=True,
                                            min=1,
                                            style={'width': '45px', 'height': '29px', 'margin': '0', 'padding': '0',
                                                   'font-size': '15px',
                                                   'text-align': 'center', 'padding-top': '3px', 'border-radius': '5px',
                                                   'color': '#333', 'max-height': '26px'})
                                    ], style={'display': 'inline-block', 'top': '-10px', 'padding-left': '5px'}),
                                )
                            ], style={'display': 'None'}, id={'type': 'degree-input-wrapper', 'index': tile}),
                            Div([
                                P([get_label('LBL_Confidence_Interval')+": "], style={'padding-left': '3px',
                                                                    'font-size': '13px', 'display': 'inline-block'}),
                                Div(
                                    children=Checklist(
                                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 5},
                                        options=[{'label': 'Yes', 'value': 'ci'}],
                                        value=ci if ci else [],
                                        style={'color': 'black', 'display': 'inline-block'}),
                                    style={'display': 'inline-flex'}),
                            ], style={'display': 'None'}, id={'type': 'confidence-interval-wrapper', 'index': tile}),
                        ],
                        style={'display': 'inline-block'} if data_fitting else DATA_CONTENT_HIDE),
                ]),
                Div([
                    Div([
                        P(
                            "{}:".format(get_label('LBL_Graphed_Variables')),
                            className='graph-option-title')],
                        style={'display': 'inline-block', 'position': 'relative', 'top': '-5px',
                               'margin-right': '40px'}),
                    Div(
                        get_secondary_hierarchy_layout(tile, df_name, secondary_hierarchy_toggle, secondary_level_value,
                                                  secondary_graph_all_toggle, secondary_nid_path, df_const=df_const,
                                                       session_key=session_key),
                        style={'display': 'inline-flex', 'flex-direction': 'column', 'max-width': '330px'}
                        if df_name == 'OPG011' else {'display': 'None'})], style={'margin-bottom': '7.5px'}),
                Div([
                    Div([
                        P(
                            "{}:".format('Color Palette'),
                            className='graph-option-title')],
                        style={'display': 'inline-block', 'position': 'relative', 'top': '-3px'}),
                    I(
                        Span(
                            Img(src="http://127.0.0.1:8080/python/dashboard/assets/color-palette.png"),
                            className='save-symbols-tooltip'),
                        className='fa fa-question-circle-o',
                        id={'type': 'color-palette-info', 'index': tile},
                        style={'position': 'relative', 'display': 'inline-block'}),
                    Div([
                        RadioItems(
                            id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 6},
                            options=[{'label': i, 'value': i} for i in COLOR_PALETTE],
                            labelStyle={'display': 'inline-block'},
                            value=color if color else 'G10',
                            style={'font-size': '13px', 'margin-left': '40px'})],
                        style={'display': 'inline-flex', 'max-width': '290px'})
                ]),
                Div(
                    Div(
                        children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                           xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                           gridline=gridline, legend=legend, graph_type='Line'),
                        id={'type': 'default-graph-options', 'index': tile}),
                    id={'type': 'default-graph-options-wrapper', 'index': tile})
            ], style={'margin-left': '15px'})]), ]


def get_bar_graph_menu(tile, x, measure_type, orientation, animate, gridline, legend, df_name, df_const, xaxis,
                       yaxis, xpos, ypos, xmodified, ymodified, secondary_level_value, secondary_nid_path,
                       secondary_hierarchy_toggle, secondary_graph_all_toggle, color, session_key):
    """
    :param tile: Index of the tile the bar graph menu corresponds to
    :param x: the x-axis value
    :param measure_type: the measure type value
    :param orientation: the orientation value
    :param animate: the animate graph value
    :param gridline: Show gridline or not
    :param legend: Show legend or not
    :param df_name: Name of the data set being used.
    :param df_const: Dataframe constants
    :param xaxis: the title of the xaxis
    :param yaxis: the title of the yaxis
    :param xpos: the x position of the legend
    :param ypos: the y position of the legend
    :param xmodified: the x title of the xaxis has been modified
    :param ymodified: the y of the yaxis title has been modified
    :param secondary_hierarchy_toggle: second hierarchy filter either specific or level
    :param secondary_level_value: level of secondary hierarchy
    :param secondary_graph_all_toggle: graph all option of hierarchy item
    :param secondary_nid_path: the path of secondary specific hierarchy
    :param color: the color palette of the graph
    :return: Menu with options to modify a bar graph
    """
    # args_value[0] = x-axis
    # args_value[1] = y-axis (measure type)
    # args_value[2] = orientation
    # args_value[3] = graphed variables
    # args_value[4] = animate graph
    # args_value[5] = color

    return [
        Div(
            children=[
                P(
                    "{}:".format(get_label('LBL_Graph_Options')),
                    className='graph-type'),
                I(
                    Span(
                        get_label("LBL_Graph_Options_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'graph-options-info', 'index': tile},
                    style={'position': 'relative'})
            ],
            id={'type': 'graph-options-info-wrapper', 'index': tile}
        ),
        Div([
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Group_By')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-15px',
                           'margin-right': '93px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in
                                 BAR_X_AXIS_OPTIONS],
                        optionHeight=30,
                        value=x,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '102px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"), 'value': i}
                                                             for i in df_const[session_key]['MEASURE_TYPE_OPTIONS']],
                        value=measure_type,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Graph_Orientation')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-3px',
                           'margin-right': '39px'}),
                Div([
                    RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[{'label': get_label('LBL_' + i), 'value': i} for i in ['Vertical', 'Horizontal']],
                        labelStyle={'display': 'inline-block'},
                        value=orientation if orientation else 'Vertical',
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-5px',
                           'margin-right': '40px'}),
                Div(
                    get_secondary_hierarchy_layout(tile, df_name, secondary_hierarchy_toggle, secondary_level_value,
                                                  secondary_graph_all_toggle, secondary_nid_path, df_const=df_const,
                                                   session_key=session_key),
                    style={'display': 'inline-flex', 'flex-direction': 'column', 'max-width': '330px'}
                    if df_name == 'OPG011' else {'display': 'None'})], style={'margin-bottom': '7.5px'}),
            Div([
                P([get_label('LBL_Animate_Over_Time') + ": "], style={'padding-right': '33px',
                                                                    'display': 'inline-block', 'font-size': '13px'}),
                Checklist(
                    id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                    options=[{'label': 'Yes', 'value': 'animate'}],
                    value=animate if animate else [],
                    style={'color': 'black', 'display': 'inline-block'}),
            ]),
            Div([
                Div([
                    P(
                        "{}:".format('Color Palette'),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-3px'}),
                I(
                    Span(
                        Img(src="http://127.0.0.1:8080/python/dashboard/assets/color-palette.png"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'color-palette-info', 'index': tile},
                    style={'position': 'relative', 'display': 'inline-block'}),
                Div([
                    RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 4},
                        options=[{'label': i, 'value': i} for i in COLOR_PALETTE],
                        labelStyle={'display': 'inline-block'},
                        value=color if color else 'G10',
                        style={'font-size': '13px', 'margin-left': '40px'})],
                    style={'display': 'inline-flex', 'max-width': '290px'})
            ]),
            Div(
                Div(
                    children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                       xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                       gridline=gridline, legend=legend, graph_type='Bar'),
                    id={'type': 'default-graph-options', 'index': tile}),
                id={'type': 'default-graph-options-wrapper', 'index': tile})
        ], style={'margin-left': '15px'})]


def get_bubble_graph_menu(tile, x, x_measure, y, y_measure, size, size_measure, gridline, legend, df_name, df_const,
                          xaxis, yaxis, xpos, ypos, xmodified, ymodified, color, session_key):
    """
    :param tile: Index of the tile the bar graph menu corresponds to
    :param x: the x-axis value
    :param x_measure: the x-axis measure
    :param y: the y-axis value
    :param y_measure: the y-axis measure
    :param size: the size value
    :param size_measure: the size measure
    :param gridline: Show gridline or not
    :param legend: Show legend or not
    :param df_name: Name of the data set being used
    :param df_const: Dataframe constants
    :param xaxis: the title of the xaxis
    :param yaxis: the title of the yaxis
    :param xpos: the x position of the legend
    :param ypos: the y position of the legend
    :param xmodified: the x title of the xaxis has been modified
    :param ymodified: the y of the yaxis title has been modified
    :param color: the color palette of the graph
    :return: Menu with options to modify a bubble graph
    """
    # args_value[0] = x-axis
    # args_value[1] = x-axis measure
    # args_value[2] = y-axis
    # args_value[3] = y-axis measure
    # args_value[4] = size
    # args_value[5] = size measure
    # args_value[6] = color

    return [
        Div(
            children=[
                P(
                    "{}:".format(get_label('LBL_Graph_Options')),
                    className='graph-type'),
                I(
                    Span(
                        get_label("LBL_Graph_Options_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'graph-options-info', 'index': tile},
                    style={'position': 'relative'})
            ],
            id={'type': 'graph-options-info-wrapper', 'index': tile}
        ),
        Div([
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_X_Axis')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '101px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else df_const[session_key]['VARIABLE_OPTIONS'] +
                                [{'label': 'Time', 'value': 'Time'}],
                        value=x,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div(
                id={'type': 'hide-xaxis-measure', 'index': tile},
                children=[
                    Div([
                        P(
                            "{}:".format(get_label('LBL_X_Axis_Measure')),
                            className='graph-option-title')],
                        style={'display': 'inline-block', 'position': 'relative', 'top': '-15px',
                               'margin-right': '56px'}),
                    Div([
                        Dropdown(
                            id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                            options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"),
                                                                  'value': i} for i in df_const[session_key]
                            ['MEASURE_TYPE_OPTIONS']],
                            value=x_measure,
                            optionHeight=30,
                            clearable=False,
                            style={'font-size': '13px'})],
                        style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})],
                style={'display': 'inline-block', 'width': '100%'}),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Y_Axis')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '101px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                        options=[] if df_const is None else df_const[session_key]['VARIABLE_OPTIONS'],
                        value=y,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Y_Axis_Measure')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-15px',
                           'margin-right': '57px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                        options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"), 'value': i}
                                                             for i in df_const[session_key]['MEASURE_TYPE_OPTIONS']],
                        value=y_measure,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Size')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'width': '50px', 'position': 'relative', 'top': '-15px',
                           'margin-right': '101px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 4},
                        options=[] if df_const is None else df_const[session_key]['VARIABLE_OPTIONS'],
                        value=size,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Size_Measure')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-15px', 'margin-right': '68px'}
                    ),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 5},
                        options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"), 'value': i}
                                                             for i in df_const[session_key]['MEASURE_TYPE_OPTIONS']],
                        value=size_measure,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format('Color Palette'),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-3px'}),
                I(
                    Span(
                        Img(src="http://127.0.0.1:8080/python/dashboard/assets/color-palette.png"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'color-palette-info', 'index': tile},
                    style={'position': 'relative', 'display': 'inline-block'}),
                Div([
                    RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 6},
                        options=[{'label': i, 'value': i} for i in COLOR_PALETTE],
                        labelStyle={'display': 'inline-block'},
                        value=color if color else 'G10',
                        style={'font-size': '13px', 'margin-left': '40px'})],
                    style={'display': 'inline-flex', 'max-width': '290px'})
            ]),
            Div(
                Div(
                    children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                       xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                       gridline=gridline, legend=legend, graph_type='Bubble'),
                    id={'type': 'default-graph-options', 'index': tile}),
                id={'type': 'default-graph-options-wrapper', 'index': tile}),
            Div(
                get_secondary_hierarchy_layout(tile, df_name, hierarchy_toggle='Level Filter',
                                              level_value='Variable Name', graph_all_toggle=None, nid_path="root",
                                              df_const=df_const, session_key=session_key),
                style={'display': 'None'})
        ], style={'margin-left': '15px'})]


def get_box_plot_menu(tile, axis_measure, graph_orientation, df_name, show_data_points, gridline,
                      legend, df_const, xaxis, yaxis, xpos, ypos, xmodified, ymodified, secondary_level_value,
                      secondary_nid_path, secondary_hierarchy_toggle, secondary_graph_all_toggle, color, session_key):
    """
        :param tile: Index of the tile the bar graph menu corresponds to
        :param axis_measure: the measure for the axis
        :param graph_orientation: the orientation value
        :param df_name: Name of the data set being used
        :param show_data_points: the animate graph value
        :param gridline: Show gridline or not
        :param legend: Show legend or not
        :param df_const: Dataframe constants
        :param xaxis: the title of the xaxis
        :param yaxis: the title of the yaxis
        :param xpos: the x position of the legend
        :param ypos: the y position of the legend
        :param xmodified: the x title of the xaxis has been modified
        :param ymodified: the y of the yaxis title has been modified
        :param secondary_hierarchy_toggle: second hierarchy filter either specific or level
        :param secondary_level_value: level of secondary hierarchy
        :param secondary_graph_all_toggle: graph all option of hierarchy item
        :param secondary_nid_path: the path of secondary specific hierarchy
        :param color: the color palette of the graph
        :return: Menu with options to modify a bar graph
        """
    # args_value[0] = measure type
    # args_value[1] = orientation
    # args_value[2] = graphed variables
    # arg_value[3] = points toggle
    # arg_value[4] = color

    return [
        Div(
            children=[
                P(
                    "{}:".format(get_label('LBL_Graph_Options')),
                    className='graph-type'),
                I(
                    Span(
                        get_label("LBL_Graph_Options_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'graph-options-info', 'index': tile},
                    style={'position': 'relative'})
            ],
            id={'type': 'graph-options-info-wrapper', 'index': tile}
        ),
        Div([
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Axis_Measure')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-15px',
                           'margin-right': '68px'}),
                Div([
                    Dropdown(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                        options=[] if df_const is None else [{'label': get_label(i, df_name+"_Measure_type"), 'value': i}
                                                             for i in df_const[session_key]['MEASURE_TYPE_OPTIONS']],
                        value=axis_measure,
                        optionHeight=30,
                        clearable=False,
                        style={'font-size': '13px'})],
                    style={'display': 'inline-block', 'width': '58%', 'max-width': '330px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Graph_Orientation')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-3px',
                           'margin-right': '15px'}),
                Div([
                    RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        options=[{'label': get_label('LBL_' + i), 'value': i} for i in ['Vertical', 'Horizontal']],
                        labelStyle={'display': 'inline-block'},
                        value=graph_orientation if graph_orientation else 'Vertical',
                        style={'font-size': '13px', 'margin-left': '25px'})],
                    style={'display': 'inline-block', 'max-width': '350px'})]),
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-5px',
                           'margin-right': '40px', }),
                Div(
                    get_secondary_hierarchy_layout(tile, df_name, secondary_hierarchy_toggle, secondary_level_value,
                                                  secondary_graph_all_toggle, secondary_nid_path, df_const=df_const,
                                                   session_key=session_key),
                    style={'display': 'inline-flex', 'flex-direction': 'column',
                           'max-width': '330px'}
                    if df_name == 'OPG011' else {'display': 'None'})], style={'margin-bottom': '7.5px'}),
            Div([
                P([get_label('LBL_Show_Data_Points') + ": "], style={'display': 'inline-block',
                                                                          'margin-right': '41px', 'font-size': '13px'}),
                Checklist(
                    id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 2},
                    options=[{'label': 'Yes', 'value': 'show'}],
                    value=show_data_points,
                    style={'color': 'black', 'display': 'inline-block'}),
            ]),
            Div([
                Div([
                    P(
                        "{}:".format('Color Palette'),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-3px'}),
                I(
                    Span(
                        Img(src="http://127.0.0.1:8080/python/dashboard/assets/color-palette.png"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'color-palette-info', 'index': tile},
                    style={'position': 'relative', 'display': 'inline-block'}),
                Div([
                    RadioItems(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 3},
                        options=[{'label': i, 'value': i} for i in COLOR_PALETTE],
                        labelStyle={'display': 'inline-block'},
                        value=color if color else 'G10',
                        style={'font-size': '13px', 'margin-left': '40px'})],
                    style={'display': 'inline-flex', 'max-width': '290px'})
            ]),
            Div(
                Div(
                    children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                       xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                       gridline=gridline, legend=legend, graph_type='Box'),
                    id={'type': 'default-graph-options', 'index': tile}),
                id={'type': 'default-graph-options-wrapper', 'index': tile})
        ], style={'margin-left': '15px'})]


def get_table_graph_menu(tile, number_of_columns, xaxis, yaxis, xpos, ypos, xmodified, ymodified, df_name, df_const,
                         session_key):
    """
    :param number_of_columns: The number of columns to display
    :param tile: Index of the tile the table instructions corresponds to
    :param xaxis: the title of the xaxis
    :param yaxis: the title of the yaxis
    :param xpos: the x position of the legend
    :param ypos: the y position of the legend
    :param xmodified: the x title of the xaxis has been modified
    :param ymodified: the y of the yaxis title has been modified
    :param df_name: Name of the data set being used
    :param df_const: Dataframe constants
    :return: Text instructions for how user can interact with table
    """
    # (args-value: {})[0] = tile index
    language = session["language"]

    return [
        Div([
            # id is used by create_graph callback to verify that the table menu is created before it activates
            Dropdown(
                id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 0},
                options=[{'label': tile, 'value': tile}],
                value=tile,
                clearable=False,
                style={'display': 'none'}),
            # page_size for table
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Num_Of_Rows')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'width': '75px', 'top': '10px'}),
                Div([
                    dcc.Input(
                        id={'type': 'args-value: {}'.replace("{}", str(tile)), 'index': 1},
                        type="number",
                        value=number_of_columns,
                        min=10,
                        max=100,
                        style={'width': '35%', 'max-width': '350px'},
                        debounce=True)],
                    style={'display': 'inline-block', 'padding': '10px'})]),
            P(
                "{}:".format(get_label('LBL_How_To_Filter_The_Table')),
                className='table-instruction'),
            Div([
                Markdown(
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
            P(
                "{}:".format(get_label('LBL_How_To_Hide_Columns')),
                className='table-instruction'),
            Div([
                Markdown(
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
            Div(
                Div(
                    children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                       xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                       gridline=None, legend=None, graph_type='Table'),
                    style=CUSTOMIZE_CONTENT_HIDE,
                    id={'type': 'default-graph-options', 'index': tile}),
                id={'type': 'default-graph-options-wrapper', 'index': tile}),
            Div(
                get_secondary_hierarchy_layout(tile, df_name, hierarchy_toggle='Level Filter',
                                              level_value='Variable Name',
                                              graph_all_toggle=None, nid_path="root", df_const=df_const,
                                               session_key=session_key),
                style={'display': 'None'})
        ], style={'font-size': '13px'})]


def get_sankey_menu(tile, df_name, df_const, xaxis, yaxis, xpos, ypos, xmodified, ymodified,
                    secondary_level_value, secondary_nid_path, secondary_hierarchy_toggle, secondary_graph_all_toggle,
                    session_key):
    """
    :param tile: Index of the tile the line graph menu corresponds to.
    :param df_name: Name of the data set being used.
    :param df_const: Dataframe constants
    :param df_const: Dataframe constants
    :param xaxis: the title of the xaxis
    :param yaxis: the title of the yaxis
    :param xpos: the x position of the legend
    :param ypos: the y position of the legend
    :param xmodified: the x title of the xaxis has been modified
    :param ymodified: the y of the yaxis title has been modified
    :param secondary_hierarchy_toggle: second hierarchy filter either specific or level
    :param secondary_level_value: level of secondary hierarchy
    :param secondary_graph_all_toggle: graph all option of hierarchy item
    :param secondary_nid_path: the path of secondary specific hierarchy
    :return: Menu with options to modify a sankey graph.
    """

    return [
        Div(
            children=[
                P(
                    "{}:".format(get_label('LBL_Graph_Options')),
                    className='graph-type'),
                I(
                    Span(
                        get_label("LBL_Graph_Options_Info"),
                        className='save-symbols-tooltip'),
                    className='fa fa-question-circle-o',
                    id={'type': 'graph-options-info', 'index': tile},
                    style={'position': 'relative'})
            ],
            id={'type': 'graph-options-info-wrapper', 'index': tile}
        ),
        Div([
            Div([
                Div([
                    P(
                        "{}:".format(get_label('LBL_Graphed_Variables')),
                        className='graph-option-title')],
                    style={'display': 'inline-block', 'position': 'relative', 'top': '-5px',
                           'margin-right': '40px', }),
                Div(
                    get_secondary_hierarchy_layout(tile, df_name, secondary_hierarchy_toggle, secondary_level_value,
                                                  secondary_graph_all_toggle, secondary_nid_path, df_const=df_const,
                                                   session_key=session_key),
                    style={'display': 'inline-flex', 'flex-direction': 'column',
                           'max-width': '330px'}
                    if df_name == 'OPG010' else {'display': 'None'})], style={'margin-bottom': '90px'}),
            Div(
                Div(
                    children=get_default_graph_options(xaxis=xaxis, yaxis=yaxis, xpos=xpos, ypos=ypos,
                                                       xmodified=xmodified, ymodified=ymodified, tile=tile,
                                                       gridline=None, legend=None, graph_type='Sankey'),
                    style=CUSTOMIZE_CONTENT_HIDE,
                    id={'type': 'default-graph-options', 'index': tile}),
                id={'type': 'default-graph-options-wrapper', 'index': tile}),

        ], style={'margin-left': '15px'})]


# create graph options
def get_default_graph_options(xaxis, yaxis, xpos, ypos, xmodified, ymodified, tile, gridline, legend, graph_type):
    return [
        Div([
            Div([
                Div([
                    P(
                        [get_label('LBL_Show_Grid_Lines') + ": "],
                        className='graph-option-title')],
                    style={'display': 'inline-block'}),
                Checklist(
                    id={'type': 'gridline', 'index': tile},
                    options=[{'label': 'Yes', 'value': 'gridline'}],
                    value=gridline if gridline else [],
                    style={'color': 'black', 'margin-left': '48px', 'display': 'inline-block'})
            ]),
            Div([
                Div([
                    P(
                    [get_label('LBL_Hide_Legend') + ": "], className='graph-option-title')],
                style={'display': 'inline-block'}),
                Checklist(
                    id={'type': 'legend', 'index': tile},
                    options=[{'label': 'Yes', 'value': 'legend'}],
                    value=legend if legend else [],
                    style={'color': 'black', 'margin-left': '70px', 'display': 'inline-block'})
            ]),
        ], style={'display': 'None'} if graph_type == 'Sankey' or 'Table' in graph_type else {}),

        Div([
            dcc.Input(
                id={'type': 'xaxis-title', 'index': tile},
                type="text",
                value=xaxis if xaxis else None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'yaxis-title', 'index': tile},
                type="text",
                value=yaxis if yaxis else None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'x-pos-legend', 'index': tile},
                type="text",
                value=xpos if xpos else None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'y-pos-legend', 'index': tile},
                type="text",
                value=ypos if ypos else None,
                style={'display': 'None'},
                debounce=True),
            # xmodified flags for when x-axis label has been modified
            Store(id={'type': 'x-modified', 'index': tile},
                      data=xmodified if xmodified else None),
            # ymodified flags for when y-axis label has been modified
            Store(id={'type': 'y-modified', 'index': tile},
                      data=ymodified if ymodified else None),
        ], style={'display': 'None'})]


# empty graph menu
def empty_graph_menu(tile):
    return [
        Div([
            Checklist(
                id={'type': 'gridline', 'index': tile},
                options=[{'label': get_label('LBL_Show_Grid_Lines'),
                          'value': 'gridline'}],
                value=[],
                style={'color': 'black', 'width': '100%', 'display': 'inline-block'}),
            Checklist(
                id={'type': 'legend', 'index': tile},
                options=[{'label': get_label('LBL_Hide_Legend'),
                          'value': 'legend'}],
                value=[],
                style={'color': 'black', 'width': '100%', 'display': 'inline-block'}),
            dcc.Input(
                id={'type': 'xaxis-title', 'index': tile},
                type="text",
                value=None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'yaxis-title', 'index': tile},
                type="text",
                value=None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'x-pos-legend', 'index': tile},
                type="text",
                value=None,
                style={'display': 'None'},
                debounce=True),
            dcc.Input(
                id={'type': 'y-pos-legend', 'index': tile},
                type="text",
                value=None,
                style={'display': 'None'},
                debounce=True),
            # xmodified flags for when x-axis label has been modified
            Store(id={'type': 'x-modified', 'index': tile},
                      data=None),
            # ymodified flags for when y-axis label has been modified
            Store(id={'type': 'y-modified', 'index': tile},
                      data=None),
            Div(
                get_secondary_hierarchy_layout(tile, df_name=None, hierarchy_toggle='Level Filter',
                                               level_value='Variable Name',
                                               graph_all_toggle=None, nid_path="root", df_const=None)
            )
        ], style={'display': 'None'})]
