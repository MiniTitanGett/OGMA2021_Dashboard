######################################################################################################################
"""
user_interface_callbacks.py

stores all callbacks for the user interface
"""
######################################################################################################################

# External Packages
import dash
import dash_html_components as html
import dash_core_components as dcc
import copy
from dash import no_update
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from re import search
from dash import no_update

# Internal Packages
from apps.app0003.layouts import get_line_graph_menu, get_bar_graph_menu, get_scatter_graph_menu, get_table_graph_menu, \
    get_tile_layout, change_index, get_data_menu, get_box_plot_menu
from apps.app0003.app import app
from apps.app0003.data import VIEW_CONTENT_HIDE, VIEW_CONTENT_SHOW, CUSTOMIZE_CONTENT_HIDE, CUSTOMIZE_CONTENT_SHOW, \
    DATA_CONTENT_HIDE, DATA_CONTENT_SHOW, get_label, LAYOUT_CONTENT_SHOW, \
    LAYOUT_CONTENT_HIDE, X_AXIS_OPTIONS, DATA_OPTIONS, MEASURE_TYPE_OPTIONS

from apps.app0003.saving_functions import saved_layouts, delete_layout, save_graph_state, save_layout_to_file, \
    save_layout_to_db


# Contents:
#   MAIN LAYOUT
#       - _new_and_delete()
#       - _unlock_new_button()
#   TILE LAYOUT
#       - _switch_tile_tab()
#   CUSTOMIZE TAB
#       - _update_graph_menu()
#   DATA SIDE-MENU
#       - _change_link()
#       - _clear_and_copy_data_menu()
#       - _show_data_menu()
#       - _highlight_slaved_tiles()


# *************************************************MAIN LAYOUT********************************************************

# NEW and DELETE button functionality
@app.callback(
    [Output('div-body', 'children'),
     Output('button-new-wrapper', 'children'),
     Output('tile-closed-trigger', 'data-'),
     # Output({'type': 'tile-index', 'index': ALL}, 'data-tile-index')
     ],
    [Input('button-new', 'n_clicks'),
     Input({'type': 'tile-close', 'index': ALL}, 'n_clicks')],
    [State({'type': 'tile', 'index': ALL}, 'children')]
)
def _new_and_delete(new_clicks, _close_clicks, input_tiles):
    """
    :param new_clicks: Detects user clicking 'NEW' button in master navigation bar and encodes the number of tiles to
    display
    :param _close_clicks: Detects user clicking close ('x') button in top right of tile
    :param input_tiles: State of all currently existing tiles
    :return: Layout of tiles for the main body, a new NEW button whose n_clicks data encodes the number of tiles to
    display, and updates the tile-closed-trigger div with the index of the deleted tile
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    deleted_tile = no_update
    # if DELETE button pressed: pop deleted input_tile index and shift following indices left and adjust main layout
    if 'tile-close' in changed_id:
        new_clicks -= 1
        flag = False
        for i in range(len(input_tiles)):
            if '{"index":{},"type":"tile-close"}.n_clicks'.replace("{}", str(i)) in changed_id:
                input_tiles.pop(i)
                flag = True
                deleted_tile = str(i)
            elif flag:
                input_tiles[i - 1] = change_index(input_tiles[i - 1], i - 1)
        children = get_tile_layout(new_clicks, input_tiles)
    # if NEW button pressed: adjust main layout and disable NEW button until it is unlocked at the end of callback chain
    elif 'button-new' in changed_id:
        children = get_tile_layout(new_clicks, input_tiles)
    # else, the page loaded, set default appearance and unlock NEW button
    else:
        children = get_tile_layout(1, input_tiles)
    # store the current number of tiles in NEW button's n_clicks data
    new_button = html.Button(
        className='master-nav', n_clicks=new_clicks, children=get_label('New'), id='button-new', disabled=True)
    return children, new_button, deleted_tile


# unlock NEW button after end of callback chain
@app.callback(
    Output('button-new', 'disabled'),
    [Input({'type': 'div-graph-options', 'index': ALL}, 'children')]
)
def _unlock_new_button(graph_options):
    """
    :param graph_options: Detects when the last callback, _update_graph_menu, in the UI update order finishes and
    encodes the state of all graph menus
    :return: Enables the NEW button
    """
    # do not unlock NEW button if there are 4 tiles
    if len(graph_options) == 4:
        raise PreventUpdate
    return False


# *************************************************TILE LAYOUT********************************************************

# manage VIEW <-> CUSTOMIZE <--> LAYOUTS for each tab
for x in range(0, 4):
    @app.callback(
        [Output({'type': 'tile-view-content', 'index': x}, 'style'),
         Output({'type': 'tile-customize-content', 'index': x}, 'style'),
         Output({'type': 'tile-layouts-content', 'index': x}, 'style'),
         Output({'type': 'tile-view', 'index': x}, 'className'),
         Output({'type': 'tile-layouts', 'index': x}, 'className'),
         Output({'type': 'tile-customize', 'index': x}, 'className')],
        [Input({'type': 'tile-view', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-customize', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-layouts', 'index': x}, 'n_clicks')],
        [State({'type': 'tile-view-content', 'index': x}, 'style'),
         State({'type': 'tile-customize-content', 'index': x}, 'style'),
         State({'type': 'tile-layouts-content', 'index': x}, 'style'),
         State({'type': 'tile-view', 'index': x}, 'className'),
         State({'type': 'tile-customize', 'index': x}, 'className'),
         State({'type': 'tile-layouts', 'index': x}, 'className')]
    )
    def _switch_tile_tab(_view_clicks, _customize_clicks, _layouts_clicks, view_content_style_state,
                         customize_content_style_state, layouts_content_style_state,
                         view_state, customize_state, layouts_state):
        """
        :param _view_clicks: Detects the user clicking the VIEW button
        :param _customize_clicks: Detects the user clicking the CUSTOMIZE button
        :param view_content_style_state: Style of the VIEW tab, either VIEW_CONTENT_SHOW or
        VIEW_CONTENT_HIDE
        :param customize_content_style_state: Style of the CUSTOMIZE tab, either CUSTOMIZE_CONTENT_SHOW or
        CUSTOMIZE_CONTENT_HIDE
        :param view_state: ClassName of the VIEW button, either 'tile-nav-selected' or 'tile-nav'
        :param customize_state: ClassName of the CUSTOMIZE button, either 'tile-nav-selected' or 'tile-nav'
        :return: The styles of the CUSTOMIZE and VIEW tabs as being either hidden or shown, and the classNames of the
        VIEW and CUSTOMIZE buttons as being either selected or unselected
        """
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        # if view button was pressed, display view content and set view button as selected
        if '"type":"tile-view"}.n_clicks' in changed_id:
            # protect against spam clicking
            if view_content_style_state == VIEW_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_SHOW
            customize_content_style = CUSTOMIZE_CONTENT_HIDE
            layouts_content_style = LAYOUT_CONTENT_HIDE
            view_className = 'tile-nav-selected'
            customize_className = 'tile-nav'
            layouts_className = 'save-nav'
        # if customize button was pressed, display customize content and set customize button as selected
        elif '"type":"tile-customize"}.n_clicks' in changed_id:
            # protect against spam clicking
            if customize_content_style_state == CUSTOMIZE_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_HIDE
            customize_content_style = CUSTOMIZE_CONTENT_SHOW
            layouts_content_style = LAYOUT_CONTENT_HIDE
            view_className = 'tile-nav'
            customize_className = 'tile-nav-selected'
            layouts_className = 'save-nav'
            # if layouts button was pressed, display layouts content and set layouts button as selected
        elif '"type":"tile-layouts"}.n_clicks' in changed_id:
            # protect against spam clicking
            if layouts_content_style_state == LAYOUT_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_HIDE
            customize_content_style = CUSTOMIZE_CONTENT_HIDE
            layouts_content_style = LAYOUT_CONTENT_SHOW
            view_className = 'tile-nav'
            customize_className = 'tile-nav'
            layouts_className = 'save-nav-selected'
        # if the main layout was updated by DELETE or NEW or page loaded (meaning changed_id == '.') conserve settings
        else:
            view_content_style = view_content_style_state
            customize_content_style = customize_content_style_state
            layouts_content_style = layouts_content_style_state
            view_className = view_state
            customize_className = customize_state
            layouts_className = layouts_state
        return view_content_style, customize_content_style, layouts_content_style, view_className, layouts_className, \
               customize_className


# ************************************************CUSTOMIZE TAB*******************************************************
# update graph menu to match selected graph type
@app.callback(
    Output({'type': 'div-graph-options', 'index': MATCH}, 'children'),
    [Input({'type': 'graph-type-dropdown', 'index': MATCH}, 'value'),
     # ------------------------------------------------------------
     # added for loading
     # selected layout
     Input({'type': 'select-layout-dropdown', 'index': MATCH}, 'value')
     # ------------------------------------------------------------
     ],
    [
        State({'type': 'div-graph-options', 'index': MATCH}, 'children'),
        State({'type': 'tile', 'index': ALL}, 'className')]
)
def _update_graph_menu(selected_graph_type, selected_layout, graph_options_state, input_tiles):
    """
    :param selected_graph_type: Selected graph type, ie. 'bar', 'line', etc.
    :param graph_options_state: State of the current graph options div
    :param input_tiles: List of the states of the classNames of all existing tiles
    :return: Graph menu corresponding to selected graph type
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # if graph type dropdown value changed or tile was created provide graph menu
    if '"type":"graph-type-dropdown"}.value' in changed_id or not graph_options_state \
            or '"type":"select-layout-dropdown"}.value' in changed_id:
        # if graph type dropdown value changed the tile id is in changed_id
        if '"type":"graph-type-dropdown"}.value' in changed_id:
            tile = search(r'\d+', changed_id).group()
        # if tile was created the tile id is the index of the last tile
        else:
            tile = len(input_tiles) - 1
        # ------------------------------------------------------------
        # added for loading works for loading in
        # This causes the saved layout to load in the customization menu as long as the
        #  selected graph is same as saved
        if selected_layout != '' and saved_layouts[selected_layout][0] == selected_graph_type:
            selected_graph_type = saved_layouts[selected_layout][0]
            x_axis = no_update
            y_axis = no_update
            measure_type = no_update
            number_of_columns = no_update
            axis_measure = no_update
            graphed_variables = no_update
            graph_orientation = no_update
            if selected_graph_type == 'Line' or selected_graph_type == 'Scatter' or selected_graph_type == 'Bar':
                x_axis = str(saved_layouts[selected_layout][1][0])
                measure_type = str(saved_layouts[selected_layout][1][1])
                y_axis = saved_layouts[selected_layout][1][2]
            elif selected_graph_type == 'Box Plot':
                axis_measure = str(saved_layouts[selected_layout][1][0])
                graphed_variables = saved_layouts[selected_layout][1][1]
                graph_orientation = str(saved_layouts[selected_layout][1][2])
            else:
                number_of_columns = int(saved_layouts[selected_layout][1][1])
        else:
            x_axis = no_update
            y_axis = no_update
            measure_type = no_update
            number_of_columns = no_update
            axis_measure = no_update
            graphed_variables = no_update
            graph_orientation = no_update
            if selected_graph_type == 'Line' or selected_graph_type == 'Scatter':
                x_axis = str(X_AXIS_OPTIONS[0])
                y_axis = str(DATA_OPTIONS[0])
                measure_type = str(MEASURE_TYPE_OPTIONS[0])
            elif selected_graph_type == 'Box Plot':
                axis_measure = str(MEASURE_TYPE_OPTIONS[0])
                graphed_variables = str(DATA_OPTIONS[0])
                graph_orientation = 'Horizontal'
            elif selected_graph_type == 'Table':
                number_of_columns = 15
            else:
                bar_x_axis_options = ['Specific Item', 'Variable Names']
                x_axis = str(bar_x_axis_options[0])
                y_axis = str(DATA_OPTIONS[0])
                measure_type = str(MEASURE_TYPE_OPTIONS[0])
        # ------------------------------------------------------------
        # apply graph selection and generate menu
        if selected_graph_type == 'Line':
            menu = get_line_graph_menu(tile, x_axis, y_axis, measure_type)
        elif selected_graph_type == 'Bar':
            menu = get_bar_graph_menu(tile, x_axis, y_axis, measure_type)
        elif selected_graph_type == 'Scatter':
            menu = get_scatter_graph_menu(tile, x_axis, y_axis, measure_type)
        elif selected_graph_type == 'Table':
            menu = get_table_graph_menu(tile, number_of_columns)
        elif selected_graph_type == 'Box Plot':
            menu = get_box_plot_menu(tile, axis_measure, graphed_variables, graph_orientation)  #
        else:
            raise PreventUpdate
    # else, make no changes
    else:
        raise PreventUpdate
    return menu


# ************************************************LAYOUTS TAB*******************************************************
# ---------------------------------------------------
# added for save functionality
# ---------------------------------------------------

for y in range(0, 4):
    @app.callback(
        [  # save message
            Output({'type': 'save-message', 'index': y}, 'children'),
            # saved-graphs, saved layouts options
            Output({'type': 'select-layout-dropdown', 'index': y}, 'options'),
            # remove, delete layout options
            Output({'type': 'delete-layout-dropdown', 'index': y}, 'options'),
            # layout-div, dropdown that holds all of the saved layouts options
            Output({'type': 'select-layout-dropdown-div', 'index': y}, 'children'),
            # delete-layout, drop down that holds all of the saved layouts for deleting
            Output({'type': 'delete-layout-dropdown-div', 'index': y}, 'children'),
        ],
        [  # save, the save button
            Input({'type': 'save-button', 'index': ALL}, 'n_clicks'),
            # remove, graph to remove
            Input({'type': 'delete-layout-dropdown', 'index': ALL}, 'value'),
        ],
        [  # the inputs that make the unique layout, these will be different due to the different data and set up
            # tile title
            State({'type': 'tile-title', 'index': ALL}, 'value'),
            # Link state
            State({'type': 'tile-link', 'index': y}, 'className'),
            # ---------------------------------------------------
            # From customize tab
            # graph type
            State({'type': 'graph-type-dropdown', 'index': y}, 'value'),
            # x-axis args_list[0], y-axis args_list[1], measure type args_list[3]
            State({'type': 'args-value: {}'.replace("{}", str(y)), 'index': ALL}, 'value'),
            # ---------------------------------------------------
            # from data menu master
            # year start
            State({'type': 'start-year-input', 'index': 4}, 'value'),
            # year end
            State({'type': 'end-year-input', 'index': 4}, 'value'),
            # hierarchy toggle
            State({'type': 'hierarchy-toggle', 'index': 4}, 'on'),
            # level filter
            State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
            # specific dropdown
            State({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'value'),
            # hierarchy display list
            State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
            # fiscal year toggle
            State({'type': 'fiscal-year-toggle', 'index': 4}, 'on'),
            # radio time frame
            State({'type': 'radio-timeframe', 'index': 4}, 'value'),
            # secondary input start (week, quarter, month)
            State({'type': 'start-secondary-input', 'index': 4}, 'value'),
            # secondary input end (week, quarter, month)
            State({'type': 'end-secondary-input', 'index': 4}, 'value'),
            # last x time period
            State({'type': 'num-periods', 'index': 4}, 'value'),
            # time period
            State({'type': 'period-type', 'index': 4}, 'value'),
            # tab
            State({'type': 'start-year-input', 'index': 4}, 'name'),
            # ---------------------------------------------------
            # from data menu for followers
            # year start
            State({'type': 'start-year-input', 'index': y}, 'value'),
            # year end
            State({'type': 'end-year-input', 'index': y}, 'value'),
            # hierarchy toggle
            State({'type': 'hierarchy-toggle', 'index': y}, 'on'),
            # level filter value
            State({'type': 'hierarchy_level_dropdown', 'index': y}, 'value'),
            # specific dropdown value
            State({'type': 'hierarchy_specific_dropdown', 'index': y}, 'value'),
            # hierarchy display list
            State({'type': 'hierarchy_display_button', 'index': y}, 'children'),
            # fiscal year toggle
            State({'type': 'fiscal-year-toggle', 'index': y}, 'on'),
            # radio time frame
            State({'type': 'radio-timeframe', 'index': y}, 'value'),
            # secondary input start (week, quarter, month)
            State({'type': 'start-secondary-input', 'index': y}, 'value'),
            # secondary input end (week, quarter, month)
            State({'type': 'end-secondary-input', 'index': y}, 'value'),
            # last x time period
            State({'type': 'num-periods', 'index': y}, 'value'),
            # time period
            State({'type': 'period-type', 'index': y}, 'value'),
            # tab
            State({'type': 'start-year-input', 'index': y}, 'name')
        ]
    )
    def save_graph(save_clicks, remove_layout, graph_title, link_state, graph_type, args_list,
                   master_year_start, master_year_end, master_hierarchy_toggle, master_hierarchy_level_dropdown,
                   master_hierarchy_specific_dropdown, master_state_of_display, master_fiscal_toggle,
                   master_input_method, master_secondary_start, master_secondary_end, master_x_time_period,
                   master_period_type, master_tab, year_start, year_end, hierarchy_toggle, hierarchy_level_dropdown,
                   hierarchy_specific_dropdown, state_of_display, fiscal_toggle, input_method, secondary_start,
                   secondary_end, x_time_period, period_type, tab):
        if link_state == 'fa fa-link':
            fiscal_toggle = master_fiscal_toggle
            year_start = master_year_start
            year_end = master_year_end
            secondary_start = master_secondary_start
            secondary_end = master_secondary_end
            x_time_period = master_x_time_period
            period_type = master_period_type
            input_method = master_input_method
            hierarchy_specific_dropdown = master_hierarchy_specific_dropdown
            hierarchy_toggle = master_hierarchy_toggle
            hierarchy_level_dropdown = master_hierarchy_level_dropdown
            state_of_display = master_state_of_display
            tab = master_tab
        if type(state_of_display) == dict:
            state_of_display = [state_of_display]
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        changed_index = 0
        if changed_id != '.':
            changed_index = int(search(r'\d+', changed_id).group())
        tile_index = int(dash.callback_context.states_list[2]['id']['index'])
        # if this tile was the one that was triggered, proceed
        if tile_index < changed_index and '"type":"save-button"}.n_clicks' in changed_id:
            graph_title = graph_title[changed_index]
            save_graph_state(graph_title, None)
            save_message = no_update
            available_to_load = [{
                'label': key, 'value': key} for key in saved_layouts]
            available_to_delete = [{
                'label': key, 'value': key} for key in saved_layouts]
            loadable_layouts_dropdown = no_update
            deletable_layouts_dropdown = no_update
        elif '"type":"save-button"}.n_clicks' in changed_id or '"type":"delete-layout-dropdown"}.value' in changed_id:
            graph_title = graph_title[changed_index]
            remove_layout = remove_layout[changed_index]
            # this is probably the reason why we are getting the two output objects when we use all as the inputs
            # Checks to see if a title has been inputted and if the user has pressed the save button
            if '"type":"save-button"}.n_clicks' in changed_id:
                if graph_title != '':
                    # checks to see if the title input is already in use
                    if graph_title in saved_layouts and saved_layouts[graph_title] is not None:
                        save_message = get_label('A graph already has this title please enter a different title')
                        # Outputs a new input element with no value
                    else:
                        # elements to save are all of the attributes that effect what the graph is displaying
                        # this is for level filter
                        if not hierarchy_toggle:
                            elements_to_save = [graph_type, args_list, fiscal_toggle, year_start, year_end,
                                                secondary_start,
                                                secondary_end, input_method, x_time_period, period_type, tab,
                                                hierarchy_toggle, hierarchy_level_dropdown, tile_index]
                        else:
                            elements_to_save = [graph_type, args_list, fiscal_toggle, year_start, year_end,
                                                secondary_start,
                                                secondary_end, input_method, x_time_period, period_type, tab,
                                                hierarchy_toggle, hierarchy_specific_dropdown, tile_index,
                                                state_of_display]
                        # calls the save_graph_state function to save the graph to the sessions dictionary
                        save_graph_state(graph_title, elements_to_save)
                        # saves the graph title and layout to the file where you are storing all of the saved layouts
                        save_layout_to_file(saved_layouts)
                        # saves the graph layout to the database
                        save_layout_to_db(graph_title)
                        save_message = get_label('You have saved the state.')
                        # Outputs a new input element with no value
                elif graph_title == '':
                    save_message = get_label('Please enter a title.')
                else:
                    save_message = get_label('The state has not been saved.')
                # checks to see if a layout has been selected to delete in the remove layout drop down
            else:
                save_message = ''
            if remove_layout != '':
                # calls the delete_layout function that removes the selected layout from the saved layouts file
                delete_layout(remove_layout, saved_layouts)
                # outputs a new drop down for selecting
                deletable_layouts_dropdown = [
                    dcc.Dropdown(id={'type': 'delete-layout-dropdown', 'index': tile_index},
                                 # may need to return options in a callback
                                 options=[{
                                     'label': key, 'value': key} for key in saved_layouts
                                 ],
                                 style={'width': '400px', 'font-size': '13px'},
                                 value='')]
            else:
                deletable_layouts_dropdown = no_update
            # Outputs new options for the drop down
            available_to_delete = [{
                'label': key, 'value': key} for key in saved_layouts]
            # Outputs a new dropdown menu for selecting the saved layouts
            loadable_layouts_dropdown = [
                dcc.Dropdown(id={'type': 'select-layout-dropdown', 'index': tile_index},
                             # may need to return options in a callback
                             options=[{
                                 'label': key, 'value': key} for key in saved_layouts
                             ],
                             style={'width': '400px', 'font-size': '13px'},
                             value='',
                             clearable=False
                             )]
            # Outputs new options for selecting the delete layout drop down
            available_to_load = [{
                'label': key, 'value': key} for key in saved_layouts]
        else:
            save_message = no_update
            available_to_load = [{
                'label': key, 'value': key} for key in saved_layouts]
            available_to_delete = [{
                'label': key, 'value': key} for key in saved_layouts]
            loadable_layouts_dropdown = no_update
            deletable_layouts_dropdown = no_update

        return save_message, available_to_load, available_to_delete, loadable_layouts_dropdown, \
            deletable_layouts_dropdown


# ************************************************DATA SIDE-MENU******************************************************

# edits made for loading
# change link button appearance
@app.callback(
    Output({'type': 'tile-link', 'index': MATCH}, 'className'),
    [
        # selected layout
        Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value'),
        Input({'type': 'tile-link', 'index': MATCH}, 'n_clicks')
    ],
    [State({'type': 'tile-link', 'index': MATCH}, 'className'),
     ]
)
def _change_link(selected_layout, _link_clicks, link_state):
    """
    :param _link_clicks: Detects the user clicking the link/unlink icon
    :param link_state: State of the link/unlink icon
    :return: New state of the link/unlink icon
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if link button was not pressed, do not update
    if '.' == changed_id:
        raise PreventUpdate
    else:
        changed_index = int(search(r'\d+', changed_id).group())

    if '"type":"select-layout-dropdown"}.value' in changed_id:
        selected = selected_layout[changed_index]
        if selected_layout != '' and selected in saved_layouts:
            if link_state == 'fa fa-link':
                link_state = 'fa fa-unlink'
            else:
                raise PreventUpdate
    else:
        selected = ''
    if f'"index":{changed_index},"type":"tile-link"}}.n_clicks' in changed_id:
        # if link button was pressed, toggle the link icon linked <--> unlinked
        link_state = 'fa fa-unlink' if link_state == 'fa fa-link' else 'fa fa-link'

    return link_state


# edits made for loading
# clear/copy tile data
@app.callback(
    [Output({'type': 'data-tile', 'index': 0}, 'children'),
     Output({'type': 'data-tile', 'index': 1}, 'children'),
     Output({'type': 'data-tile', 'index': 2}, 'children'),
     Output({'type': 'data-tile', 'index': 3}, 'children')],
    [Input('tile-closed-trigger', 'data-'),
     Input({'type': 'tile-link', 'index': ALL}, 'className'),
     # selected layout
     Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value')
     ],
    [State({'type': 'data-tile', 'index': ALL}, 'children')]
)
def _clear_and_copy_data_menu(closed_tile, links_style, selected_layout, data_states):
    """
    :param closed_tile: Detects when a tile has been deleted and encodes the index of the deleted tile
    param links_style: State of all link/unlink icons and detects user clicking a link icon
    :param data_states: State of all data side-menus
    :return: Data side-menus for all 5 side-menus
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    data = [no_update, no_update, no_update, no_update]
    # if NEW button was clicked, prevent update
    if '.' == changed_id:
        raise PreventUpdate
    # link button for a tile was toggled
    elif '"type":"tile-link"}.className' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        selected = selected_layout[changed_index]
        # unlinked --> linked: prevent update for all data menus except fourth to trigger display/hide data menu
        if links_style[changed_index] == 'fa fa-link':
            data[3] = data_states[3]
        # if linked --> unlinked: copy master tile data to unique tile data
        elif links_style[changed_index] == 'fa fa-unlink' and selected == '':
            master_copy = copy.deepcopy(data_states[4])
            data[changed_index] = change_index(master_copy, changed_index)
    # if a tile was deleted clear tile 4 data and shift data for tiles following the deleted tile and < index 4 left
    elif changed_id == 'tile-closed-trigger.data-':
        data_copy = copy.deepcopy(data_states)
        flag = False
        for i in range(4):
            if i == int(closed_tile):
                flag = True
            if flag and not i == 3:
                data[i] = change_index(data_copy[i + 1], i)
            elif flag and i == 3:
                data[3] = get_data_menu(3)
    return data[0], data[1], data[2], data[3],


# display or hide side menu for selected tile
@app.callback(
    [Output({'type': 'data-tile', 'index': 0}, 'style'),
     Output({'type': 'data-tile', 'index': 1}, 'style'),
     Output({'type': 'data-tile', 'index': 2}, 'style'),
     Output({'type': 'data-tile', 'index': 3}, 'style'),
     Output({'type': 'data-tile', 'index': 4}, 'style')],
    [Input({'type': 'tile', 'index': ALL}, 'dir'),
     Input({'type': 'tile-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-menu-close', 'index': ALL}, 'n_clicks'),
     Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value')],
    [State({'type': 'tile-link', 'index': ALL}, 'className'),
     State({'type': 'data-tile', 'index': ALL}, 'style')]
)
def _show_data_menu(_tile, _data_clicks, _close_clicks, _load_clicks, link_state, sidemenu_style_states):
    """
    :param _tile: Detects NEW/DELETE changes to div body
    :param _data_clicks: Detects user clicking DATA button within tile
    :param _close_clicks: Detects user clicking close ('x') button in the top right of a tile
    :param _load_clicks: Detects user loading a saved tile
    :param link_state: State of all link/unlink icons
    :param sidemenu_style_states: State of all data side-menu styles, either DATA_CONTENT_SHOW or DATA_CONTENT_HIDE
    :return: Styles to display or hide appropriate data side-menu
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # if no data submenu is active AND data display not requested - no update
    if sidemenu_style_states.count(DATA_CONTENT_SHOW) == 0 and '"type":"tile-data"}.n_clicks' not in changed_id:
        raise PreventUpdate
    # by default all data sidebars remain hidden, previously displayed side-menu is the only DATA_CONTENT_HIDE entry
    sidemenu_styles = [None, None, None, None, None]
    for i in range(5):
        if '"type":"select-layout-dropdown"' in changed_id:
            sidemenu_styles[i] = DATA_CONTENT_HIDE
        elif sidemenu_style_states == DATA_CONTENT_HIDE:
            sidemenu_styles[i] = no_update
        else:
            sidemenu_styles[i] = DATA_CONTENT_HIDE
    # if a tile's data button is clicked, display that tiles' data menu
    if '"type":"tile-data"}.n_clicks' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        # if tile is slaved to master display master data side-menu
        if link_state[changed_index] == 'fa fa-link':
            # check for spam clicking
            if sidemenu_style_states[4] == DATA_CONTENT_SHOW:
                raise PreventUpdate
            sidemenu_styles[4] = DATA_CONTENT_SHOW
        # if tile is not linked to master display unique data side-menu
        else:
            # check for spam clicking
            if sidemenu_style_states[changed_index] == DATA_CONTENT_SHOW:
                raise PreventUpdate
            sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
    return sidemenu_styles[0], sidemenu_styles[1], sidemenu_styles[2], sidemenu_styles[3], sidemenu_styles[4]


# highlight tiles slaved to displayed data sidebar
for x in range(4):
    @app.callback(
        Output({'type': 'tile', 'index': x}, 'className'),
        [Input({'type': 'data-tile', 'index': ALL}, 'style')],
        [State({'type': 'data-tile', 'index': x}, 'style'),
         State({'type': 'data-tile', 'index': 4}, 'style'),
         State({'type': 'tile-link', 'index': x}, 'className')]
    )
    def _highlight_slaved_tiles(_sidebar_styles, sidebar_style, master_sidebar_style, link_state):
        """
        :param _sidebar_styles: Detects hiding/showing of data side-menus
        :param sidebar_style: State of the style of the data side-menu
        :param master_sidebar_style: State of the style of the master data side-menu
        :param link_state: State of the link/unlink icon
        :return: Highlights tiles slaved to the displayed date side-menu
        """
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if changed_id == '.':
            raise PreventUpdate
        if ('"type":"data-tile"}.style' in changed_id) and (sidebar_style == DATA_CONTENT_SHOW
                                                            or (master_sidebar_style == DATA_CONTENT_SHOW
                                                                and link_state == 'fa fa-link')):
            tile_class = 'tile-highlight'
        else:
            tile_class = 'tile-container'
        return tile_class

# ************************************************ LOADING ******************************************************


for y in range(0, 4):
    @app.callback(
        [
            # From customize tab
            # graph type
            Output({'type': 'graph-type-dropdown', 'index': y}, 'value'),
            # ---------------------------------------------------
            # from data menu for followers
            Output({'type': 'radio-timeframe', 'index': y}, 'value'),
            # year type
            Output({'type': 'fiscal-year-toggle', 'index': y}, 'on'),
            # tab (division type)
            Output({'type': 'start-year-input', 'index': y}, 'name'),
            # Hierarchy toggle
            Output({'type': 'hierarchy-toggle', 'index': y}, 'on'),
            # level filter value
            Output({'type': 'hierarchy_level_dropdown', 'index': y}, 'value'),
            # start of year
            Output({'type': 'start-year-input', 'index': y}, 'value'),
            # end of year
            Output({'type': 'end-year-input', 'index': y}, 'value'),
            # secondary start
            Output({'type': 'start-secondary-input', 'index': y}, 'value'),
            # secondary end
            Output({'type': 'end-secondary-input', 'index': y}, 'value'),
            # graph title
            Output({'type': 'tile-title', 'index': y}, 'value')
        ],
        [
            # selected layout
            Input({'type': 'select-layout-dropdown', 'index': y}, 'value')
        ],
    )
    def load_layout(selected_layout):
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if changed_id == '.':
            raise PreventUpdate
        if '"type":"select-layout-dropdown"}.value' in changed_id and selected_layout != '' and selected_layout in \
                saved_layouts:
            if not saved_layouts[selected_layout][11]:
                return saved_layouts[selected_layout][0], saved_layouts[selected_layout][7], \
                       saved_layouts[selected_layout][2], saved_layouts[selected_layout][10], \
                       saved_layouts[selected_layout][11], saved_layouts[selected_layout][12], \
                       saved_layouts[selected_layout][3], saved_layouts[selected_layout][4], \
                       saved_layouts[selected_layout][5], saved_layouts[selected_layout][6], selected_layout
            else:
                return saved_layouts[selected_layout][0], saved_layouts[selected_layout][7], \
                       saved_layouts[selected_layout][2], saved_layouts[selected_layout][10], \
                       saved_layouts[selected_layout][11], no_update, \
                       saved_layouts[selected_layout][3], saved_layouts[selected_layout][4], \
                       saved_layouts[selected_layout][5], saved_layouts[selected_layout][6], selected_layout
        else:
            raise PreventUpdate
