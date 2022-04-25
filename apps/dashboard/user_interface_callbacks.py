######################################################################################################################
"""
user_interface_callbacks.py

Stores all callbacks for the user interface.
"""
######################################################################################################################

# External Packages
import copy
from re import search
from urllib.parse import parse_qsl
import dash_core_components as dcc
import dash
import dash_html_components as html
from dash import no_update
from dash.dependencies import Input, Output, State, ALL, MATCH, ClientsideFunction
from dash.exceptions import PreventUpdate
from dash_core_components import Store
from flask import url_for

# Internal Modules
from apps.dashboard.app import app
from apps.dashboard.data import DATA_CONTENT_HIDE, DATA_CONTENT_SHOW, get_label, X_AXIS_OPTIONS, \
    session, BAR_X_AXIS_OPTIONS, generate_constants, dataset_to_df, GRAPH_OPTIONS, CUSTOMIZE_CONTENT_HIDE, LAYOUTS
from apps.dashboard.layouts import get_line_scatter_graph_menu, get_bar_graph_menu, get_table_graph_menu, \
    get_tile_layout, change_index, get_box_plot_menu, get_default_tab_content, get_layout_dashboard, get_layout_graph, \
    get_data_menu, get_sankey_menu, get_dashboard_title_input, get_bubble_graph_menu


# *************************************************MAIN LAYOUT********************************************************


# Determine layout on callback.
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
# takes x,y,z and throw away inputs to trigger when tabs are modified.
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


# NEW and DELETE button functionality.
@app.callback(
    # change the firing order to fire the tile close first to solve a bug
    # causing the tile close trigger to never fire in the data menu
    [Output('tile-closed-trigger', 'data-'),
     Output('div-body', 'children'),
     Output('div-body', 'layouts'),
     Output('button-new-wrapper', 'children'),
     Output('num-tiles-2', 'data-num-tiles')],
    [Input('button-new', 'n_clicks'),
     Input('tile-closed-input-trigger', 'data'),
     Input('dashboard-reset-confirmation', 'data-')],
    [State({'type': 'tile-title', 'index': ALL}, 'value'),
     State({'type': 'tile-link', 'index': ALL}, 'className'),
     State({'type': 'tile-customize-content', 'index': ALL}, 'children'),
     State('num-tiles', 'data-num-tiles'),
     State('button-new', 'disabled'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set', 'index': 4}, 'value'),
     State({'type': 'data-set-parent', 'index': 4}, 'value')],
    prevent_initial_call=True
)
def _new_and_delete(_new_clicks, close_id, _dashboard_reset, tile_titles, tile_links, tile_customize_menus, num_tiles,
                    new_disabled, df_const, parent_df, confirm_parent):
    """
    :param _new_clicks: Detects user clicking 'NEW' button in parent navigation bar and encodes the number of tiles to
    display
    :return: Layout of tiles for the main body, a NEW button whose n_clicks data encodes the number of tiles to
    display, and updates the tile-closed-trigger div with the index of the deleted tile
    """
    # -------------------------------------------Variable Declarations--------------------------------------------------
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    changed_value = [p['value'] for p in dash.callback_context.triggered][0]
    deleted_tile = no_update
    input_tiles = []
    for i in range(len(tile_titles)):
        input_tiles.append({'Tile Title': tile_titles[i],
                            'Link': tile_links[i],
                            'Customize Content': tile_customize_menus[i],
                            'Rebuild Menu': False})
    # ------------------------------------------------------------------------------------------------------------------
    # if NEW callback chain has not been completed and NEW button enabled, prevent update
    if new_disabled:
        raise PreventUpdate

    # if DELETE button pressed: pop deleted input_tile index and shift following indices left and adjust main layout
    if 'tile-close' in changed_id and num_tiles != 1 and changed_value is not None:
        num_tiles -= 1
        flag = False
        for i in range(len(input_tiles)):
            if i == close_id:
                input_tiles.pop(i)
                flag = True
                deleted_tile = str(i)
            elif flag:
                input_tiles[i - 1] = change_index(input_tiles[i - 1], i - 1)
        children = get_tile_layout(num_tiles, tile_keys=input_tiles, parent_df=parent_df)
    # if NEW button pressed: adjust main layout and disable NEW button until it is unlocked at the end of callback chain
    elif 'button-new' in changed_id:
        if num_tiles == 4:
            raise PreventUpdate
        num_tiles += 1
        input_tiles.append(None)
        if parent_df is None and confirm_parent is None:
            children = get_tile_layout(num_tiles, tile_keys=input_tiles, parent_df=None)
        else:
            if confirm_parent:
                parent_df = confirm_parent
            children = get_tile_layout(num_tiles, tile_keys=input_tiles, parent_df=parent_df if (df_const is not None
                                                                        and df_const[parent_df] is not None) else None)
    # if RESET dashboard requested, set dashboard to default appearance
    elif 'dashboard-reset' in changed_id:
        num_tiles = 1
        children = get_tile_layout(num_tiles, [], parent_df=None)
    # else, a tab change was made, prevent update
    else:
        raise PreventUpdate
    # disable the NEW button
    new_button = html.Button(
        className='parent-nav', n_clicks=0, children=get_label('LBL_Add_Tile'), id='button-new', disabled=True)
    return deleted_tile, children, LAYOUTS[num_tiles - 1], new_button, num_tiles


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

# Manage tab saves.
@app.callback(
    [Output('tab-storage', 'data'),
     Output('tab-content-wrapper', 'data-active-tab'),
     Output('tab-header', 'children'),
     Output('tab-content', 'children'),
     Output('num-tiles-3', 'data-num-tiles'),
     Output('dashboard-title-wrapper', 'children'),
     Output('tab-swap-flag-wrapper', 'children')],
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
    children = []
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
        return data, active_tab, tab_toggle_children, no_update, no_update, no_update, no_update

    for tile in range(4):
        children.append(Store(id={'type': 'tab-swap-flag', 'index': tile}, data=False))
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

        for i in range(4):
            if i < data[new_tab]['content'][0]['props']['data-num-tiles']:
                children[i] = Store(id={'type': 'tab-swap-flag', 'index': i}, data=True)
            else:
                children[i] = Store(id={'type': 'tab-swap-flag', 'index': i}, data=False)
        # remove the tab and its x from the children
        del tab_toggle_children[deleted_tab_index]
        # remove the tab data from the storage
        del data[deleted_tab_index]
        # shift all tab button indices down one following deleted tab
        for i in tab_toggle_children[deleted_tab_index:]:
            # decrement close button index
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
            return data, new_tab, tab_toggle_children, data[new_tab]['content'], no_update, title_wrapper, children
        return data, new_tab, tab_toggle_children, no_update, no_update, no_update, children

    # else, user requested a tab change
    new_tab = int(search(r'\d+', changed_id).group())
    # if user requested the active tab, prevent update
    if new_tab == active_tab:
        raise PreventUpdate
    for i in range(4):
        if i < data[new_tab]['content'][0]['props']['data-num-tiles']:
            children[i] = Store(id={'type': 'tab-swap-flag', 'index': i}, data=True)
        else:
            children[i] = Store(id={'type': 'tab-swap-flag', 'index': i}, data=False)
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
    return data, new_tab, tab_toggle_children, data[new_tab]['content'], num_tiles, title_wrapper, children


# Update num-tiles.
app.clientside_callback(
    """
    function _update_num_tiles(input1, input2, input3){
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
        let result = dash_clientside.no_update;
    
        if (triggered.includes('num-tiles-2')){
            result = input1;
        }
        if (triggered.includes('num-tiles-3')){
            result = input2;
        }
        if (triggered.includes('num-tiles-4')){
            result = input3;
        }
        return result;
    }
    """,
    Output('num-tiles', 'data-num-tiles'),
    [Input('num-tiles-2', 'data-num-tiles'),
     Input('num-tiles-3', 'data-num-tiles'),
     Input('num-tiles-4', 'data-num-tiles')],
    prevent_initial_call=True
)


# Update tab name.
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

# Serve the float menu to the user.
for x in range(4):
    @app.callback(
        [Output({'type': 'float-menu-trigger-wrapper', 'index': x}, 'children'),
         Output({'type': 'tile-customize', 'index': x}, 'className'),
         Output({'type': 'tile-layouts', 'index': x}, 'className'),
         Output({'type': 'tile-customize-content-wrapper', 'index': x}, 'children')],
        [Input({'type': 'tile-customize', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-layouts', 'index': x}, 'n_clicks'),
         Input({'type': 'float-menu-result', 'index': 2}, 'children')],
        [State('float-menu-title', 'data-'),
         State({'type': 'tile-customize-content', 'index': x}, 'children')],
        prevent_initial_call=True
    )
    def _serve_float_menu_and_take_result(_customize_n_clicks, _layouts_n_clicks, float_menu_result, float_menu_data,
                                          customize_menu):
        # -------------------------------------------Variable Declarations----------------------------------------------
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        customize_menu_output = no_update
        float_menu_trigger = no_update
        # --------------------------------------------------------------------------------------------------------------

        if changed_id == '.' or len(dash.callback_context.triggered) > 1 \
                or 'float-menu-result' in changed_id and float_menu_result is None:
            raise PreventUpdate

        # set which tile is being modified
        if 'float-menu-result' in changed_id:
            tile = float_menu_data[1]
        else:
            tile = int(search(r'\d+', changed_id).group())

        # catch tile callback discrepancy due to looping
        if dash.callback_context.inputs_list[0]['id']['index'] != tile:
            raise PreventUpdate

        # switch statement
        if 'tile-customize' in changed_id:
            # [[mode/prompt_trigger, tile, stored_menu_for_cancel], menu_style/show_hide, menu_title,
            # show_hide_load_warning, isTrip]
            float_menu_trigger = Store(id={'type': 'float-menu-trigger', 'index': tile},
                                           data=[['customize', tile, customize_menu], {}, get_label('LBL_Edit_Graph'),
                                                 session['tile_edited'][tile]])
            customize_className = 'tile-nav tile-nav--customize tile-nav--selected'
            layouts_className = 'tile-nav tile-nav--layout'
        elif 'tile-layouts' in changed_id:
            float_menu_trigger = Store(id={'type': 'float-menu-trigger', 'index': tile},
                                           data=[['layouts', tile], {}, get_label('LBL_Load_Graph'),
                                                 session['tile_edited'][tile]])
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout tile-nav--selected'
        elif float_menu_result == 'ok':
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout'
        # cancel
        else:
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout'
            if float_menu_data[0] == 'customize':
                customize_menu_output = html.Div(
                    float_menu_data[2],
                    style=CUSTOMIZE_CONTENT_HIDE,
                    id={'type': 'tile-customize-content', 'index': tile},
                    className='customize-content',
                    **{'data-loaded': True})

        return float_menu_trigger, customize_className, layouts_className, customize_menu_output

# Initialize menu, shows which menu you need.
app.clientside_callback(
    """
    function _init_float_menu(menu_trigger_0, menu_trigger_1, menu_trigger_2, menu_trigger_3, menu_trigger_4, 
             close_n_clicks, cancel_n_clicks, ok_n_clicks, float_menu_data) {
        // init variables
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
        let float_menu_trigger = dash_clientside.no_update;
        let result = dash_clientside.no_update;
        let result_0 = dash_clientside.no_update;
        let result_1 = dash_clientside.no_update;
        
        // serve the menu by taking the tile and retrieving what was requested to put into body
        if (triggered.includes('float-menu-trigger')) {
            let trigger_arr = [menu_trigger_0, menu_trigger_1, menu_trigger_2, menu_trigger_3, menu_trigger_4];
            let tile = triggered.match(/\d+/)[0];
            let menu = null;
            float_menu_trigger = trigger_arr[tile];
            if (float_menu_trigger[0][0] == 'customize') {
                menu = document.getElementById(`{"index":${tile},"type":"tile-customize-content"}`);
            }
            if (float_menu_trigger[0][0] == 'layouts') {
                menu = document.getElementById(`{"index":${tile},"type":"tile-layouts-content"}`);
            }
            if (float_menu_trigger[0][0] == 'dashboard_layouts') {
                menu = document.getElementById('load-dashboard-menu');
            }
            document.getElementById("float-menu-body").appendChild(menu).style.display = ''; 
            
            if (float_menu_trigger[3]) {
                document.getElementById(`{"index":${tile},"type":"tile-layouts-warning"}`).style.display = '';
            }
            else {
                document.getElementById(`{"index":${tile},"type":"tile-layouts-warning"}`).style.display = 'none';
            }
        }
        // otherwise, input from menu needs to be handled to output to correct callback chain
        else {
            float_menu_trigger = [float_menu_data, {'display': 'none'}, dash_clientside.no_update, ''];
            let tile = float_menu_data[1];
            let menu = null;
            if (float_menu_trigger[0][0] == 'customize') {
                menu = document.getElementById(`{"index":${tile},"type":"tile-customize-content"}`);
                document.getElementById(`{"index":${tile},"type":"tile-customize-content-wrapper"}`).appendChild(
                    menu).style.display = 'none'; 
            }
            if (float_menu_trigger[0][0] == 'layouts') {
                menu = document.getElementById(`{"index":${tile},"type":"tile-layouts-content"}`);
                document.getElementById(`{"index":${tile},"type":"tile-body"}`).appendChild(
                    menu).style.display = 'none'; 
            }
            if (float_menu_trigger[0][0] == 'dashboard_layouts') {
                menu = document.getElementById('load-dashboard-menu');
                document.getElementById('button-save-dashboard-wrapper').appendChild(menu).style.display = 'none';
            }
            
            if (triggered == 'float-menu-close.n_clicks' || triggered == 'float-menu-cancel.n_clicks') {
                result = 'cancel';
            }
            if (triggered == 'float-menu-ok.n_clicks') {result = 'ok';}
            
            // ensure result gets sent to correct callbacks
            // result always get sent to _serve_float_menu_and_take_result() for styles
            if (float_menu_trigger[0][0] == 'layouts') {result_0 = result;} 
            if (float_menu_trigger[0][0] == 'dashboard_layouts') {result_1 = result;} 
            
        }
        return [float_menu_trigger[0], float_menu_trigger[1], float_menu_trigger[2], result_0, result_1, result];
    }
    """,
    [Output('float-menu-title', 'data-'),  # index value and reason for prompt
     Output('float-menu-obscure', 'style'),
     Output('float-menu-title', 'children'),
     Output({'type': 'float-menu-result', 'index': 0}, 'children'),  # _manage_tile_save_load_trigger() callback
     Output({'type': 'float-menu-result', 'index': 1}, 'children'),  # _manage_dashboard_saves_and_reset() callback
     Output({'type': 'float-menu-result', 'index': 2}, 'children')],  # _serve_float_menu_and_take_result() callback
    [Input({'type': 'float-menu-trigger', 'index': 0}, 'data'),
     Input({'type': 'float-menu-trigger', 'index': 1}, 'data'),
     Input({'type': 'float-menu-trigger', 'index': 2}, 'data'),
     Input({'type': 'float-menu-trigger', 'index': 3}, 'data'),
     Input({'type': 'float-menu-trigger', 'index': 4}, 'data'),
     Input('float-menu-close', 'n_clicks'),
     Input('float-menu-cancel', 'n_clicks'),
     Input('float-menu-ok', 'n_clicks')],
    [State('float-menu-title', 'data-')],
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
     State({'type': 'data-set-parent', 'index': 4}, 'value')]
)
def _update_graph_type_options(trigger, link_states, df_name, df_name_parent, graph_type, df_confirm):
    # -------------------------------------------Variable Declarations--------------------------------------------------
    graph_options = no_update
    options = []
    link_trigger = no_update
    type_style = {}
    message_style = DATA_CONTENT_HIDE
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    changed_value = [p['value'] for p in dash.callback_context.triggered][0]
    # ------------------------------------------------------------------------------------------------------------------

    if changed_id == '.' or link_states is []:
        raise PreventUpdate

    if '"type":"tile-link"}.className' in changed_id and changed_value == 'fa fa-unlink' or \
            (changed_value == 'fa fa-link' and df_name is None and df_name_parent is None) or (
            trigger is None and df_confirm is None and df_name is None and df_name_parent is None):
        raise PreventUpdate

    # check for keyword in df_name_parent and df_name
    if 'OPG010' in df_name_parent:
        df_name_parent = 'OPG010'
    elif 'OPG011' in df_name_parent:
        df_name_parent = 'OPG011'

    # if new tile is created and is on a dataset that is not confirmed use previous data set that has been confirmed
    if '"type":"tile-link"}.className' in changed_id and changed_value == 'fa fa-link' and df_confirm is not None:
        if 'OPG010' in df_confirm:
            df_confirm = 'OPG010'
        elif 'OPG011' in df_confirm:
            df_confirm = 'OPG011'
        graph_options = GRAPH_OPTIONS[df_confirm]
        # for i in graph_options:
        #    options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
        options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graph_options]

    # when dataset is swapped to a different dataset get parent graph options
    elif '"type":"tile-link"}.className' in changed_id:
        if "OPG" in df_name_parent:
            graph_options = GRAPH_OPTIONS[df_name_parent]
        else:
            graph_options = []
        # for i in graph_options:
        #     options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
        options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graph_options]

    # set customize menu of the unlinked tile
    elif trigger == 'fa fa-unlink':
        link_trigger = "fa fa-unlink"
        if df_name is not None:
            if 'OPG010' in df_name:
                df_name = 'OPG010'
            elif 'OPG011' in df_name:
                df_name = 'OPG011'
            graph_options = GRAPH_OPTIONS[df_name]
            # for i in graph_options:
            #     options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
            options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graph_options]
    # set customize menu back to parent dataset
    elif trigger == 'fa fa-link':
        graph_options = GRAPH_OPTIONS[df_name_parent]
        # for i in graph_options:
        #     options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
        options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graph_options]
    else:
        if "OPG010" in trigger:
            graph_options = GRAPH_OPTIONS["OPG010"]
        elif "OPG011" in trigger:
            graph_options = GRAPH_OPTIONS["OPG011"]
        else:
            graph_options = []
        # for i in graph_options:
        #     options.append({'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i})
        options = [{'label': get_label('LBL_' + i.replace(' ', '_')), 'value': i} for i in graph_options]

    # loads in a default graph when dataset is first chosen
    if '"type":"tile-link"}.className' not in changed_id and graph_type is None:
        graph_value = options[0]['value']
    # relink selected first graph option of parent data set not in graph options
    elif '"type":"tile-link"}.className' in changed_id and changed_value == 'fa fa-link' \
            and graph_type not in graph_options:
        graph_value = options[0]['value']
    # linked and changing the dataset of parent to a different dataset get first option of dataset
    elif '"type":"set-graph-options-trigger"}.options-' in changed_id and graph_type is not None \
            and graph_type not in graph_options:
        graph_value = options[0]['value']
    # unlink and don't change graph option
    else:
        graph_value = no_update

    return link_trigger, options, graph_value, type_style, message_style


# Reveals the data-fitting options when conditions needed for data-fitting are met.
app.clientside_callback(
    """
    function _update_data_fitting(trigger, style){
        if (trigger.includes('show')){
            if (isEquivalent(style, {'display': 'inline-flex', 'flex-direction': 'row', 'width': '280px'
                                                                                            , 'flex-wrap': 'wrap'})){
                style = dash_clientside.no_update;
            }
            else{
                style = {'display': 'inline-flex', 'flex-direction': 'row', 'width': '280px', 'flex-wrap': 'wrap'};
            }
        }

        else if(trigger.includes('hide')){
            if (isEquivalent(style, {'display': 'none'})){
                style = dash_clientside.no_update;
            } 
            else {
                style = {'display': 'none'}
            }
        }
        else{
            throw dash_clientside.PreventUpdate;
        }
        return style;
    }
    """,
    Output({'type': 'data-fitting-wrapper', 'index': MATCH}, 'style'),
    Input({'type': 'data-fitting-trigger', 'index': MATCH}, 'value'),
    State({'type': 'data-fitting-wrapper', 'index': MATCH}, 'style'),
    prevent_initial_call=True
)


# Update graph menu to match selected graph type.
@app.callback(
    [Output({'type': 'div-graph-options', 'index': MATCH}, 'children'),
     Output({'type': 'update-graph-trigger', 'index': MATCH}, 'data-graph_menu_trigger'),
     Output({'type': 'update-graph-trigger', 'index': MATCH}, 'data-graph_menu_table_trigger'),
     Output({'type': 'tile-customize-content', 'index': MATCH}, 'data-loaded'),
     Output({'type': 'tile-rebuild-menu-flag', 'index': MATCH}, 'data')],
     # Output({'type': 'tab-swap-flag', 'index': MATCH}, 'data')],
    [Input({'type': 'graph-menu-trigger', 'index': MATCH}, 'data-'),
     Input({'type': 'graph-type-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'tile-link', 'index': MATCH}, 'className')],
    [State({'type': 'tile-rebuild-menu-flag', 'index': MATCH}, 'data'),
     State({'type': 'tile-customize-content', 'index': MATCH}, 'data-loaded'),
     State({'type': 'data-set', 'index': MATCH}, 'value'),
     State({'type': 'data-set', 'index': 4}, 'value'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set-parent', 'index': 4}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
     State({'type': 'graph_children_toggle', 'index': MATCH}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': MATCH}, 'value'),
     State({'type': 'tab-swap-flag', 'index': ALL}, 'data')],
    prevent_initial_call=True
)
def _update_graph_menu(gm_trigger, selected_graph_type, link_state, rebuild_menu,
                       is_loaded, df_name, parent_df_name, df_const, df_confirm, parent_graph_all,
                       parent_hierarchy_toggle, graph_all, hierarchy_toggle, swap_flag):
    """
    :param selected_graph_type: Selected graph type, i.e. 'bar', 'line', etc.
    :return: Graph menu corresponding to selected graph type
    """
    # -------------------------------------------Variable Declarations--------------------------------------------------
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][-1]
    # ------------------------------------------------------------------------------------------------------------------
    changed_index = int(search(r'\d+', changed_id).group())
    swap_flag_output = False
    # if tab swapped or load triggered, don't reset menus
    if not rebuild_menu or len(dash.callback_context.triggered) == 4 or swap_flag[changed_index] is True:
        return no_update, 1, no_update, no_update, True

    # if link state has changed from linked --> unlinked the data has not changed, prevent update
    if '"type":"tile-link"}.className' in changed_id and link_state == 'fa fa-unlink':
        if selected_graph_type is None:
            return None, no_update, no_update, no_update, no_update
        else:
            raise PreventUpdate

    # Sets the data_fitting boolean to true or false dependant on the link-state of the tile being modified and then the
    # tiles associated data menu
    if link_state == 'fa fa-link':
        if parent_hierarchy_toggle == 'Specific Item' and parent_graph_all == []:
            data_fitting = True
        else:
            data_fitting = False
    else:
        if hierarchy_toggle == 'Specific Item' and graph_all == []:
            data_fitting = True
        else:
            data_fitting = False

    # if the data set is selected but has not been confirmed, use previous data set
    if link_state == 'fa fa-link' and ('graph-type-dropdown' in changed_id and df_confirm is not None) or \
       ('graph-menu-trigger' in changed_id and parent_df_name not in df_const):
        df_name = df_confirm
    elif link_state == 'fa fa-link':
        df_name = parent_df_name

    # if graph menu trigger has value 'tile closed' then a tile was closed, don't update menu, still update table
    if 'graph-menu-trigger"}.data-' in changed_id and gm_trigger == 'tile closed':
        return no_update, no_update, 1, no_update, True

    # if this has been loaded from the cancel of a graph menu edit then set to false and prevent update
    if 'graph-type-dropdown"}.value' in changed_id and is_loaded:
        return no_update, no_update, no_update, False, True

    tile = int(dash.callback_context.inputs_list[0]['id']['index'])

    # apply graph selection and generate menu
    if selected_graph_type == 'Line' or selected_graph_type == 'Scatter':
        menu = get_line_scatter_graph_menu(tile=tile,
                                           x=X_AXIS_OPTIONS[0],
                                           mode=selected_graph_type,
                                           measure_type=None if df_const is None else
                                           df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                           data_fit=None,
                                           degree=None,
                                           gridline=None,
                                           legend=None,
                                           xaxis=None,
                                           yaxis=None,
                                           xpos=None,
                                           ypos=None,
                                           xmodified=None,
                                           ymodified=None,
                                           df_name=df_name,
                                           df_const=df_const,
                                           data_fitting=data_fitting,
                                           ci=None,
                                           secondary_level_value='Variable Name',
                                           secondary_nid_path="root",
                                           secondary_hierarchy_toggle='Level Filter',
                                           secondary_graph_all_toggle=None,
                                           color=None)
    elif selected_graph_type == 'Bar':
        menu = get_bar_graph_menu(tile=tile,
                                  x=BAR_X_AXIS_OPTIONS[0],
                                  measure_type=None if df_const is None else
                                  df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                  orientation=None,
                                  animate=None,
                                  gridline=None,
                                  legend=None,
                                  xaxis=None,
                                  yaxis=None,
                                  xpos=None,
                                  ypos=None,
                                  xmodified=None,
                                  ymodified=None,
                                  df_name=df_name,
                                  df_const=df_const,
                                  secondary_level_value='Variable Name',
                                  secondary_nid_path="root",
                                  secondary_hierarchy_toggle='Level Filter',
                                  secondary_graph_all_toggle=None,
                                  color=None)
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
                                     legend=None,
                                     xaxis=None,
                                     yaxis=None,
                                     xpos=None,
                                     ypos=None,
                                     xmodified=None,
                                     ymodified=None,
                                     df_name=df_name,
                                     df_const=df_const,
                                     color=None)
    elif selected_graph_type == 'Table':
        menu = get_table_graph_menu(tile=tile, number_of_columns=15,
                                    xaxis=None,
                                    yaxis=None,
                                    xpos=None,
                                    ypos=None,
                                    xmodified=None,
                                    ymodified=None,
                                    df_name=df_name,
                                    df_const=df_const)

    elif selected_graph_type == 'Box_Plot':
        menu = get_box_plot_menu(tile=tile,
                                 axis_measure=None if df_const is None else
                                 df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                 graph_orientation='Horizontal',
                                 df_name=df_name,
                                 show_data_points=[],
                                 gridline=None,
                                 legend=None,
                                 xaxis=None,
                                 yaxis=None,
                                 xpos=None,
                                 ypos=None,
                                 xmodified=None,
                                 ymodified=None,
                                 df_const=df_const,
                                 secondary_level_value='Variable Name',
                                 secondary_nid_path="root",
                                 secondary_hierarchy_toggle='Level Filter',
                                 secondary_graph_all_toggle=None,
                                 color=None)
    elif selected_graph_type == 'Sankey':
        menu = get_sankey_menu(tile=tile,
                               df_name=df_name,
                               df_const=df_const,
                               xaxis=None,
                               yaxis=None,
                               xpos=None,
                               ypos=None,
                               xmodified=None,
                               ymodified=None,
                               secondary_level_value='Variable Name',
                               secondary_nid_path="root",
                               secondary_hierarchy_toggle='Level Filter',
                               secondary_graph_all_toggle=None,)
    else:
        raise PreventUpdate

    if '"type":"tile-link"}.className' in changed_id or 'graph-menu-trigger"}.data-' in changed_id \
            or '"type":"graph-type-dropdown"}.value' in changed_id:
        update_graph_trigger = 1
    else:
        update_graph_trigger = no_update
    return menu, update_graph_trigger, no_update, no_update, True


# ************************************************DATA SIDE-MENU******************************************************


# Manage data side-menu appearance and content.
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
     Output({'type': 'data-set-prev-selected', 'index': 0}, 'data'),
     Output({'type': 'data-set-prev-selected', 'index': 1}, 'data'),
     Output({'type': 'data-set-prev-selected', 'index': 2}, 'data'),
     Output({'type': 'data-set-prev-selected', 'index': 3}, 'data'),
     Output({'type': 'data-set-prev-selected', 'index': 4}, 'data'),
     Output({'type': 'data-set', 'index': 0}, 'value'),
     Output({'type': 'data-set', 'index': 1}, 'value'),
     Output({'type': 'data-set', 'index': 2}, 'value'),
     Output({'type': 'data-set', 'index': 3}, 'value'),
     Output({'type': 'data-set', 'index': 4}, 'value'),
     Output({'type': 'set-graph-options-trigger', 'index': 0}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 1}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 2}, 'options-'),
     Output({'type': 'set-graph-options-trigger', 'index': 3}, 'options-'),
     Output({'type': 'prompt-trigger-wrapper', 'index': 5}, 'children'),
     Output({'type': 'data-set-parent', 'index': 4}, 'value'),
     Output({'type': 'update-date-picker-trigger', 'index': 0}, 'data-boolean'),
     Output({'type': 'update-date-picker-trigger', 'index': 1}, 'data-boolean'),
     Output({'type': 'update-date-picker-trigger', 'index': 2}, 'data-boolean'),
     Output({'type': 'update-date-picker-trigger', 'index': 3}, 'data-boolean'),
     Output({'type': 'update-date-picker-trigger', 'index': 4}, 'data-boolean'),
     Output('data-set-result-wrapper', 'children')],
    [Input('tile-closed-trigger', 'data-'),
     Input({'type': 'tile-link', 'index': ALL}, 'className'),
     Input({'type': 'tile-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-menu-close', 'index': ALL}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'data-set', 'index': 0}, 'value'),
     Input({'type': 'data-set', 'index': 1}, 'value'),
     Input({'type': 'data-set', 'index': 2}, 'value'),
     Input({'type': 'data-set', 'index': 3}, 'value'),
     Input({'type': 'data-set', 'index': 4}, 'value'),
     Input({'type': 'confirm-load-data', 'index': 0}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-load-data', 'index': 1}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-load-data', 'index': 2}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-load-data', 'index': 3}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-load-data', 'index': 4}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-data-set-refresh', 'index': 0}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-data-set-refresh', 'index': 1}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-data-set-refresh', 'index': 2}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-data-set-refresh', 'index': 3}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'confirm-data-set-refresh', 'index': 4}, 'n_clicks'),  # TODO: unused state
     Input({'type': 'prompt-result', 'index': 2}, 'children')],
    [State('prompt-title', 'data-'),
     State({'type': 'data-tile', 'index': ALL}, 'children'),
     State({'type': 'data-tile', 'index': ALL}, 'style'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set-prev-selected', 'index': 0}, 'data'),
     State({'type': 'data-set-prev-selected', 'index': 1}, 'data'),
     State({'type': 'data-set-prev-selected', 'index': 2}, 'data'),
     State({'type': 'data-set-prev-selected', 'index': 3}, 'data'),
     State({'type': 'data-set-prev-selected', 'index': 4}, 'data'),
     State({'type': 'graph-type-dropdown', 'index': ALL}, 'value'),
     # Date picker states for parent data menu
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
def _manage_data_sidemenus(closed_tile, links_style, data_clicks,
                           _data_close_clicks, df_name_0, df_name_1, df_name_2, df_name_3, df_name_4, _confirm_clicks_0,
                           _confirm_clicks_1, _confirm_clicks_2, _confirm_clicks_3, _confirm_clicks_4,
                           _refresh_clicks_0, _refresh_clicks_1, _refresh_clicks_2, _refresh_clicks_3,
                           _refresh_clicks_4, prompt_result, prompt_data, data_states, sidemenu_style_states, df_const,
                           prev_selection_0, prev_selection_1, prev_selection_2, prev_selection_3, prev_selection_4,
                           graph_types,
                           parent_secondary_type, parent_timeframe, parent_fiscal_toggle, parent_start_year,
                           parent_end_year, parent_start_secondary, parent_end_secondary, parent_hierarchy_toggle,
                           parent_hierarchy_drop, parent_num_state, parent_period_type, parent_graph_child_toggle,
                           state_of_display):
    """
    :param closed_tile: Detects when a tile has been deleted and encodes the index of the deleted tile
    param links_style: State of all link/unlink icons and detects user clicking a link icon
    :param data_states: State of all data side-menus
    :return: Data side-menus for all 5 side-menus
    """
    # -------------------------------------------Variable Declarations--------------------------------------------------
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # initialize return variables, data is NONE and sidemenus are hidden by default
    data = [None] * 5
    sidemenu_styles = [DATA_CONTENT_HIDE] * 5
    graph_triggers = [no_update] * 5
    confirm_button = [no_update] * 5
    refresh_button = [no_update] * 5
    store = no_update
    options_triggers = [no_update] * 5
    date_picker_triggers = [no_update] * 5
    df_name_confirm = no_update
    prompt_trigger = no_update
    data_set_val = [no_update] * 5
    df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]
    # unknown why but this has to be done this way instead of using ALL since ALL was changing the order in seemingly
    # random ways
    prev_selection = [prev_selection_0, prev_selection_1, prev_selection_2, prev_selection_3, prev_selection_4]
    # flag for the dataset selector result menu
    data_set_flag=[]
    for i in range(4):
        data_set_flag.append(Store(id={'type': 'data-set-result', 'index': i}, data= False))
    df_tile = None
    # ------------------------------------------------------------------------------------------------------------------
    # if changed id == '.' due to NEW being requested, preserve data menu display.
    if changed_id == '.':
        raise PreventUpdate

    # if 'tile-data' in changed id but n_clicks == 0, meaning a tile was created from blank display, prevent update
    if '{"index":0,"type":"tile-data"}.n_clicks' == changed_id and not data_clicks[0]:
        for i in range(len(links_style)):
            if links_style[i] == 'fa fa-link':
                prev_selection[i] = df_names[4]
            else:
                prev_selection[i] = df_names[i]
        if 'fa fa-link' in links_style:
            prev_selection[4] = df_names[4]
    # if 'data-menu-close' or 'select-dashboard-dropdown' requested, close all data menus
    # don't close if no data set has been chosen
    elif 'data-menu-close' in changed_id or 'select-dashboard-dropdown' in changed_id:
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
            # if the parent data menu is active and there are any linked tiles, the parent data menu stays open
            if active_tile == 4 and links_style.count('fa fa-link') > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
            # else, the parent data menu is not active while any linked tiles exist
            else:
                deleted_tile = int(closed_tile)
                # if the parent data menu is active and there are no linked tiles, the linked tile was deleted
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
        df_name = df_names[changed_index]
        sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
        if df_name in session:
            # if returning to last loaded un-hide data (generally after look, cancel, then return to start)
            if df_name == prev_selection[changed_index] and prev_selection[changed_index] is not None:
                confirm_button[changed_index] = DATA_CONTENT_HIDE
                refresh_button[changed_index] = {'padding': '10px 13px', 'width': '15px', 'height': '15px',
                                                 'position': 'relative', 'vertical-align': 'top'}
            # if tile has been reset and the dataset is loaded
            elif prev_selection[changed_index] is None:
                data[changed_index] = get_data_menu(changed_index, df_name, df_const=df_const)
                graph_triggers[changed_index] = df_name
                options_triggers[changed_index] = df_name
                df_names[changed_index] = df_name
                prev_selection[changed_index] = df_name
                # set up required triggers
                # parent data menu
                if changed_index == 4:
                    for i in range(len(links_style)):
                        if links_style[i] == 'fa fa-link':
                            prev_selection[i] = df_name
                            # check if the keywords are in df_name
                            if 'OPG010' in df_name:
                                df_tile = 'OPG010'
                            elif 'OPG011' in df_name:
                                df_tile = 'OPG011'
                            if graph_types[i] is None or graph_types[i] in GRAPH_OPTIONS[df_tile]:
                                graph_triggers[i] = df_name
                                options_triggers[i] = df_name
                                df_names[i] = df_name
                # child data menu
                else:
                    graph_triggers[changed_index] = df_name
                    options_triggers[changed_index] = df_name
            # send out a prompt
            elif changed_index == 4:  # prompt with trip prompt
                prompt_trigger = Store(
                    id={'type': 'prompt-trigger', 'index': 5},
                    data=[['loaded_dataset_swap', changed_index], {}, get_label('LBL_Load_Dataset'),
                          get_label('LBL_Load_Dataset_Prompt'), True])
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        confirm_button[i] = DATA_CONTENT_HIDE
                        refresh_button[i] = {'padding': '10px 13px', 'width': '15px', 'height': '15px',
                                             'position': 'relative', 'vertical-align': 'top'}
            else:  # prompt with only two options
                prompt_trigger = Store(
                    id={'type': 'prompt-trigger', 'index': 5},
                    data=[['loaded_dataset_swap', changed_index], {}, get_label('LBL_Load_Dataset'),
                          get_label('LBL_Load_Dataset_Duo_Prompt'), False])
        else:
            # trigger update for all tiles that are linked to the active data menu
            if changed_index == 4:
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        confirm_button[i] = {'padding': '10px 13px', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
                        refresh_button[i] = DATA_CONTENT_HIDE
            confirm_button[changed_index] = {'padding': '10px 13px', 'width': '15px', 'height': '15px',
                                             'position': 'relative', 'vertical-align': 'top'}
            refresh_button[changed_index] = DATA_CONTENT_HIDE
            # if data set is selected but not confirmed use previous selected data set
            if df_name not in session and prev_selection[changed_index] is not None:
                df_name_confirm = prev_selection[changed_index]
    # elif 'data-set' in changed id, reset data tile with new df set as active, keep shown, and trigger graph update
    elif '"type":"confirm-data-set-refresh"}.n_clicks' in changed_id or \
            '"type":"confirm-load-data"}.n_clicks' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        if '"type":"confirm-load-data"}.n_clicks' in changed_id \
                and (prev_selection[changed_index] is not None):
            if df_names[changed_index] not in session and prev_selection[changed_index] is not None:
                df_name_confirm = None
            if changed_index == 4:  # prompt with trip prompt
                prompt_trigger = Store(
                    id={'type': 'prompt-trigger', 'index': 5},
                    data=[['load_dataset', changed_index], {}, get_label('LBL_Load_Dataset'),
                          get_label('LBL_Load_Dataset_Prompt'), True])
            else:  # prompt with only two options
                prompt_trigger = Store(
                    id={'type': 'prompt-trigger', 'index': 5},
                    data=[['load_dataset', changed_index], {}, get_label('LBL_Load_Dataset'),
                          get_label('LBL_Load_Dataset_Duo_Prompt'), False])
        # The first instance that the datasets are loaded in
        else:
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
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        prev_selection[i] = df_name
                        # check if the keywords are in df_name
                        if 'OPG010' in df_name:
                            df_tile = 'OPG010'
                        elif 'OPG011' in df_name:
                            df_tile = 'OPG011'
                        if graph_types[i] is None or graph_types[i] in GRAPH_OPTIONS[df_tile]:
                            graph_triggers[i] = df_name
                            options_triggers[i] = df_name
                            df_names[i] = df_name
            else:
                graph_triggers[changed_index] = df_name
                options_triggers[changed_index] = df_name

            prev_selection[changed_index] = df_name
            confirm_button[changed_index] = DATA_CONTENT_HIDE
            refresh_button[changed_index] = {'padding': '10px 13px', 'width': '15px', 'height': '15px',
                                             'position': 'relative', 'vertical-align': 'top'}
    # elif prompt has been received, handle request for cancel, load, swap dataset, link, unlink
    elif 'prompt-result' in changed_id:
        if prompt_data[0] == 'loaded_dataset_swap' or prompt_data[0] == 'load_dataset':
            tile = prompt_data[1]
            df_name = df_names[tile]
            # see if a trip option or not
            if tile == 4:
                # cancelled, reset dropdown
                if prompt_result == 'op-1' or prompt_result == 'close':
                    sidemenu_styles[tile] = DATA_CONTENT_SHOW
                    if prompt_data[0] == 'loaded_dataset_swap':
                        data_set_val[tile] = prev_selection[tile]
                else:
                    # set previous
                    prev_selection[tile] = df_name
                    df_name = df_names[tile]

                    # if load called, load dataset here
                    if prompt_data[0] == 'load_dataset':
                        session[df_name] = dataset_to_df(df_name)
                        if df_const is None:
                            df_const = {}

                        df_const[df_name] = generate_constants(df_name)
                        store = df_const

                    # reset data menu for tile no matter what
                    data[tile] = get_data_menu(tile, df_name, df_const=df_const)

                    # op-2 is continue the dataset change but unlink my graph
                    # op-3 is continue the dataset change and modify my graph as necessary (keeping the link)
                    # trigger update for all tiles that are linked to the active data menu
                    for i in range(len(links_style)):
                        if links_style[i] == 'fa fa-link':
                            if 'OPG010' in df_name:
                                df_tile = 'OPG010'
                            elif 'OPG011' in df_name:
                                df_tile = 'OPG011'

                            # The graph type is none or mismatch and the option for unlink graph
                            if (graph_types[i] is None or graph_types[i] in GRAPH_OPTIONS[df_tile]) and \
                                    prompt_result != 'op-2':
                                graph_triggers[i] = df_name
                                options_triggers[i] = df_name
                                df_names[i] = df_name
                                prev_selection[i] = df_name
                            else:
                                # [i]= 'fa-fa-unlink'
                                # set the dataset of the new menu from unlinking
                                if type(state_of_display) == dict:
                                    state_of_display = [state_of_display]

                                nid_path = "root"

                                for button in state_of_display:
                                    nid_path += '^||^{}'.format(button['props']['children'])

                                df_names[i] = prev_selection[i]
                                data[i] = get_data_menu(i, df_names[i],
                                                        hierarchy_toggle=parent_hierarchy_toggle,
                                                        level_value=parent_hierarchy_drop,
                                                        nid_path=nid_path,
                                                        graph_all_toggle=parent_graph_child_toggle,
                                                        fiscal_toggle=parent_fiscal_toggle,
                                                        input_method=parent_timeframe,
                                                        num_periods=parent_num_state,
                                                        period_type=parent_period_type,
                                                        prev_selection=prev_selection[i],
                                                        df_const=df_const) if prompt_result == 'op-2' \
                                    else get_data_menu(i, df_names[i],
                                                       prev_selection=prev_selection[i],
                                                       df_const=df_const)
                                refresh_button[i] = {'padding': '10px 0', 'width': '15px',
                                                     'height': '15px',
                                                     'position': 'relative',
                                                     'margin-right': '10px', 'margin-left': '10px',
                                                     'vertical-align': 'top'}

                                if parent_timeframe == "select-range":
                                    date_picker_triggers[i] = {"Input Method": parent_timeframe,
                                                               "Start Year Selection": parent_start_year,
                                                               "End Year Selection": parent_end_year,
                                                               "Start Secondary Selection": parent_start_secondary,
                                                               "End Secondary Selection": parent_end_secondary,
                                                               "Tab": parent_secondary_type}

                                # continue the dataset change and modify my graph as necessary (keeping the link)
                                if prompt_result == 'op-3':
                                    options_triggers[i] = 'fa fa-link'
                                    sidemenu_styles[tile] = DATA_CONTENT_SHOW
                                    prev_selection[i] = df_name
                                # unlink the graph then load new dataset in parent data menu
                                else:
                                    options_triggers[i] = 'fa fa-unlink'
                                    data_set_flag[i] = Store(id={'type': 'data-set-result', 'index': i},
                                                                 data= True)
            # duo options
            else:
                if prompt_result == 'ok':
                    links_style[tile] = 'fa fa-unlink'
                    prev_selection[tile] = df_name

                    if prompt_data[0] == 'load_dataset':
                        session[df_name] = dataset_to_df(df_name)

                        if df_const is None:
                            df_const = {}

                        df_const[df_name] = generate_constants(df_name)
                        store = df_const
                    # [i]= 'fa-fa-unlink'
                    # set the dataset of the new menu from unlinking
                    if type(state_of_display) == dict:
                        state_of_display = [state_of_display]

                    nid_path = "root"

                    for button in state_of_display:
                        nid_path += '^||^{}'.format(button['props']['children'])

                    data[tile] = get_data_menu(tile, df_names[tile],
                                               prev_selection=prev_selection[tile],
                                               df_const=df_const)
                    refresh_button[tile] = {'padding': '10px 0', 'width': '15px',
                                            'height': '15px',
                                            'position': 'relative',
                                            'margin-right': '10px', 'margin-left': '10px',
                                            'vertical-align': 'top'}

                    options_triggers[tile] = df_name
                    sidemenu_styles[tile] = DATA_CONTENT_SHOW
                    prev_selection[tile] = df_name
                # cancel was called
                else:
                    sidemenu_styles[tile] = DATA_CONTENT_SHOW

                    if prompt_data[0] == 'loaded_dataset_swap':
                        data_set_val[tile] = prev_selection[tile]
        # elif 'RESET' dashboard requested, hide and reset all data tiles
        elif prompt_data[0] == 'reset' and prompt_result == 'ok':
            for i in range(len(data)):
                data[i] = get_data_menu(i, df_const=df_const)
                prev_selection[i] = None
        else:
            raise PreventUpdate
    # else, 'data', 'tile-link', or 'select-layout' requested
    else:
        changed_index = int(search(r'\d+', changed_id).group())
        # if 'tile-link' requested
        if '"type":"tile-link"}.className' in changed_id:
            # if linked --> unlinked: copy parent tile data to unique tile data
            if links_style[changed_index] == 'fa fa-unlink':
                parent_copy = copy.deepcopy(data_states[4])
                data[changed_index] = change_index(parent_copy, changed_index)
            elif links_style[changed_index] == 'fa fa-link':
                df_name = df_names[4]
                prev_selection[changed_index] = df_name
                data_set_val[changed_index] = df_name
                graph_triggers[changed_index] = df_name
                options_triggers[changed_index] = df_name
                df_names[changed_index] = df_name

        # if tile is child to parent and a layout was not selected, display parent data
        if links_style[changed_index] == 'fa fa-link' and '"type":"select-layout-dropdown"}.value' not in changed_id:
            # if 'data' requested or a data menu is already open, display parent data
            if '"type":"tile-data"}.n_clicks' in changed_id or sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
        # if tile is not linked to parent or a layout was selected, display unique data side-menu
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
            # for all tiles besides parent data tile do not update if style has not changed
            if i != 4:
                sidemenu_styles[i] = no_update
            # if parent data is SHOWN, do not prevent update to force trigger highlight tiles callback
            elif sidemenu_styles[4] != DATA_CONTENT_SHOW:
                sidemenu_styles[4] = no_update

    return (data[0], data[1], data[2], data[3], data[4],
            sidemenu_styles[0], sidemenu_styles[1], sidemenu_styles[2], sidemenu_styles[3], sidemenu_styles[4],
            graph_triggers[0], graph_triggers[1], graph_triggers[2], graph_triggers[3], store,
            confirm_button[0], confirm_button[1], confirm_button[2], confirm_button[3], confirm_button[4],
            refresh_button[0], refresh_button[1], refresh_button[2], refresh_button[3], refresh_button[4],
            prev_selection[0], prev_selection[1], prev_selection[2], prev_selection[3], prev_selection[4],
            data_set_val[0], data_set_val[1], data_set_val[2], data_set_val[3], data_set_val[4],
            options_triggers[0], options_triggers[1], options_triggers[2], options_triggers[3], prompt_trigger,
            df_name_confirm,
            date_picker_triggers[0], date_picker_triggers[1], date_picker_triggers[2], date_picker_triggers[3],
            date_picker_triggers[4], data_set_flag)


app.clientside_callback(
    """
        function _resize_for_resizable_graphs(load_data_trigger, refresh_data_trigger){
            // This code is added to ensure the graph area is always resized to fit, 
            // otherwise the graphing area will be squished or put to one side
            window.dispatchEvent(new Event('resize'));
            return dash_clientside.no_update;
        }
    """,
    Output({'type': 'data-tile', 'index': 4}, 'data-throwaway'),
    Input({'type': 'data-tile', 'index': ALL}, 'style'),
)

# http://adripofjavascript.com/blog/drips/object-equality-in-javascript.html#:~:text=Here%20is%20a%20very%20basic,are%20not%20equivalent%20if%20(aProps.
app.clientside_callback(
    """
       function _data_set_confirmation_visuals(load_data_trigger, refresh_data_trigger){
            let DATA_CONTENT_HIDE = {'display': 'none'};  
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

# Highlight tiles child to displayed data sidebar.
for x in range(4):
    app.clientside_callback(
        """
        function _highlight_tiles(_sidebar_styles, link_state, sidebar_style, parent_sidebar_style){
            let tile_class = dash_clientside.no_update;
            let DATA_CONTENT_SHOW = {
                'max-width': '300px', 
                'min-width': '300px',
                'background-color':'#fffafa',
                'border-right': '1px solid #c7c7c7',
                'flex-grow': '1', 
                'display': 'inline'};

            if (isEquivalent(sidebar_style, DATA_CONTENT_SHOW) || 
                (isEquivalent(parent_sidebar_style, DATA_CONTENT_SHOW) && link_state == 'fa fa-link')){
                tile_class = 'tile-highlight';
            }
            else{
                tile_class = 'tile-container';
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
        [Input({'type': 'tile-save-trigger', 'index': x}, 'data')],
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
    """
    function datasetLoadScreen(n_click_load, n_click_reset, float_menu_result, prompt_result, float_menu_data,
                               selected_dashboard, prompt_data, prev_selected) {
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
        let changed_index = null;
        if (triggered.match(/\d+/)){
            changed_index = parseInt(triggered.match(/\d+/)[0]);
        }
        if (triggered != "" &&
             (changed_index != null && n_click_load != ',,,,' && prompt_result != "op-1" &&
              prompt_result != "close" && prev_selected[changed_index] == null || n_click_reset != ',,,,' ||
             (typeof float_menu_data != 'undefined' && float_menu_data[0] == 'dashboard_layouts' &&
              selected_dashboard != null && float_menu_result == 'ok') ||
             (typeof prompt_data != 'undefined' && prompt_data[0] == 'load_dataset' && prompt_result != "op-1" &&
              prompt_result != "close" && !triggered.includes('confirm-load-data')))){
            if ($("._data-loading")[0]){
                if (prompt_result == "cancel"){
                    try{
                        document.getElementById('loading').remove();
                    }catch{ /* Do Nothing */ }
                }
                else{
                    return 0;
                }
            }
            else if(triggered.includes('"prompt-result')){
                if (prompt_result == "cancel"){
                    try{
                            document.getElementById('loading').remove();
                        }catch{ /* Do Nothing */ }
                }
                else if (prompt_result == "op-2"){
                        let newDiv = document.createElement('div');
                        newDiv.className = '_data-loading';
                        newDiv.id = 'loading';
                        document.body.appendChild(newDiv, document.getElementById('content'));
                }
                else {
                        return 0;
                }
            } 
            else {
                // Do something if class does not exist
                let newDiv = document.createElement('div');
                newDiv.className = '_data-loading';
                newDiv.id = 'loading';
                document.body.appendChild(newDiv, document.getElementById('content'));
            }   

        }
        return 0;
    }
    """,
    Output('dataset-confirmation-symbols', 'n_clicks'),
    [Input({'type': 'confirm-load-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': ALL}, 'n_clicks'),
     Input({'type': 'float-menu-result', 'index': 1}, 'children'),
     Input({'type': 'prompt-result', 'index': 2}, 'children')],
    [State('float-menu-title', 'data-'),
     State('select-dashboard-dropdown', 'value'),
     State('prompt-title', 'data-'),
     State({'type': 'data-set-prev-selected', 'index': ALL}, 'data')],
    prevent_initial_call=True
)

app.clientside_callback(
    """
    function datasetRemoveLoadScreen(data, graph_displays, num_tiles,result_0,result_1,result_2) {
        let triggered = dash_clientside.callback_context.triggered.map(t => t.prop_id);
        if (triggered.includes("df-constants-storage.data") || triggered.includes("num-tiles.data-num-tiles")){
            try{
                document.getElementById('loading').remove();
            }catch{ /* Do Nothing */ }
        }
        else {
            triggered = triggered[triggered.length - 1];
            let tile = parseInt(triggered.match(/\d+/)[0]) + 1;
            if (tile == num_tiles){
                try{
                    document.getElementById('loading').remove();
                }catch{ /* Do Nothing */ }
            }
        }
        return 0;
    }
    """,
    Output('df-constants-storage', 'n_clicks'),
    [Input('df-constants-storage', 'data'),
     Input({'type': 'graph_display', 'index': ALL}, 'children'),
     Input({'type': 'float-menu-result', 'index': 1}, 'children'),
     Input('num-tiles', 'data-num-tiles')],
    prevent_initial_call=True
)

# *************************************************PROMPT*********************************************************


# Initialize prompt.
app.clientside_callback(
    """
    function _serve_prompt(prompt_trigger_0, prompt_trigger_1, prompt_trigger_2, prompt_trigger_3, prompt_trigger_4,
             prompt_trigger_5, close_n_clicks, cancel_n_clicks, ok_n_clicks, op1_n_clicks, op2_n_clicks, op3_n_clicks, 
             prompt_data){
        // init variables
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
        let prompt_trigger = dash_clientside.no_update;
        let result = dash_clientside.no_update;
        let result_0 = dash_clientside.no_update;
        let result_1 = dash_clientside.no_update;
        let result_2 = dash_clientside.no_update;
        let duo_style = {};
        let trip_style = {'display': 'none'};
        
        // if input, serve the prompt
        if (triggered.includes('prompt-trigger')){
            let trigger_arr = [prompt_trigger_0, prompt_trigger_1, prompt_trigger_2, prompt_trigger_3, prompt_trigger_4,
                               prompt_trigger_5];
            let tile = triggered.match(/\d+/)[0];
            prompt_trigger = trigger_arr[tile];
            if (prompt_trigger[4]){
                duo_style = {'display': 'none'};
                trip_style = {};
            } 
        }
        // else, return what was clicked
        else {
            if (triggered == 'prompt-close.n_clicks') {result = 'close';}
            else if (triggered == 'prompt-cancel.n_clicks'){result = 'cancel';}
            else if (triggered == 'prompt-ok.n_clicks'){result = 'ok';}
            else if (triggered == 'prompt-option-1.n_clicks'){result = 'op-1';}
            else if (triggered == 'prompt-option-2.n_clicks'){result = 'op-2';}
            else if (triggered == 'prompt-option-3.n_clicks'){result = 'op-3';}
            
            prompt_trigger = [prompt_data, {'display': 'none'}, dash_clientside.no_update, dash_clientside.no_update];
            
            // ensure it gets returned to correct callback
            switch(prompt_data[0]){
                case 'delete':
                case 'overwrite':
                case 'link':
                    result_0 = result;
                    break;
                case 'delete_dashboard':
                case 'overwrite_dashboard':
                case 'close':
                    result_1 = result;
                    break;
                case 'reset':
                    result_1 = result;
                    result_2 = result;
                    break;
                case 'loaded_dataset_swap':
                case 'load_dataset':
                    result_2 = result;
                    break;
            }
        }
        
        return [prompt_trigger[0], prompt_trigger[1], prompt_trigger[2], prompt_trigger[3], 
                result_0, result_1, result_2, duo_style, trip_style];
    }
    """,
    [Output('prompt-title', 'data-'),  # index value and reason for prompt
     Output('prompt-obscure', 'style'),
     Output('prompt-title', 'children'),
     Output('prompt-body', 'children'),
     Output({'type': 'prompt-result', 'index': 0}, 'children'),  # _manage_tile_save_load_trigger() callback
     Output({'type': 'prompt-result', 'index': 1}, 'children'),  # _manage_dashboard_saves_and_reset() callback
     Output({'type': 'prompt-result', 'index': 2}, 'children'),  # _manage_data_sidemenus() callback
     Output('prompt-button-wrapper-duo', 'style'),
     Output('prompt-button-wrapper-trip', 'style')],
    [Input({'type': 'prompt-trigger', 'index': 0}, 'data'),  # tile 0
     Input({'type': 'prompt-trigger', 'index': 1}, 'data'),  # tile 1
     Input({'type': 'prompt-trigger', 'index': 2}, 'data'),  # tile 2
     Input({'type': 'prompt-trigger', 'index': 3}, 'data'),  # tile 3
     Input({'type': 'prompt-trigger', 'index': 4}, 'data'),  # dashboard
     Input({'type': 'prompt-trigger', 'index': 5}, 'data'),  # sidemenus
     Input('prompt-close', 'n_clicks'),
     Input('prompt-cancel', 'n_clicks'),
     Input('prompt-ok', 'n_clicks'),
     Input('prompt-option-1', 'n_clicks'),
     Input('prompt-option-2', 'n_clicks'),
     Input('prompt-option-3', 'n_clicks')],
    State('prompt-title', 'data-'),
    prevent_initial_call=True
)

# this function gets called on graph draw and sets a JS function to the graph display if there isn't one
# attached function then sends edited values on plot changes (edits, clicks, moves of legend, etc.) to the following:
# {"index":x,"type":"xaxis-title"}, {"index":x,"type":"yaxis-title"},
# {"index":x,"type":"x-legend"}, {"index":x,"type":"y-legend"}
app.clientside_callback(
    """
    function _update_axes_titles(graph, hasTrigger){
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));

        let tile = triggered.match(/\d+/)[0];
        let javascript = dash_clientside.no_update;
        
        if (hasTrigger == null){
            javascript = `
                let target = '{"index":${tile},"type":"graph_display"}';  
                $(document.getElementById(target)).on('plotly_relayout', (e) => {  
                    let x_axis = dash_clientside.no_update;
                    let y_axis = dash_clientside.no_update;
                    let x_legend = dash_clientside.no_update;
                    let y_legend = dash_clientside.no_update;
                    let x_modified = false;
                    let y_modified = false;
                    
                    // try setting the values if they exist
                    try { 
                        x_axis = e.target.layout.xaxis.title.text;
                    } catch { /* Do Nothing */}
                    try { 
                        y_axis = e.target.layout.yaxis.title.text;
                    } catch { /* Do Nothing */}
                    
                    try { 
                        x_legend = e.target.layout.legend.x;
                    } catch { /* Do Nothing */}
                    try { 
                        y_legend = e.target.layout.legend.y;
                    } catch { /* Do Nothing */}
                    
                    setProps({ 
                        'event': {'x_axis': x_axis, 
                                  'y_axis': y_axis,
                                  'x_legend': x_legend,
                                  'y_legend': y_legend,
                                  'x_modified': x_modified,
                                  'y_modified': y_modified}
                    });
                });
            `
        }
        
        return [true, javascript];
    }
    """,
    [Output({'type': 'graph_display', 'index': MATCH}, 'data-'),
     Output({'type': 'javascript', 'index': MATCH}, 'run')],
    Input({'type': 'graph_display', 'index': MATCH}, 'children'),
    State({'type': 'graph_display', 'index': MATCH}, 'data-'),
    prevent_initial_call=True
)

# The above function set on the graph_display sets a prop as an event to the javascript object which will set the
# axis_titles
for x in range(4):
    app.clientside_callback(
        """
        function _update_axes_titles(event, dfConst, graphType, dfName, dfNameParent, linkState,argValue){
            if(linkState == 'fa fa-link'){
                    dfName=dfNameParent;
                }
            if(event.x_axis != ""){
                switch(graphType){
                    case 'Line':
                    case 'Scatter':
                        if(event.x_axis != 'Date of Event'){
                            event.x_modified = true;
                            break;
                        }
                        else{
                            event.x_modified = false;
                            break;
                        }
                    case 'Bar':
                        if (argValue[2] == 'Horizontal'){
                            if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(event.x_axis)){
                                event.x_modified = false;
                            }
                            else{
                                event.x_modified = true;
                            }
                            temp=event.x_axis;
                            break;
                        }
                        else if (event.x_axis == ""){
                            event.x_modified = false;
                            break;
                        }
                        else{
                            event.x_modified = true;
                            break;
                        }
                    case 'Bubble':
                        string= event.x_axis.split(" (")
                        if(string.length==1){
                            if(argValue[0]=='Time' && event.x_axis == 'Time'){
                                event.x_modified = false;
                                break;
                            }
                            else{ 
                                event.x_modified = true;
                                break;
                            }
                        }
                        else{
                            string[1]=string[1].replace(')','')
                            if(dfConst[dfName]['VARIABLE_OPTION_LISTS'].includes(string[0])){
                                if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(string[1])){
                                    event.x_modified = false;
                                    break;
                                }
                            }
                            event.x_modified = true;
                            break;
                        }
                    case 'Box_Plot':
                        if(argValue[1]=='Vertical'){
                            if (event.x_axis == ""){
                                event.x_modified = false;
                            }
                            else{
                                event.x_modified = true;
                            }
                            temp=event.x_axis;
                            break;  
                        }
                        else if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(event.x_axis)){
                            event.x_modified = false;
                            break;
                        }
                        else{
                            event.x_modified = true;
                            break;
                        }
                    default:
                        event.x_modified = false;
                        break;
                }
            }
            if(event.y_axis != ""){
                switch(graphType){
                    case 'Line':
                    case 'Scatter':
                        if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(event.y_axis)){
                        event.y_modified = false;
                        break;
                        }
                        else{
                            event.y_modified = true;
                            break;
                        }
                    case 'Bar':
                        if (argValue[2] == 'Horizontal'){
                            if (event.y_axis == ""){
                                event.y_modified = false;
                            }
                            else{
                                event.y_modified = true;
                            }
                            event.x_axis = event.y_axis;
                            event.y_axis = temp;
                            break;
                        }
                        else if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(event.y_axis)){
                            event.y_modified = false;
                            break;
                        }
                        else{
                           event.y_modified = true;
                           break;
                        }
                    case 'Bubble':
                        string= event.y_axis.split(" (")
                        if(string.length==1){
                            if(argValue[0]=='Time'){
                                if(dfConst[dfName]['VARIABLE_OPTION_LISTS'].includes(string[0])){
                                    event.y_modified = false;
                                    break;
                                }
                                else{
                                    event.y_modified = true;
                                }
                                break;
                            }
                            else{ 
                                event.y_modified = true;
                                break;
                            }
                        }
                        else{
                            string[1]=string[1].replace(')','')
                            if(dfConst[dfName]['VARIABLE_OPTION_LISTS'].includes(string[0])){
                                if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(string[1])){
                                    event.y_modified = false;
                                    break;
                                }
                            }
                            event.y_modified = true;
                            break;
                        }
                    case 'Box_Plot':
                        if(argValue[1]=='Vertical'){
                            if(dfConst[dfName]['MEASURE_TYPE_VALUES'].includes(event.y_axis)){
                                event.y_modified = false;
                            }
                            else{
                                event.y_modified = true;
                            }
                            event.x_axis = event.y_axis;
                            event.y_axis = temp;
                            break;
                        }
                        else if (event.y_axis == ""){
                            event.y_modified = false;
                            break;
                        }
                        else{
                            event.y_modified = true;
                            break;
                        }  
                    default:
                        event.y_modified = false;
                        break;
                }
            }
            return [event.x_axis, event.y_axis, event.x_legend, event.y_legend, event.x_modified, event.y_modified];
        }
        """,
        [Output({"type": "xaxis-title", "index": x}, 'value'),
         Output({"type": "yaxis-title", "index": x}, 'value'),
         Output({'type': 'x-pos-legend', 'index': x}, 'value'),
         Output({'type': 'y-pos-legend', 'index': x}, 'value'),
         Output({'type': 'x-modified', 'index': x}, 'data'),
         Output({'type': 'y-modified', 'index': x}, 'data')],
        Input({'type': 'javascript', 'index': x}, 'event'),
        [State('df-constants-storage', 'data'),
         State({'type': 'graph-type-dropdown', 'index': x}, 'value'),
         State({'type': 'data-set', 'index': x}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         State({'type': 'tile-link', 'index': x}, 'className'),
         State({'type': 'args-value: {}'.replace("{}", str(x)), 'index': ALL}, 'value')],
        prevent_initial_call=True
    )
