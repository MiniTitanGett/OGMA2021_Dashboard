from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import session


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
    return date(year, 12, 31)


def data_filter(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                timeframe, fiscal_toggle, num_periods, period_type, hierarchy_toggle, hierarchy_level_dropdown,
                hierarchy_graph_children, df_name, df_const):
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
                    for z in range(end_year - start_year + 1):
                        year = start_year + z
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
                                # TODO: secondary should be month not the quarter
                                date_of_event = get_last_day_of_quarter(date(year, int(secondary), 1))
                                year_of_event = year
                                quarter = secondary_type
                                month_of_event = ""
                                week_of_event = ""
                            # secondary_type == "Month"
                            else:
                                date_of_event = get_last_day_of_month(date(year, int(secondary), 1))
                                year_of_event = year
                                quarter = unique_data['Quarter'].iloc[0]
                                month_of_event = secondary_type
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
        time_df = time_df[time_df['Date of Event'] >= start_date]
        time_df = time_df[time_df['Date of Event'] <= end_date]

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
                                 # TODO: secondary should be month not the quarter
                                 get_last_day_of_month(date(year, int(secondary), 1)) if secondary_type == "Month" else
                                 get_last_day_of_quarter(date(year, int(secondary), 1)),
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
            # TODO: can reduce the aggregation loop due to only needing to account for yearly data
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
                        unique_secondary = yearly_data['Year of Event'].dropna().unique().tolist()
                        for w in range(len(unique_secondary)):
                            secondary = unique_secondary[w]
                            unique_data = yearly_data[yearly_data['Year of Event'] == secondary]
                            measure_value = unique_data['Measure Value'].sum()
                            date_of_event = get_last_day_of_year(year)
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
                                 date_of_event, "Year", year, "", "", "",
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
