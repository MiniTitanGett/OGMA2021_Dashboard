######################################################################################################################
"""
datepicker.py

stores the layout and helper functions for datepicker
"""
######################################################################################################################

# External Packages
import dash_core_components as dcc
import dash_html_components as html

# Internal Modules
from apps.OPG001.data import CLR, get_label, LANGUAGE, LOADED_DFS


# Contents:
#   DATE-PICKER LAYOUT
#       - get_date_picker()
#   DATE-PICKER FUNCTIONS
#       - get_date_box()
#       - get_secondary_data()
#       - get_date_functions()

# ********************************************DATE-PICKER LAYOUT**************************************************


# datepicker layout
def get_date_picker(tile, df_name, fiscal_toggle, input_method, num_periods, period_type):
    children = [
        html.H6(
            '{}:'.format(get_label("Calendar Type")),
            style={'margin-top': '20px', 'color': CLR['text1']} if LOADED_DFS[df_name].FISCAL_AVAILABLE
            else {'display': 'None'}),
        dcc.Tabs([
            dcc.Tab(label="{}".format(get_label("Gregorian")), value='Gregorian'),
            dcc.Tab(label="{}".format(get_label("Fiscal")), value='Fiscal')],
            id={'type': 'fiscal-year-toggle', 'index': tile},
            className='toggle-tabs-wrapper',
            value=fiscal_toggle,
            style={'display': 'block', 'text-align': 'center'} if LOADED_DFS[df_name].FISCAL_AVAILABLE
            else {'display': 'none'}),
        html.H6(
            '{}:'.format(get_label("Timeframe")),
            style={'margin-top': '20px', 'color': CLR['text1']}),
        dcc.RadioItems(
            id={'type': 'radio-timeframe', 'index': tile},
            options=[
                {'label': get_label('All-Time (Monthly)'),
                 'value': 'all-time'},
                {'label': '{}'.format(get_label('Last') if LANGUAGE == 'en' else '........... ' + get_label('Last')),
                 'value': 'to-current'},
                {'label': get_label('Select Range'),
                 'value': 'select-range'}],
            value=input_method,
            className='seperated-radio-buttons',
            style={'margin-left': '15px', 'color': CLR['text1']}),
        html.Div([
            dcc.Input(
                id={'type': 'num-periods', 'index': tile},
                className='num-periods',
                value=num_periods,
                disabled=input_method != 'to-current',
                type='number',
                required=True,
                min=1,
                style={'width': '45px', 'height': '27px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                       'text-align': 'center', 'padding-top': '7px', 'border-radius': '0', 'color': '#333'})
        ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                  'left': '73px' if LANGUAGE == 'en' else '36px'}),
        html.Div([
            dcc.Dropdown(
                id={'type': 'period-type', 'index': tile},
                value=period_type,
                disabled=input_method != 'to-current',
                clearable=False,
                options=[
                    {'label': get_label('Year(s)'),
                     'value': 'last-years'},
                    {'label': get_label('Quarter(s)'),
                     'value': 'last-quarters'},
                    {'label': get_label('Month(s)'),
                     'value': 'last-months'},
                    {'label': get_label('Week(s)'),
                     'value': 'last-weeks'}],
                style={'width': '100px', 'height': '27px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                       'display': 'inline-block', 'text-align': 'center', 'border-radius': '0', 'color': '#333'})
        ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                  'left': '125px' if LANGUAGE == 'en' else '150px'}),
        html.P(
            "{}: {} - {}".format(get_label('Available'), LOADED_DFS[df_name].MIN_DATE_UNF.strftime('%m/%d/%Y'),
                                 LOADED_DFS[df_name].MAX_DATE_UNF.strftime('%m/%d/%Y')),
            style={'margin-top': '10px', 'text-align': 'center', 'font-size': '85%', 'color': CLR['text1']}),
        html.Div([
            # placeholders for datepicker inputs to avoid callback errors. Inputs are initialized to 1 so that they are
            # only 'None' if an invalid date has been entered.
            html.Div([
                html.Button(id={'type': 'date-picker-year-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-quarter-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-month-button', 'index': tile}),
                html.Button(id={'type': 'date-picker-week-button', 'index': tile}),
                dcc.Input(
                    id={'type': 'start-year-input', 'index': tile},
                    value=1),
                dcc.Input(
                    id={'type': 'end-year-input', 'index': tile},
                    value=1),
                dcc.Input(
                    id={'type': 'start-secondary-input', 'index': tile},
                    value=1),
                dcc.Input(
                    id={'type': 'end-secondary-input', 'index': tile},
                    value=1),
            ], style={'width': '0', 'height': '0', 'overflow': 'hidden'})
        ], id={'type': 'div-date-range-selection', 'index': tile},
            style={'padding-bottom': '20px'}),
        # date picker trigger boolean for use in chaining update_date_picker to update_graph
        html.Div(
            id={'type': 'date-picker-trigger', 'index': tile},
            **{'data-boolean': True},
            style={'display': 'none'})]

    return children


# ********************************************DATE-PICKER FUNCTIONS**************************************************

# get datepicker input box
def get_date_box(id, value, min, max, name=None):
    return dcc.Input(id=id,
                     type='number',
                     value=value,
                     min=min,
                     max=max,
                     name=name,
                     required=True,
                     style={'width': '100%'})


# define variables necessary for having secondary input boxes
def get_secondary_data(conditions, fiscal_toggle, df_name):
    # all tabs are enabled initially but the button for the tab the user is inside is disabled later
    quarter_disabled = month_disabled = week_disabled = False
    # all tabs are initially unselected
    quarter_class_name = month_class_name = week_class_name = 'date-picker-nav'
    # if inside quarter tab
    if conditions[0]:
        new_tab = 'Quarter'
        quarter_class_name = 'date-picker-nav-selected'
        quarter_disabled = True
        default_max = 4
        if fiscal_toggle == 'Gregorian':
            fringe_min = LOADED_DFS[df_name].GREGORIAN_QUARTER_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].GREGORIAN_QUARTER_FRINGE_MAX
            max_year = LOADED_DFS[df_name].GREGORIAN_QUARTER_MAX_YEAR
        else:
            fringe_min = LOADED_DFS[df_name].FISCAL_QUARTER_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].FISCAL_QUARTER_FRINGE_MAX
            max_year = LOADED_DFS[df_name].FISCAL_QUARTER_MAX_YEAR
        if fringe_max == 4:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1
    # if inside month tab
    elif conditions[1]:
        new_tab = 'Month'
        month_class_name = 'date-picker-nav-selected'
        month_disabled = True
        default_max = 12
        if fiscal_toggle == 'Gregorian':
            fringe_min = LOADED_DFS[df_name].GREGORIAN_MONTH_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].GREGORIAN_MONTH_FRINGE_MAX
            max_year = LOADED_DFS[df_name].GREGORIAN_MONTH_MAX_YEAR
        else:
            fringe_min = LOADED_DFS[df_name].FISCAL_MONTH_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].FISCAL_MONTH_FRINGE_MAX
            max_year = LOADED_DFS[df_name].FISCAL_MONTH_MAX_YEAR
        if fringe_max == 12:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1
    # if inside week tab
    else:
        new_tab = 'Week'
        week_class_name = 'date-picker-nav-selected'
        week_disabled = True
        default_max = 52
        if fiscal_toggle == 'Gregorian':
            fringe_min = LOADED_DFS[df_name].GREGORIAN_WEEK_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].GREGORIAN_WEEK_FRINGE_MAX
            max_year = LOADED_DFS[df_name].GREGORIAN_WEEK_MAX_YEAR
        else:
            fringe_min = LOADED_DFS[df_name].FISCAL_WEEK_FRINGE_MIN
            fringe_max = LOADED_DFS[df_name].FISCAL_WEEK_FRINGE_MAX
            max_year = LOADED_DFS[df_name].FISCAL_WEEK_MAX_YEAR
        if fringe_max == 52:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1
    return quarter_class_name, quarter_disabled, month_class_name, month_disabled, week_class_name, week_disabled, \
           fringe_min, fringe_max, default_max, max_year, new_tab


# create left and right columns for tabs with secondary time options (beneath years)
def update_date_columns(changed_id, selected_min_year, min_year, fringe_min, selected_max_year, max_year, fringe_max,
                        default_max, tab, selected_secondary_min, selected_secondary_max, tile):
    # if max/min year changed, reset corresponding max/min (period) selection to max/min
    if 'start-year-input' in changed_id:
        if selected_min_year == min_year:
            selected_secondary_min = fringe_min
        else:
            selected_secondary_min = 1
    elif 'end-year-input' in changed_id:
        if selected_max_year == max_year:
            selected_secondary_max = fringe_max
        else:
            selected_secondary_max = default_max
    # Fiscal <---> Gregorian changed, reset to maximum boundaries
    elif 'fiscal-year-toggle' in changed_id:
        selected_min_year = min_year
        selected_max_year = max_year
        selected_secondary_min = fringe_min
        selected_secondary_max = fringe_max
    # if min and max years are the same
    if selected_min_year == selected_max_year:
        modifier_min = 0
        modifier_max = 1
        if (selected_min_year == min_year) & (selected_min_year == max_year):
            min_min = fringe_min
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = fringe_max
        elif selected_min_year == min_year:
            min_min = fringe_min
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = default_max
        elif selected_min_year == max_year:
            min_min = 1
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = fringe_max
        else:
            min_min = 1
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = default_max
    # else, min and max years are different
    else:
        modifier_min = 1
        modifier_max = 0
        if selected_min_year == min_year:
            min_min = fringe_min
            min_max = default_max
        else:
            min_min = 1
            min_max = default_max
        if selected_max_year == max_year:
            max_min = 1
            max_max = fringe_max
        else:
            max_min = 1
            max_max = default_max
    # if min (period) is (default_max), don't allow max year to be same year
    if selected_secondary_min == default_max:
        year_modifier_max = 1
    else:
        year_modifier_max = 0
    # if max (period) is 1, don't allow min year to be same year
    if selected_secondary_max == 1:
        year_modifier_min = 0
    else:
        year_modifier_min = 1
    # min year changed - change min year and reset min (period)
    if 'start-year-input' in changed_id:
        min_value = min_min
        min_max += modifier_min
        max_value = selected_secondary_max
        max_min += modifier_max
        max_max += 1
    # max year changed - change max year and reset max (period)
    elif 'end-year-input' in changed_id:
        min_value = selected_secondary_min
        min_max += modifier_min
        max_value = max_max
        max_min += modifier_max
        max_max += 1
    # (period) changed, apply change
    else:
        min_value = selected_secondary_min
        min_max += modifier_min
        max_value = selected_secondary_max
        max_min += modifier_max
        max_max += 1
    year_input_min = get_date_box(id={'type': 'start-year-input', 'index': tile},
                                  value=selected_min_year,
                                  min=min_year,
                                  max=selected_max_year + year_modifier_min - 1,
                                  name=tab)
    year_input_max = get_date_box(id={'type': 'end-year-input', 'index': tile},
                                  value=selected_max_year,
                                  min=selected_min_year + year_modifier_max,
                                  max=max_year)
    secondary_input_min = get_date_box(id={'type': 'start-secondary-input', 'index': tile},
                                       value=min_value,
                                       min=min_min,
                                       max=min_max - 1)
    secondary_input_max = get_date_box(id={'type': 'end-secondary-input', 'index': tile},
                                       value=max_value,
                                       min=max_min,
                                       max=max_max - 1)
    return [year_input_min, secondary_input_min], [year_input_max, secondary_input_max]
