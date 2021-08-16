######################################################################################################################
"""
functionality_callbacks.py

stores all callbacks for the functionality of the app
"""
######################################################################################################################

# External Packages
import math
import dash
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
from re import search
from flask import session

# Internal Packages
from apps.dashboard.graphs import __update_graph
from apps.dashboard.hierarchy_filter import generate_history_button, generate_dropdown
from apps.dashboard.app import app
from apps.dashboard.data import data_filter, CLR, get_label, GRAPH_OPTIONS
from apps.dashboard.datepicker import get_date_box, update_date_columns, get_secondary_data

# Contents:
#   GRAPH
#       - _update_graph()
#   HIERARCHY
#       - _print_choice_to_display_and_modify_dropdown()
#       - _show_filter_based_on_hierarchy_toggle()
#   DATE PICKER
#       - _update_date_picker()
#       - _unlock_past_x_selections()
#   DATA-TABLE
#       - operators
#       - split_filter_part()
#       - _update_table()
# ********************************************Arbitrary Constants*****************************************************

plotly_graph = {'Line': 'line', 'Bar': 'bar', 'Scatter': 'scatter', 'Bubble': 'bubble',
                'Box_Plot': 'box', 'Table': 'table', 'Sankey': 'sankey'}
# ***************************************************GRAPH************************************************************

# update graph
for x in range(4):
    @app.callback(
        Output({'type': 'graph_display', 'index': x}, 'children'),
        # Graph menu update graph trigger
        [Input({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_trigger'),
         # Customize menu inputs
         Input({'type': 'args-value: {}'.replace("{}", str(x)), 'index': ALL}, 'value'),
         Input({'type': 'graph-type-dropdown', 'index': x}, 'value'),
         # View menu inputs
         Input({'type': 'tile-title', 'index': x}, 'value'),
         # Tile date picker inputs
         Input({'type': 'date-picker-trigger', 'index': x}, 'data-boolean'),
         Input({'type': 'num-periods', 'index': x}, 'value'),
         Input({'type': 'period-type', 'index': x}, 'value'),
         # Date Picker parent inputs
         Input({'type': 'date-picker-trigger', 'index': 4}, 'data-boolean'),
         Input({'type': 'num-periods', 'index': 4}, 'value'),
         Input({'type': 'period-type', 'index': 4}, 'value'),
         # Hierarchy inputs for tiles data menu
         Input({'type': 'hierarchy-toggle', 'index': x}, 'value'),
         Input({'type': 'hierarchy_level_dropdown', 'index': x}, 'value'),
         Input({'type': 'graph_children_toggle', 'index': x}, 'value'),
         Input({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         # Hierarchy inputs for parent data menu
         Input({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         Input({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
         Input({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         Input({'type': 'graph_children_toggle', 'index': 4}, 'value')],
        # Date picker states for tiles data menu
        [State({'type': 'start-year-input', 'index': x}, 'name'),
         State({'type': 'radio-timeframe', 'index': x}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': x}, 'value'),
         State({'type': 'start-year-input', 'index': x}, 'value'),
         State({'type': 'end-year-input', 'index': x}, 'value'),
         State({'type': 'start-secondary-input', 'index': x}, 'value'),
         State({'type': 'end-secondary-input', 'index': x}, 'value'),
         # Date picker states for parent data menu
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value'),
         State({'type': 'graph_display', 'index': x}, 'children'),
         # Data set states
         State({'type': 'data-set', 'index': x}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         # Link state
         State({'type': 'tile-link', 'index': x}, 'className'),
         # Hierarchy Options
         State({'type': 'hierarchy_specific_dropdown', 'index': x}, 'options'),
         State({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'options'),
         # Constants
         State('df-constants-storage', 'data'),
         # Float menu result
         State({'type': 'data-set-parent', 'index': 4}, 'value'),
         # Axes titles
         State({'type': 'xaxis-title', 'index': x}, 'value'),
         State({'type': 'yaxis-title', 'index': x}, 'value'),
         # Legend Position
         State({'type': 'x-pos-legend', 'index': x}, 'value'),
         State({'type': 'y-pos-legend', 'index': x}, 'value')],
        prevent_initial_call=True
    )
    def _update_graph(_df_trigger, arg_value, graph_type, tile_title, _datepicker_trigger,
                      num_periods, period_type, _parent_datepicker_trigger, parent_num_periods,
                      parent_period_type, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                      state_of_display, parent_state_of_display, parent_hierarchy_toggle,
                      parent_hierarchy_level_dropdown, parent_hierarchy_graph_children, secondary_type,
                      timeframe, fiscal_toggle, start_year, end_year, start_secondary, end_secondary,
                      parent_secondary_type, parent_timeframe, parent_fiscal_toggle, parent_start_year, parent_end_year,
                      parent_start_secondary, parent_end_secondary, graph_display, df_name, parent_df_name,
                      link_state, hierarchy_options, parent_hierarchy_options, df_const, df_confirm, xaxis, yaxis,
                      xlegend, ylegend):

        # -------------------------------------------Variable Declarations----------------------------------------------
        changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]
        tile = dash.callback_context.inputs_list[0]['id']['index']
        df_tile = None
        # --------------------------------------------------------------------------------------------------------------
        # check if keyword in df_name
        if df_name is not None:
            df_tile = df_name
            if 'OPG001' in df_name:
                df_name = 'OPG001'
            elif 'OPG010' in df_name:
                df_name = 'OPG010'

        if '"type":"tile-view"}.className' in changed_id and df_name is None and parent_df_name is None:
            return None

        # if new/delete while the graph already exists, prevent update
        if changed_id == '.' and graph_display:
            raise PreventUpdate

        if len(arg_value) == 0:
            return None

        # if unlinked and parent changes, prevent update
        if (link_state == 'fa fa-unlink' and '"index":4' in changed_id) and 'args-value' not in changed_id:
            raise PreventUpdate

        # if linked --> unlinked prevent update
        if link_state == 'fa fa-unlink' and '"type":"tile-link"}.className' in changed_id:
            raise PreventUpdate

        # if linked and graph-type is in both data sets update graph
        if link_state == 'fa fa-link' and (df_name is not None
                                           and graph_type in GRAPH_OPTIONS[df_name] and df_name != parent_df_name) or \
                (df_name is None and df_confirm is not None and parent_df_name != df_confirm):
            if df_confirm is not None:
                df_tile = df_confirm
            graph = __update_graph(df_tile, arg_value, graph_type, tile_title, num_periods, period_type,
                                   hierarchy_toggle,
                                   hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_options,
                                   state_of_display,
                                   secondary_type, timeframe, fiscal_toggle, start_year, end_year, start_secondary,
                                   end_secondary, df_const, xaxis, yaxis, xlegend, ylegend)
            return graph

        # account for tile being linked or not
        if link_state == 'fa fa-link':
            secondary_type = parent_secondary_type
            timeframe = parent_timeframe
            fiscal_toggle = parent_fiscal_toggle
            start_year = parent_start_year
            end_year = parent_end_year
            start_secondary = parent_start_secondary
            end_secondary = parent_end_secondary
            hierarchy_toggle = parent_hierarchy_toggle
            hierarchy_level_dropdown = parent_hierarchy_level_dropdown
            state_of_display = parent_state_of_display
            hierarchy_graph_children = parent_hierarchy_graph_children
            num_periods = parent_num_periods
            period_type = parent_period_type
            df_name = parent_df_name
            hierarchy_options = parent_hierarchy_options
        else:
            df_name = df_tile

        # prevent update if invalid selections exist - should be handled by update_datepicker, but double check
        if not start_year or not end_year or not start_secondary or not end_secondary or \
                (not num_periods and timeframe == 'to-current') or df_name is None:
            raise PreventUpdate

        # warning on load logic for if anything has been changed for a dashboard and graph
        if not session['tile_edited'][4]:
            session['tile_edited'][4] = True
        elif session['tile_edited'][4] == tile + 1:  # to check if it is the last draw on a load
            session['tile_edited'][4] = False

        if session['tile_edited'][tile] == 'Load':  # to set to false after load
            session['tile_edited'][tile] = False
        else:
            session['tile_edited'][tile] = True

        # added to remove the the data-fitting traces from the graph when the hierarchy toggle is changed or
        # graph all in dropdown is selected
        if graph_type == "Line" or graph_type == "Scatter":
            if arg_value[4] != 'no-fit' and (hierarchy_toggle != 'Specific Item' or hierarchy_graph_children != []):
                arg_value[4] = 'no-fit'

        graph = __update_graph(df_name, arg_value, graph_type, tile_title, num_periods, period_type, hierarchy_toggle,
                               hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_options, state_of_display,
                               secondary_type, timeframe, fiscal_toggle, start_year, end_year, start_secondary,
                               end_secondary, df_const, xaxis, yaxis, xlegend, ylegend)

        if graph is None:
            raise PreventUpdate

        return graph

# *******************************************************HIERARCHY***************************************************

# updates the hierarchy dropdown and hierarchy button path
for x in range(5):
    @app.callback(
        [Output({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         Output({'type': 'hierarchy_specific_dropdown_container', 'index': x}, 'children'),
         Output({'type': 'graph_children_toggle', 'index': x}, 'options')],
        [Input({'type': 'hierarchy_specific_dropdown', 'index': x}, 'value'),
         Input({'type': 'hierarchy_revert', 'index': x}, 'n_clicks'),
         Input({'type': 'hierarchy_to_top', 'index': x}, 'n_clicks'),
         Input({'type': 'button: {}'.replace("{}", str(x)), 'index': ALL}, 'n_clicks')],
        [State({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         State({'type': 'data-set', 'index': x}, 'value')],
        prevent_initial_call=True
    )
    def _print_choice_to_display_and_modify_dropdown(dropdown_val, _n_clicks_r, _n_clicks_tt,
                                                     n_clicks_click_history, state_of_display,
                                                     df_name):

        changed_id = [i['prop_id'] for i in dash.callback_context.triggered][0]

        # if page loaded - prevent update
        if changed_id == '.':
            raise PreventUpdate

        # create a comma delimited string for hierarchy (node id) navigation
        def get_nid_path(sod=None, dropdown_value=None):
            if sod is None:
                sod = []
            path = "root"
            for i in sod:
                path += ('^||^{}'.format(i['props']['children']))
            if dropdown_value:
                path += ('^||^{}'.format(dropdown_value))
            return path

        changed_index = None

        if 'button: ' in changed_id:
            for i in range(5):
                if 'button: {}'.replace("{}", str(i)) in changed_id:
                    changed_index = i
        else:
            changed_index = int(search(r'\d+', changed_id).group())

        # Ensures that state_of_display is a list of dictionaries
        if type(state_of_display) == dict:
            state_of_display = [state_of_display]

        # if 'back' requested
        if 'hierarchy_revert' in changed_id:
            # if at the end, prevent update
            if len(state_of_display) == 0:
                raise PreventUpdate
            # else, pop the top button and generate dropdown
            state_of_display.pop()
            display_button = state_of_display
            nid_path = get_nid_path(sod=state_of_display)
            dropdown = generate_dropdown(changed_index, df_name, nid_path)

        elif 'hierarchy_to_top' in changed_id or 'data-set' in changed_id:
            display_button = []
            nid_path = get_nid_path()
            dropdown = generate_dropdown(changed_index, df_name, nid_path)

        elif 'hierarchy_specific_dropdown' in changed_id:
            # If dropdown has been remade, do not modify the history
            if dropdown_val is None:
                raise PreventUpdate
            # If nothing in history return value
            elif not state_of_display:
                display_button = generate_history_button(dropdown_val, 0, changed_index)
                nid_path = get_nid_path(dropdown_value=dropdown_val)
                dropdown = generate_dropdown(changed_index, df_name, nid_path)
            # If something is in the history preserve it and add value to it
            else:
                display_button = state_of_display + [
                    (generate_history_button(dropdown_val, len(state_of_display), changed_index))]
                nid_path = get_nid_path(sod=state_of_display, dropdown_value=dropdown_val)
                dropdown = generate_dropdown(changed_index, df_name, nid_path)

        # If update triggered due to creation of a button do not update anything
        elif all(i == 0 for i in n_clicks_click_history):
            raise PreventUpdate

        # If the history has been selected find the value of the button pressed and get it to reset the history and
        # dropdown to that point
        else:
            index = [i != 0 for i in n_clicks_click_history].index(True)
            history = state_of_display[:index + 1]
            history[index]['props']['n_clicks'] = 0
            display_button = history
            nid_path = get_nid_path(sod=history)
            dropdown = generate_dropdown(changed_index, df_name, nid_path)

        # check if leaf node, if so say graph all siblings instead of graph all in dropdown
        if 'options=[]' not in str(dropdown):
            options = [{'label': get_label('LBL_Graph_All_In_Dropdown'), 'value': 'graph_children'}]
        else:
            options = [{'label': get_label('LBL_Graph_All_Siblings'), 'value': 'graph_children'}]

        return display_button, dropdown, options

# swaps between displaying the SPECIFIC and LEVEL hierarchy menus
app.clientside_callback(
    """
    function(hierarchy_toggle){
        if (hierarchy_toggle == 'Level Filter'){
            return [{}, {'display': 'none'}];
        }
        else{
            return [{'display': 'none'}, {}];
        }
    }
    """,
    [Output({'type': 'hierarchy_level_filter', 'index': MATCH}, 'style'),
     Output({'type': 'hierarchy_specific_filter', 'index': MATCH}, 'style')],
    [Input({'type': 'hierarchy-toggle', 'index': MATCH}, 'value')],
    prevent_initial_call=True
)


# ***************************************************DATE PICKER****************************************************

# update date picker
@app.callback(
    [Output({'type': 'div-date-range-selection', 'index': MATCH}, 'children'),
     Output({'type': 'date-picker-trigger', 'index': MATCH}, 'data-boolean')],
    [Input({'type': 'radio-timeframe', 'index': MATCH}, 'value'),
     Input({'type': 'fiscal-year-toggle', 'index': MATCH}, 'value'),
     Input({'type': 'date-picker-year-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-quarter-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-month-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'date-picker-week-button', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'start-year-input', 'index': MATCH}, 'value'),
     Input({'type': 'end-year-input', 'index': MATCH}, 'value'),
     Input({'type': 'start-secondary-input', 'index': MATCH}, 'value'),
     Input({'type': 'end-secondary-input', 'index': MATCH}, 'value'),
     Input({'type': 'update-date-picker-trigger', 'index': MATCH}, 'data-boolean')
     ],
    [State({'type': 'start-year-input', 'index': MATCH}, 'name'),
     State({'type': 'data-set', 'index': MATCH}, 'value'),
     State('df-constants-storage', 'data')],
    prevent_initial_call=True
)
def _update_date_picker(input_method, fiscal_toggle, _year_button_clicks, _quarter_button_clicks,
                        _month_button_clicks, _week_button_clicks, start_year_selection, end_year_selection,
                        start_secondary_selection, end_secondary_selection, update_trigger, tab, df_name, df_const):

    # ----------------------------------------------Variable Declarations-----------------------------------------------
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    tile = dash.callback_context.inputs_list[0]['id']['index']
    # ------------------------------------------------------------------------------------------------------------------

    if changed_id == '.':
        raise PreventUpdate

    if 'update-date-picker-trigger' in changed_id:
        input_method = update_trigger["Input Method"]
        start_year_selection = update_trigger["Start Year Selection"]
        end_year_selection = update_trigger["End Year Selection"]
        start_secondary_selection = update_trigger["Start Secondary Selection"]
        end_secondary_selection = update_trigger["End Secondary Selection"]
        tab = update_trigger["Tab"]

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
        year_classname = quarter_classname = month_classname = week_classname = 'date-picker-nav'
        year_disabled = quarter_disabled = month_disabled = week_disabled = False
        # secondary input boxes do not exist if inside of year tab - their data is None unless otherwise specified
        fringe_min = fringe_max = selected_secondary_min = selected_secondary_max = default_max = None
        # if tabs do not exist or the 'year' tab was requested or year type changed,
        # generate the tabs with the 'year' tab as active
        if 'radio-timeframe' in changed_id or 'date-picker-year-button' in changed_id:
            year_classname = 'date-picker-nav-selected'
            year_disabled = True
            # use the year scheme (gregorian/fiscal) selected by the user
            if fiscal_toggle == 'Gregorian':
                min_year = df_const[df_name]['GREGORIAN_MIN_YEAR']
                max_year = df_const[df_name]['GREGORIAN_YEAR_MAX']
            else:
                min_year = df_const[df_name]['FISCAL_MIN_YEAR']
                max_year = df_const[df_name]['FISCAL_YEAR_MAX']
            left_column = html.Div([
                get_date_box(index={'type': 'start-year-input', 'index': tile},
                             value=min_year,
                             minimum=min_year,
                             maximum=max_year,
                             name='Year'),
                dcc.Input(
                    id={'type': 'start-secondary-input', 'index': tile},
                    value=1,
                    style={'display': 'none'})])
            right_column = html.Div([
                get_date_box(index={'type': 'end-year-input', 'index': tile},
                             value=max_year + 1,
                             minimum=min_year + 1,
                             maximum=max_year + 1),
                dcc.Input(
                    id={'type': 'end-secondary-input', 'index': tile},
                    value=1,
                    style={'display': 'none'})])

        # if a tab was requested other than 'year', generate the default appearance of the selected tab
        elif 'n_clicks' in changed_id:
            conditions = ['date-picker-quarter-button' in changed_id, 'date-picker-month-button' in changed_id]
            quarter_classname, quarter_disabled, month_classname, month_disabled, week_classname, week_disabled, \
                fringe_min, fringe_max, default_max, max_year, \
                new_tab = get_secondary_data(conditions, fiscal_toggle, df_name, df_const)
            # set min_year according to user selected fiscal/gregorian time type
            if fiscal_toggle == 'Gregorian':
                min_year = df_const[df_name]['GREGORIAN_MIN_YEAR']
            else:
                min_year = df_const[df_name]['FISCAL_MIN_YEAR']
            # if data exists for only one year, use fringe extremes
            if min_year == max_year:
                max_min = fringe_min + 1
                min_max = fringe_max - 1
            # if data exists for more than one year the interior extrema are as expected
            else:
                min_max = default_max
                max_min = 1
            year_input_min = get_date_box(index={'type': 'start-year-input', 'index': tile},
                                          value=min_year,
                                          minimum=min_year,
                                          maximum=max_year,
                                          name=new_tab)
            year_input_max = get_date_box(index={'type': 'end-year-input', 'index': tile},
                                          value=max_year,
                                          minimum=min_year,
                                          maximum=max_year)
            secondary_input_min = get_date_box(index={'type': 'start-secondary-input', 'index': tile},
                                               value=fringe_min,
                                               minimum=fringe_min,
                                               maximum=min_max, )
            secondary_input_max = get_date_box(index={'type': 'end-secondary-input', 'index': tile},
                                               value=fringe_max,
                                               minimum=max_min,
                                               maximum=fringe_max)
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
                year_classname = 'date-picker-nav-selected'
                year_disabled = True
                if fiscal_toggle == 'Gregorian':
                    max_year = df_const[df_name]['GREGORIAN_YEAR_MAX']
                else:
                    max_year = df_const[df_name]['FISCAL_YEAR_MAX']
            # if not inside of year tab, get secondary data
            else:
                selected_secondary_min = start_secondary_selection
                selected_secondary_max = end_secondary_selection
                conditions = [tab == 'Quarter', tab == 'Month']
                quarter_classname, quarter_disabled, month_classname, month_disabled, week_classname, week_disabled, \
                    fringe_min, fringe_max, default_max, max_year, \
                    new_tab = get_secondary_data(conditions, fiscal_toggle, df_name, df_const)
            # set min_year according to user selected time type (gregorian/fiscal)
            if fiscal_toggle == 'Gregorian':
                min_year = df_const[df_name]['GREGORIAN_MIN_YEAR']
            else:
                min_year = df_const[df_name]['FISCAL_MIN_YEAR']
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
                    get_date_box(index={'type': 'start-year-input', 'index': tile},
                                 value=selected_min_year,
                                 minimum=min_year,
                                 maximum=selected_max_year - 1,
                                 name='Year'),
                    dcc.Input(
                        id={'type': 'start-secondary-input', 'index': tile},
                        value=1,
                        style={'display': 'none'})])
                right_column = html.Div([
                    get_date_box(index={'type': 'end-year-input', 'index': tile},
                                 value=selected_max_year,
                                 minimum=selected_min_year + 1,
                                 maximum=max_year + 1),
                    dcc.Input(
                        id={'type': 'end-secondary-input', 'index': tile},
                        value=1,
                        style={'display': 'none'})])

        # do not move the arrow upwards unless secondary selection input boxes exist
        bottom = '0' if not fringe_min else '17px'
        children = [
            html.Header([
                html.Button(get_label("LBL_Year"), className=year_classname,
                            id={'type': 'date-picker-year-button', 'index': tile},
                            disabled=year_disabled),
                html.Button(get_label("LBL_Quarter"), className=quarter_classname,
                            id={'type': 'date-picker-quarter-button', 'index': tile},
                            disabled=quarter_disabled),
                html.Button(get_label("LBL_Month"), className=month_classname,
                            id={'type': 'date-picker-month-button', 'index': tile},
                            disabled=month_disabled),
                html.Button(get_label("LBL_Week"), className=week_classname,
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
            ], style={'width': '100%', 'height': '100%', 'margin-top': '8px'})]

    return children, True


# enable past __ ___ selections
app.clientside_callback(
    """
    function(selected_timeframe){
        if (selected_timeframe == 'to-current'){
            return [false, false];
        }
        else{
            return [true, true];
        }
    }
    """,
    [Output({'type': 'num-periods', 'index': MATCH}, 'disabled'),
     Output({'type': 'period-type', 'index': MATCH}, 'disabled')],
    [Input({'type': 'radio-timeframe', 'index': MATCH}, 'value')],
    prevent_initial_call=True
)

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
         # update graph trigger
         Input({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_trigger'),
         # update table trigger
         Input({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_table_trigger')],
        # Link state
        [State({'type': 'tile-link', 'index': x}, 'className'),
         # Data set state
         State({'type': 'data-set', 'index': x}, 'value'),
         # Date picker state
         State({'type': 'start-year-input', 'index': x}, 'name'),
         State({'type': 'radio-timeframe', 'index': x}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': x}, 'value'),
         State({'type': 'start-year-input', 'index': x}, 'value'),
         State({'type': 'end-year-input', 'index': x}, 'value'),
         State({'type': 'start-secondary-input', 'index': x}, 'value'),
         State({'type': 'end-secondary-input', 'index': x}, 'value'),
         State({'type': 'num-periods', 'index': x}, 'value'),
         State({'type': 'period-type', 'index': x}, 'value'),
         # Hierarchy states for tile
         State({'type': 'hierarchy-toggle', 'index': x}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': x}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': x}, 'children'),
         State({'type': 'graph_children_toggle', 'index': x}, 'value'),
         State({'type': 'hierarchy_specific_dropdown', 'index': x}, 'options'),
         # Date picker states for parent data menu
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value'),
         State({'type': 'num-periods', 'index': 4}, 'value'),
         State({'type': 'period-type', 'index': 4}, 'value'),
         # Hierarchy States for parent data menu
         State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
         State({'type': 'hierarchy_specific_dropdown', 'index': 4}, 'options'),
         # Parent Data set
         State({'type': 'data-set', 'index': 4}, 'value'),
         State('df-constants-storage', 'data'),
         State({'type': 'data-set-parent', 'index': 4}, 'value')]
    )
    def _update_table(page_current, page_size, sort_by, filter_query, _graph_trigger, _table_trigger, link_state,
                      df_name, secondary_type, timeframe, fiscal_toggle, start_year, end_year, start_secondary,
                      end_secondary, num_periods, period_type, hierarchy_toggle, hierarchy_level_dropdown,
                      state_of_display, hierarchy_graph_children, hierarchy_options, parent_secondary_type,
                      parent_timeframe, parent_fiscal_toggle, parent_start_year, parent_end_year,
                      parent_start_secondary, parent_end_secondary, parent_num_periods, parent_period_type,
                      parent_hierarchy_toggle, parent_hierarchy_level_dropdown, parent_state_of_display,
                      parent_hierarchy_graph_children, parent_hierarchy_options, parent_df_name, df_const, df_confirm):

        if link_state == 'fa fa-link':
            secondary_type = parent_secondary_type
            timeframe = parent_timeframe
            fiscal_toggle = parent_fiscal_toggle
            start_year = parent_start_year
            end_year = parent_end_year
            start_secondary = parent_start_secondary
            end_secondary = parent_end_secondary
            hierarchy_toggle = parent_hierarchy_toggle
            hierarchy_level_dropdown = parent_hierarchy_level_dropdown
            state_of_display = parent_state_of_display
            hierarchy_graph_children = parent_hierarchy_graph_children
            num_periods = parent_num_periods
            period_type = parent_period_type
            hierarchy_options = parent_hierarchy_options
            if df_confirm is not None:
                df_name = df_confirm
            else:
                df_name = parent_df_name

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

        if hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
            # If at a leaf node then display it's parents data
            nid_path = "root"
            for i in list_of_names:
                nid_path += ('^||^{}'.format(i))
            if not hierarchy_options:
                list_of_names.pop()

        # If "Last ___ ____" is active and the num_periods is invalid (None), return an empty graph
        if timeframe == 'to-current' and not num_periods:
            return [], 0
        # else, filter normally
        else:
            dff = data_filter(list_of_names, secondary_type, end_secondary, end_year, start_secondary, start_year,
                              timeframe, fiscal_toggle, num_periods, period_type, hierarchy_toggle,
                              hierarchy_level_dropdown, hierarchy_graph_children, df_name, df_const)

        # Reformat date column
        dff['Date of Event'] = dff['Date of Event'].transform(lambda y: y.strftime(format='%Y-%m-%d'))

        # Filter based on datatable filters
        filtering_expressions = filter_query.split(' && ')
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
                inplace=False)

        return dff.iloc[page_current * page_size: (page_current + 1) * page_size].to_dict('records'), \
            math.ceil(dff.iloc[:, 0].size / page_size)

# *************************************************DATA-FITTING******************************************************
# update the data fitting section of the edit graph menu
for x in range(4):
    app.clientside_callback(
        """
        function _update_data_fitting_options(degree_input){
            const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));
            let degree_input_wrapper = dash_clientside.no_update;
            let confidence_interval_wrapper = dash_clientside.no_update;
            
            if (degree_input == 'no-fit' || degree_input == 'linear-fit'){
                degree_input_wrapper = {'display': 'none'};
                if (degree_input == 'no-fit'){
                    confidence_interval_wrapper = {'display': 'none'};
                }
                else{
                    confidence_interval_wrapper = {'display': 'inline'};
                }
            }
            else if (degree_input == 'curve-fit'){
                degree_input_wrapper = {'display': 'inline'};
                confidence_interval_wrapper = {'display': 'inline'};
            }
            else{
                degree_input_wrapper = dash_clientside.no_update;
                confidence_interval_wrapper = dash_clientside.no_update;
            }
    
            return [degree_input_wrapper, confidence_interval_wrapper];
        }
        """,
        [Output({'type': 'degree-input-wrapper', 'index': x}, 'style'),
         Output({'type': 'confidence-interval-wrapper', 'index': x}, 'style')],
        [Input({'type': 'args-value: {}'.replace("{}", str(x)), 'index': 4}, 'value')],
        prevent_initial_call=True
    )

for x in range(4):
    app.clientside_callback(
        """
        function _hide_animated_bubble_options(xaxis, graph_type){
            let hide_xaxis_measure = dash_clientside.no_update;
            let hide_yaxis_measure = dash_clientside.no_update;
            let hide_size_measure = dash_clientside.no_update;
            if (xaxis == 'Time' && graph_type == 'Bubble'){
                hide_xaxis_measure = {'display': 'none'};
                hide_yaxis_measure = {'display': 'none'};
                hide_size_measure = {'display': 'none'};
                }
            else{
                hide_xaxis_measure = {'display': 'inline-block', 'width': '80%','max-width': '350px'};
                hide_yaxis_measure = {'display': 'inline-block', 'width': '80%','max-width': '350px'};
                hide_size_measure = {'display': 'inline-block', 'width': '80%','max-width': '350px'};
                }
            return [hide_xaxis_measure, hide_yaxis_measure, hide_size_measure];
        }
            """,

        [Output({'type': 'hide-xaxis-measure', 'index': x}, 'style'),
         Output({'type': 'hide-yaxis-measure', 'index': x}, 'style'),
         Output({'type': 'hide-size-measure', 'index': x}, 'style')],
        Input({'type': 'args-value: {}'.replace("{}", str(x)), 'index': 0}, 'value'),
        State({'type': 'graph-type-dropdown', 'index': x}, 'value'),
        prevent_initial_call=True
    )
