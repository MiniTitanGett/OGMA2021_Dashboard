######################################################################################################################
"""
functionality_callbacks.py

stores all callbacks for the functionality of the app
"""
######################################################################################################################

# External Packages
import math
import dash
from dash import no_update
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
from re import search
import locale
import logging

# Internal Packages
from apps.app0003.graphs import get_line_figure, get_scatter_figure, get_bar_figure, get_table_figure, get_box_figure
from apps.app0003.hierarchy_filter import generate_history_button, generate_dropdown
from apps.app0003.app import app
from apps.app0003.data import TREE, data_filter, CLR, GREGORIAN_MIN_YEAR, FISCAL_MIN_YEAR, GREGORIAN_YEAR_MAX, \
    FISCAL_YEAR_MAX, LANGUAGE, get_label
from apps.app0003.datepicker import get_date_box, update_date_columns, get_secondary_data

# --------------------------------------------------------------
# added for loading functionality
from apps.app0003.saving_functions import saved_layouts


# --------------------------------------------------------------

# Contents:
#   GRAPH
#       - _store_tile_view_clicks()
#       - _update_graph()
#   HIERARCHY
#       - _print_choice_to_display_and_modify_dropdown()
#       - _show_filter_based_on_hierarchy_toggle()
#   DATE PICKER
#       - _set_year_range()
#       - _set_division_range()
#   DATA-TABLE
#       - operators
#       - split_filter_part()
#       - _update_table()


# ***************************************************GRAPH************************************************************

# update graph internal - can be called from callbacks or programatically
def __update_graph(graph_options, graph_type, graph_title,  num_periods,
                   period_type,
                   hierarchy_specific_dropdown, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                   state_of_display, secondary_type, timeframe,
                   fiscal_toggle, start_year, end_year, start_secondary, end_secondary):

    # Creates a hierarchy trail from the display
    if type(state_of_display) == dict:
        state_of_display = [state_of_display]
    list_of_names = []
    if len(state_of_display) > 0:
        for obj in state_of_display:
            list_of_names.append(obj['props']['children'])

    # Apply data filtering
    filtered_df = data_filter(list_of_names, hierarchy_specific_dropdown, secondary_type, end_secondary, end_year,
                              start_secondary, start_year, timeframe, fiscal_toggle, num_periods, period_type,
                              hierarchy_toggle,
                              hierarchy_level_dropdown, hierarchy_graph_children, graph_options)

    # Change language of dates for French
    if LANGUAGE == 'FR':
        # Formats the dates in french
        locale.setlocale(locale.LC_TIME, 'fr_FR')
        filtered_df['Date of Event'] = filtered_df['Date of Event'].transform(
            lambda x: x.strftime(format='%d  %B, %Y'))

    # line graph creation
    if graph_type == 'Line':
        return get_line_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                               list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title)
    # scatter graph creation
    elif graph_type == 'Scatter':
        return get_scatter_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                  list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title)
    # bar graph creation
    elif graph_type == 'Bar':
        return get_bar_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title)
    # box plot creation
    elif graph_type == 'Box Plot':
        return get_box_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title)
    # table creation
    elif graph_type == 'Table':
        # code to fix shifting
        changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]
        changed_index = dash.callback_context.inputs_list[1]['id']['index']
        if search(r'\d+', changed_id) and int(search(r'\d+', changed_id).group()) != 4:
            changed_index = int(search(r'\d+', changed_id).group())
        return get_table_figure(graph_options, filtered_df, changed_index, graph_title)
    # catch all
    else:
        return None


# code for ensuring in the customize tab the graphs are not drawn
for x in range(4):
    @app.callback(
        Output({'type': 'tile-view-store', 'index': x}, 'data'),
        [Input({'type': 'tile-customize', 'index': x}, 'n_clicks')],
        [State({'type': 'tile-view', 'index': x}, 'n_clicks')]
    )
    def _store_tile_view_clicks(customize_clicks, view_clicks):
        if customize_clicks and view_clicks is not None and view_clicks != customize_clicks:
            return view_clicks

# update graph
for x in range(4):
    @app.callback(
        Output({'type': 'graph_display', 'index': x}, 'children'),
        # Customize menu inputs
        [Input({'type': 'args-value: {}'.replace("{}", str(x)), 'index': ALL}, 'value'),
         Input({'type': 'graph-type-dropdown', 'index': x}, 'value'),
         # View menu inputs
         Input({'type': 'tile-view', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-title', 'index': x}, 'value'),
         # Link state
         Input({'type': 'tile-link', 'index': x}, 'className'),
         # Date Picker tile inputs
         Input({'type': 'date-picker-trigger', 'index': x}, 'data-boolean'),
         Input({'type': 'num-periods', 'index': x}, 'value'),
         Input({'type': 'period-type', 'index': x}, 'value'),
         # Date Picker master inputs
         Input({'type': 'date-picker-trigger', 'index': 4}, 'data-boolean'),
         Input({'type': 'num-periods', 'index': 4}, 'value'),
         Input({'type': 'period-type', 'index': 4}, 'value'),
         # Hierarchy inputs for tiles data menu
         Input({'type': 'hierarchy_specific_dropdown', 'index': x}, 'value'),  # ALL
         Input({'type': 'hierarchy-toggle', 'index': x}, 'on'),
         Input({'type': 'hierarchy_level_dropdown', 'index': x}, 'value'),
         Input({'type': 'graph_children_toggle', 'index': x}, 'value'),
         # Hierarchy inputs for master data menu
         Input({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'value'),
         Input({'type': 'hierarchy-toggle', 'index': 4}, 'on'),
         Input({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         Input({'type': 'graph_children_toggle', 'index': 4}, 'value')],
        [State({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         State({'type': 'tile-view-store', 'index': x}, 'data'),
         # Date picker states for tiles data menu
         State({'type': 'start-year-input', 'index': x}, 'name'),
         State({'type': 'radio-timeframe', 'index': x}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': x}, 'on'),
         State({'type': 'start-year-input', 'index': x}, 'value'),
         State({'type': 'end-year-input', 'index': x}, 'value'),
         State({'type': 'start-secondary-input', 'index': x}, 'value'),
         State({'type': 'end-secondary-input', 'index': x}, 'value'),
         # Date picker states for master data menu
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'on'),
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value')]
    )
    def _update_graph(arg_value, graph_type, view_clicks, tile_title, link_state, _datepicker_trigger, num_periods,
                      period_type, _master_datepicker_trigger, master_num_periods, master_period_type,
                      hierarchy_specific_dropdown, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                      master_hierarchy_specific_dropdown, master_hierarchy_toggle,
                      master_hierarchy_level_dropdown, master_hierarchy_graph_children,
                      state_of_display, master_state_of_display, stored_view_clicks, secondary_type, timeframe,
                      fiscal_toggle, start_year, end_year, start_secondary, end_secondary, master_secondary_type,
                      master_timeframe, master_fiscal_toggle, master_start_year, master_end_year,
                      master_start_secondary, master_end_secondary):

        # works alongside _store_tile_view_clicks to ensure in the customize tab, graphs are not drawn
        if stored_view_clicks is None:
            stored_view_clicks = -1
        if not view_clicks > stored_view_clicks:
            raise PreventUpdate

        # checks if graph menu has been loaded yet - prevents update if not
        if len(arg_value) == 0:
            raise PreventUpdate

        # account for tile being linked or not
        if link_state == 'fa fa-link':
            secondary_type = master_secondary_type
            timeframe = master_timeframe
            fiscal_toggle = master_fiscal_toggle
            start_year = master_start_year
            end_year = master_end_year
            start_secondary = master_start_secondary
            end_secondary = master_end_secondary
            hierarchy_specific_dropdown = master_hierarchy_specific_dropdown
            hierarchy_toggle = master_hierarchy_toggle
            hierarchy_level_dropdown = master_hierarchy_level_dropdown
            state_of_display = master_state_of_display
            hierarchy_graph_children = master_hierarchy_graph_children
            num_periods = master_num_periods
            period_type = master_period_type

        # prevent update if invalid selections exist - should be handled by update_datepicker, but double check
        if not start_year or not end_year or not start_secondary or not end_secondary or \
                (not num_periods and timeframe == 'to-current'):
            raise PreventUpdate

        graph = __update_graph(arg_value, graph_type, tile_title,
                               num_periods,
                               period_type,
                               hierarchy_specific_dropdown, hierarchy_toggle, hierarchy_level_dropdown,
                               hierarchy_graph_children,
                               state_of_display, secondary_type, timeframe,
                               fiscal_toggle, start_year, end_year, start_secondary, end_secondary)

        if graph is None:
            raise PreventUpdate

        return graph

# *******************************************************HIERARCHY***************************************************
for x in range(4):
    @app.callback(
        [Output({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         Output({'type': 'hierarchy_specific_dropdown_container', 'index': x}, 'children')],
        [Input({'type': 'hierarchy_specific_dropdown', 'index': x}, 'value'),
         Input({'type': 'hierarchy_revert', 'index': x}, 'n_clicks'),
         Input({'type': 'hierarchy_to_top', 'index': x}, 'n_clicks'),
         Input({'type': 'button: {}'.replace("{}", str(x)), 'index': ALL}, 'n_clicks'),
         Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value')],
        [State({'type': 'hierarchy_display_button', 'index': x}, 'children')]
    )
    def _print_choice_to_display_and_modify_dropdown(dropdown_val, _n_clicks_r, _n_clicks_tt, n_clicks_click_history,
                                                     selected_layout, state_of_display):
        changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]
        tile = int(dash.callback_context.inputs_list[0]['id']['index'])
        if changed_id == '.':
            raise PreventUpdate
        selected = ''
        # if page loaded - prevent update
        changed_index = None
        if not search(r'\d+', changed_id):
            raise PreventUpdate
        elif 'button: ' in changed_id:
            for i in range(5):
                if 'button: {}'.replace("{}", str(i)) in changed_id:
                    changed_index = i
        else:
            changed_index = int(search(r'\d+', changed_id).group())
            if changed_index < 4:
                selected = selected_layout[changed_index]
                if selected != '' and not saved_layouts[selected][11]:
                    raise PreventUpdate

        if 'select-layout-dropdown' in changed_id and selected != '':
            state_of_display = saved_layouts[selected][14]
            dropdown_val = saved_layouts[selected][12]

        # Ensures that state_of_display is a list of dictionaries
        if type(state_of_display) == dict:
            state_of_display = [state_of_display]
        # Creates a string of names for tree navigation
        string_of_names = "root"
        for i in state_of_display:
            string_of_names += (', {}'.format(i['props']['children']))

        # If revert is pressed and nothing is in history, do nothing.
        # If revert is pressed and history contains a value, pop it into prev_selected which will redraw dropdown
        # If revert is pressed and history contained a single value, set history to "" and regen dropdown at root
        if 'hierarchy_revert' in changed_id:
            if state_of_display:
                state_of_display.pop()
                display_button = state_of_display
                dropdown = generate_dropdown(changed_index, state_of_display)
            else:
                display_button = []
                dropdown = generate_dropdown(changed_index)
        elif 'hierarchy_to_top' in changed_id:
            display_button = []
            dropdown = generate_dropdown(changed_index)
        elif 'hierarchy_specific_dropdown' in changed_id:
            logging.debug(dropdown_val)
            # If dropdown has been remade, do not modify the history
            # If the node has no data (leaf node) then do not add it to history
            if dropdown_val is None or TREE.get_node(
                    '{}, {}'.format(string_of_names, dropdown_val)).is_leaf():
                display_button = dropdown = no_update
            # If nothing in history return value
            elif not state_of_display:
                display_button = generate_history_button(dropdown_val, 0, changed_index)
                dropdown = generate_dropdown(changed_index, dropdown_value=dropdown_val)
            # If something is in the history preserve it and add value to it
            else:
                display_button = state_of_display + [
                    (generate_history_button(dropdown_val, len(state_of_display), changed_index))]
                dropdown = generate_dropdown(changed_index, state_of_display, dropdown_val)
        elif 'select-layout-dropdown' in changed_id and selected != '':
            display_button = state_of_display
            dropdown = generate_dropdown(tile, state_of_display, dropdown_val)
        # If update triggered due to creation of a button do not update anything
        elif all(i == 0 for i in n_clicks_click_history):
            display_button = dropdown = no_update
        # If the history has been selected find the value of the button pressed and get it to reset the history and
        # dropdown to that point
        else:
            index = [i != 0 for i in n_clicks_click_history].index(True)
            history = state_of_display[:index + 1]
            history[index]['props']['n_clicks'] = 0
            display_button = history
            dropdown = generate_dropdown(changed_index, history)
        # loads in the saved hierarchy display button and menu selections

        return display_button, dropdown


@app.callback(
    [Output({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
     Output({'type': 'hierarchy_specific_dropdown_container', 'index': 4}, 'children')],
    [Input({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'value'),
     Input({'type': 'hierarchy_revert', 'index': 4}, 'n_clicks'),
     Input({'type': 'hierarchy_to_top', 'index': 4}, 'n_clicks'),
     Input({'type': 'button: {}'.replace("{}", str(4)), 'index': ALL}, 'n_clicks')],
    [State({'type': 'hierarchy_display_button', 'index': 4}, 'children')]
)
def _print_choice_to_display_and_modify_dropdown(dropdown_val, _n_clicks_r, _n_clicks_tt, n_clicks_click_history,
                                                 state_of_display):
    changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]
    if changed_id == '.':
        raise PreventUpdate
    # if page loaded - prevent update
    changed_index = None
    if not search(r'\d+', changed_id):
        raise PreventUpdate
    elif 'button: ' in changed_id:
        for i in range(5):
            if 'button: {}'.replace("{}", str(i)) in changed_id:
                changed_index = i
    else:
        changed_index = int(search(r'\d+', changed_id).group())

    # Ensures that state_of_display is a list of dictionaries
    if type(state_of_display) == dict:
        state_of_display = [state_of_display]
    # Creates a string of names for tree navigation
    string_of_names = "root"
    for i in state_of_display:
        string_of_names += (', {}'.format(i['props']['children']))

    # If revert is pressed and nothing is in history, do nothing.
    # If revert is pressed and history contains a value, pop it into prev_selected which will redraw dropdown
    # If revert is pressed and history contained a single value, set history to "" and regen dropdown at root
    if 'hierarchy_revert' in changed_id:
        if state_of_display:
            state_of_display.pop()
            display_button = state_of_display
            dropdown = generate_dropdown(changed_index, state_of_display)
        else:
            display_button = []
            dropdown = generate_dropdown(changed_index)
    elif 'hierarchy_to_top' in changed_id:
        display_button = []
        dropdown = generate_dropdown(changed_index)
    elif 'hierarchy_specific_dropdown' in changed_id:
        # If dropdown has been remade, do not modify the history
        # If the node has no data (leaf node) then do not add it to history
        if dropdown_val is None or TREE.get_node(
                '{}, {}'.format(string_of_names, dropdown_val)).is_leaf():
            display_button = dropdown = no_update
        # If nothing in history return value
        elif not state_of_display:
            display_button = generate_history_button(dropdown_val, 0, changed_index)
            dropdown = generate_dropdown(changed_index, dropdown_value=dropdown_val)
        # If something is in the history preserve it and add value to it
        else:
            display_button = state_of_display + [
                (generate_history_button(dropdown_val, len(state_of_display), changed_index))]
            dropdown = generate_dropdown(changed_index, state_of_display, dropdown_val)
    # If update triggered due to creation of a button do not update anything
    elif all(i == 0 for i in n_clicks_click_history):
        display_button = dropdown = no_update
    # If the history has been selected find the value of the button pressed and get it to reset the history and
    # dropdown to that point
    else:
        index = [i != 0 for i in n_clicks_click_history].index(True)
        history = state_of_display[:index + 1]
        history[index]['props']['n_clicks'] = 0
        display_button = history
        dropdown = generate_dropdown(changed_index, history)
    # loads in the saved hierarchy display button and menu selections

    return display_button, dropdown


@app.callback(
    [Output({'type': 'hierarchy_level_filter', 'index': MATCH}, 'style'),
     Output({'type': 'hierarchy_specific_filter', 'index': MATCH}, 'style')],
    [Input({'type': 'hierarchy-toggle', 'index': MATCH}, 'on')]
)
def _show_filter_based_on_hierarchy_toggle(hierarchy_toggle):
    if not hierarchy_toggle:
        return {}, {'display': 'none'}
    else:
        return {'display': 'none'}, {}


# ***************************************************DATE PICKER****************************************************

# update date picker
@app.callback(
    [Output({'type': 'div-date-range-selection', 'index': MATCH}, 'children'),
     Output({'type': 'date-picker-trigger', 'index': MATCH}, 'data-boolean')],
    [Input({'type': 'radio-timeframe', 'index': MATCH}, 'value'),
     Input({'type': 'fiscal-year-toggle', 'index': MATCH}, 'on'),
     Input({'type': 'date-picker-year-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-quarter-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-month-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-week-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'start-year-input', 'index': MATCH}, 'value'),
     Input({'type': 'end-year-input', 'index': MATCH}, 'value'),
     Input({'type': 'start-secondary-input', 'index': MATCH}, 'value'),
     Input({'type': 'end-secondary-input', 'index': MATCH}, 'value')],
    [State({'type': 'start-year-input', 'index': MATCH}, 'name')
     ]
)
def update_date_picker(input_method, fiscal_toggle, _year_button_clicks, _quarter_button_clicks, _month_button_clicks,
                       _week_button_clicks, start_year_selection, end_year_selection, start_secondary_selection,
                       end_secondary_selection, tab):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    tile = dash.callback_context.inputs_list[0]['id']['index']
    if changed_id == '.':
        raise PreventUpdate

    # if "All-Time" or 'Past ___ ___' radio selected, return only hidden id placeholders
    if input_method == 'all-time' or input_method == 'to-current':
        children = [
            html.Div([
                html.Button(id={'type': 'date-picker-year-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-quarter-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-month-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-week-button', 'index': tile}),
                dcc.Input(id={'type': 'start-year-input', 'index': tile},
                          value=1),
                dcc.Input(id={'type': 'end-year-input', 'index': tile},
                          value=1),
                dcc.Input(id={'type': 'start-secondary-input', 'index': tile},
                          value=1),
                dcc.Input(id={'type': 'end-secondary-input', 'index': tile},
                          value=1)
            ], style={'width': '0', 'height': '0', 'overflow': 'hidden'})]

    # 'Select Range' was selected
    else:
        # tabs are unselected and enabled unless otherwise specified
        year_className = quarter_className = month_className = week_className = 'date-picker-nav'
        year_disabled = quarter_disabled = month_disabled = week_disabled = False
        # secondary input boxes do not exist if inside of year tab - their data is None unless otherwise specified
        fringe_min = fringe_max = selected_secondary_min = selected_secondary_max = default_max = None

        # if tabs do not exist or the 'year' tab was requested or year type changed,
        # generate the tabs with the 'year' tab as active
        if 'radio-timeframe' in changed_id or 'date-picker-year-button' in changed_id:
            year_className = 'date-picker-nav-selected'
            year_disabled = True
            # use the year scheme (gregorian/fiscal) selected by the user
            if not fiscal_toggle:
                min_year = GREGORIAN_MIN_YEAR
                max_year = GREGORIAN_YEAR_MAX
            else:
                min_year = FISCAL_MIN_YEAR
                max_year = FISCAL_YEAR_MAX
            left_column = html.Div([
                get_date_box(id={'type': 'start-year-input', 'index': tile},
                             value=min_year,
                             min=min_year,
                             max=max_year,
                             name='Year'),
                dcc.Input(
                    id={'type': 'start-secondary-input', 'index': tile},
                    value=1,
                    style={'display': 'none'})
            ])
            right_column = html.Div([
                get_date_box(id={'type': 'end-year-input', 'index': tile},
                             value=max_year + 1,
                             min=min_year + 1,
                             max=max_year + 1),
                dcc.Input(
                    id={'type': 'end-secondary-input', 'index': tile},
                    value=1,
                    style={'display': 'none'})
            ])

        # if a tab was requested other than 'year', generate the default appearance of the selected tab
        elif 'n_clicks' in changed_id:
            conditions = ['date-picker-quarter-button' in changed_id, 'date-picker-month-button' in changed_id]
            quarter_className, quarter_disabled, month_className, month_disabled, week_className, week_disabled, \
            fringe_min, fringe_max, default_max, max_year, new_tab = get_secondary_data(conditions, fiscal_toggle)
            # set min_year according to user selected fiscal/gregorian time type
            if not fiscal_toggle:
                min_year = GREGORIAN_MIN_YEAR
            else:
                min_year = FISCAL_MIN_YEAR
            # if data exists for only one year, use fringe extremes
            if min_year == max_year:
                max_min = fringe_min + 1
                min_max = fringe_max - 1
            # if data exists for more than one year the interior extrema are as expected
            else:
                min_max = default_max
                max_min = 1
            year_input_min = get_date_box(id={'type': 'start-year-input', 'index': tile},
                                          value=min_year,
                                          min=min_year,
                                          max=max_year,
                                          name=new_tab)
            year_input_max = get_date_box(id={'type': 'end-year-input', 'index': tile},
                                          value=max_year,
                                          min=min_year,
                                          max=max_year)
            secondary_input_min = get_date_box(id={'type': 'start-secondary-input', 'index': tile},
                                               value=fringe_min,
                                               min=fringe_min,
                                               max=min_max, )
            secondary_input_max = get_date_box(id={'type': 'end-secondary-input', 'index': tile},
                                               value=fringe_max,
                                               min=max_min,
                                               max=fringe_max)
            left_column = [year_input_min, secondary_input_min]
            right_column = [year_input_max, secondary_input_max]

        # if an input within a tab changed to a valid value or fiscal year toggle changed, apply the change
        else:
            # if an invalid input exists, do not update
            if not start_year_selection or not end_year_selection or not start_secondary_selection \
                    or not end_secondary_selection:
                raise PreventUpdate
            selected_min_year = start_year_selection
            selected_max_year = end_year_selection
            # if inside of year tab
            if tab == 'Year':
                year_className = 'date-picker-nav-selected'
                year_disabled = True
                if not fiscal_toggle:
                    max_year = GREGORIAN_YEAR_MAX
                else:
                    max_year = FISCAL_YEAR_MAX
            # if not inside of year tab, get secondary data
            else:
                selected_secondary_min = start_secondary_selection
                selected_secondary_max = end_secondary_selection
                conditions = [tab == 'Quarter', tab == 'Month']
                quarter_className, quarter_disabled, month_className, month_disabled, week_className, week_disabled, \
                fringe_min, fringe_max, default_max, max_year, new_tab = get_secondary_data(conditions, fiscal_toggle)
            # set min_year according to user selected time type (gregorian/fiscal)
            if not fiscal_toggle:
                min_year = GREGORIAN_MIN_YEAR
            else:
                min_year = FISCAL_MIN_YEAR
            # if not inside year tab, generate left and right columns with secondary input boxes
            if fringe_min and fringe_max:
                left_column, right_column = update_date_columns(
                    changed_id, selected_min_year, min_year, fringe_min, selected_max_year, max_year, fringe_max,
                    default_max, tab, selected_secondary_min, selected_secondary_max, tile)
            # else inside year tab, do not generate secondary input boxes
            else:
                # set selections to extremes if Gregorian <--> Fiscal
                if 'fiscal-year-toggle' in changed_id:
                    selected_min_year = min_year
                    selected_max_year = max_year + 1
                left_column = html.Div([
                    get_date_box(id={'type': 'start-year-input', 'index': tile},
                                 value=selected_min_year,
                                 min=min_year,
                                 max=selected_max_year - 1,
                                 name='Year'),
                    dcc.Input(
                        id={'type': 'start-secondary-input', 'index': tile},
                        value=1,
                        style={'display': 'none'})])
                right_column = html.Div([
                    get_date_box(id={'type': 'end-year-input', 'index': tile},
                                 value=selected_max_year,
                                 min=selected_min_year + 1,
                                 max=max_year + 1),
                    dcc.Input(
                        id={'type': 'end-secondary-input', 'index': tile},
                        value=1,
                        style={'display': 'none'})])

        # do not move the arrow upwards unless secondary selection input boxes exist
        bottom = '0' if not fringe_min else '17px'
        children = [
            html.Header([
                html.Button(get_label("Year"), className=year_className,
                            id={'type': 'date-picker-year-button', 'index': tile},
                            disabled=year_disabled),
                html.Button(get_label("Quarter"), className=quarter_className,
                            id={'type': 'date-picker-quarter-button', 'index': tile},
                            disabled=quarter_disabled),
                html.Button(get_label("Month"), className=month_className,
                            id={'type': 'date-picker-month-button', 'index': tile},
                            disabled=month_disabled),
                html.Button(get_label("Week"), className=week_className,
                            id={'type': 'date-picker-week-button', 'index': tile},
                            disabled=week_disabled)
            ], style={'display': 'inline-block', 'width': '100%'}),
            html.Div([
                html.Div(style={'width': '40%', 'display': 'inline-block'},
                         children=left_column),
                html.P(className='fa fa-arrow-right',
                       style={'color': CLR['text1'], 'width': '20%', 'display': 'inline-block',
                              'text-align': 'center', 'position': 'relative', 'bottom': bottom}),
                html.Div(style={'width': '40%', 'display': 'inline-block'},
                         children=right_column)
            ], style={'width': '100%', 'height': '100%', 'margin-top': '8px'})
        ]
    return children, True


# enable past __ ___ selections
@app.callback(
    [Output({'type': 'num-periods', 'index': MATCH}, 'disabled'),
     Output({'type': 'period-type', 'index': MATCH}, 'disabled')],
    [Input({'type': 'radio-timeframe', 'index': MATCH}, 'value')]
)
def unlock_past_x_selections(selected_timeframe):
    disabled = False if selected_timeframe == 'to-current' else True
    return disabled, disabled


# *************************************************DATA-TABLE*********************************************************

operators = [[' ge ', '>='],
             [' le ', '<='],
             [' lt ', '<'],
             [' gt ', '>'],
             [' ne ', '!='],
             [' eq ', '='],
             [' contains '],
             [' datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', '`'):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


for x in range(4):
    @app.callback(
        [Output({'type': 'datatable', 'index': x}, 'data'),
         Output({'type': 'datatable', 'index': x}, 'page_count')],
        [Input({'type': 'datatable', 'index': x}, "page_current"),
         Input({'type': 'datatable', 'index': x}, "page_size"),
         Input({'type': 'datatable', 'index': x}, 'sort_by'),
         Input({'type': 'datatable', 'index': x}, 'filter_query'),
         # Link state
         Input({'type': 'tile-link', 'index': x}, 'className')],
        # Date picker states for tile
        [State({'type': 'start-year-input', 'index': x}, 'name'),
         State({'type': 'radio-timeframe', 'index': x}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': x}, 'on'),
         State({'type': 'start-year-input', 'index': x}, 'value'),
         State({'type': 'end-year-input', 'index': x}, 'value'),
         State({'type': 'start-secondary-input', 'index': x}, 'value'),
         State({'type': 'end-secondary-input', 'index': x}, 'value'),
         State({'type': 'num-periods', 'index': x}, 'value'),
         State({'type': 'period-type', 'index': x}, 'value'),
         # Hierarchy states for tile
         State({'type': 'hierarchy-toggle', 'index': x}, 'on'),
         State({'type': 'hierarchy_level_dropdown', 'index': x}, 'value'),
         State({'type': 'hierarchy_specific_dropdown', 'index': x}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         State({'type': 'graph_children_toggle', 'index': x}, 'value'),
         State({'type': 'args-value: {}'.replace("{}", str(x)), 'index': ALL}, 'value'),
         # Date picker states for master data menu
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'on'),
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value'),
         State({'type': 'num-periods', 'index': 4}, 'value'),
         State({'type': 'period-type', 'index': 4}, 'value'),
         # Hierarchy States for master data menu
         State({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy-toggle', 'index': 4}, 'on'),
         State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         State({'type': 'graph_children_toggle', 'index': 4}, 'value')]
    )
    def _update_table(page_current, page_size, sort_by, filter, link_state, secondary_type, timeframe, fiscal_toggle,
                      start_year, end_year, start_secondary, end_secondary, num_periods, period_type, hierarchy_toggle,
                      hierarchy_level_dropdown,
                      hierarchy_specific_dropdown, state_of_display, hierarchy_graph_children, arg_value,
                      master_secondary_type,
                      master_timeframe, master_fiscal_toggle, master_start_year, master_end_year,
                      master_start_secondary,
                      master_end_secondary, master_num_periods, master_period_type, master_hierarchy_specific_dropdown,
                      master_hierarchy_toggle,
                      master_hierarchy_level_dropdown, master_state_of_display, master_hierarchy_graph_children):
        if link_state == 'fa fa-link':
            secondary_type = master_secondary_type
            timeframe = master_timeframe
            fiscal_toggle = master_fiscal_toggle
            start_year = master_start_year
            end_year = master_end_year
            start_secondary = master_start_secondary
            end_secondary = master_end_secondary
            hierarchy_specific_dropdown = master_hierarchy_specific_dropdown
            hierarchy_toggle = master_hierarchy_toggle
            hierarchy_level_dropdown = master_hierarchy_level_dropdown
            state_of_display = master_state_of_display
            hierarchy_graph_children = master_hierarchy_graph_children
            num_periods = master_num_periods
            period_type = master_period_type

        # prevent update if invalid selections exist - should be handled by update_datepicker, but double check
        if not start_year or not end_year or not start_secondary or not end_secondary:
            raise PreventUpdate

        # Creates a hierarchy trail from the display
        if type(state_of_display) == dict:
            state_of_display = [state_of_display]
        list_of_names = []
        if len(state_of_display) > 0:
            for obj in state_of_display:
                list_of_names.append(obj['props']['children'])

        # Apply data filtering
        dff = data_filter(list_of_names, hierarchy_specific_dropdown, secondary_type, end_secondary, end_year,
                          start_secondary, start_year, timeframe, fiscal_toggle, num_periods, period_type,
                          hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, arg_value)

        # Reformat date column
        dff['Date of Event'] = dff['Date of Event'].transform(lambda x: x.strftime(format='%Y-%m-%d'))

        # Filter based on datatable filters
        filtering_expressions = filter.split(' && ')
        for filter_part in filtering_expressions:
            col_name, operator, filter_value = split_filter_part(filter_part)

            if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                # these operators match pandas series operator method names
                dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
            elif operator == 'contains':
                if type(filter_value) is not str:
                    continue
                dff = dff.loc[dff[col_name].astype(str).str.lower().str.contains(filter_value.lower())]
            elif operator == 'datestartswith':
                if type(filter_value) is not str:
                    continue
                # this is a simplification of the front-end filtering logic,
                # only works with complete fields in standard format
                dff = dff.loc[dff[col_name].astype(str).str.lower().str.startswith(filter_value.lower())]

        if len(sort_by):
            dff = dff.sort_values(
                [col['column_id'] for col in sort_by],
                ascending=[
                    col['direction'] == 'asc'
                    for col in sort_by
                ],
                inplace=False
            )

        page = page_current
        size = page_size
        return dff.iloc[page * size: (page + 1) * size].to_dict('records'), math.ceil(dff.iloc[:, 0].size / page_size)
