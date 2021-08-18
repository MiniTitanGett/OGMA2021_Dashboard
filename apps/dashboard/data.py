######################################################################################################################
"""
data.py

contains arbitrary constants, data constants, and data manipulation functions
"""
######################################################################################################################

from datetime import datetime, timedelta, date

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
from server import get_org_parent

GRAPH_OPTIONS = {
    'OPG001': ['Line', 'Bar', 'Scatter', 'Bubble', 'Box_Plot', 'Table'],
    'OPG010': ['Sankey', 'Table'],
    'OPG011': ['Line', 'Bar', 'Scatter', 'Bubble', 'Box_Plot', 'Table']
}
for k in GRAPH_OPTIONS.values():
    k.sort()

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

    if df_name == 'OPG010':
        query = """\
        declare @p_result_status varchar(255)
        exec dbo.opp_get_dataset_nodedata {}, \'{}\', \'{}\', @p_result_status output
        select @p_result_status as result_status
        """.format(session["sessionID"], session["language"], df_name)

        node_df = exec_storedproc_results(query)
        node_df[['x_coord', 'y_coord']] = node_df[['x_coord', 'y_coord']].apply(pd.to_numeric)

        session[df_name + "_NodeData"] = node_df

    if df_name == 'OPG011':
        df[["OPG Data Set",
            "Hierarchy One Name",
            "Hierarchy One Top",
            "Hierarchy One -1",
            "Hierarchy One -2",
            "Hierarchy One -3",
            "Hierarchy One -4",
            "Hierarchy One Leaf"]] = np.NaN

        # TODO: SETUP VAR HIERARCHY ITERATION HERE

    else:
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
        # add all variable names without qualifiers to col
        col = pd.Series(df['Variable Name'][df['Variable Name Qualifier'].isna()])
        # combine variable hierarchy columns into col for rows with qualifiers
        col = col.append(
            pd.Series(
                df['Variable Name'][df['Variable Name Qualifier'].notna()]
                + " "
                + df['Variable Name Qualifier'][df['Variable Name Qualifier'].notna()]))
        df['Variable Name'] = col

    # Can be redone to exclude hierarchy one name and to include more levels
    df = df.rename(columns={'Hierarchy One Top': 'H0',
                            'Hierarchy One -1': 'H1',
                            'Hierarchy One -2': 'H2',
                            'Hierarchy One -3': 'H3',
                            'Hierarchy One -4': 'H4',
                            'Hierarchy One Leaf': 'H5'})

    # replaces all strings that are just spaces with NaN
    df.replace(to_replace=r'^\s*$', value=np.NaN, regex=True, inplace=True)
    df.replace(to_replace='', value=np.NaN, inplace=True)

    # if OPG011 we need to construct the tree by asking for the parents of unique values
    if df_name == "OPG011":
        list_of_depths = [[], [], [], [], [], []]
        dff = df[["Hierarchy Value", "Hierarchy Level"]].drop_duplicates()
        # init the depth lists
        for x in dff["Hierarchy Value"]:
            depth = int(dff.loc[dff["Hierarchy Value"] == x]["Hierarchy Level"].iloc[0])
            list_of_depths[depth].append(x)
            df.loc[df["Hierarchy Value"] == x, "H{}".format(depth)] = x

        # begin reverse breadth first traversal, filling hierarchy along the way
        depth = 6
        for nodes_at_depth in reversed(list_of_depths):
            depth = depth - 1
            for node in nodes_at_depth:
                parent = get_org_parent(node, depth)
                if parent not in list_of_depths[depth - 1]:
                    list_of_depths[depth - 1].append(parent)
                # insert parent into table
                df.loc[df["H{}".format(depth)] == node, "H{}".format(depth - 1)] = parent

    df = create_categories(df, ['H0', 'H1', 'H2', 'H3', 'H4', 'H5'])

    logging.debug("dataset {} loaded.".format(df_name))

    # If we are dealing with links in the future we must format them as follows and edit the table drawer
    # dataframe_table.Link = list(map(lambda x: '[Link]({})'.format(x), dataframe_table.Link))
    return df


# generates the constants required to be stored for the given dataset
def generate_constants(df_name):
    HIERARCHY_LEVELS = ['H{}'.format(i) for i in range(6)]

    df = session[df_name]

    # list of variable column names
    VARIABLE_LEVEL = 'Variable Name'

    # list of column names
    COLUMN_NAMES = df.columns.values

    # list of measure type options
    MEASURE_TYPE_OPTIONS = df['Measure Type'].dropna().unique().tolist()
    MEASURE_TYPE_OPTIONS.sort()

    if df_name == 'OPG011':
        try:
            min_date_unf = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(),
                                                    'Date of Event'], '%Y/%m/%d')
        except TypeError:
            min_date_unf = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(),
                                  'Date of Event']

        try:
            max_date_unf = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(),
                                                    'Date of Event'], '%Y/%m/%d')
        except TypeError:
            max_date_unf = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(),
                                  'Date of Event']

        # New date picker values
        GREGORIAN_MIN_YEAR = int(min_date_unf.year)
        GREGORIAN_YEAR_MAX = int(max_date_unf.year)
        GREGORIAN_QUARTER_MAX_YEAR = int(max_date_unf.year)
        GREGORIAN_QUARTER_FRINGE_MIN = int((min_date_unf.month - 1) // 3 + 1)
        GREGORIAN_QUARTER_FRINGE_MAX = int((max_date_unf.month - 1) // 3 + 1)
        GREGORIAN_MONTH_MAX_YEAR = int(max_date_unf.year)
        GREGORIAN_MONTH_FRINGE_MIN = int(min_date_unf.month)
        GREGORIAN_MONTH_FRINGE_MAX = int(max_date_unf.month)

        if len(df[df['Calendar Entry Type'] == 'Week']) > 0:
            GREGORIAN_WEEK_AVAILABLE = True  # not currently used
            GREGORIAN_WEEK_MAX_YEAR = int(max_date_unf.year)
            GREGORIAN_WEEK_FRINGE_MIN = int(min_date_unf.strftime("%W")) + 1
            GREGORIAN_WEEK_FRINGE_MAX = int(max_date_unf.strftime("%W")) + 1
        else:
            GREGORIAN_WEEK_AVAILABLE = False  # not currently used, so set fake values
            GREGORIAN_WEEK_MAX_YEAR = 52
            GREGORIAN_WEEK_FRINGE_MIN = 1
            GREGORIAN_WEEK_FRINGE_MAX = 52

        # TODO: Calc and set values based off of client org system setting
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
        MIN_DATE_UNF = min_date_unf.strftime('%m/%d/%Y')
        MAX_DATE_UNF = max_date_unf.strftime('%m/%d/%Y')
    else:
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
            GREGORIAN_WEEK_MAX_YEAR = 52
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


# ****************************************************DATE FUNCTIONS**************************************************

# given a date returns the last day of the month
def get_last_day_of_month(day):
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


# given a date determines the week number
def week_number_of_month(date_value):
    return date_value.isocalendar()[1] - date_value.replace(day=1).isocalendar()[1] + 1


# given a date returns the start of a quarter
def get_quarter_start(day):
    return date(day.year, (day.month - 1) // 3 * 3 + 1, 1)


# given a date returns the end of a quarter
def get_last_day_of_quarter(day):
    quarter_start = get_quarter_start(day)
    return quarter_start + relativedelta(months=3, days=-1)


# returns the last day of a given year
def get_last_day_of_year(year):
    return date(int(year), 12, 31)


def get_month(day):
    return day.astype('datetime64[M]').astype(int) % 12 + 1


def get_quarter(day):
    return (get_month(day) - 1) // 3 + 1

# **********************************************DATA MANIPULATION FUNCTIONS*******************************************


def data_manipulator(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, df_name,
                     df_const, secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe,
                     fiscal_toggle, num_periods, period_type, arg_values=None, graph_type=None):

    if df_name != 'OPG011':
        filtered_df = data_hierarchy_filter(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown,
                                            hierarchy_graph_children, df_name, df_const)
        filtered_df = data_time_filter(secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe,
                                       fiscal_toggle, num_periods, period_type, df_name, df_const, filtered_df)
    else:
        df = session[df_name].copy()

        # initial hierarchy filtering (remove all children of a level to prep for agg)
        if hierarchy_toggle == 'Level Filter' or (
                (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):

            if hierarchy_toggle == 'Level Filter':
                # If anything is in the drop down
                if hierarchy_level_dropdown:
                    # Take the level and clear the other columns
                    # Ex) H2 picked --> H3, H4, H5 get wiped
                    df[df_const[df_name]['HIERARCHY_LEVELS'][int(hierarchy_level_dropdown[1]) + 1:]] = np.nan
                else:
                    # Returns empty data frame with column names
                    df = df[0:0]
            else:
                # Filters out all rows that are less specific than given path length
                for i in range(len(hierarchy_path)):
                    df = df[
                        df[df_const[df_name]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]
                # Filters out all rows that are more specific than given path length plus one to preserve the children
                df[df_const[df_name]['HIERARCHY_LEVELS'][int(len(hierarchy_path)) + 1:]] = np.nan
        else:
            # Filters out all rows that don't include path member at specific level
            for i in range(len(hierarchy_path)):
                df = df[df[df_const[df_name]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]
            # Filters out all rows that are more specific than given path
            df.loc[:, df_const[df_name]['HIERARCHY_LEVELS'][int(len(hierarchy_path)):]] = np.nan

        if graph_type == "Line" or graph_type == "Scatter" or graph_type == "Bar" or graph_type == "Box":
            filtered_df = data_time_aggregator_simplified(hierarchy_path, secondary_type, end_secondary, end_year,
                                                          start_secondary, start_year, timeframe, fiscal_toggle,
                                                          num_periods, period_type, df_name, df_const, arg_values,
                                                          graph_type, df)

        else:
            filtered_df = data_time_aggregator(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary,
                                               start_year, timeframe, fiscal_toggle, num_periods, period_type, df_name,
                                               df_const, df)
        # TODO: Write hierarchy aggregator when date_time_aggregator is complete
        filtered_df = data_hierarchy_aggregator(filtered_df, hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown,
                                                hierarchy_graph_children, df_name, df_const)

    return filtered_df


def data_hierarchy_filter(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, df_name,
                          df_const):
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

    return filtered_df


def data_hierarchy_aggregator(filtered_df, hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown,
                              hierarchy_graph_children, df_name, df_const):
    # NOTE: This assumes hierarchy path is a list of all previously selected levels

    if hierarchy_toggle == 'Level Filter' or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
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
        # Filters out all rows that don't include path member at specific level
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df[filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]
        # Filters out all rows that are more specific than given path
        for i in range(len(df_const[df_name]['HIERARCHY_LEVELS']) - len(hierarchy_path)):
            bool_series = pd.isnull(filtered_df[df_const[df_name]['HIERARCHY_LEVELS'][
                len(df_const[df_name]['HIERARCHY_LEVELS']) - 1 - i]])
            filtered_df = filtered_df[bool_series]

    return filtered_df


def data_time_filter(secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe, fiscal_toggle,
                     num_periods, period_type, df_name, df_const, filtered_df):
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


def data_time_aggregator(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                         timeframe, fiscal_toggle, num_periods, period_type, df_name, df_const, filtered_df):
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

        # Builds the data for the respective filter, either year, month or quarter
        if df_name == "OPG011" and current_filter != 'Week':
            measure_types = filtered_df['Measure Type'].unique().tolist()
            variable_names = filtered_df['Variable Name'].unique().tolist()
            row_list = []

            # Builds data based on all measure types, variable names, and selected time frame
            for x in range(len(measure_types)):
                measure_type = measure_types[x]
                reduced_df = filtered_df[filtered_df['Measure Type'] == measure_type]
                for y in range(len(variable_names)):
                    variable_name = variable_names[y]
                    further_reduced_df = reduced_df[reduced_df['Variable Name'] == variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                        # TODO: needs to filter on unique secondary types not unique dates
                        unique_dates = yearly_data["Date of Event"].unique()
                        for w in range(len(unique_dates)):
                            if current_filter == 'Year':
                                unique_secondary = unique_dates[w].year
                                unique_data = yearly_data[yearly_data["Date of Event"].year == unique_secondary]
                                date_of_event = get_last_day_of_year(year)
                                year_of_event = year
                                quarter = ""
                                month_of_event = ""
                                week_of_event = ""
                            elif current_filter == 'Quarter':
                                unique_secondary = get_quarter(unique_dates[w])
                                unique_data = yearly_data[get_quarter(yearly_data["Date of Event"]) == unique_secondary]
                                date_of_event = get_last_day_of_quarter(unique_dates[w])
                                year_of_event = year
                                quarter = unique_secondary
                                month_of_event = ""
                                week_of_event = ""
                            else:
                                unique_secondary = get_month(unique_dates[w])
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_secondary]
                                date_of_event = get_last_day_of_month(date(year, int(unique_secondary), 1))
                                year_of_event = year
                                quarter = get_quarter(unique_dates[w])
                                month_of_event = unique_secondary
                                week_of_event = ""

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
                                 date_of_event, current_filter, year_of_event, quarter, month_of_event, week_of_event,
                                 '', '', '', '', '', '', measure_value, measure_type, ''])

            time_df = pd.DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        # Creates a copy of the filtered data frame that just contains the weekly data
        else:  # elif df_name == "OPG011" and current_filter == 'Week':
            time_df = filtered_df.copy()

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date.date()]
        time_df = time_df[time_df['Date of Event'] <= end_date.date()]

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
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
                    yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                    # TODO: needs to filter on unique secondary types not unique dates
                    unique_dates = yearly_data["Date of Event"].unique()
                    for w in range(len(unique_dates)):
                        if secondary_type == 'Quarter':
                            secondary = get_quarter(unique_dates[w])
                            unique_data = yearly_data[get_quarter(yearly_data["Date of Event"]) == secondary]
                        else:
                            secondary = get_month(unique_dates[w])
                            unique_data = yearly_data[yearly_data["Date of Event"].dt.month == secondary]
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
                             get_last_day_of_quarter(unique_dates[w]),
                             secondary_type, year,
                             secondary if secondary_type == "Quarter" else get_quarter(unique_dates[w]),
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
        measure_types = filtered_df['Measure Type'].unique().tolist()
        variable_names = filtered_df['Variable Name'].unique().tolist()
        row_list = []

        for x in range(len(measure_types)):
            measure_type = measure_types[x]
            reduced_df = filtered_df[filtered_df['Measure Type'] == measure_type]
            for y in range(len(variable_names)):
                variable_name = variable_names[y]
                further_reduced_df = reduced_df[reduced_df['Variable Name'] == variable_name]
                unique_secondary = further_reduced_df['Date of Event'].dt.year.unique().tolist()
                for z in range(len(unique_secondary)):
                    secondary = unique_secondary[z]
                    unique_data = further_reduced_df[further_reduced_df['Date of Event'].dt.year == secondary]
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

    return time_df


def data_time_aggregator_simplified(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary,
                                    start_year, timeframe, fiscal_toggle, num_periods, period_type, df_name, df_const,
                                    arg_values, graph_type, df):
    if graph_type == "Box":
        measure_type = arg_values[0]
        variable_names = arg_values[1]
    else:
        measure_type = arg_values[1]
        variable_names = arg_values[2]

    filtered_df = df[df['Measure Type'] == measure_type]

    # ensure variable_names is a list of variable values
    if type(variable_names) is not list:
        variable_names = [variable_names]

    row_list = []

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

        # Builds the data for the respective filter, either year, month or quarter
        if df_name == "OPG011" and current_filter != 'Week':

            # Builds data based on all measure types, variable names, and selected time frame
            for y in range(len(variable_names)):
                variable_name = variable_names[y]
                further_reduced_df = filtered_df[filtered_df['Variable Name'] == variable_name]
                for z in range(end_date.year - start_date.year + 1):
                    year = start_date.year + z
                    yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                    # TODO: needs to filter on unique secondary types not unique dates
                    unique_dates = yearly_data["Date of Event"].unique()
                    for w in range(len(unique_dates)):
                        if current_filter == 'Year':
                            unique_secondary = unique_dates[w].year
                            unique_data = yearly_data[yearly_data["Date of Event"].year == unique_secondary]
                            date_of_event = get_last_day_of_year(year)
                            year_of_event = year
                            quarter = ""
                            month_of_event = ""
                            week_of_event = ""
                        elif current_filter == 'Quarter':
                            unique_secondary = get_quarter(unique_dates[w])
                            unique_data = yearly_data[get_quarter(yearly_data["Date of Event"]) == unique_secondary]
                            date_of_event = get_last_day_of_quarter(unique_dates[w])
                            year_of_event = year
                            quarter = unique_secondary
                            month_of_event = ""
                            week_of_event = ""
                        else:
                            unique_secondary = get_month(unique_dates[w])
                            unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_secondary]
                            date_of_event = get_last_day_of_month(date(year, int(unique_secondary), 1))
                            year_of_event = year
                            quarter = get_quarter(unique_dates[w])
                            month_of_event = unique_secondary
                            week_of_event = ""

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
                             date_of_event, current_filter, year_of_event, quarter, month_of_event, week_of_event,
                             '', '', '', '', '', '', measure_value, measure_type, ''])
            time_df = pd.DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        # Creates a copy of the filtered data frame that just contains the weekly data
        else:  # elif df_name == "OPG011" and current_filter == 'Week':
            time_df = filtered_df.copy()

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date.date()]
        time_df = time_df[time_df['Date of Event'] <= end_date.date()]

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        for y in range(len(variable_names)):
            variable_name = variable_names[y]
            reduced_df = filtered_df[filtered_df['Variable Name'] == variable_name]
            for z in range(end_year - start_year + 1):
                year = start_year + z
                yearly_data = reduced_df[reduced_df["Date of Event"].dt.year == year]
                # TODO: this filtering can create duplicate data and it needs to be fixed (same with above)
                unique_dates = yearly_data["Date of Event"].unique()
                for w in range(len(unique_dates)):
                    if secondary_type == 'Quarter':
                        secondary = get_quarter(unique_dates[w])
                        unique_data = yearly_data[get_quarter(yearly_data["Date of Event"]) == secondary]
                    else:
                        secondary = get_month(unique_dates[w])
                        unique_data = yearly_data[yearly_data["Date of Event"].dt.month == secondary]
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
                         get_last_day_of_month(unique_dates[w]) if secondary_type == "Month" else
                         get_last_day_of_quarter(unique_dates[w]),
                         secondary_type, year,
                         secondary if secondary_type == "Quarter" else get_quarter(unique_dates[w]),
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
        for y in range(len(variable_names)):
            variable_name = variable_names[y]
            further_reduced_df = filtered_df[filtered_df['Variable Name'] == variable_name]
            unique_secondary = further_reduced_df['Date of Event'].dt.year.unique().tolist()
            for z in range(len(unique_secondary)):
                secondary = unique_secondary[z]
                unique_data = further_reduced_df[further_reduced_df['Date of Event'].dt.year == secondary]
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
