######################################################################################################################
"""
data.py

contains arbitrary constants, data constants, and data manipulation functions
"""
######################################################################################################################

from datetime import datetime, timedelta

import numpy as np
# External Packages
import pandas as pd
# import pyodbc
import logging
from dateutil.relativedelta import relativedelta
from flask import session
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from sklearn.preprocessing import PolynomialFeatures

# import config
from conn import get_ref, exec_storedproc_results


# ***********************************************ARBITRARY CONSTANTS*************************************************

GRAPH_OPTIONS = {
    'OPG001': ['Line', 'Bar', 'Scatter', 'Bubble', 'Box_Plot', 'Table'],
    'OPG010': ['Sankey', 'Table']
}

X_AXIS_OPTIONS = ['Time']

BAR_X_AXIS_OPTIONS = ['Specific Item', 'Variable Names']

CLR = {'text1': 'black',
       'text2': '#EED5DD',
       'black': 'black',
       'white': 'white',
       'background1': '#99002e',
       'background2': '#9B6072',
       'highlight': '#ff407a',
       'lightgray': '#c7c7c7',
       'lightpink': '#fffafa',
       'lightergray': '#dedede',
       'sidebar-final': '#fffafa',
       'sidebar-initial': '#9B6072'}

# ******************************************STYLE RETURNS FOR CALLBACKS***********************************************

VIEW_CONTENT_SHOW = {'min-height': '0', 'overflow': 'hidden'}
VIEW_CONTENT_HIDE = {'display': 'none'}

CUSTOMIZE_CONTENT_SHOW = {'flex-grow': '1'}
CUSTOMIZE_CONTENT_HIDE = {'display': 'none'}

LAYOUT_CONTENT_SHOW = {'flex-grow': '1'}
LAYOUT_CONTENT_HIDE = {'display': 'none'}

DATA_CONTENT_SHOW = {'max-width': '300px', 'min-width': '300px', 'background-color': CLR['sidebar-final'],
                     'border-right': '1px solid {}'.format(CLR['lightgray']),
                     'flex-grow': '1', 'display': 'inline', 'overflow-y': 'auto'}
DATA_CONTENT_HIDE = {'display': 'none'}


# ********************************************DATASET*****************************************************************

def dataset_to_df(df_name):
    logging.debug("loading dataset {}...".format(df_name))

    # conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
    # sql_query = pd.read_sql_query(
    #     '''
    # SELECT * FROM [OGMA_Test].[dbo].[{}]
    # '''.format(df_name.split('.')[0]), conn)
    # df = pd.DataFrame(sql_query)
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.OPP_Get_DataSet {}, \'{}\', \'{}\', @p_result_status output
    select @p_result_status as result_status
    """.format(session["sessionID"], session["language"], df_name)

    df = exec_storedproc_results(query)
    df[['Year of Event',
        'Quarter',
        'Month of Event',
        'Week of Event',
        'Fiscal Year of Event',
        'Fiscal Quarter',
        'Fiscal Month of Event',
        'Fiscal Week of Event',
        'Julian Day',
        'Activity Event Id',
        'Measure Value']] = df[['Year of Event',
                                'Quarter',
                                'Month of Event',
                                'Week of Event',
                                'Fiscal Year of Event',
                                'Fiscal Quarter',
                                'Fiscal Month of Event',
                                'Fiscal Week of Event',
                                'Julian Day',
                                'Activity Event Id',
                                'Measure Value']].apply(pd.to_numeric)

    if df_name == 'OPG010':
        query = """\
        declare @p_result_status varchar(255)
        exec dbo.opp_get_dataset_nodedata {}, \'{}\', \'{}\', @p_result_status output
        select @p_result_status as result_status
        """.format(session["sessionID"], session["language"], df_name)

        node_df = exec_storedproc_results(query)
        node_df[['x_coord', 'y_coord']] = node_df[['x_coord', 'y_coord']].apply(pd.to_numeric)

        session[df_name + "_NodeData"] = node_df

    # add all variable names without qualifiers to col
    col = pd.Series(df['Variable Name'][df['Variable Name Qualifier'].isna()])
    # combine variable hierarchy columns into col for rows with qualifiers
    col = col.append(
        pd.Series(
            df['Variable Name'][df['Variable Name Qualifier'].notna()]
            + "|"
            + df['Variable Name Qualifier'][df['Variable Name Qualifier'].notna()]))
    df['Variable Name'] = col

    # Can be redone to exclude hierarchy one name and to include more levels
    df = df.rename(columns={'Hierarchy One Top': 'H1',
                            'Hierarchy One -1': 'H2',
                            'Hierarchy One -2': 'H3',
                            'Hierarchy One -3': 'H4',
                            'Hierarchy One -4': 'H5',
                            'Hierarchy One Leaf': 'H6'})

    # Shrinks Data Size
    df = create_categories(df, ['H1', 'H2', 'H3', 'H4', 'H5', 'H6'])

    # replaces all strings that are just spaces with NaN
    df.replace(to_replace=r'^\s*$', value=np.NaN, regex=True, inplace=True)
    df.replace(to_replace='', value=np.NaN, inplace=True)

    logging.debug("dataset {} loaded.".format(df_name))

    # If we are dealing with links in the future we must format them as follows and edit the table drawer
    # dataframe_table.Link = list(map(lambda x: '[Link]({})'.format(x), dataframe_table.Link))
    return df


# generates the constants required to be stored for the given dataset
def generate_constants(df_name):
    HIERARCHY_LEVELS = ['H{}'.format(i + 1) for i in range(6)]

    df = session[df_name]

    # list of variable column names
    VARIABLE_LEVEL = 'Variable Name'

    # list of column names
    COLUMN_NAMES = df.columns.values

    # list of measure type options
    MEASURE_TYPE_OPTIONS = df['Measure Type'].dropna().unique().tolist()
    MEASURE_TYPE_OPTIONS.sort()

    # New date picker values
    GREGORIAN_MIN_YEAR = int(df['Year of Event'].min())
    GREGORIAN_YEAR_MAX = int(df['Year of Event'][df['Calendar Entry Type'] == 'Year'].max())
    GREGORIAN_QUARTER_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Quarter'].max())
    GREGORIAN_QUARTER_FRINGE_MIN = int(df['Quarter'][df['Year of Event'] == GREGORIAN_MIN_YEAR].min())
    GREGORIAN_QUARTER_FRINGE_MAX = \
        int(df['Quarter'][df['Year of Event'] == GREGORIAN_QUARTER_MAX_YEAR].max())
    GREGORIAN_MONTH_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Month'].max())
    GREGORIAN_MONTH_FRINGE_MIN = \
        int(df['Month of Event'][df['Year of Event'] == GREGORIAN_MIN_YEAR].min())
    GREGORIAN_MONTH_FRINGE_MAX = \
        int(df['Month of Event'][df['Year of Event'] == GREGORIAN_MONTH_MAX_YEAR].max())

    if len(df[df['Calendar Entry Type'] == 'Week']) > 0:
        GREGORIAN_WEEK_AVAILABLE = True  # not currently used
        GREGORIAN_WEEK_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Week'].max())
        GREGORIAN_WEEK_FRINGE_MIN = int(
            df['Week of Event'][df['Year of Event'] == GREGORIAN_MIN_YEAR].min())
        GREGORIAN_WEEK_FRINGE_MAX = int(
            df['Week of Event'][df['Year of Event'] == GREGORIAN_WEEK_MAX_YEAR].max())
    else:
        GREGORIAN_WEEK_AVAILABLE = False  # not currently used, so set fake values
        GREGORIAN_WEEK_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Week'].max())
        # GREGORIAN_WEEK_MAX_YEAR = 52
        GREGORIAN_WEEK_FRINGE_MIN = 1
        GREGORIAN_WEEK_FRINGE_MAX = 52

    if len(df['Fiscal Year of Event'].unique()) != 1 and df['Fiscal Year of Event'].unique()[0] is not None:
        FISCAL_AVAILABLE = True

        FISCAL_MIN_YEAR = int(df['Fiscal Year of Event'].min())
        FISCAL_YEAR_MAX = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Fiscal Year'].max())
        FISCAL_QUARTER_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Quarter'].max())
        FISCAL_QUARTER_FRINGE_MIN = \
            int(df['Fiscal Quarter'][df['Fiscal Year of Event'] == FISCAL_MIN_YEAR].min())
        FISCAL_QUARTER_FRINGE_MAX = int(
            df['Fiscal Quarter'][df['Fiscal Year of Event'] == FISCAL_QUARTER_MAX_YEAR].max())
        FISCAL_MONTH_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Month'].max())
        FISCAL_MONTH_FRINGE_MIN = \
            int(df['Fiscal Month of Event'][df['Fiscal Year of Event'] == FISCAL_MIN_YEAR].min())
        FISCAL_MONTH_FRINGE_MAX = int(
            df['Fiscal Month of Event'][df['Fiscal Year of Event'] == FISCAL_MONTH_MAX_YEAR].max())
        FISCAL_WEEK_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Week'].max())
        FISCAL_WEEK_FRINGE_MIN = int(df['Fiscal Week of Event'][df['Fiscal Year of Event']
                                                                == FISCAL_MIN_YEAR].min())
        FISCAL_WEEK_FRINGE_MAX = int(df['Fiscal Week of Event'][df['Fiscal Year of Event']
                                                                == FISCAL_WEEK_MAX_YEAR].max())
    else:
        FISCAL_AVAILABLE = False
        FISCAL_MIN_YEAR = None
        FISCAL_YEAR_MAX = None
        FISCAL_QUARTER_MAX_YEAR = None
        FISCAL_QUARTER_FRINGE_MIN = None
        FISCAL_QUARTER_FRINGE_MAX = None
        FISCAL_MONTH_MAX_YEAR = None
        FISCAL_MONTH_FRINGE_MIN = None
        FISCAL_MONTH_FRINGE_MAX = None
        FISCAL_WEEK_MAX_YEAR = None
        FISCAL_WEEK_FRINGE_MIN = None
        FISCAL_WEEK_FRINGE_MAX = None

    # MIN_DATE_UNF = datetime.strptime(str(df.loc[df['Date of Event'].idxmin(), 'Date of Event']), '%Y%m%d')
    # MAX_DATE_UNF = datetime.strptime(str(df.loc[df['Date of Event'].idxmax(), 'Date of Event']), '%Y%m%d')

    # this is a hack until we get the data delivered from the database
    try:
        MIN_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(),
                                                'Date of Event'], '%Y/%m/%d')
    except TypeError:
        MIN_DATE_UNF = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(),
                              'Date of Event'].strftime('%m/%d/%Y')

    try:
        MAX_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(),
                                                'Date of Event'], '%Y/%m/%d')
    except TypeError:
        MAX_DATE_UNF = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(),
                              'Date of Event'].strftime('%m/%d/%Y')

    # replaces all Y in Partial Period with True & False
    df['Partial Period'] = df['Partial Period'].transform(lambda x: x == 'Y')

    # Sets the Date of Event in the df to be in the correct format for Plotly
    # df['Date of Event'] = df['Date of Event'].transform(
    #     lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))

    options = []

    unique_vars = df[VARIABLE_LEVEL].unique()
    cleaned_list = [x for x in unique_vars if str(x) != 'nan']
    cleaned_list.sort()

    for unique_var in cleaned_list:
        options.append(
            {'label': "  " * unique_var.count("|") + str(unique_var).replace('|', ', '), 'value': unique_var})

    VARIABLE_OPTIONS = options

    storage = {
        'HIERARCHY_LEVELS': HIERARCHY_LEVELS,
        'VARIABLE_LEVEL': VARIABLE_LEVEL,
        'COLUMN_NAMES': COLUMN_NAMES,
        'MEASURE_TYPE_OPTIONS': MEASURE_TYPE_OPTIONS,
        'GREGORIAN_MIN_YEAR': GREGORIAN_MIN_YEAR,
        'GREGORIAN_YEAR_MAX': GREGORIAN_YEAR_MAX,
        'GREGORIAN_QUARTER_MAX_YEAR': GREGORIAN_QUARTER_MAX_YEAR,
        'GREGORIAN_QUARTER_FRINGE_MIN': GREGORIAN_QUARTER_FRINGE_MIN,
        'GREGORIAN_QUARTER_FRINGE_MAX': GREGORIAN_QUARTER_FRINGE_MAX,
        'GREGORIAN_MONTH_MAX_YEAR': GREGORIAN_MONTH_MAX_YEAR,
        'GREGORIAN_MONTH_FRINGE_MIN': GREGORIAN_MONTH_FRINGE_MIN,
        'GREGORIAN_MONTH_FRINGE_MAX': GREGORIAN_MONTH_FRINGE_MAX,
        'GREGORIAN_WEEK_AVAILABLE': GREGORIAN_WEEK_AVAILABLE,
        'GREGORIAN_WEEK_MAX_YEAR': GREGORIAN_WEEK_MAX_YEAR,
        'GREGORIAN_WEEK_FRINGE_MIN': GREGORIAN_WEEK_FRINGE_MIN,
        'GREGORIAN_WEEK_FRINGE_MAX': GREGORIAN_WEEK_FRINGE_MAX,
        'FISCAL_AVAILABLE': FISCAL_AVAILABLE,
        'FISCAL_MIN_YEAR': FISCAL_MIN_YEAR,
        'FISCAL_YEAR_MAX': FISCAL_YEAR_MAX,
        'FISCAL_QUARTER_MAX_YEAR': FISCAL_QUARTER_MAX_YEAR,
        'FISCAL_QUARTER_FRINGE_MIN': FISCAL_QUARTER_FRINGE_MIN,
        'FISCAL_QUARTER_FRINGE_MAX': FISCAL_QUARTER_FRINGE_MAX,
        'FISCAL_MONTH_MAX_YEAR': FISCAL_MONTH_MAX_YEAR,
        'FISCAL_MONTH_FRINGE_MIN': FISCAL_MONTH_FRINGE_MIN,
        'FISCAL_MONTH_FRINGE_MAX': FISCAL_MONTH_FRINGE_MAX,
        'FISCAL_WEEK_MAX_YEAR': FISCAL_WEEK_MAX_YEAR,
        'FISCAL_WEEK_FRINGE_MIN': FISCAL_WEEK_FRINGE_MIN,
        'FISCAL_WEEK_FRINGE_MAX': FISCAL_WEEK_FRINGE_MAX,
        'MIN_DATE_UNF': MIN_DATE_UNF,
        'MAX_DATE_UNF': MAX_DATE_UNF,
        'VARIABLE_OPTIONS': VARIABLE_OPTIONS
    }
    return storage


# **********************************************DATA MANIPULATION FUNCTIONS*******************************************


def data_filter(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                timeframe, fiscal_toggle, num_periods, period_type, hierarchy_toggle, hierarchy_level_dropdown,
                hierarchy_graph_children, df_name, df_const):
    # NOTE: This assumes hierarchy path is a list of all previously selected levels

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

        # Filters out unused calender values
        time_df = filtered_df.copy()
        time_df = time_df[time_df['Calendar Entry Type'] == current_filter]

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date]
        time_df = time_df[time_df['Date of Event'] <= end_date]

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
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
        # Data frame filtered to be in inputted year range
        time_df = filtered_df.copy()
        time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] >= start_year]
        time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] <= end_year - 1]

        # Filters out month and quarter values (whole year)
        time_df = time_df[time_df['Calendar Entry Type'] == '{}Year'.replace("{}", year_prefix)]
    return time_df


# Filters data based on customize menu inputs
def customize_menu_filter(dff, df_name, measure_type, variable_names, df_const):
    if measure_type == 'Link':
        filtered_df = dff[dff['Measure Fcn'] == 'Link']
    else:
        filtered_df = dff[dff['Measure Type'] == measure_type]

    if variable_names is not None:

        # ensure variable_names is a list of variable values
        if type(variable_names) is not list:
            variable_names = [variable_names]

        aggregate_df = pd.DataFrame()

        # for each selection, add the rows defined by the selection
        for variable_name in variable_names:
            # Filters based on rows that match the variable name path
            aggregate_df = aggregate_df.append(
                filtered_df[filtered_df[df_const[df_name]['VARIABLE_LEVEL']] == variable_name])

        filtered_df = aggregate_df

    return filtered_df


# This uses pandas categories to shrink the data
def create_categories(dff, hierarchy_columns):
    to_category = ['Calendar Entry Type', 'Measure Type', 'OPG Data Set', 'Hierarchy One Name', 'Variable Name',
                   'Variable Name Qualifier', 'Variable Name Sub Qualifier', 'Partial Period']
    to_category = hierarchy_columns + to_category
    for i in to_category:
        dff[i] = pd.Categorical(dff[i])
    return dff


def get_table_columns(dff):
    df = dff.drop(
        # ['OPG 001 Time Series Measures', 'Calendar Entry Type', 'Year of Event',
        ['OPG Data Set', 'Calendar Entry Type', 'Year of Event', 'Month of Event'], axis=1)
    df = df.dropna(how='all', axis=1)
    return df.columns


# *********************************************LANGUAGE DATA***********************************************************

def get_label(label, table=None):
    if label is None:
        return None

    lookup = "labels"

    if table is None:
        table = "Labels"
    elif table.lower != "labels":
        lookup = lookup + "_" + table.lower()

    language_df = session.get(lookup)

    if language_df is None:
        language_df = get_ref(table, session["language"])
        session[lookup] = language_df

    row = language_df[language_df["ref_value"] == label]

    if len(row) != 1:
        return 'Key Error: {}|{}'.format(table, label)

    return row["ref_desc"].iloc[0]


# loads labels from language data from database
# conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
# sql_query = pd.read_sql_query('''exec dbo.reftable''',conn)
# LANGUAGE_DF = session["labels"]  # pd.DataFrame(sql_query)
# LANGUAGE_DF = pd.read_csv('apps/OPG001/test_data/Language Data JG.csv')

# Apparently will be passed in via the server
# 'En' = English
# 'Fr' = French
# LANGUAGE = session["language"]

# *********************************************DATAFRAME OPERATIONS***************************************************

# DATA_SETS = ['OPG001_2016-17_Week_v3.xlsx']  # 'OPG001_2016-17_Week_v2.xlsx'
# DATA_SETS = ['Graphics 1 example dataset V4', 'Other DF Test (V1)', 'OPG010 example V1 JG']
# DATA_SETS = ['OPG010 SanKey Series.csv']  # 'OPG010 Pruned',
# DATA_SETS = ['OPG001_2016-17_Week_v3.xlsx', 'OPG010 Pruned 2.xlsx']
# GOOD!!! DATA_SETS = ['OPG010 Pruned 2.xlsx']
# DATA_SETS = ['OPG010 Pruned.csv']
# DATA_SETS = ['OPG010 Missing Node Test.xlsx']

# DATA_SETS = ['OPG001 Graph Data.xlsx', 'OPG010 Sankey Data.xlsx']
# DATA_SETS = ['OPG010 Sankey Data.xlsx']
# DATA_SETS = ['OPG001_2016-17_Week_v3.xlsx']
# DATA_SETS = ['OPG001_2016-17_Week_v3.csv']

# from dotenv import load_dotenv, find_dotenv
# import os
# import json

# # load data sets from environment variables if .env created or load default data sets
# # example of environment variable: DATA_SETS = '["OPG001_2016-17_Week_v3.csv", "OPG010 Sankey Data.xlsx"]'
# if load_dotenv(find_dotenv()):
#     load_dotenv()
#     DATA_SETS = json.loads(os.environ['DATA_SETS'])
# else:
#     print("The .env file. was not found, loading default data sets")
#     DATA_SETS = ['OPG001_2016-17_Week_v3.csv', 'OPG010 Sankey Data.xlsx']
# DATA_SETS = config.DATA_SETS

# DATA_SETS = config.DATA_SETS

# cnxn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
# sql_query = pd.read_sql_query('''exec dbo.OPP_retrieve_datasets''', cnxn)
# DATA_SETS = pd.DataFrame(sql_query)['ref_value'].tolist()
# cnxn.close()

# ********************************************DATA FITTING OPERATIONS**************************************************

def linear_regression(df, x, y, ci):
    df_best_fit = pd.DataFrame()

    df_best_fit['timestamp'] = pd.to_datetime(df[x])
    df_best_fit['serialtime'] = [(d - datetime(1970, 1, 1)).days for d in df_best_fit['timestamp']]

    x_axis = sm.add_constant(df_best_fit['serialtime'])
    # creates statistical model from ordinary lease squares method
    model = sm.OLS(df[y], x_axis).fit()
    df_best_fit['Best Fit'] = model.fittedvalues

    if ci:
        df_best_fit["Upper Interval"], df_best_fit["Lower Interval"] = confidence_intervals(model)

    return df_best_fit


def polynomial_regression(df, x, y, degree, ci):
    df_best_fit = pd.DataFrame()

    df_best_fit['timestamp'] = pd.to_datetime(df[x])
    df_best_fit['serialtime'] = [(d - datetime(1970, 1, 1)).days for d in df_best_fit['timestamp']]

    polynomial_features = PolynomialFeatures(degree=degree)
    xp = polynomial_features.fit_transform(df_best_fit['serialtime'].to_numpy().reshape(-1, 1))
    # creates statistical model from ordinary lease squares method
    model = sm.OLS(df[y], xp).fit()
    # creates best fit with generated polynomial
    df_best_fit["Best Fit"] = model.predict(xp)

    if ci:
        df_best_fit["Lower Interval"], df_best_fit["Upper Interval"] = confidence_intervals(model)

    return df_best_fit


def confidence_intervals(model):
    # calculates standard deviation and confidence interval for prediction
    _, lower, upper = wls_prediction_std(model)
    # returns the upper and lower confidence interval
    return lower, upper
