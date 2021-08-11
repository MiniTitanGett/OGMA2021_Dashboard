from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import session

data = 'filtered_df_leaf_all_time.csv'

filtered_df_1 = pd.read_csv(data,
                            header=0,
                            index_col=False,
                            keep_default_na=True)

filtered_df_t = filtered_df_1[filtered_df_1['Calendar Entry Type'] == 'Week']


def get_last_day_of_month(day):
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def week_number_of_month(date_value):
    return date_value.isocalendar()[1] - date_value.replace(day=1).isocalendar()[1] + 1


def get_quarter_start(day):
    return date(day.year, (day.month - 1) // 3 * 3 + 1, 1)


def get_last_day_of_quarter(day):
    quarter_start = get_quarter_start(day)
    return quarter_start + relativedelta(months=3, days=-1)


def get_last_day_of_year(year):
    return date(int(year), 12, 31)


hierarchy_path_t = ['Los Angeles Department of Water and Power', 'CORPORATE SERVICES', 'SUPPLY CHAIN SERVICES',
                    'CORPORATE PURCHASING', 'CORPORATE PURCHASING', 'CORPORATE PURCHASING']
secondary_type_t = 'None'
end_secondary_t = 1
end_year_t = 1
start_secondary_t = 1
start_year_t = 1
timeframe_t = 'all-time'
fiscal_toggle_t = ''
num_periods_t = 5
period_type_t = 'last-years'
df_name_t = 'OPG011'
df_const_t = {'OPG011': {'HIERARCHY_LEVELS': ['H0', 'H1', 'H2', 'H3', 'H4', 'H5'],
                         'VARIABLE_LEVEL': 'Variable Name', 'COLUMN_NAMES':
                             ['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'Variable Name',
                              'Variable Name Qualifier', 'Variable Name Sub Qualifier', 'Date of Event',
                              'Calendar Entry Type', 'Year of Event', 'Quarter', 'Month of Event', 'Week of Event',
                              'Fiscal Year of Event', 'Fiscal Quarter', 'Fiscal Month of Event', 'Fiscal Week of Event',
                              'Julian Day', 'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'],
                         'MEASURE_TYPE_OPTIONS': ['Count', 'Dollar', 'Duration'], 'GREGORIAN_MIN_YEAR': 2016,
                         'GREGORIAN_YEAR_MAX': 2017, 'GREGORIAN_QUARTER_MAX_YEAR': 2017,
                         'GREGORIAN_QUARTER_FRINGE_MIN': 1, 'GREGORIAN_QUARTER_FRINGE_MAX': 4,
                         'GREGORIAN_MONTH_MAX_YEAR': 2017, 'GREGORIAN_MONTH_FRINGE_MIN': 1,
                         'GREGORIAN_MONTH_FRINGE_MAX': 12, 'GREGORIAN_WEEK_AVAILABLE': True,
                         'GREGORIAN_WEEK_MAX_YEAR': 2017, 'GREGORIAN_WEEK_FRINGE_MIN': 1,
                         'GREGORIAN_WEEK_FRINGE_MAX': 50,
                         'FISCAL_AVAILABLE': False, 'FISCAL_MIN_YEAR': None, 'FISCAL_YEAR_MAX': None,
                         'FISCAL_QUARTER_MAX_YEAR': None, 'FISCAL_QUARTER_FRINGE_MIN': None,
                         'FISCAL_QUARTER_FRINGE_MAX': None, 'FISCAL_MONTH_MAX_YEAR': None,
                         'FISCAL_MONTH_FRINGE_MIN': None, 'FISCAL_MONTH_FRINGE_MAX': None, 'FISCAL_WEEK_MAX_YEAR': None,
                         'FISCAL_WEEK_FRINGE_MIN': None, 'FISCAL_WEEK_FRINGE_MAX': None, 'MIN_DATE_UNF': '01/02/2016',
                         'MAX_DATE_UNF': '12/31/2017',
                         'VARIABLE_OPTIONS': [{'label': 'Bid ', 'value': 'Bid '},
                                              {'label': 'Bid Invitation for Bid Against an Agreement',
                                               'value': 'Bid Invitation for Bid Against an Agreement'},
                                              {'label': 'Bid Invitation for Bid Board Awarded',
                                               'value': 'Bid Invitation for Bid Board Awarded'},
                                              {'label': 'Bid Invitation for Bid GM Awarded Price & Time',
                                               'value': 'Bid Invitation for Bid GM Awarded Price & Time'},
                                              {'label': 'Bid Invitation for Bid Spot <$25,000',
                                               'value': 'Bid Invitation for Bid Spot <$25,000'},
                                              {'label': 'Bid Invitation for Bid Spot > $25,000 < $150,000',
                                               'value': 'Bid Invitation for Bid Spot > $25,000 < $150,000'},
                                              {'label': 'Bid Request for Proposal / Qualifications',
                                               'value': 'Bid Request for Proposal / Qualifications'},
                                              {'label': 'Purchase Order ', 'value': 'Purchase Order '},
                                              {'label': 'Purchase Order Blanket Authority - Government',
                                               'value': 'Purchase Order Blanket Authority - Government'},
                                              {'label': 'Purchase Order Blanket Authority - Service/Commodity',
                                               'value': 'Purchase Order Blanket Authority - Service/Commodity'},
                                              {'label': 'Purchase Order Blanket Authority - Utility',
                                               'value': 'Purchase Order Blanket Authority - Utility'},
                                              {'label': 'Purchase Order Legal Agreements',
                                               'value': 'Purchase Order Legal Agreements'},
                                              {'label': 'Purchase Order Memberships & Subscriptions',
                                               'value': 'Purchase Order Memberships & Subscriptions'},
                                              {'label': 'Purchase Order Personal Purchase Order',
                                               'value': 'Purchase Order Personal Purchase Order'},
                                              {'label': 'Purchase Order Price & Time Board Awarded',
                                               'value': 'Purchase Order Price & Time Board Awarded'},
                                              {'label': 'Purchase Order Price & Time GM Awarded',
                                               'value': 'Purchase Order Price & Time GM Awarded'},
                                              {'label': 'Purchase Order Professional / Personal Services',
                                               'value': 'Purchase Order Professional / Personal Services'},
                                              {'label': 'Purchase Order Rentals & Services',
                                               'value': 'Purchase Order Rentals & Services'},
                                              {'label': 'Purchase Order Spot PO Board Awarded',
                                               'value': 'Purchase Order Spot PO Board Awarded'},
                                              {'label': 'Purchase Order Spot PO Informal <$25,000',
                                               'value': 'Purchase Order Spot PO Informal <$25,000'},
                                              {'label': 'Purchase Order Spot PO Informal >$25,000<$150,000',
                                               'value': 'Purchase Order Spot PO Informal >$25,000<$150,000'},
                                              {'label': 'Requisition ', 'value': 'Requisition '},
                                              {'label': 'Requisition Advertising / Special Events',
                                               'value': 'Requisition Advertising / Special Events'},
                                              {'label': 'Requisition IT Related', 'value': 'Requisition IT Related'},
                                              {'label': 'Requisition Non-Stock / Non Contract',
                                               'value': 'Requisition Non-Stock / Non Contract'},
                                              {'label': 'Requisition Promotional Items',
                                               'value': 'Requisition Promotional Items'},
                                              {'label': 'Requisition Requisition for Blanket Authority - Government',
                                               'value': 'Requisition Requisition for Blanket Authority - Government'},
                                              {'label': 'Requisition Requisition for Blanket Authority - Utility',
                                               'value': 'Requisition Requisition for Blanket Authority - Utility'},
                                              {'label': 'Requisition Requisition for Board Awarded Non-Stock',
                                               'value': 'Requisition Requisition for Board Awarded Non-Stock'},
                                              {'label': 'Requisition Requisition for Board Awarded Spot Non-Stock',
                                               'value': 'Requisition Requisition for Board Awarded Spot Non-Stock'},
                                              {'label': 'Requisition Requisition for Board Awarded Stock Material',
                                               'value': 'Requisition Requisition for Board Awarded Stock Material'},
                                              {'label': 'Requisition Requisition for Personal Purchase Order',
                                               'value': 'Requisition Requisition for Personal Purchase Order'},
                                              {'label': 'Requisition Requisition for Price & Time Non-Stock',
                                               'value': 'Requisition Requisition for Price & Time Non-Stock'},
                                              {'label': 'Requisition Requisition for Price & Time Stock Material',
                                               'value': 'Requisition Requisition for Price & Time Stock Material'},
                                              {
                                                  'label': 'Requisition Requisition for Professional / Personal Services (RFP/RFQ)',
                                                  'value': 'Requisition Requisition for Professional / Personal Services (RFP/RFQ)'},
                                              {'label': 'Requisition Requisition for SPO',
                                               'value': 'Requisition Requisition for SPO'},
                                              {'label': 'Requisition Safety Awards & Lunches',
                                               'value': 'Requisition Safety Awards & Lunches'},
                                              {'label': 'Requisition Services', 'value': 'Requisition Services'},
                                              {'label': 'Requisition Stock / Non-Contract',
                                               'value': 'Requisition Stock / Non-Contract'},
                                              {'label': 'Requisition Training - Offsite',
                                               'value': 'Requisition Training - Offsite'},
                                              {'label': 'SPO ', 'value': 'SPO '},
                                              {'label': 'SPO SPO against Blanket Authority - Government',
                                               'value': 'SPO SPO against Blanket Authority - Government'},
                                              {'label': 'SPO SPO against Blanket Authority - Service/Commodity',
                                               'value': 'SPO SPO against Blanket Authority - Service/Commodity'},
                                              {'label': 'SPO SPO against Legal Agreement',
                                               'value': 'SPO SPO against Legal Agreement'},
                                              {'label': 'SPO SPO against Price & Time Board Awarded',
                                               'value': 'SPO SPO against Price & Time Board Awarded'},
                                              {'label': 'SPO SPO against Price & Time GM Awarded',
                                               'value': 'SPO SPO against Price & Time GM Awarded'}]}}


# TODO: remove filtered_Df parameter
def data_filter(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                timeframe, fiscal_toggle, num_periods, period_type, df_name, df_const, filtered_df):
    """
    if hierarchy_toggle == 'Level Filter' or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
        filtered_df = session[df_name].copy()

        if hierarchy_toggle == 'Level Filter':
            # If anything is in the drop down
            if hierarchy_level_dropdown:
                # Filter based on hierarchy level
                filtered_df.dropna(subset=[hierarchy_level_dropdown], inplace=True)
                for i in range(len(df_const[df_name]['HIERARCHY_LEVELS']) - int(hierarchy_level_dropdown[1])):
                    bool_series = pd.isnull(filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][
                        len(df_const[df_name]['HIERARCHY_LEVELS']) - 1 - i]])
                    filtered_df = filtered_df[bool_series]
            else:
                # Returns empty data frame with column names
                filtered_df = filtered_df[0:0]
        else:
            # Filters out all rows that are less specific than given path length
            for i in range(len(hierarchy_path)):
                filtered_df = filtered_df[filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]
            # Filters out all rows that are more specific than given path length plus one to preserve the child column
            for i in range(len(df_const[df_name]['HIERARCHY_LEVELS']) - (len(hierarchy_path) + 1)):
                bool_series = pd.isnull(filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][
                    len(df_const[df_name]['HIERARCHY_LEVELS']) - 1 - i]])
                filtered_df = filtered_df[bool_series]
            filtered_df.dropna(subset=[df_const[df_name]['HIERARCHY_LEVELS'][len(hierarchy_path)]], inplace=True)
    else:
        filtered_df = session[df_name]
        # Filters out all rows that don't include path member at specific level
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df[filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]
        # Filters out all rows that are more specific than given path
        for i in range(len(df_const[df_name]['HIERARCHY_LEVELS']) - len(hierarchy_path)):
            bool_series = pd.isnull(filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][
                len(df_const[df_name]['HIERARCHY_LEVELS']) - 1 - i]])
            filtered_df = filtered_df[bool_series]

    # filtered_df.to_csv('filtered_df_1_test.csv')
    # print("Data Frame to csv completed")
    """

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[df_name]['FISCAL_MIN_YEAR']
            end_year = df_const[df_name]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[df_name]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[df_name]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[df_name]['GREGORIAN_MIN_YEAR']
            end_year = df_const[df_name]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[df_name]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[df_name]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

    # account for special timeframe case 'to-current'
    if timeframe == 'to-current':
        num_periods = int(num_periods)
        end_date = datetime.today()
        if period_type == 'last-years':
            if num_periods > int(end_date.year) - start_year:
                num_periods = int(end_date.year) - start_year
            start_date = end_date - relativedelta(years=num_periods)
            current_filter = '{}Year'.replace("{}", year_prefix)
        elif period_type == 'last-quarters':
            if num_periods > (int(end_date.year) - start_year) * 4:
                num_periods = (int(end_date.year) - start_year) * 4
            start_date = end_date - relativedelta(months=3 * num_periods)
            current_filter = 'Quarter'
        elif period_type == 'last-months':
            if num_periods > (int(end_date.year) - start_year) * 12:
                num_periods = (int(end_date.year) - start_year) * 12
            start_date = end_date - relativedelta(months=num_periods)
            current_filter = 'Month'
        else:  # period_type == 'last-weeks'
            if num_periods > (int(end_date.year) - start_year) * 53:
                num_periods = (int(end_date.year) - start_year) * 53
            start_date = end_date - timedelta(weeks=num_periods)
            current_filter = 'Week'

        if df_name == "OPG011" and current_filter != 'Week':
            if current_filter == 'Year':
                division_column = '{}Year of Event'.format(year_prefix)
            elif current_filter == 'Quarter':
                division_column = '{}Quarter'.format(year_prefix)
            else:
                division_column = '{}Month of Event'.format(year_prefix)

            measure_types = filtered_df['Measure Type'].unique().tolist()
            variable_names = filtered_df['Variable Name'].unique().tolist()
            row_list = []

            for x in range(len(measure_types)):
                measure_type = measure_types[x]
                reduced_df = filtered_df[filtered_df['Measure Type'] == measure_type]
                for y in range(len(variable_names)):
                    variable_name = variable_names[y]
                    further_reduced_df = reduced_df[reduced_df['Variable Name'] == variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        yearly_data = further_reduced_df[further_reduced_df['Year of Event'] == year]
                        unique_secondary = yearly_data[division_column].dropna().unique().tolist()
                        for w in range(len(unique_secondary)):
                            secondary = unique_secondary[w]
                            unique_data = yearly_data[yearly_data[division_column] == secondary]
                            measure_value = unique_data['Measure Value'].sum()
                            if current_filter == "Year":
                                date_of_event = get_last_day_of_year(year)
                                year_of_event = year
                                quarter = ""
                                month_of_event = ""
                                week_of_event = ""
                            elif current_filter == "Quarter":
                                date_of_event = get_last_day_of_quarter(
                                    date(year, int(unique_data['{}Month of Event'.format(year_prefix)].iloc[0]), 1))
                                year_of_event = year
                                quarter = secondary
                                month_of_event = ""
                                week_of_event = ""
                            # secondary_type == "Month"
                            else:
                                date_of_event = get_last_day_of_month(date(year, int(secondary), 1))
                                year_of_event = year
                                quarter = unique_data['Quarter'].iloc[0]
                                month_of_event = secondary
                                week_of_event = ""
                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 hierarchy_path[0] if len(hierarchy_path) >= 1 else '',
                                 hierarchy_path[1] if len(hierarchy_path) >= 2 else '',
                                 hierarchy_path[2] if len(hierarchy_path) >= 3 else '',
                                 hierarchy_path[3] if len(hierarchy_path) >= 4 else '',
                                 hierarchy_path[4] if len(hierarchy_path) >= 5 else '',
                                 hierarchy_path[5] if len(hierarchy_path) >= 6 else '',
                                 variable_name, unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0],
                                 date_of_event, current_filter, year_of_event, quarter, month_of_event, week_of_event,
                                 '', '', '', '', '', '', measure_value, measure_type, ''])

            time_df = pd.DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        elif df_name == "OPG011" and current_filter == 'Week':
            time_df = filtered_df.copy()
        else:
            # Filters out unused calender values
            time_df = filtered_df.copy()
            time_df = time_df[time_df['Calendar Entry Type'] == current_filter]

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date.date()]
        time_df = time_df[time_df['Date of Event'] <= end_date.date()]

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        if df_name == "OPG011":
            if secondary_type == 'Quarter':
                division_column = '{}Quarter'.format(year_prefix)
            else:
                division_column = '{}Month of Event'.format(year_prefix)

            measure_types = filtered_df['Measure Type'].unique().tolist()
            variable_names = filtered_df['Variable Name'].unique().tolist()
            row_list = []

            for x in range(len(measure_types)):
                measure_type = measure_types[x]
                reduced_df = filtered_df[filtered_df['Measure Type'] == measure_type]
                for y in range(len(variable_names)):
                    variable_name = variable_names[y]
                    further_reduced_df = reduced_df[reduced_df['Variable Name'] == variable_name]
                    for z in range(end_year - start_year + 1):
                        year = start_year + z
                        yearly_data = further_reduced_df[further_reduced_df['Year of Event'] == year]
                        unique_secondary = yearly_data[division_column].dropna().unique().tolist()
                        for w in range(len(unique_secondary)):
                            secondary = unique_secondary[w]
                            unique_data = yearly_data[yearly_data[division_column] == secondary]
                            measure_value = unique_data['Measure Value'].sum()
                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 hierarchy_path[0] if len(hierarchy_path) >= 1 else '',
                                 hierarchy_path[1] if len(hierarchy_path) >= 2 else '',
                                 hierarchy_path[2] if len(hierarchy_path) >= 3 else '',
                                 hierarchy_path[3] if len(hierarchy_path) >= 4 else '',
                                 hierarchy_path[4] if len(hierarchy_path) >= 5 else '',
                                 hierarchy_path[5] if len(hierarchy_path) >= 6 else '',
                                 variable_name, unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0],
                                 get_last_day_of_month(date(year, int(secondary), 1)) if secondary_type == "Month" else
                                 get_last_day_of_quarter(
                                     date(year, int(unique_data['{}Month of Event'.format(year_prefix)].iloc[0]), 1)),
                                 secondary_type, year,
                                 secondary if secondary_type == "Quarter" else unique_data['Quarter'].iloc[0],
                                 secondary if secondary_type == "Month" else "",
                                 '', '', '', '', '', '', '', measure_value,
                                 measure_type, ''])

            time_df = pd.DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        else:
            # Data frame filtered to be in inputted year range
            time_df = filtered_df[filtered_df['{}Year of Event'.format(year_prefix)] >= int(start_year)]
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] <= end_year]

            # Filters out unused calender values
            time_df = time_df[time_df['Calendar Entry Type'] == secondary_type]

            if secondary_type == 'Quarter':
                division_column = '{}Quarter'.format(year_prefix)
            else:
                division_column = '{}Month of Event'.format(year_prefix)

            if start_year == end_year:  # Don't have to deal with in between years
                # Filter out all rows outside specified range
                time_df = time_df[time_df[division_column] >= start_secondary]
                time_df = time_df[time_df[division_column] < end_secondary]

            else:  # Handles in-between years
                # Filter starting year above threshold
                range_df = time_df[time_df['{}Year of Event'.format(year_prefix)] == start_year]
                range_df = range_df[range_df[division_column] >= start_secondary]

                for i in range(end_year - start_year - 1):
                    # Include entirety of in-between years
                    range_df = range_df.append(
                        time_df[time_df['{}Year of Event'.format(year_prefix)] == (start_year + i + 1)])

                # Filter end year below threshold
                time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] == end_year]
                time_df = time_df[time_df[division_column] < end_secondary]
                range_df = range_df.append(time_df)

                # Update working df
                time_df = range_df.copy()
    else:
        if df_name == "OPG011":
            measure_types = filtered_df['Measure Type'].unique().tolist()
            variable_names = filtered_df['Variable Name'].unique().tolist()
            row_list = []

            for x in range(len(measure_types)):
                measure_type = measure_types[x]
                reduced_df = filtered_df[filtered_df['Measure Type'] == measure_type]
                for y in range(len(variable_names)):
                    variable_name = variable_names[y]
                    further_reduced_df = reduced_df[reduced_df['Variable Name'] == variable_name]
                    unique_secondary = further_reduced_df['Year of Event'].dropna().unique().tolist()
                    for z in range(len(unique_secondary)):
                        secondary = unique_secondary[z]
                        unique_data = further_reduced_df[further_reduced_df['Year of Event'] == secondary]
                        measure_value = unique_data['Measure Value'].sum()
                        date_of_event = get_last_day_of_year(secondary)
                        row_list.append(
                            [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                             hierarchy_path[0] if len(hierarchy_path) >= 1 else '',
                             hierarchy_path[1] if len(hierarchy_path) >= 2 else '',
                             hierarchy_path[2] if len(hierarchy_path) >= 3 else '',
                             hierarchy_path[3] if len(hierarchy_path) >= 4 else '',
                             hierarchy_path[4] if len(hierarchy_path) >= 5 else '',
                             hierarchy_path[5] if len(hierarchy_path) >= 6 else '',
                             variable_name, unique_data['Variable Name Qualifier'].iloc[0],
                             unique_data['Variable Name Sub Qualifier'].iloc[0],
                             date_of_event, "Year", secondary, "", "", "",
                             '', '', '', '', '', '', measure_value, measure_type, ''])

            time_df = pd.DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        else:
            # Data frame filtered to be in inputted year range
            time_df = filtered_df.copy()
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] >= start_year]
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] <= end_year - 1]

            # Filters out month and quarter values (whole year)
            time_df = time_df[time_df['Calendar Entry Type'] == '{}Year'.replace("{}", year_prefix)]

    return time_df


def data_aggregator_no_customization_filter(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary,
                                            start_year, timeframe, fiscal_toggle, num_periods, period_type, df_name,
                                            df_const, df, measure_type, variable_names):
    filtered_df = df[df['Measure Type'] == measure_type]

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[df_name]['FISCAL_MIN_YEAR']
            end_year = df_const[df_name]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[df_name]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[df_name]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[df_name]['GREGORIAN_MIN_YEAR']
            end_year = df_const[df_name]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[df_name]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[df_name]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

    # ensure variable_names is a list of variable values
    if type(variable_names) is not list:
        variable_names = [variable_names]

    row_list = []

    if secondary_type == 'Quarter':
        division_column = '{}Quarter'.format(year_prefix)
    else:
        division_column = '{}Month of Event'.format(year_prefix)

    for y in range(len(variable_names)):
        variable_name = variable_names[y]
        reduced_df = filtered_df[filtered_df['Variable Name'] == variable_name]
        for z in range(end_year - start_year + 1):
            year = start_year + z
            yearly_data = reduced_df[reduced_df['Year of Event'] == year]
            unique_secondary = yearly_data[division_column].dropna().unique().tolist()
            for w in range(len(unique_secondary)):
                secondary = unique_secondary[w]
                unique_data = yearly_data[yearly_data[division_column] == secondary]
                measure_value = unique_data['Measure Value'].sum()
                row_list.append(
                    [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                     hierarchy_path[0] if len(hierarchy_path) >= 1 else '',
                     hierarchy_path[1] if len(hierarchy_path) >= 2 else '',
                     hierarchy_path[2] if len(hierarchy_path) >= 3 else '',
                     hierarchy_path[3] if len(hierarchy_path) >= 4 else '',
                     hierarchy_path[4] if len(hierarchy_path) >= 5 else '',
                     hierarchy_path[5] if len(hierarchy_path) >= 6 else '',
                     variable_name, unique_data['Variable Name Qualifier'].iloc[0],
                     unique_data['Variable Name Sub Qualifier'].iloc[0],
                     get_last_day_of_month(date(year, int(secondary), 1)) if secondary_type == "Month" else get_last_day_of_quarter(
                                     date(year, int(unique_data['{}Month of Event'.format(year_prefix)].iloc[0]), 1)),
                     secondary_type, year,
                     secondary if secondary_type == "Quarter" else unique_data['Quarter'].iloc[0],
                     secondary if secondary_type == "Month" else "",
                     '', '', '', '', '', '', '', measure_value,
                     measure_type, ''])

    time_df = pd.DataFrame(row_list,
                           columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                    'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                    'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                    'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                    'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                    'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

    return time_df
