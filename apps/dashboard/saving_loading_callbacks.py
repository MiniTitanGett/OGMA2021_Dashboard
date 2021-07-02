######################################################################################################################
"""
saving_loading_callbacks.py

stores all callbacks for managing saves/loading tiles/dashboards
"""
######################################################################################################################

# External Packages
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from re import search
from dash import no_update
import dash_html_components as html
from flask import session

# Internal Packages
from apps.dashboard.layouts import get_data_menu, get_customize_content, get_div_body
from apps.dashboard.app import app
from apps.dashboard.data import get_label, CLR, dataset_to_df, generate_constants
from apps.dashboard.saving_functions import delete_layout, save_layout_state, save_layout_to_db, \
    save_dashboard_state, save_dashboard_to_db, delete_dashboard, load_graph_menu

#   SAVING
#       - _save_tile()
#       _ _save_tile()
#       - _save_dashboard()
#   LOADING
#       - _load_tile_layout()
#       - _reset_selected_layout()

# **********************************************GLOBAL VARIABLES*****************************************************

REPORT_POINTER_PREFIX = 'Report_Ext_'
DASHBOARD_POINTER_PREFIX = 'Dashboard_Ext_'


# ************************************SHARED TILE LOADING/DASHBOARD SAVING*******************************************


# load the tile title
@app.callback(
    Output({'type': 'tile-title', 'index': MATCH}, 'value'),
    [Input({'type': 'set-tile-title-trigger', 'index': MATCH}, 'data-tile_load_title'),
     Input({'type': 'set-tile-title-trigger', 'index': MATCH}, 'data-dashboard_load_title')],
    prevent_initial_call=True
)
def _load_tile_title(tile_load_title, dashboard_load_title):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    if 'data-tile_load_title' in changed_id:
        title = tile_load_title
    else:
        title = dashboard_load_title

    return title


# ***********************************************SHARED SAVING*******************************************************

# update the dropdown options of available tile layouts
@app.callback(
    Output({'type': 'select-layout-dropdown', 'index': ALL}, 'options'),
    [Input({'type': 'set-dropdown-options-trigger', 'index': ALL}, 'data-tile_saving'),
     Input({'type': 'set-dropdown-options-trigger', 'index': 0}, 'data-dashboard_saving')],
    [State({'type': 'tile-link', 'index': ALL}, 'className')],
    prevent_initial_call=True
)
def _update_tile_loading_dropdown_options(_tile_saving_trigger, _dashboard_saving_trigger, links):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    # graph titles was previously session['saved_layouts']
    return [[{'label': session['saved_layouts'][key]['Title'], 'value': key} for key in
             session['saved_layouts']]] * len(links)


# *************************************************TILE SAVING********************************************************

# manage tile saves trigger
@app.callback(
    Output('tile-save-trigger-wrapper', 'children'),  # formatted in two chained callbacks to mix ALL and y values
    [Input({'type': 'save-button', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-button', 'index': ALL}, 'n_clicks'),
     Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value'),
     Input('prompt-result', 'children')],
    State('prompt-title', 'data-'),
    prevent_initial_call=True
)
def _manage_tile_save_and_load_trigger(save_clicks, delete_clicks, load_value, prompt_result, prompt_data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.' or len(dash.callback_context.triggered) > 1:
        raise PreventUpdate

    if 'prompt-result' in changed_id:
        changed_index = prompt_data[1]
    else:
        changed_index = int(search(r'\d+', changed_id).group())

    # Blank prevent updates
    if '"type":"save-button"}.n_clicks' in changed_id and save_clicks[changed_index] == 0:
        raise PreventUpdate
    if '"type":"delete-button"}.n_clicks' in changed_id and delete_clicks[changed_index] == 0:
        raise PreventUpdate
    if '"type":"select-layout-dropdown"}.value' in changed_id and None in load_value:
        raise PreventUpdate

    # switch statement
    if 'save-button' in changed_id:
        mode = "save"
    elif 'delete-button' in changed_id:
        mode = "delete"
    elif 'select-layout-dropdown' in changed_id:
        mode = "load"
    elif prompt_data[0] == 'delete' and prompt_result == 'ok':
        mode = "confirm-delete"
    elif prompt_data[0] == 'overwrite' and prompt_result == 'ok':
        mode = "confirm-overwrite"
    elif prompt_data[0] == 'load' and prompt_result == 'ok':
        mode = "confirm-load"
    else:
        mode = "cancel"

    children = dcc.Dropdown(
        id={'type': 'tile-save-trigger', 'index': changed_index},
        value=mode)

    return children


# Tile saving/save deleting/tile loading - serves prompt
for y in range(4):
    @app.callback(
        # LAYOUT components
        [Output({'type': 'prompt-trigger', 'index': y}, 'data-'),
         Output({'type': 'set-dropdown-options-trigger', 'index': y}, 'data-tile_saving'),
         Output({'type': 'minor-popup', 'index': y}, 'children'),
         Output({'type': 'minor-popup', 'index': y}, 'is_open'),
         # load tile layout outputs
         Output({'type': 'set-tile-title-trigger', 'index': y}, 'data-tile_load_title'),
         Output({'type': 'tile-customize-content', 'index': y}, 'children'),
         Output({'type': 'data-menu-tile-loading', 'index': y}, 'children'),
         Output({'type': 'select-layout-dropdown', 'index': y}, 'value'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-tab'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-start_year'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-end_year'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-start_secondary'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-end_secondary'),
         Output({'type': 'tile-link-wrapper', 'index': y}, 'children'),
         Output({'type': 'df-constants-storage-tile-wrapper', 'index': y}, 'children')],
        [Input({'type': 'tile-save-trigger', 'index': y}, 'value')],
        # Tile features
        [State({'type': 'tile-title', 'index': y}, 'value'),
         State({'type': 'tile-link', 'index': y}, 'className'),
         State({'type': 'graph-type-dropdown', 'index': y}, 'value'),
         State({'type': 'args-value: {}'.replace("{}", str(y)), 'index': ALL}, 'value'),
         # Data set states
         State({'type': 'data-set', 'index': y}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         # master data menu states
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value'),
         State({'type': 'num-periods', 'index': 4}, 'value'),
         State({'type': 'period-type', 'index': 4}, 'value'),
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         # tile data menu states
         State({'type': 'start-year-input', 'index': y}, 'value'),
         State({'type': 'end-year-input', 'index': y}, 'value'),
         State({'type': 'hierarchy-toggle', 'index': y}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': y}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': y}, 'children'),
         State({'type': 'graph_children_toggle', 'index': y}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': y}, 'value'),
         State({'type': 'radio-timeframe', 'index': y}, 'value'),
         State({'type': 'start-secondary-input', 'index': y}, 'value'),
         State({'type': 'end-secondary-input', 'index': y}, 'value'),
         State({'type': 'num-periods', 'index': y}, 'value'),
         State({'type': 'period-type', 'index': y}, 'value'),
         State({'type': 'start-year-input', 'index': y}, 'name'),
         # load layout states
         State({'type': 'select-layout-dropdown', 'index': y}, 'value'),
         State('df-constants-storage', 'data')],
        prevent_initial_call=True
    )
    def _manage_tile_save_and_load(trigger, graph_title, link_state, graph_type, args_list, df_name, master_df_name,
                                   master_year_start, master_year_end, master_hierarchy_toggle,
                                   master_hierarchy_level_dropdown, master_state_of_display,
                                   master_graph_children_toggle, master_fiscal_toggle, master_input_method,
                                   master_secondary_start, master_secondary_end, master_x_time_period,
                                   master_period_type, master_tab, year_start, year_end, hierarchy_toggle,
                                   hierarchy_level_dropdown, state_of_display, graph_children_toggle, fiscal_toggle,
                                   input_method, secondary_start, secondary_end, x_time_period, period_type, tab,
                                   selected_layout, df_const):

        if link_state == 'fa fa-link':
            fiscal_toggle = master_fiscal_toggle
            year_start = master_year_start
            year_end = master_year_end
            secondary_start = master_secondary_start
            secondary_end = master_secondary_end
            x_time_period = master_x_time_period
            period_type = master_period_type
            input_method = master_input_method
            hierarchy_toggle = master_hierarchy_toggle
            hierarchy_level_dropdown = master_hierarchy_level_dropdown
            state_of_display = master_state_of_display
            tab = master_tab
            df_name = master_df_name
            graph_children_toggle = master_graph_children_toggle

        if type(state_of_display) == dict:
            state_of_display = [state_of_display]

        nid_path = "root"
        for button in state_of_display:
            nid_path += '^||^{}'.format(button['props']['children'])

        tile = int(dash.callback_context.inputs_list[0]['id']['index'])

        # Outputs
        update_options_trigger = no_update
        # [mode/prompt_trigger, tile], prompt_style/show_hide, prompt_title, prompt_body]
        prompt_trigger = no_update
        popup_text = no_update
        popup_is_open = no_update
        tile_title_trigger = no_update
        customize_content = no_update
        data_content = no_update
        layout_dropdown = no_update
        tab_output = no_update
        start_year = no_update
        end_year = no_update
        start_secondary = no_update
        end_secondary = no_update
        unlink = no_update
        df_const_output = no_update

        # if save requested or the overwrite was confirmed, check for exceptions and save
        if trigger == 'save' or trigger == 'confirm-overwrite':

            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")
            # regex.sub('[^A-Za-z0-9]+', '', graph_title)

            graph_titles = []

            for layout in session['saved_layouts']:
                graph_titles.append(session['saved_layouts'][layout]['Title'])

            # if tile is untitled, prevent updates but return save message
            if graph_title == '':
                prompt_trigger = [['empty_title', tile], {}, get_label('LBL_Untitled_Graph'),
                                  get_label('LBL_Untitled_Graph_Prompt')]

            # if conflicting tiles and overwrite not requested, prompt overwrite
            elif intermediate_pointer in session['saved_layouts'] \
                    and session['saved_layouts'][intermediate_pointer]['Title'] == graph_title \
                    and 'confirm-overwrite' != trigger:

                prompt_trigger = [['overwrite', tile], {}, get_label('LBL_Overwrite_Graph'),
                                  get_label('LBL_Overwrite_Graph_Prompt')]

            # else, title is valid to be saved
            else:
                while True:
                    if intermediate_pointer in session['saved_layouts'] and trigger != "confirm-overwrite":
                        layout_pointer = intermediate_pointer + "_"
                        intermediate_pointer = layout_pointer
                    else:
                        layout_pointer = intermediate_pointer
                        break

                elements_to_save = {'Graph Type': graph_type,
                                    'Args List': args_list,
                                    'Fiscal Toggle': fiscal_toggle,
                                    'Timeframe': input_method,
                                    'Num Periods': x_time_period,
                                    'Period Type': period_type,
                                    'Hierarchy Toggle': hierarchy_toggle,
                                    'Level Value': hierarchy_level_dropdown,
                                    'Data Set': df_name,
                                    'Graph All Toggle': graph_children_toggle,
                                    'NID Path': nid_path,
                                    'Title': graph_title}
                # if input method is 'select-range', add the states of the select range inputs
                if input_method == 'select-range':
                    elements_to_save['Date Tab'] = tab
                    elements_to_save['Start Year'] = year_start
                    elements_to_save['End Year'] = year_end
                    elements_to_save['Start Secondary'] = secondary_start
                    elements_to_save['End Secondary'] = secondary_end

                # calls the save_graph_state function to save the graph to the sessions dictionary
                save_layout_state(layout_pointer, elements_to_save)
                # saves the graph title and layout to the file where you are storing all of the saved layouts
                # save_layout_to_file(session['saved_layouts'])
                # saves the graph layout to the database
                save_layout_to_db(layout_pointer, graph_title, 'save' == trigger)

                prompt_trigger = [None, {'display': 'hide'}, None, None]
                popup_text = get_label('LBL_Your_Graph_Has_Been_Saved').format(graph_title)
                popup_is_open = True
                update_options_trigger = 'trigger'

        # if delete button was pressed, prompt delete
        elif trigger == 'delete':

            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")

            graph_titles = []

            for layout in session['saved_layouts']:
                graph_titles.append(session['saved_layouts'][layout]['Title'])

            # if tile exists in session, send delete prompt
            if intermediate_pointer in session['saved_layouts'] \
                    and session['saved_layouts'][intermediate_pointer]['Title'] == graph_title:
                prompt_trigger = [['delete', tile], {}, get_label('LBL_Delete_Graph'),
                                  get_label('LBL_Delete_Graph_Prompt').format(graph_title)]
            else:
                prompt_trigger = [None, {'display': 'hide'}, None, None]

        # If confirm delete button has been pressed
        elif trigger == 'confirm-delete':
            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")
            delete_layout(intermediate_pointer)
            update_options_trigger = 'trigger'
            prompt_trigger = [None, {'display': 'hide'}, None, None]
            popup_text = get_label('LBL_Your_Graph_Has_Been_Deleted').format(graph_title)
            popup_is_open = True

        # if load then we send the load prompt
        elif trigger == 'load':
            prompt_trigger = [['load', tile], {}, get_label('LBL_Load_Graph'), get_label('LBL_Load_Graph_Prompt')]

        # if confirm-load then we load what was selected
        elif trigger == 'confirm-load':
            df_name = session['saved_layouts'][selected_layout]['Data Set']

            # check if data is loaded
            if df_name not in session:
                session[df_name] = dataset_to_df(df_name)
                if df_const is None:
                    df_const = {}
                df_const[df_name] = generate_constants(df_name)

            #  --------- create customize menu ---------

            graph_type = session['saved_layouts'][selected_layout]['Graph Type']
            args_list = session['saved_layouts'][selected_layout]['Args List']

            graph_menu = load_graph_menu(graph_type=graph_type, tile=tile, df_name=df_name, args_list=args_list,
                                         df_const=df_const)

            customize_content = get_customize_content(tile=tile, graph_type=graph_type, graph_menu=graph_menu,
                                                      df_name=df_name)

            #  --------- create data sidemenu ---------

            # set hierarchy toggle value (level vs specific)
            hierarchy_toggle = session['saved_layouts'][selected_layout]['Hierarchy Toggle']
            # set level value selection
            level_value = session['saved_layouts'][selected_layout]['Level Value']
            # retrieve nid string
            nid_path = session['saved_layouts'][selected_layout]['NID Path']
            # set the value of "Graph All" checkbox
            graph_all_toggle = session['saved_layouts'][selected_layout]['Graph All Toggle']
            # set gregorian/fiscal toggle value
            fiscal_toggle = session['saved_layouts'][selected_layout]['Fiscal Toggle']
            # set timeframe radio buttons selection
            input_method = session['saved_layouts'][selected_layout]['Timeframe']
            # set num periods
            num_periods = session['saved_layouts'][selected_layout]['Num Periods']
            # set period type
            period_type = session['saved_layouts'][selected_layout]['Period Type']

            data_content = get_data_menu(tile=tile, df_name=df_name, mode='tile-loading',
                                         hierarchy_toggle=hierarchy_toggle, level_value=level_value,
                                         nid_path=nid_path, graph_all_toggle=graph_all_toggle,
                                         fiscal_toggle=fiscal_toggle, input_method=input_method,
                                         num_periods=num_periods,
                                         period_type=period_type, df_const=df_const)

            # show and set 'Select Range' inputs if selected, else leave hidden and unset
            if session['saved_layouts'][selected_layout]['Timeframe'] == 'select-range':
                tab_output = session['saved_layouts'][selected_layout]['Date Tab']
                start_year = session['saved_layouts'][selected_layout]['Start Year']
                end_year = session['saved_layouts'][selected_layout]['End Year']
                start_secondary = session['saved_layouts'][selected_layout]['Start Secondary']
                end_secondary = session['saved_layouts'][selected_layout]['End Secondary']
            else:
                tab_output = start_year = end_year = start_secondary = end_secondary = no_update

            df_const_output = dcc.Store(
                id='df-constants-storage',
                storage_type='memory',
                data=df_const)
            for x in range(tile):
                df_const = html.Div(
                    df_const,
                    id={'type': 'df-constants-storage-tile-wrapper', 'index': x}
                )

            unlink = html.I(
                className='fa fa-unlink',
                id={'type': 'tile-link', 'index': tile},
                style={'position': 'relative'})
            tile_title_trigger = session['saved_layouts'][selected_layout]['Title']
            popup_text = get_label('LBL_Your_Graph_Has_Been_Loaded').format(tile_title_trigger)
            popup_is_open = True
            layout_dropdown = None

        # if anything was cancelled, clear display
        elif trigger == 'cancel':
            prompt_trigger = [None, {'display': 'hide'}, None, None]
            layout_dropdown = None

        return prompt_trigger, update_options_trigger, popup_text, popup_is_open, tile_title_trigger, \
            customize_content, data_content, layout_dropdown, tab_output, start_year, end_year, start_secondary, \
            end_secondary, unlink, df_const_output


# **********************************************DASHBOARD SAVING******************************************************

# dashboard saving/save deleting
@app.callback(
    [Output('dashboard-save-status-symbols', 'children'),
     Output('delete-dashboard', 'options'),
     Output('select-dashboard-dropdown', 'options'),
     Output('delete-dashboard', 'value'),
     Output({'type': 'set-dropdown-options-trigger', 'index': 0}, 'data-dashboard_saving'),
     Output({'type': 'set-tile-title-trigger', 'index': 0}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 1}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 2}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 3}, 'data-dashboard_load_title')],
    [Input('button-save-dashboard', 'n_clicks'),
     Input('confirm-delete-dashboard', 'n_clicks'),
     Input({'type': 'dashboard-overwrite', 'index': ALL}, 'n_clicks')],
    # title of dashboard requested to be deleted
    [State('delete-dashboard', 'value'),
     # dashboard info
     State('dashboard-title', 'value'),
     # tile info
     State({'type': 'tile-title', 'index': ALL}, 'value'),
     State({'type': 'tile-link', 'index': ALL}, 'className'),
     State({'type': 'graph-type-dropdown', 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(0)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(1)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(2)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(3)), 'index': ALL}, 'value'),
     # data sets
     State({'type': 'data-set', 'index': 0}, 'value'),
     State({'type': 'data-set', 'index': 1}, 'value'),
     State({'type': 'data-set', 'index': 2}, 'value'),
     State({'type': 'data-set', 'index': 3}, 'value'),
     State({'type': 'data-set', 'index': 4}, 'value'),
     # start years
     State({'type': 'start-year-input', 'index': 0}, 'value'),
     State({'type': 'start-year-input', 'index': 1}, 'value'),
     State({'type': 'start-year-input', 'index': 2}, 'value'),
     State({'type': 'start-year-input', 'index': 3}, 'value'),
     State({'type': 'start-year-input', 'index': 4}, 'value'),
     # end years
     State({'type': 'end-year-input', 'index': 0}, 'value'),
     State({'type': 'end-year-input', 'index': 1}, 'value'),
     State({'type': 'end-year-input', 'index': 2}, 'value'),
     State({'type': 'end-year-input', 'index': 3}, 'value'),
     State({'type': 'end-year-input', 'index': 4}, 'value'),
     # hierarchy toggles
     State({'type': 'hierarchy-toggle', 'index': 0}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 1}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 2}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 3}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
     # graph children toggles
     State({'type': 'graph_children_toggle', 'index': 0}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 1}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 2}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 3}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
     # hierarchy level dropdown values
     State({'type': 'hierarchy_level_dropdown', 'index': 0}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 1}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 2}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 3}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
     # hieararchy display paths children
     State({'type': 'hierarchy_display_button', 'index': 0}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 1}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 2}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 3}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
     # Fiscal year toggle
     State({'type': 'fiscal-year-toggle', 'index': 0}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 1}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 2}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 3}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
     # radio timeframes
     State({'type': 'radio-timeframe', 'index': 0}, 'value'),
     State({'type': 'radio-timeframe', 'index': 1}, 'value'),
     State({'type': 'radio-timeframe', 'index': 2}, 'value'),
     State({'type': 'radio-timeframe', 'index': 3}, 'value'),
     State({'type': 'radio-timeframe', 'index': 4}, 'value'),
     # start secondary values
     State({'type': 'start-secondary-input', 'index': 0}, 'value'),
     State({'type': 'start-secondary-input', 'index': 1}, 'value'),
     State({'type': 'start-secondary-input', 'index': 2}, 'value'),
     State({'type': 'start-secondary-input', 'index': 3}, 'value'),
     State({'type': 'start-secondary-input', 'index': 4}, 'value'),
     # end secondary values
     State({'type': 'end-secondary-input', 'index': 0}, 'value'),
     State({'type': 'end-secondary-input', 'index': 1}, 'value'),
     State({'type': 'end-secondary-input', 'index': 2}, 'value'),
     State({'type': 'end-secondary-input', 'index': 3}, 'value'),
     State({'type': 'end-secondary-input', 'index': 4}, 'value'),
     # num periods values
     State({'type': 'num-periods', 'index': 0}, 'value'),
     State({'type': 'num-periods', 'index': 1}, 'value'),
     State({'type': 'num-periods', 'index': 2}, 'value'),
     State({'type': 'num-periods', 'index': 3}, 'value'),
     State({'type': 'num-periods', 'index': 4}, 'value'),
     # period types
     State({'type': 'period-type', 'index': 0}, 'value'),
     State({'type': 'period-type', 'index': 1}, 'value'),
     State({'type': 'period-type', 'index': 2}, 'value'),
     State({'type': 'period-type', 'index': 3}, 'value'),
     State({'type': 'period-type', 'index': 4}, 'value'),
     # select-range tabs
     State({'type': 'start-year-input', 'index': 0}, 'name'),
     State({'type': 'start-year-input', 'index': 1}, 'name'),
     State({'type': 'start-year-input', 'index': 2}, 'name'),
     State({'type': 'start-year-input', 'index': 3}, 'name'),
     State({'type': 'start-year-input', 'index': 4}, 'name')],
    prevent_initial_call=True
)
def _save_dashboard(_save_clicks, _delete_clicks, _dashboard_overwrite_inputs,
                    remove_dashboard, dashboard_title, tile_titles, links, graph_types,
                    args_list_0, args_list_1, args_list_2, args_list_3,
                    df_name_0, df_name_1, df_name_2, df_name_3, df_name4,
                    start_year_0, start_year_1, start_year_2, start_year_3, start_year_4,
                    end_year_0, end_year_1, end_year_2, end_year_3, end_year_4,
                    hierarchy_toggle_0, hierarchy_toggle_1, hierarchy_toggle_2, hierarchy_toggle_3, hierarchy_toggle_4,
                    graph_all_toggle_0, graph_all_toggle_1, graph_all_toggle_2, graph_all_toggle_3, graph_all_toggle_4,
                    level_value_0, level_value_1, level_value_2, level_value_3, level_value_4,
                    button_path_0, button_path_1, button_path_2, button_path_3, button_path_4,
                    fiscal_toggle_0, fiscal_toggle_1, fiscal_toggle_2, fiscal_toggle_3, fiscal_toggle_4,
                    timeframe_0, timeframe_1, timeframe_2, timeframe_3, timeframe_4,
                    start_secondary_0, start_secondary_1, start_secondary_2, start_secondary_3, start_secondary_4,
                    end_secondary_0, end_secondary_1, end_secondary_2, end_secondary_3, end_secondary_4,
                    num_periods_0, num_periods_1, num_periods_2, num_periods_3, num_periods_4,
                    period_type_0, period_type_1, period_type_2, period_type_3, period_type_4,
                    date_tab_0, date_tab_1, date_tab_2, date_tab_3, date_tab_4):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    options = no_update
    delete_dropdown_val = no_update
    update_graph_options_trigger = no_update
    tile_title_returns = [no_update] * 4
    auto_named_titles = [no_update] * 4

    # if save requested or the overwrite was confirmed, check for exceptions and save
    if 'button-save-dashboard' in changed_id or '{"index":0,"type":"dashboard-overwrite"}.n_clicks' == changed_id:

        intermediate_dashboard_pointer = DASHBOARD_POINTER_PREFIX + dashboard_title.replace(" ", "")
        # regex.sub('[^A-Za-z0-9]+', '', dashboard_title)

        while True:
            if intermediate_dashboard_pointer in session['saved_layouts']:
                dashboard_pointer = intermediate_dashboard_pointer + "_"
                intermediate_dashboard_pointer = dashboard_pointer
            else:
                dashboard_pointer = intermediate_dashboard_pointer
                break

        used_dashboard_titles = []

        for dashboard_layout in session['saved_dashboards']:
            used_dashboard_titles.append(session['saved_dashboards'][dashboard_layout]['Dashboard Title'])

        # get non-overwriting status symbol display (check-mark or ban symbol)
        def get_status_symbol_display(tooltip, symbol):
            return html.I(
                html.Span(
                    tooltip,
                    className='save-symbols-tooltip'),
                className=symbol,
                id='save-status-symbols-inner',
                style={'padding': '10px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                       'text-align': 'center'})

        # auto name blank tile titles
        for idx, tile_title in enumerate(tile_titles):
            if tile_title == '':
                auto_named_titles[idx] = tile_titles[idx] = dashboard_title + '-' + str(idx + 1)

        used_titles = []

        for key in session['saved_layouts']:
            used_titles.append(session['saved_layouts'][key]["Title"])

        # check if the dashboard title is blank
        if dashboard_title == '':
            save_error_tooltip = get_label('LBL_Dashboards_Require_A_Title_To_Be_Saved')
            save_symbol = 'fa fa-ban'
            save_status_symbols = get_status_symbol_display(save_error_tooltip, save_symbol)

        # check if the dashboard is empty
        elif len(links) == 0:
            save_error_tooltip = get_label('LBL_Dashboard_Must_Not_Be_Empty')
            save_symbol = 'fa fa-ban'
            save_status_symbols = get_status_symbol_display(save_error_tooltip, save_symbol)

        # if conflicting tiles or dashboard and overwrite not requested, prompt overwrite
        elif ((dashboard_title in used_dashboard_titles or any(x in used_titles for x in tile_titles))
              and '{"index":0,"type":"dashboard-overwrite"}.n_clicks' != changed_id):

            # dashboard-overwrite index 0 = confirm overwrite
            # dashboard-overwrite index 1 = cancel overwrite
            # if conflicting graph titles

            if any(x in used_titles for x in tile_titles):
                conflicting_graphs = ''
                conflicting_graphs_list = [i for i in tile_titles if i in used_titles]  # was session['saved_layouts']
                for idx, conflicting_graph in enumerate(conflicting_graphs_list):
                    conflicting_graphs += '\'' + conflicting_graph + '\''
                    if idx != (len(conflicting_graphs_list) - 1):
                        conflicting_graphs += ', '
                # if conflicting graph titles and dashboard title
                if dashboard_title in used_dashboard_titles:  # was session['saved_dashboards']
                    overwrite_tooltip = "{} \'{}\', {} {}".format(
                        get_label('LBL_Overwrite_Dashboard'),
                        dashboard_title,
                        get_label('LBL_And_The_Graphs' if len(conflicting_graphs_list) > 1 else 'LBL_And_The_Graph'),
                        conflicting_graphs)
                # else, just conflicting graph titles
                else:
                    overwrite_tooltip = "{} {}".format(
                        get_label(
                            'LBL_Overwrite_Graphs' if len(conflicting_graphs_list) > 1 else 'LBL_Overwrite_Graph'),
                        conflicting_graphs)

            # else, just conflicting dashboard title
            else:
                overwrite_tooltip = f"{get_label('LBL_Overwrite_Dashboard')} \'{dashboard_title}\'"

            save_status_symbols = html.Div([
                html.I(
                    html.Span(
                        overwrite_tooltip,
                        className='save-symbols-tooltip'),
                    id={'type': 'dashboard-overwrite', 'index': 0},
                    className='fa fa-floppy-o',
                    style={'padding': '7px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                           'margin-right': '10px', 'margin-left': '7px', 'vertical-align': 'top'}),
                html.Span([
                    html.I(
                        [],
                        className='fa fa-floppy-o',
                        style={'position': 'absolute', 'left': '0', 'width': '15px'}),
                    html.I(
                        [],
                        className='fa fa-ban fa-2x',
                        style={'position': 'absolute', 'top': '50%', 'margin-left': '-13px', 'width': '26px',
                               'margin-top': '-15px', 'color': CLR['background1']}),
                    html.Span(
                        get_label("LBL_Cancel_Save_Attempt"),
                        className='save-symbols-tooltip')],
                    id={'type': 'dashboard-overwrite', 'index': 1},
                    className='save-overwrite-symbols',
                    style={'padding': '7px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                           'margin-left': '10px', 'margin-right': '14px', 'display': 'inline-block',
                           'vertical-align': 'top'})],
                id='save-status-symbols-inner',
                style={'width': '71px', 'border': '1px solid {}'.format(CLR['lightgray']), 'margin': '2px 0',
                       'border-radius': '6px'})

        # else, save/overwrite the dashboard and contained tiles
        else:

            df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name4]

            start_years = [start_year_0, start_year_1, start_year_2, start_year_3, start_year_4]

            end_years = [end_year_0, end_year_1, end_year_2, end_year_3, end_year_4]

            hierarchy_toggles = [hierarchy_toggle_0, hierarchy_toggle_1, hierarchy_toggle_2, hierarchy_toggle_3,
                                 hierarchy_toggle_4]

            graph_all_toggles = [graph_all_toggle_0, graph_all_toggle_1, graph_all_toggle_2, graph_all_toggle_3,
                                 graph_all_toggle_4]

            level_values = [level_value_0, level_value_1, level_value_2, level_value_3, level_value_4]

            button_paths = [button_path_0, button_path_1, button_path_2, button_path_3, button_path_4]

            fiscal_toggles = [fiscal_toggle_0, fiscal_toggle_1, fiscal_toggle_2, fiscal_toggle_3, fiscal_toggle_4]

            timeframes = [timeframe_0, timeframe_1, timeframe_2, timeframe_3, timeframe_4]

            start_secondaries = [start_secondary_0, start_secondary_1, start_secondary_2, start_secondary_3,
                                 start_secondary_4]

            end_secondaries = [end_secondary_0, end_secondary_1, end_secondary_2, end_secondary_3, end_secondary_4]

            num_periods = [num_periods_0, num_periods_1, num_periods_2, num_periods_3, num_periods_4]

            period_types = [period_type_0, period_type_1, period_type_2, period_type_3, period_type_4]

            date_tabs = [date_tab_0, date_tab_1, date_tab_2, date_tab_3, date_tab_4]

            dashboard_saves = {'Dashboard Title': dashboard_title}

            # if any tiles are linked, save the master data menu
            if links.count('fa fa-link') > 0:

                master_nid_path = "root"
                for button in button_paths[4]:
                    master_nid_path += '^||^{}'.format(button['props']['children'])

                master_data = {
                    'Fiscal Toggle': fiscal_toggles[4],
                    'Timeframe': timeframes[4],
                    'Num Periods': num_periods[4],
                    'Hierarchy Toggle': hierarchy_toggles[4],
                    'Period Type': period_types[4],
                    'Level Value': level_values[4],
                    'Data Set': df_names[4],
                    'Graph All Toggle': graph_all_toggles[4],
                    'NID Path': master_nid_path,
                }

                # if input method is 'select-range', add the states of the select range inputs
                if timeframes[4] == 'select-range':
                    master_data['Date Tab'] = date_tabs[4]
                    master_data['Start Year'] = start_years[4]
                    master_data['End Year'] = end_years[4]
                    master_data['Start Secondary'] = start_secondaries[4]
                    master_data['End Secondary'] = end_secondaries[4]

                dashboard_saves['Master Data'] = master_data

            for i in range(len(links)):

                intermediate_pointer = REPORT_POINTER_PREFIX + tile_titles[i].replace(" ", "")
                # regex.sub('[^A-Za-z0-9]+', '', tile_titles[i])

                used_titles = []

                for key in session['saved_layouts']:
                    used_titles.append(session['saved_layouts'][key]["Title"])

                while True:
                    if intermediate_pointer in session['saved_layouts'] \
                            and session['saved_layouts'][intermediate_pointer]["Title"] not in used_titles:
                        tile_pointer = intermediate_pointer + "_"
                        intermediate_pointer = tile_pointer
                    else:
                        tile_pointer = intermediate_pointer
                        break

                if i == 0:
                    args_list = args_list_0
                elif i == 1:
                    args_list = args_list_1
                elif i == 2:
                    args_list = args_list_2
                else:
                    args_list = args_list_3

                if type(button_paths[i]) == dict:
                    button_paths[i] = [button_paths[i]]

                nid_path = "root"
                for button in button_paths[i]:
                    nid_path += '^||^{}'.format(button['props']['children'])

                # ---------- save dashboard reference to tile ----------
                dashboard_saves['Tile ' + str(i)] = {
                    'Tile Pointer': tile_pointer,
                    # 'Tile Title': tile_titles[i],
                    'Link': links[i]
                }

                # ---------- save tile ----------

                # if tile is unlinked, save data menu
                if links[i] == 'fa fa-unlink':
                    tile_data = {
                        'Fiscal Toggle': fiscal_toggles[i],
                        'Timeframe': timeframes[i],
                        'Num Periods': num_periods[i],
                        'Hierarchy Toggle': hierarchy_toggles[i],
                        'Period Type': period_types[i],
                        'Level Value': level_values[i],
                        'Data Set': df_names[i],
                        'Graph All Toggle': graph_all_toggles[i],
                        'NID Path': nid_path,
                    }

                    # if input method is 'select-range', add the states of the select range inputs
                    if timeframes[i] == 'select-range':
                        tile_data['Date Tab'] = date_tabs[i]
                        tile_data['Start Year'] = start_years[i]
                        tile_data['End Year'] = end_years[i]
                        tile_data['Start Secondary'] = start_secondaries[i]
                        tile_data['End Secondary'] = end_secondaries[i]

                else:
                    tile_data = dashboard_saves['Master Data']

                # save tile to file
                save_layout_state(tile_pointer, {'Graph Type': graph_types[i], 'Args List': args_list, **tile_data,
                                                 'Title': tile_titles[i]})
                # save_layout_to_file(session['saved_layouts'])
                save_layout_to_db(tile_pointer, tile_titles[i], True)

            # save dashboard to file
            # Change to a dashboard pointer from dashboard_title
            save_dashboard_state(dashboard_pointer, dashboard_saves)
            # save_dashboard_to_file(session['saved_dashboards'])
            save_dashboard_to_db(dashboard_pointer, dashboard_title)

            save_error_tooltip = ''
            update_graph_options_trigger = 'trigger'
            save_symbol = 'fa fa-check'
            tile_title_returns = auto_named_titles
            options = [{'label': session['saved_dashboards'][key]['Dashboard Title'], 'value': key} for key in
                       session['saved_dashboards']]
            save_status_symbols = get_status_symbol_display(save_error_tooltip, save_symbol)

    # elif the overwrite was cancelled, clear displayed symbols
    elif '{"index":1,"type":"dashboard-overwrite"}.n_clicks' == changed_id:
        save_status_symbols = []

    # else, 'confirm-delete-dashboard' requested
    else:

        if remove_dashboard != '':
            delete_dashboard(remove_dashboard)
            update_graph_options_trigger = 'trigger'
            options = [{'label': session['saved_dashboards'][key]["Dashboard Title"], 'value': key} for key in
                       session['saved_dashboards']]
            delete_dropdown_val = ''

        save_status_symbols = []

    return save_status_symbols, options, options, delete_dropdown_val, update_graph_options_trigger, \
        tile_title_returns[0], tile_title_returns[1], tile_title_returns[2], tile_title_returns[3]


# *********************************************SHARED LOADING********************************************************

# load select range inputs, prompting the date picker callback to instantiate the layout of the datepicker for us
@app.callback(
    [Output({'type': 'start-year-input', 'index': MATCH}, 'name'),
     Output({'type': 'start-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'start-secondary-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-secondary-input', 'index': MATCH}, 'value')],
    [Input({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-tab'),
     Input({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-tab')],
    [State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-start_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-end_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-start_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-end_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-start_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-end_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-start_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-end_secondary')],
    prevent_initial_call=True
)
def _load_select_range_inputs(tile_tab, dashboard_tab, tile_start_year, tile_end_year, tile_start_secondary,
                              tile_end_secondary, dashboard_start_year, dashboard_end_year, dashboard_start_secondary,
                              dashboard_end_secondary):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    # if loading type is tile
    if 'data-tile-tab' in changed_id:
        date_tab = tile_tab
        start_year = tile_start_year
        end_year = tile_end_year
        start_secondary = tile_start_secondary
        end_secondary = tile_end_secondary

    # else, loading type is dashboard
    else:
        date_tab = dashboard_tab
        start_year = dashboard_start_year
        end_year = dashboard_end_year
        start_secondary = dashboard_start_secondary
        end_secondary = dashboard_end_secondary

    return date_tab, start_year, end_year, start_secondary, end_secondary


# *********************************************DASHBOARD LOADING*****************************************************

# load dashboard layout
@app.callback(
    # dashboard title
    [Output('dashboard-title', 'value'),
     # tile content
     Output('div-body-wrapper', 'children'),
     # data tile 0
     Output({'type': 'data-menu-dashboard-loading', 'index': 0}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-end_secondary'),
     # data tile 1
     Output({'type': 'data-menu-dashboard-loading', 'index': 1}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-end_secondary'),
     # data tile 2
     Output({'type': 'data-menu-dashboard-loading', 'index': 2}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-end_secondary'),
     # data tile 3
     Output({'type': 'data-menu-dashboard-loading', 'index': 3}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-end_secondary'),
     # data tile 4
     Output({'type': 'data-menu-dashboard-loading', 'index': 4}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-end_secondary'),
     # num tiles update
     Output('num-tiles-4', 'data-num-tiles'),
     Output('df-constants-storage-dashboard-wrapper', 'children')],
    [Input('select-dashboard-dropdown', 'value')],
    [State('df-constants-storage', 'data')],
    prevent_initial_call=True
)
def _load_dashboard_layout(selected_dashboard, df_const):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    tile_keys = [{}] * 4

    dms = [{'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update}]

    num_tiles = 0

    for dict_key, dict_value in session['saved_dashboards'][selected_dashboard].items():

        if 'Tile' in dict_key:

            num_tiles += 1

            tile_index = data_index = int(search(r'\d+', dict_key).group())

            # Change key to Tile Pointer instead of Tile Title
            tile_pointer = dict_value['Tile Pointer']
            link_state = dict_value['Link']

            if tile_pointer in session['saved_layouts']:
                tile_data = session['saved_layouts'][tile_pointer].copy()
                tile_title = tile_data.pop("Title")
            # TODO: In 'prod' we will check for pointers and only do a 'virtual' delete for
            #  the single user
            else:
                tile_title = "This Graph has been deleted"
                tile_data = {
                    "Args List": ["", "", ""],
                    "Data Set": "OPG001",  # "Data Set": "OPG001_2016-17_Week_v3.csv",
                    "Fiscal Toggle": "Gregorian",
                    "Graph All Toggle": [],
                    "Graph Type": "Line",
                    "Hierarchy Toggle": "Level Filter",
                    "Level Value": None,
                    "NID Path": "root",
                    "Num Periods": "5",
                    "Period Type": "last-years",
                    "Timeframe": "all-time",
                    "Title": "This Graph has been deleted"}

            # pop graph_type/args_list to compare the dashboard master data menu to the saved tile data menu
            graph_type = tile_data.pop('Graph Type')
            args_list = tile_data.pop('Args List')
            df_name = tile_data['Data Set']

            # check if data is loaded
            if df_name not in session:
                session[df_name] = dataset_to_df(df_name)
                if df_const is None:
                    df_const = {}
                df_const[df_name] = generate_constants(df_name)

            if link_state == 'fa fa-link':
                # if tile was linked but it's data menu has changed and no longer matches master data, unlink
                if tile_data != session['saved_dashboards'][selected_dashboard]['Master Data']:
                    link_state = 'fa fa-unlink'

                # else, the tile is valid to be linked, generate master menu if it has not been created yet
                else:
                    data_index = 4

            # create tile keys
            graph_menu = load_graph_menu(graph_type=graph_type, tile=tile_index, df_name=df_name, args_list=args_list,
                                         df_const=df_const)
            # TODO: Need to add df name
            customize_content = get_customize_content(tile=tile_index, graph_type=graph_type, graph_menu=graph_menu,
                                                      df_name=df_name)
            tile_key = {'Tile Title': tile_title, 'Link': link_state, 'Customize Content': customize_content}
            tile_keys[tile_index] = tile_key

            # if tile is unlinked, or linked while the master does not exist, create data menu
            if link_state == 'fa fa-unlink' or (link_state == 'fa fa-link' and dms[4]['Content'] == no_update):

                hierarchy_toggle = tile_data['Hierarchy Toggle']
                level_value = tile_data['Level Value']
                nid_path = tile_data['NID Path']
                graph_all_toggle = tile_data['Graph All Toggle']
                fiscal_toggle = tile_data['Fiscal Toggle']
                timeframe = tile_data['Timeframe']
                num_periods = tile_data['Num Periods']
                period_type = tile_data['Period Type']

                dms[data_index]['Content'] = get_data_menu(
                    tile=data_index, df_name=df_name, mode='dashboard-loading', hierarchy_toggle=hierarchy_toggle,
                    level_value=level_value, nid_path=nid_path,
                    graph_all_toggle=graph_all_toggle, fiscal_toggle=fiscal_toggle, input_method=timeframe,
                    num_periods=num_periods, period_type=period_type, df_const=df_const)

                if timeframe == 'select-range':
                    dms[data_index]['Tab'] = tile_data['Date Tab']
                    dms[data_index]['Start Year'] = tile_data['Start Year']
                    dms[data_index]['End Year'] = tile_data['End Year']
                    dms[data_index]['Start Secondary'] = tile_data['Start Secondary']
                    dms[data_index]['End Secondary'] = tile_data['End Secondary']

    children = get_div_body(num_tiles=num_tiles, input_tiles=None, tile_keys=tile_keys)

    df_const = html.Div(
        html.Div(
            html.Div(
                html.Div(
                    dcc.Store(
                        id='df-constants-storage',
                        storage_type='memory',
                        data=df_const),
                    id={'type': 'df-constants-storage-tile-wrapper', 'index': 0}),
                id={'type': 'df-constants-storage-tile-wrapper', 'index': 1}),
            id={'type': 'df-constants-storage-tile-wrapper', 'index': 2}),
        id={'type': 'df-constants-storage-tile-wrapper', 'index': 3}),

    return (session['saved_dashboards'][selected_dashboard]['Dashboard Title'],

            children,

            dms[0]['Content'], dms[0]['Tab'], dms[0]['Start Year'], dms[0]['End Year'], dms[0]['Start Secondary'],
            dms[0]['End Secondary'],

            dms[1]['Content'], dms[1]['Tab'], dms[1]['Start Year'], dms[1]['End Year'], dms[1]['Start Secondary'],
            dms[1]['End Secondary'],

            dms[2]['Content'], dms[2]['Tab'], dms[2]['Start Year'], dms[2]['End Year'], dms[2]['Start Secondary'],
            dms[2]['End Secondary'],

            dms[3]['Content'], dms[3]['Tab'], dms[3]['Start Year'], dms[3]['End Year'], dms[3]['Start Secondary'],
            dms[3]['End Secondary'],

            dms[4]['Content'], dms[4]['Tab'], dms[4]['Start Year'], dms[4]['End Year'], dms[4]['Start Secondary'],
            dms[4]['End Secondary'],

            num_tiles, df_const)


# resets selected dashboard dropdown value to ''
app.clientside_callback(
    """
    function(_trigger){
        return '';
    }
    """,
    Output('select-dashboard-dropdown', 'value'),
    [Input({'type': 'select-range-trigger', 'index': ALL}, 'data-dashboard-tab')],
    prevent_initial_call=True
)
