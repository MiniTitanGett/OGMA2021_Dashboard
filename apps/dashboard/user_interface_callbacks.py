######################################################################################################################
"""
user_interface_callbacks.py

stores all callbacks for the user interface
"""
######################################################################################################################

# External Packages
import copy
from re import search
from urllib.parse import parse_qsl

import dash
import dash_html_components as html
from dash import no_update
from dash.dependencies import Input, Output, State, ALL, MATCH, ClientsideFunction
from dash.exceptions import PreventUpdate
from flask import url_for

# Internal Packages
from apps.dashboard.app import app
from apps.dashboard.data import DATA_CONTENT_HIDE, DATA_CONTENT_SHOW, get_label, X_AXIS_OPTIONS, \
    session, BAR_X_AXIS_OPTIONS, generate_constants, dataset_to_df, GRAPH_OPTIONS, CUSTOMIZE_CONTENT_HIDE
from apps.dashboard.layouts import get_line_scatter_graph_menu, get_bar_graph_menu, get_table_graph_menu, \
    get_tile_layout, change_index, get_box_plot_menu, get_default_tab_content, get_layout_dashboard, get_layout_graph, \
    get_data_menu, get_sankey_menu, get_dashboard_title_input, get_bubble_graph_menu


# Contents:
#   MAIN LAYOUT
#       - _generate_layout()
#       - _new_and_delete()
#       - _unlock_new_button()
#   TAB LAYOUT
#       - _change_tab()
#       - _update_num_tiles()
#       - _update_tab_title()
#   TILE LAYOUT
#       - _switch_tile_tab()
#   CUSTOMIZE TAB
#       - _update_graph_type_options()
#       - _update_graph_menu()
#   DATA SIDE-MENU
#       - _change_link()
#       - _manage_data_sidemenus()
#       - _highlight_slaved_tiles()
#   Load Screen
#       - client side callbacks

# *************************************************MAIN LAYOUT********************************************************


# determine layout on callback
# https://community.plotly.com/t/dash-on-multi-page-site-app-route-flask-to-dash/4582/11
@app.callback(Output('page-content', 'children'),
              [Input('url', 'href')],
              [State('url', 'pathname'), State('url', 'search')],
              prevent_initial_call=True)
def _generate_layout(_href, _pathname, query_string):
    # print('HREF:', href)
    # print('PATHNAME:', pathname)
    # print('SEARCH:', query_string)

    if not query_string:
        query_string = '?'

    query_params = dict(parse_qsl(query_string.strip('?')))

    if 'reportName' in query_params and query_params['reportName']:
        return [get_layout_graph(query_params['reportName'])]
    else:
        if session['language'] == 'En':
            return [get_layout_dashboard()]
        else:
            return [html.Div([get_layout_dashboard(),
                              html.Link(rel='stylesheet',
                                        href=url_for("static", filename="BBB - french stylesheet1.css"))])]


# Handles Resizing of ContentWrapper, uses tab-content-wrapper n-clicks as a throw away output
# takes x,y,z and throw away inputs to trigger when tabs are modified
app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='resizeContentWrapper'
    ),
    Output('tab-content-wrapper', 'n_clicks'),
    [Input({'type': 'dashboard-tab', 'index': ALL}, 'n_clicks'),
     Input({'type': 'dashboard-tab-close', 'index': ALL}, 'n_clicks'),
     Input('tab-add', 'n_clicks')]
)


# NEW and DELETE button functionality
@app.callback(
    [Output('div-body', 'children'),
     Output('button-new-wrapper', 'children'),
     Output('tile-closed-trigger', 'data-'),
     Output('num-tiles-2', 'data-num-tiles'),
     Output('dashboard-reset-trigger', 'data-')],
    [Input('button-new', 'n_clicks'),
     Input({'type': 'tile-close', 'index': ALL}, 'n_clicks'),
     Input('confirm-dashboard-reset', 'n_clicks')],
    [State({'type': 'tile', 'index': ALL}, 'children'),
     State('num-tiles', 'data-num-tiles'),
     State('button-new', 'disabled'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set', 'index': 4}, 'value')],
    prevent_initial_call=True
)
def _new_and_delete(_new_clicks, _close_clicks, _dashboard_reset, input_tiles, num_tiles, new_disabled, _df_const,
                    master_df):
    """
    :param _new_clicks: Detects user clicking 'NEW' button in master navigation bar and encodes the number of tiles to
    display
    :param _close_clicks: Detects user clicking close ('x') button in top right of tile
    :param input_tiles: State of all currently existing tiles
    :return: Layout of tiles for the main body, a new NEW button whose n_clicks data encodes the number of tiles to
    display, and updates the tile-closed-trigger div with the index of the deleted tile
    """

    # if NEW callback chain has not been completed and NEW button enabled, prevent update
    if new_disabled:
        raise PreventUpdate

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    changed_value = [p['value'] for p in dash.callback_context.triggered][0]
    deleted_tile = no_update
    dashboard_reset_trigger = no_update

    # if DELETE button pressed: pop deleted input_tile index and shift following indices left and adjust main layout
    if 'tile-close' in changed_id and num_tiles != 1 and changed_value is not None:
        num_tiles -= 1
        flag = False
        for i in range(len(input_tiles)):
            if '{"index":{},"type":"tile-close"}.n_clicks'.replace("{}", str(i)) in changed_id:
                input_tiles.pop(i)
                flag = True
                deleted_tile = str(i)
            elif flag:
                input_tiles[i - 1] = change_index(input_tiles[i - 1], i - 1)
        children = get_tile_layout(num_tiles, input_tiles, master_df=master_df)
    # if NEW button pressed: adjust main layout and disable NEW button until it is unlocked at the end of callback chain
    elif 'button-new' in changed_id:
        if num_tiles == 4:
            raise PreventUpdate
        num_tiles += 1
        children = get_tile_layout(num_tiles, input_tiles, master_df=master_df)
    # if RESET dashboard requested, set dashboard to default appearance
    elif 'dashboard-reset' in changed_id:
        num_tiles = 1
        children = get_tile_layout(num_tiles, [], master_df=master_df)
        dashboard_reset_trigger = 'trigger'
    # else, a tab change was made, prevent update
    else:
        raise PreventUpdate
    # disable the NEW button
    new_button = html.Button(
        className='master-nav', n_clicks=0, children=get_label('LBL_Add_Tile'), id='button-new', disabled=True)
    return children, new_button, deleted_tile, num_tiles, dashboard_reset_trigger


# unlock NEW button after end of callback chain
app.clientside_callback(
    """
    function(_graph_options, disabled){
        if (!disabled) {
            // Do Nothing
        }
        else{
            return false;
        }
    }
    """,
    Output('button-new', 'disabled'),
    [Input({'type': 'div-graph-options', 'index': ALL}, 'children')],
    [State('button-new', 'disabled')],
    prevent_initial_call=True
)


# *************************************************TAB LAYOUT********************************************************

# manage tab saves
@app.callback(
    [Output('tab-storage', 'data'),
     Output('tab-content-wrapper', 'data-active-tab'),
     Output('tab-header', 'children'),
     Output('tab-content', 'children'),
     Output('num-tiles-3', 'data-num-tiles'),
     Output('dashboard-title-wrapper', 'children')],
    [Input({'type': 'dashboard-tab', 'index': ALL}, 'n_clicks'),
     Input({'type': 'dashboard-tab-close', 'index': ALL}, 'n_clicks'),
     Input('tab-add', 'n_clicks')],
    [State('tab-content', 'children'),
     State('tab-content-wrapper', 'data-active-tab'),
     State('tab-storage', 'data'),
     State('tab-header', 'children'),
     State('button-new', 'disabled'),
     State('dashboard-title', 'value')],
    prevent_initial_call=True
)
def _change_tab(_tab_clicks, _tab_close_clicks, _tab_add_nclicks,
                tab_content, active_tab, data, tab_toggle_children, new_disabled, dashboard_title):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if page loaded (changed_id == '.') or new button is disabled, prevent update
    if changed_id == '.' or new_disabled:
        raise PreventUpdate

    # if user requested to add a new tab
    if 'tab-add.n_clicks' in changed_id:
        if len(tab_toggle_children) >= 12:
            raise PreventUpdate
        tab_toggle_children = tab_toggle_children + [
            html.Div([
                html.Button(
                    get_label("LBL_Tab"),
                    id={'type': 'dashboard-tab', 'index': len(tab_toggle_children)},
                    className='dashboard-tab-button'),
                html.Button(
                    "x",
                    id={'type': 'dashboard-tab-close', 'index': len(tab_toggle_children)},
                    className='dashboard-tab-close')],
                className='dashboard-tab')]
        data.append({'content': get_default_tab_content(), 'title': ''})
        return data, active_tab, tab_toggle_children, no_update, no_update, no_update

    # if user requested to delete a tab
    if '"type":"dashboard-tab-close"}.n_clicks' in changed_id:
        deleted_tab_index = int(search(r'\d+', changed_id).group())
        # this is shifting logic to act like chrome or any other internet browser
        if deleted_tab_index == active_tab:
            if active_tab == len(data) - 1:
                new_tab = active_tab - 1
            else:
                new_tab = active_tab
            # if requesting to delete the only tab prevent it
            if new_tab < 0:
                raise PreventUpdate
        elif deleted_tab_index > active_tab:
            new_tab = active_tab
        else:
            new_tab = active_tab - 1
        # remove the tab and its x from the children
        del tab_toggle_children[deleted_tab_index]
        # remove the tabs data from the storage
        del data[deleted_tab_index]
        # shift all tab button indices down one following deleted tab
        for i in tab_toggle_children[deleted_tab_index:]:
            # decremement close button index
            i['props']['children'][0]['props']['id']['index'] -= 1
            # decrement tab button index
            i['props']['children'][1]['props']['id']['index'] -= 1
        # set active tab style as selected
        tab_toggle_children[new_tab]['props']['className'] = 'dashboard-tab-selected'
        # disable active tab button
        tab_toggle_children[new_tab]['props']['children'][0]['props']['disabled'] = True
        # set active tab close button style as selected
        tab_toggle_children[new_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close-selected'
        # force a load if required else return new tab that's been shifted
        if deleted_tab_index == active_tab:
            title_wrapper = get_dashboard_title_input(data[new_tab]['title'])
            return data, new_tab, tab_toggle_children, data[new_tab]['content'], no_update, title_wrapper
        return data, new_tab, tab_toggle_children, no_update, no_update, no_update

    # else, user requested a tab change
    new_tab = int(search(r'\d+', changed_id).group())
    # if user requested the active tab, prevent update
    if new_tab == active_tab:
        raise PreventUpdate
    # else, user requested a different tab. Save the current tab content to the appropriate save location and swap tabs
    data[active_tab]['content'] = tab_content
    data[active_tab]['title'] = dashboard_title
    # set old active tab style as unselected
    tab_toggle_children[active_tab]['props']['className'] = 'dashboard-tab'
    # enable old active tab button
    tab_toggle_children[active_tab]['props']['children'][0]['props']['disabled'] = False
    # set old active tab close button style as unselected
    tab_toggle_children[active_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close'
    # set new tab style as selected
    tab_toggle_children[new_tab]['props']['className'] = 'dashboard-tab-selected'
    # disable new tab button
    tab_toggle_children[new_tab]['props']['children'][0]['props']['disabled'] = True
    # set new tab close button style as selected
    tab_toggle_children[new_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close-selected'
    # set the number of tiles to the number of tiles in the new tab
    num_tiles = data[new_tab]['content'][0]['props']['data-num-tiles']
    # create dashboard title wrapper
    title_wrapper = get_dashboard_title_input(data[new_tab]['title'])
    return data, new_tab, tab_toggle_children, data[new_tab]['content'], num_tiles, title_wrapper


# update num-tiles
@app.callback(
    Output('num-tiles', 'data-num-tiles'),
    [Input('num-tiles-2', 'data-num-tiles'),
     Input('num-tiles-3', 'data-num-tiles'),
     Input('num-tiles-4', 'data-num-tiles')],
    prevent_initial_call=True
)
def _update_num_tiles(input1, input2, input3):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    result = no_update

    if changed_id == '.':
        raise PreventUpdate

    if 'num-tiles-2' in changed_id:
        result = input1

    if 'num-tiles-3' in changed_id:
        result = input2

    if 'num-tiles-4' in changed_id:
        result = input3

    return result


# update tab name
@app.callback(
    Output({'type': 'dashboard-tab', 'index': ALL}, 'children'),
    [Input('dashboard-title', 'value')],
    [State('tab-content-wrapper', 'data-active-tab'),
     State({'type': 'dashboard-tab', 'index': ALL}, 'children')],
    prevent_initial_call=True
)
def _update_tab_title(title, active_tab, list_of_children):
    if title == '':
        list_of_children[active_tab] = get_label('LBL_Tab')
    else:
        if len(title) > 5:
            title = title[:3] + '...'
        list_of_children[active_tab] = title
    return list_of_children


# ************************************************TILE SETTINGS*******************************************************

# Serve the float menu to the user
for x in range(4):
    @app.callback(
        [Output({'type': 'float-menu-trigger', 'index': x}, 'data-'),
         Output({'type': 'tile-customize', 'index': x}, 'className'),
         Output({'type': 'tile-layouts', 'index': x}, 'className'),
         Output({'type': 'tile-customize-content-wrapper', 'index': x}, 'children')],
        [Input({'type': 'tile-customize', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-layouts', 'index': x}, 'n_clicks'),
         Input('float-menu-result', 'children')],
        [State('float-menu-title', 'data-'),
         State({'type': 'tile-customize-content', 'index': x}, 'children')],
        prevent_initial_call=True
    )
    def _serve_float_menu_and_take_result(_customize_n_clicks, _layouts_n_clicks, float_menu_result, float_menu_data, customize_menu):
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

        if changed_id == '.' or len(dash.callback_context.triggered) > 1:
            raise PreventUpdate

        if 'float-menu-result' in changed_id:
            tile = float_menu_data[1]
        else:
            tile = int(search(r'\d+', changed_id).group())

        customize_menu_output = no_update

        # switch statement
        if 'tile-customize' in changed_id:
            float_menu_trigger = [['customize', tile, customize_menu], {}, get_label('LBL_Edit_Graph')]
            customize_className = 'tile-nav tile-nav--customize tile-nav--selected'
            layouts_className = 'tile-nav tile-nav--layout'
        elif 'tile-layouts' in changed_id:
            float_menu_trigger = [['layouts', tile], {}, get_label('LBL_Load_Graph')]
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout tile-nav--selected'
        elif float_menu_result == 'ok':
            float_menu_trigger = [None, {'display': 'hide'}, None]
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout'
        # cancel
        else:
            customize_menu_output = html.Div(
                    float_menu_data[2],
                    style=CUSTOMIZE_CONTENT_HIDE,
                    id={'type': 'tile-customize-content', 'index': tile},
                    className='customize-content'),
            float_menu_trigger = [None, {'display': 'hide'}, None]
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout'
        return float_menu_trigger, customize_className, layouts_className, customize_menu_output

# initialize menu, shows which menu you need
app.clientside_callback(
    """
    function(float_menu_trigger_0, float_menu_trigger_1, float_menu_trigger_2, float_menu_trigger_3, 
             close_n_clicks, cancel_n_clicks, ok_n_clicks, float_menu_data) {
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
        
        var float_menu_trigger = null;
        var result = null;
        if (triggered.includes('float-menu-trigger')) {
            var trigger_arr = [float_menu_trigger_0, float_menu_trigger_1, float_menu_trigger_2, float_menu_trigger_3]
            var tile = triggered.match(/\d+/)[0];
            float_menu_trigger = trigger_arr[tile];
            if (float_menu_trigger[0][0] == 'customize') {
                var menu = document.getElementById(`{"index":${tile},"type":"tile-customize-content"}`);
            }
            else {
                var menu = document.getElementById(`{"index":${tile},"type":"tile-layouts-content"}`);
            }
            document.getElementById("float-menu-body").appendChild(menu).style.display = ''; 
        }
        else {
            float_menu_trigger = [float_menu_data, {'display': 'none'}, '', ''];
            var tile = float_menu_data[1];
            if (float_menu_trigger[0][0] == 'customize') {
                var menu = document.getElementById(`{"index":${tile},"type":"tile-customize-content"}`);
            }
            else {
                var menu = document.getElementById(`{"index":${tile},"type":"tile-layouts-content"}`);
            }
            document.getElementById(`{"index":${tile},"type":"tile-body"}`).appendChild(menu).style.display = 'none'; 
        
            if (triggered == 'float-menu-close.n_clicks' || triggered == 'float-menu-cancel.n_clicks') {result = 'cancel';}
            if (triggered == 'float-menu-ok.n_clicks') {result = 'ok';}
        }
        return [float_menu_trigger[0], float_menu_trigger[1], float_menu_trigger[2], result];
    }
    """,
    [Output('float-menu-title', 'data-'),  # index value and reason for prompt
     Output('float-menu-obscure', 'style'),
     Output('float-menu-title', 'children'),
     Output('float-menu-result', 'children')],
    [Input({'type': 'float-menu-trigger', 'index': 0}, 'data-'),
     Input({'type': 'float-menu-trigger', 'index': 1}, 'data-'),
     Input({'type': 'float-menu-trigger', 'index': 2}, 'data-'),
     Input({'type': 'float-menu-trigger', 'index': 3}, 'data-'),
     Input('float-menu-close', 'n_clicks'),
     Input('float-menu-cancel', 'n_clicks'),
     Input('float-menu-ok', 'n_clicks')],
    State('float-menu-title', 'data-'),
    prevent_initial_call=True
)


# ************************************************CUSTOMIZE TAB*******************************************************
# update graph options to match data set
@app.callback(
    [Output({'type': 'set-tile-link-trigger', 'index': MATCH}, 'link-'),
     Output({'type': 'graph-type-dropdown', 'index': MATCH}, 'options'),
     Output({'type': 'graph-type-dropdown', 'index': MATCH}, 'value'),
     Output({'type': 'div-graph-type', 'index': MATCH}, 'style'),
     Output({'type': 'div-customize-warning-message', 'index': MATCH}, 'style')],
    [Input({'type': 'set-graph-options-trigger', 'index': MATCH}, 'options-'),
     Input({'type': 'tile-link', 'index': ALL}, 'className')],
    [State({'type': 'data-set', 'index': MATCH}, 'value'),
     State({'type': 'data-set', 'index': 4}, 'value'),
     State({'type': 'graph-type-dropdown', 'index': MATCH}, 'value'),
     State({'type': 'graph-type-dropdown', 'index': MATCH}, 'options')]
    # TODO: Why are we calling the state of things we are taking in as inputs
)
def _update_graph_type_options(trigger, link_states, df_name, df_name_parent, graph_type, _type_options):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    changed_value = [p['value'] for p in dash.callback_context.triggered][0]



    if changed_id == '.' or link_states is []:
        raise PreventUpdate

    if '"type":"tile-link"}.className' in changed_id and changed_value == 'fa fa-unlink':
        raise PreventUpdate

    changed_index = int(search(r'\d+', changed_id).group())

    graph_options = no_update
    options = []

    link_trigger = no_update  # None

    type_style = {'margin-left': '15px'}
    message_style = DATA_CONTENT_HIDE

    if '"type":"tile-link"}.className' in changed_id:
        if df_name_parent == "OPG001":
            graph_options = GRAPH_OPTIONS["OPG001"]
        elif df_name_parent == "OPG010":
            graph_options = GRAPH_OPTIONS["OPG010"]
        else:
            graph_options = []
        graph_options.sort()
        for i in graph_options:
            options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
    elif trigger == 'fa fa-unlink':
        link_trigger = "fa fa-unlink"
        if df_name is not None:
            graph_options = GRAPH_OPTIONS[df_name]
            graph_options.sort()
            for i in graph_options:
                options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
    else:
        if (df_name or df_name_parent) == "OPG001":
            graph_options = GRAPH_OPTIONS["OPG001"]
            if graph_type is not None and graph_type not in graph_options:
                link_states[changed_index] = "fa fa-unlink"
        elif (df_name or df_name_parent) == "OPG010":
            graph_options = GRAPH_OPTIONS["OPG010"]
            if graph_type is not None and graph_type not in graph_options:
                link_states[changed_index] = "fa fa-unlink"
        else:
            graph_options = []
        graph_options.sort()
        for i in graph_options:
            options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})

    #loads in a default graph when dataset is first choosen
    if '"type":"tile-link"}.className' not in changed_id and graph_type is None:
        graph_value = options[0]['value']
    #relink selected first graph option of parent data set not in graph options
    elif '"type":"tile-link"}.className' in changed_id and changed_value == 'fa fa-link' and graph_type not in graph_options:
        graph_value = options[0]['value']
    elif '"type":"set-graph-options-trigger"}.options-' in changed_id and graph_type is not None and graph_type not in graph_options:
        graph_value = options[0]['value']
    else:
        graph_value = graph_type

    return link_trigger, options, graph_value, type_style, message_style


# update graph menu to match selected graph type
for x in range(4):
    @app.callback(
        [Output({'type': 'div-graph-options', 'index': x}, 'children'),
         Output({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_trigger'),
         Output({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_table_trigger')],
        [Input({'type': 'graph-menu-trigger', 'index': x}, 'data-'),
         Input({'type': 'graph-type-dropdown', 'index': x}, 'value'),
         Input({'type': 'tile-link', 'index': x}, 'className')],
        [State({'type': 'div-graph-options', 'index': x}, 'children'),
         State({'type': 'graph-type-dropdown', 'index': ALL}, 'value'),
         State({'type': 'data-set', 'index': x}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         State('df-constants-storage', 'data')],
        prevent_initial_call=True
    )
    def _update_graph_menu(gm_trigger, selected_graph_type, link_state, graph_options_state, _graph_option, df_name,
                           master_df_name, df_const):
        """
        :param selected_graph_type: Selected graph type, ie. 'bar', 'line', etc.
        :param graph_options_state: State of the current graph options div
        :return: Graph menu corresponding to selected graph type
        """

        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][-1]

        if '"type":"tile-link"}.className' in changed_id and  master_df_name is None and df_name is None:
            return None, 1, no_update

        # if link state has changed from linked --> unlinked the data has not changed, prevent update
        if '"type":"tile-link"}.className' in changed_id and link_state == 'fa fa-unlink':
            if selected_graph_type is None:
                return None, no_update, no_update
            else:
                raise PreventUpdate

        # if link state from unlinked --> linked and the data set has not changed, don't update menu, still update graph
        if ('"type":"tile-link"}.className' in changed_id and link_state == 'fa fa-link') \
                or ('type":"graph-type-dropdown"}.value' in changed_id and link_state == 'fa fa-link'
                    and selected_graph_type is None):
            if master_df_name is None and df_name is None:
                return None, 1,no_update
            if selected_graph_type not in GRAPH_OPTIONS[master_df_name] or selected_graph_type is None:
                return None, 1, no_update
            elif selected_graph_type in GRAPH_OPTIONS[master_df_name]:
                return no_update, 1, no_update
            else:
                raise PreventUpdate

        if link_state == 'fa fa-link':
            df_name = master_df_name

        # if graph menu trigger has value 'tile closed' then a tile was closed, don't update menu, still update table
        if 'graph-menu-trigger"}.data-' in changed_id and gm_trigger == 'tile closed':
            return no_update, no_update, 1

        # if changed id == '.' and the graph menu already exists, prevent update
        if changed_id == '.' and graph_options_state or df_const is None or df_name not in df_const:
            raise PreventUpdate

        tile = int(dash.callback_context.inputs_list[0]['id']['index'])

        # apply graph selection and generate menu
        if selected_graph_type == 'Line' or selected_graph_type == 'Scatter':
            menu = get_line_scatter_graph_menu(tile=tile,
                                               x=X_AXIS_OPTIONS[0],
                                               y=None if df_const is None else
                                               df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                               mode=selected_graph_type,
                                               measure_type=None if df_const is None else
                                               df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                               gridline=None,
                                               df_name=df_name,
                                               df_const=df_const)

        elif selected_graph_type == 'Bar':
            menu = get_bar_graph_menu(tile=tile,
                                      x=BAR_X_AXIS_OPTIONS[0],
                                      y=None if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                      measure_type=None if df_const is None else
                                      df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                      orientation=None,
                                      animate=None,
                                      gridline=None,
                                      df_name=df_name,
                                      df_const=df_const)

        elif selected_graph_type == 'Bubble':
            menu = get_bubble_graph_menu(tile=tile,
                                         x=None if df_const is None else
                                         df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                         x_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         y=None if df_const is None else
                                         df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                         y_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         size=None if df_const is None else
                                         df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                         size_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         gridline=None,
                                         df_name=df_name,
                                         df_const=df_const)

        elif selected_graph_type == 'Table':
            menu = get_table_graph_menu(tile=tile, number_of_columns=15)

        elif selected_graph_type == 'Box_Plot':
            menu = get_box_plot_menu(tile=tile,
                                     axis_measure=None if df_const is None else
                                     df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                     graphed_variables=None if df_const is None else
                                     df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                     graph_orientation='Horizontal',
                                     df_name=df_name,
                                     show_data_points=[],
                                     gridline=None,
                                     df_const=df_const)

        elif selected_graph_type == 'Sankey':
            menu = get_sankey_menu(tile=tile,
                                   graphed_options=None if df_const is None else
                                   df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                   df_name=df_name,
                                   df_const=df_const)

        else:
            raise PreventUpdate

        if '"type":"tile-link"}.className' in changed_id or 'graph-menu-trigger"}.data-' in changed_id \
                or '"type":"graph-type-dropdown"}.value' in changed_id:
            update_graph_trigger = 1
        else:
            update_graph_trigger = no_update

        return menu, update_graph_trigger, no_update


# ************************************************DATA SIDE-MENU******************************************************

# change link button appearance
@app.callback(
    Output({'type': 'tile-link', 'index': MATCH}, 'className'),
    [Input({'type': 'tile-link', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'set-tile-link-trigger', 'index': MATCH}, 'link-')],
    [State({'type': 'tile-link', 'index': MATCH}, 'className')],
    prevent_initial_call=True
)
def _change_link(_link_clicks, link_trigger, link_state):
    """
    :param _link_clicks: Detects the user clicking the link/unlink icon
    :param link_state: State of the link/unlink icon
    :return: New state of the link/unlink icon
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if link button was not pressed and layout was not selected, do not update
    if '.' == changed_id:  # or link_trigger is None
        raise PreventUpdate

    if '"type":"select-layout-dropdown"}.value' in changed_id:
        link_state = 'fa fa-unlink'

    if '"type":"tile-link"}.n_clicks' in changed_id:
        # if link button was pressed, toggle the link icon linked <--> unlinked
        if link_state == "fa fa-link":
            link_state = 'fa fa-unlink'
        else:
            link_state = 'fa fa-link'

    if '"type":"set-tile-link-trigger"}.link-' in changed_id and link_trigger is not None:
        link_state = 'fa fa-unlink'

    return link_state


# manage data sidemenu appearance and content
@app.callback(
    [Output({'type': 'data-tile', 'index': 0}, 'children'),
     Output({'type': 'data-tile', 'index': 1}, 'children'),
     Output({'type': 'data-tile', 'index': 2}, 'children'),
     Output({'type': 'data-tile', 'index': 3}, 'children'),
     Output({'type': 'data-tile', 'index': 4}, 'children'),
     Output({'type': 'data-tile', 'index': 0}, 'style'),
     Output({'type': 'data-tile', 'index': 1}, 'style'),
     Output({'type': 'data-tile', 'index': 2}, 'style'),
     Output({'type': 'data-tile', 'index': 3}, 'style'),
     Output({'type': 'data-tile', 'index': 4}, 'style'),
     Output({'type': 'graph-menu-trigger', 'index': 0}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 1}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 2}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 3}, 'data-'),
     Output('df-constants-storage', 'data'),
     Output({'type': 'confirm-load-data', 'index': 0}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 1}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 2}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 3}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 4}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 0}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 1}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 2}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 3}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 4}, 'style'),
     Output({'type': 'data-set', 'index': 0}, 'data-'),
     Output({'type': 'data-set', 'index': 1}, 'data-'),
     Output({'type': 'data-set', 'index': 2}, 'data-'),
     Output({'type': 'data-set', 'index': 3}, 'data-'),
     Output({'type': 'data-set', 'index': 4}, 'data-'),
     Output({'type': 'set-graph-options-trigger', 'index': 0}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 1}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 2}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 3}, 'options-'), ],
    [Input('dashboard-reset-trigger', 'data-'),
     Input('tile-closed-trigger', 'data-'),
     Input('select-dashboard-dropdown', 'value'),
     Input({'type': 'tile-link', 'index': ALL}, 'className'),
     Input({'type': 'tile-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-menu-close', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-set', 'index': 0}, 'value'),
     Input({'type': 'data-set', 'index': 1}, 'value'),
     Input({'type': 'data-set', 'index': 2}, 'value'),
     Input({'type': 'data-set', 'index': 3}, 'value'),
     Input({'type': 'data-set', 'index': 4}, 'value'),
     Input({'type': 'confirm-load-data', 'index': 0}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 1}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 2}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 3}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 4}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 0}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 1}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 2}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 3}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 4}, 'n_clicks')],
    [State({'type': 'data-tile', 'index': ALL}, 'children'),
     State({'type': 'data-tile', 'index': ALL}, 'style'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set', 'index': ALL}, 'data-'),
     State({'type': 'graph-type-dropdown', 'index': ALL}, 'value'),
     # Date picker states for master data menu
     State({'type': 'start-year-input', 'index': 4}, 'name'),
     State({'type': 'radio-timeframe', 'index': 4}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
     State({'type': 'start-year-input', 'index': 4}, 'value'),
     State({'type': 'end-year-input', 'index': 4}, 'value'),
     State({'type': 'start-secondary-input', 'index': 4}, 'value'),
     State({'type': 'end-secondary-input', 'index': 4}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
     State({'type': 'num-periods', 'index': 4}, 'value'),
     State({'type': 'period-type', 'index': 4}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 4}, 'value'),  # graph all toggle
     State({'type': 'hierarchy_display_button', 'index': 4}, 'children')],
    prevent_initial_call=True
)
def _manage_data_sidemenus(_dashboard_reset, closed_tile, _loaded_dashboard, links_style, data_clicks,
                           _data_close_clicks, df_name_0, df_name_1, df_name_2, df_name_3, df_name_4, _confirm_clicks_0,
                           _confirm_clicks_1, _confirm_clicks_2, _confirm_clicks_3, _confirm_clicks_4,
                           _refresh_clicks_0, _refresh_clicks_1, _refresh_clicks_2, _refresh_clicks_3,
                           _refresh_clicks_4, data_states, sidemenu_style_states, df_const, prev_selection, graph_types,
                           _master_secondary_type, master_timeframe, master_fiscal_toggle, _master_start_year,
                           _master_end_year, _master_start_secondary, _master_end_secondary, master_hierarchy_toggle,
                           master_hierarchy_drop, master_num_state, master_period_type, master_graph_child_toggle,
                           state_of_display):
    """
    :param closed_tile: Detects when a tile has been deleted and encodes the index of the deleted tile
    param links_style: State of all link/unlink icons and detects user clicking a link icon
    :param data_states: State of all data side-menus
    :return: Data side-menus for all 5 side-menus
    """

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if changed id == '.' due to NEW being requested, preserve data menu display.
    if changed_id == '.':
        raise PreventUpdate

    # if 'tile-data' in changed id but n_clicks == 0, meaning a tile was created from blank display, prevent update
    if '{"index":0,"type":"tile-data"}.n_clicks' == changed_id and not data_clicks[0]:
        raise PreventUpdate

    # initialize return variables, data is NONE and sidemenus are hidden by default
    data = [None] * 5
    sidemenu_styles = [DATA_CONTENT_HIDE] * 5
    graph_triggers = [no_update] * 5
    confirm_button = [no_update] * 5
    refresh_button = [no_update] * 5
    store = no_update
    options_triggers = [no_update] * 5
    date_picker_triggers = [no_update] * 5

    # if 'data-menu-close' or 'select-dashboard-dropdown' requested, close all data menus
    if 'data-menu-close' in changed_id or 'select-dashboard-dropdown' in changed_id:
        pass

    # if 'tile-closed-trigger' requested
    elif 'tile-closed-trigger.data-' == changed_id:
        # trigger graph-menu-trigger
        graph_triggers[int(closed_tile)] = 'tile closed'
        # shuffle data tiles
        data_copy = copy.deepcopy(data_states)
        flag = False
        for i in range(4):
            if i == int(closed_tile):
                flag = True
            if flag and not i == 3:
                data[i] = change_index(data_copy[i + 1], i)
        # if a data menu is open and the only tile was not deleted, select the new open data menu
        if sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0 and len(links_style) != 0:
            active_tile = sidemenu_style_states.index(DATA_CONTENT_SHOW)
            # if the master data menu is active and there are any linked tiles, the master data menu stays open
            if active_tile == 4 and links_style.count('fa fa-link') > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
            # else, the master data menu is not active while any linked tiles exist
            else:
                deleted_tile = int(closed_tile)
                # if the master data menu is active and there are no linked tiles, the linked tile was deleted
                if active_tile == 4:
                    active_tile = deleted_tile
                if deleted_tile == active_tile:
                    if active_tile == len(links_style):
                        new_active_tile = active_tile - 1
                    else:
                        new_active_tile = active_tile
                elif deleted_tile > active_tile:
                    new_active_tile = active_tile
                else:
                    new_active_tile = active_tile - 1
                if links_style[new_active_tile] == 'fa fa-link':
                    sidemenu_styles[4] = DATA_CONTENT_SHOW
                else:
                    sidemenu_styles[new_active_tile] = DATA_CONTENT_SHOW

    # elif 'data-set' in changed id keep shown and show confirmation button
    elif '"type":"data-set"}.value' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]
        df_name = df_names[changed_index]
        sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
        if df_name in session:
            confirm_button[changed_index] = DATA_CONTENT_HIDE
            refresh_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
            sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
            # refresh data menu if not returning to last loaded
            if df_name is not prev_selection[changed_index]:
                data[changed_index] = get_data_menu(changed_index, df_name, df_const=df_const)
            # trigger update for all tiles that are linked to the active data menu
            if changed_index == 4:
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        # graph_triggers[i] = df_name
                        confirm_button[i] = DATA_CONTENT_HIDE
                        refresh_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
                        prev_selection[i] = df_name
                        options_triggers[i] = df_name
            else:
                # graph_triggers[changed_index] = df_name
                prev_selection[changed_index] = df_name
                options_triggers[changed_index] = df_name
        else:
            if changed_index == 4:
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        confirm_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
                        refresh_button[i] = DATA_CONTENT_HIDE
            confirm_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
            refresh_button[changed_index] = DATA_CONTENT_HIDE

    # elif 'data-set' in changed id, reset data tile with new df set as active, keep shown, and trigger graph update
    elif '"type":"confirm-load-data"}.n_clicks' in changed_id \
            or '"type":"confirm-data-set-refresh"}.n_clicks' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]

        df_name = df_names[changed_index]
        session[df_name] = dataset_to_df(df_name)

        if df_const is None:
            df_const = {}
        df_const[df_name] = generate_constants(df_name)
        store = df_const
        data[changed_index] = get_data_menu(changed_index, df_name, df_const=df_const)
        sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
        # trigger update for all tiles that are linked to the active data menu
        if changed_index == 4:
            prev_selection[changed_index] = df_name
            for i in range(len(links_style)):
                if links_style[i] == 'fa fa-link':
                    prev_selection[i] = df_name
                    if graph_types[i] is None or graph_types[i] in GRAPH_OPTIONS[df_name]:
                        graph_triggers[i] = df_name
                        options_triggers[i] = df_name
                        df_names[i] = df_name

                    else:
                        links_style[i] = 'fa fa-unlink'
                        # [i]= 'fa-fa-unlink'
                        # set the dataset of the new menu from unlinking
                        if type(state_of_display) == dict:
                            state_of_display = [state_of_display]
                        nid_path = "root"
                        for button in state_of_display:
                            nid_path += '^||^{}'.format(button['props']['children'])

                        if df_name == "OPG001":
                            df_names[i] = "OPG010"
                            df_const[df_names[i]] = generate_constants(df_names[i])
                            data[i] = get_data_menu(i, df_names[i],
                                                    hierarchy_toggle=master_hierarchy_toggle,
                                                    level_value=master_hierarchy_drop,
                                                    nid_path=nid_path, graph_all_toggle=master_graph_child_toggle,
                                                    fiscal_toggle=master_fiscal_toggle, input_method=master_timeframe,
                                                    num_periods=master_num_state, period_type=master_period_type,
                                                    df_const=df_const)
                            # sidemenu_styles[i] = DATA_CONTENT_SHOW
                            refresh_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                                 'position': 'relative',
                                                 'margin-right': '10px', 'margin-left': '10px',
                                                 'vertical-align': 'top'}
                            if master_timeframe == "select-range":
                                date_picker_triggers[i] = "triggered"

                        elif df_name == "OPG010":
                            df_names[i] = "OPG001"
                            df_const[df_names[i]] = generate_constants(df_names[i])
                            data[i] = get_data_menu(i, df_names[i], mode='tile-loading',
                                                    hierarchy_toggle=master_hierarchy_toggle,
                                                    level_value=master_hierarchy_drop,
                                                    nid_path=nid_path, graph_all_toggle=master_graph_child_toggle,
                                                    fiscal_toggle=master_fiscal_toggle, input_method=master_timeframe,
                                                    num_periods=master_num_state, period_type=master_period_type,
                                                    df_const=df_const)
                            # sidemenu_styles[i] = DATA_CONTENT_SHOW
                            refresh_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                                 'position': 'relative',
                                                 'margin-right': '10px', 'margin-left': '10px',
                                                 'vertical-align': 'top'}
                            if master_timeframe == "select-range":
                                date_picker_triggers[i] = "triggered"
                        options_triggers[i] = 'fa fa-unlink'
        else:
            graph_triggers[changed_index] = df_name
            options_triggers[changed_index] = df_name
        prev_selection[changed_index] = df_name
        confirm_button[changed_index] = DATA_CONTENT_HIDE
        refresh_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                                         'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}

    # elif 'RESET' dashboard requested, hide and reset all data tiles
    elif 'dashboard-reset-trigger' in changed_id:
        for i in range(len(data)):
            data[i] = get_data_menu(i, df_const=df_const)

    # else, 'data', 'tile-link', or 'select-layout' requested
    else:
        changed_index = int(search(r'\d+', changed_id).group())
        # if 'tile-link' requested
        if '"type":"tile-link"}.className' in changed_id:
            # if linked --> unlinked: copy master tile data to unique tile data
            if links_style[changed_index] == 'fa fa-unlink':
                master_copy = copy.deepcopy(data_states[4])
                data[changed_index] = change_index(master_copy, changed_index)
        # if tile is slaved to master and a layout was not selected, display master data
        if links_style[changed_index] == 'fa fa-link' and '"type":"select-layout-dropdown"}.value' not in changed_id:
            # if 'data' requested or a data menu is already open, display master data
            if '"type":"tile-data"}.n_clicks' in changed_id or sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
        # if tile is not linked to master or a layout was selected, display unique data side-menu
        else:
            # if 'data' requested or a data menu is already open, display tile data
            if '"type":"tile-data"}.n_clicks' in changed_id or sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0:
                sidemenu_styles[changed_index] = DATA_CONTENT_SHOW

    # determine returns
    for i in range(5):
        # if the data was not changed, do not update
        if data[i] is None:
            data[i] = no_update
        # if the style of a data tile has not changed, do not update
        if sidemenu_styles[i] == sidemenu_style_states[i]:
            # for all tiles besides master data tile do not update if style has not changed
            if i != 4:
                sidemenu_styles[i] = no_update
            # if master data is SHOWN, do not prevent update to force trigger highlight tiles callback
            elif sidemenu_styles[4] != DATA_CONTENT_SHOW:
                sidemenu_styles[4] = no_update

    return (data[0], data[1], data[2], data[3], data[4],
            sidemenu_styles[0], sidemenu_styles[1], sidemenu_styles[2], sidemenu_styles[3], sidemenu_styles[4],
            graph_triggers[0], graph_triggers[1], graph_triggers[2], graph_triggers[3], store,
            confirm_button[0], confirm_button[1], confirm_button[2], confirm_button[3], confirm_button[4],
            refresh_button[0], refresh_button[1], refresh_button[2], refresh_button[3], refresh_button[4],
            prev_selection[0], prev_selection[1], prev_selection[2], prev_selection[3], prev_selection[4],
            options_triggers[0], options_triggers[1], options_triggers[2], options_triggers[3])


"""
@app.callback(
    [Output({'type': 'start-year-input', 'index': MATCH}, 'name'),
     Output({'type': 'start-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'start-secondary-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-secondary-input', 'index': MATCH}, 'value')],
    [Input({'type': 'set-date-picker-trigger', 'index': MATCH}, 'picker-')],
    [State({'type': 'start-year-input', 'index': 4}, 'name'),
     State({'type': 'start-year-input', 'index': 4}, 'value'),
     State({'type': 'end-year-input', 'index': 4}, 'value'),
     State({'type': 'start-secondary-input', 'index': 4}, 'value'),
     State({'type': 'end-secondary-input', 'index': 4}, 'value'),
     ]
)
def _date_picker_inputs(trigger, tile_tab, tile_start_year, tile_end_year, tile_start_secondary, tile_end_secondary):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    date_tab = tile_tab
    start_year = tile_start_year
    end_year = tile_end_year
    start_secondary = tile_start_secondary
    end_secondary = tile_end_secondary

    return date_tab, start_year, end_year, start_secondary, end_secondary"""

# http://adripofjavascript.com/blog/drips/object-equality-in-javascript.html#:~:text=Here%20is%20a%20very%20basic,are%20not%20equivalent%20if%20(aProps.
app.clientside_callback(
    """
       function(load_data_trigger, refresh_data_trigger){
            function isEquivalent(a, b) {
                // Create arrays of property names
                var aProps = Object.getOwnPropertyNames(a);
                var bProps = Object.getOwnPropertyNames(b);

                // If number of properties is different,
                // objects are not equivalent
                if (aProps.length != bProps.length) {
                    return false;
                }

                for (var i = 0; i < aProps.length; i++) {
                    var propName = aProps[i];

                    // If values of same property are not equal,
                    // objects are not equivalent
                    if (a[propName] !== b[propName]) {
                        return false;
                    }
                }

                // If we made it this far, objects
                // are considered equivalent
                return true;
            }
            var DATA_CONTENT_HIDE = {'display': 'none'};  
            if (isEquivalent(load_data_trigger, DATA_CONTENT_HIDE) 
                && !isEquivalent(refresh_data_trigger, DATA_CONTENT_HIDE)){
                return {};
            }
            else{
                return DATA_CONTENT_HIDE;
            }
        }
    """,
    Output({'type': 'data-menu-controls', 'index': MATCH}, 'style'),
    [Input({'type': 'confirm-load-data', 'index': MATCH}, 'style'),
     Input({'type': 'confirm-data-set-refresh', 'index': MATCH}, 'style')]
)

# highlight tiles slaved to displayed data sidebar
for x in range(4):
    app.clientside_callback(
        """
        function(_sidebar_styles, link_state, sidebar_style, master_sidebar_style){
            function isEquivalent(a, b) {
                // Create arrays of property names
                var aProps = Object.getOwnPropertyNames(a);
                var bProps = Object.getOwnPropertyNames(b);

                // If number of properties is different,
                // objects are not equivalent
                if (aProps.length != bProps.length) {
                    return false;
                }

                for (var i = 0; i < aProps.length; i++) {
                    var propName = aProps[i];

                    // If values of same property are not equal,
                    // objects are not equivalent
                    if (a[propName] !== b[propName]) {
                        return false;
                    }
                }

                // If we made it this far, objects
                // are considered equivalent
                return true;
            }

            var DATA_CONTENT_SHOW = {
                'max-width': '300px', 
                'min-width': '300px',
                'background-color':'#fffafa',
                'border-right': '1px solid #c7c7c7',
                'flex-grow': '1', 
                'display': 'inline', 
                'overflow-y': 'auto'};

            if (isEquivalent(sidebar_style, DATA_CONTENT_SHOW) || 
                (isEquivalent(master_sidebar_style, DATA_CONTENT_SHOW) && link_state == 'fa fa-link')){
                var tile_class = 'tile-highlight';
            }
            else{
                var tile_class = 'tile-container';
            }
            return tile_class;
        }
        """,
        Output({'type': 'tile', 'index': x}, 'className'),
        [Input({'type': 'data-tile', 'index': ALL}, 'style'),
         Input({'type': 'tile-link', 'index': x}, 'className')],
        [State({'type': 'data-tile', 'index': x}, 'style'),
         State({'type': 'data-tile', 'index': 4}, 'style')]
    )

# *************************************************LOADSCREEN*********************************************************

# All clientside callback functions referred to are stored in /assets/ClientsideCallbacks.js
for x in range(4):
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='graphLoadScreen{}'.format(x)
        ),
        Output({'type': 'tile-menu-header', 'index': x}, 'n_clicks'),
        [Input({'type': 'tile-view', 'index': x}, 'n_clicks')],
        [State({'type': 'tile-view', 'index': x}, 'className')],
        prevent_initial_call=True
    )

    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='graphRemoveLoadScreen{}'.format(x)
        ),
        Output({'type': 'graph_display', 'index': x}, 'n_clicks'),
        [Input({'type': 'graph_display', 'index': x}, 'children')],
        State('num-tiles', 'data-num-tiles'),
        prevent_initial_call=True
    )

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='datasetLoadScreen'
    ),
    Output('dataset-confirmation-symbols', 'n_clicks'),
    [Input({'type': 'confirm-load-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': ALL}, 'n_clicks'),
     Input('select-dashboard-dropdown', 'value')],
    prevent_initial_call=True
)

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='datasetRemoveLoadScreen'
    ),
    Output('df-constants-storage', 'n_clicks'),
    [Input('df-constants-storage', 'data')],
    prevent_initial_call=True
)

# *************************************************PROMPT*********************************************************

# initialize prompt
app.clientside_callback(
    """
    function(prompt_trigger_0, prompt_trigger_1, prompt_trigger_2, prompt_trigger_3, 
             close_n_clicks, cancel_n_clicks, ok_n_clicks, prompt_data){
        const triggered = dash_clientside.callback_context.triggered.map(t => t.prop_id);
        var prompt_trigger = null;
        var result = null;
        
        if (triggered == '{"index":0,"type":"prompt-trigger"}.data-'){
            prompt_trigger = prompt_trigger_0;
        }
        if (triggered == '{"index":1,"type":"prompt-trigger"}.data-'){
            prompt_trigger = prompt_trigger_1;
        }
        if (triggered == '{"index":2,"type":"prompt-trigger"}.data-'){
            prompt_trigger = prompt_trigger_2;
        }
        if (triggered == '{"index":3,"type":"prompt-trigger"}.data-'){
            prompt_trigger = prompt_trigger_3;
        }
        
        if (triggered == 'prompt-close.n_clicks') {
            prompt_trigger = [prompt_data, {'display': 'none'}, '', ''];
            result = 'close';
        }
        if (triggered == 'prompt-cancel.n_clicks'){
            prompt_trigger = [prompt_data, {'display': 'none'}, '', ''];
            result = 'cancel';
        }
        if (triggered == 'prompt-ok.n_clicks'){
            prompt_trigger = [prompt_data, {'display': 'none'}, '', ''];
            result = 'ok';
        }
        
        return [prompt_trigger[0], prompt_trigger[1], prompt_trigger[2], prompt_trigger[3], result];
    }
    """,
    [Output('prompt-title', 'data-'),  # index value and reason for prompt
     Output('prompt-obscure', 'style'),
     Output('prompt-title', 'children'),
     Output('prompt-body', 'children'),
     Output('prompt-result', 'children')],
    [Input({'type': 'prompt-trigger', 'index': 0}, 'data-'),
     Input({'type': 'prompt-trigger', 'index': 1}, 'data-'),
     Input({'type': 'prompt-trigger', 'index': 2}, 'data-'),
     Input({'type': 'prompt-trigger', 'index': 3}, 'data-'),
     Input('prompt-close', 'n_clicks'),
     Input('prompt-cancel', 'n_clicks'),
     Input('prompt-ok', 'n_clicks')],
    State('prompt-title', 'data-'),
    prevent_initial_call=True
)
