######################################################################################################################
"""
data.py

Contains arbitrary constants, data constants, and data manipulation functions.
"""
######################################################################################################################

# External Packages
from datetime import datetime, timedelta, date

# import numpy as np
import pandas as pd
import logging
from pandas import DataFrame
from vaex import from_pandas
from numpy import nan, datetime64, float64, full
# import pyodbc
from dateutil.relativedelta import relativedelta
from flask import session
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from sklearn.preprocessing import PolynomialFeatures

# Internal Modules
# import config
from conn import get_ref, exec_storedproc_results
from server import get_hierarchy  # , get_hierarchy_parent, get_variable_parent,

# ***********************************************ARBITRARY CONSTANTS*************************************************

GRAPH_OPTIONS = {
    'OPG010': ['Sankey', 'Table'],
    'OPG011': ['Line', 'Bar', 'Scatter', 'Bubble', 'Box_Plot', 'Table']
}
for k in GRAPH_OPTIONS.values():
    k.sort()

X_AXIS_OPTIONS = ['Time']

BAR_X_AXIS_OPTIONS = ['Specific Item', 'Variable Names']

COLOR_PALETTE = ['G10', 'Bold', 'Vivid', 'Dark24', 'Pastel', 'Color Blind Friendly']

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

LAYOUTS = [{'lg': [{'i': "tile-wrapper: 0", 'x': 0, 'y': 0, 'w': 24, 'h': 18}]},
           {'lg': [
               {'i': "tile-wrapper: 0", 'x': 0, 'y': 0, 'w': 12, 'h': 18},
               {'i': "tile-wrapper: 1", 'x': 12, 'y': 0, 'w': 12, 'h': 18}]},
           {'lg': [
               {'i': "tile-wrapper: 0", 'x': 0, 'y': 0, 'w': 12, 'h': 9},
               {'i': "tile-wrapper: 1", 'x': 12, 'y': 0, 'w': 12, 'h': 9},
               {'i': "tile-wrapper: 2", 'x': 0, 'y': 9, 'w': 24, 'h': 9}]},
           {'lg': [
               {'i': "tile-wrapper: 0", 'x': 0, 'y': 0, 'w': 12, 'h': 9},
               {'i': "tile-wrapper: 1", 'x': 12, 'y': 0, 'w': 12, 'h': 9},
               {'i': "tile-wrapper: 2", 'x': 0, 'y': 9, 'w': 12, 'h': 9},
               {'i': "tile-wrapper: 3", 'x': 12, 'y': 9, 'w': 12, 'h': 9}]}]

# ******************************************STYLE RETURNS FOR CALLBACKS***********************************************

VIEW_CONTENT_SHOW = {'min-height': '0', 'overflow': 'hidden'}
VIEW_CONTENT_HIDE = {'display': 'none'}

CUSTOMIZE_CONTENT_SHOW = {'flex-grow': '1'}
CUSTOMIZE_CONTENT_HIDE = {'display': 'none'}

LAYOUT_CONTENT_SHOW = {'flex-grow': '1'}
LAYOUT_CONTENT_HIDE = {'display': 'none'}

DATA_CONTENT_SHOW = {'max-width': '300px', 'min-width': '300px', 'background-color': CLR['sidebar-final'],
                     'border-right': '1px solid {}'.format(CLR['lightgray']),
                     'flex-grow': '1', 'display': 'inline'}
DATA_CONTENT_HIDE = {'display': 'none'}


# ********************************************DATASET*****************************************************************


def dataset_to_df(df_name, time_period):
    """Queries for the dataset and returns a formatted pandas, data frame."""
    query = """\
    declare @p_result_status varchar(255)
    exec dbo.OPP_Get_DataSet {}, \'{}\', \'{}\',\'{}\', @p_result_status output
    select @p_result_status as result_status
    """.format(session["sessionID"], session["language"], df_name, time_period)
    df = exec_storedproc_results(query)
    if df.empty:
        return df
    df_vaex = from_pandas(df)
    df_vaex.variables['nan'] = nan
    logging.debug("done converting pandas to vaex")

    if df_name == 'OPG010':
        query = """\
        declare @p_result_status varchar(255)
        exec dbo.opp_get_dataset_nodedata {}, \'{}\', \'{}\', @p_result_status output
        select @p_result_status as result_status
        """.format(session["sessionID"], session["language"], df_name)

        node_df = exec_storedproc_results(query)
        node_df_vaex = from_pandas(node_df)

        node_df_vaex['x_coord'] = node_df_vaex['x_coord'].astype('float64')
        node_df_vaex['y_coord'] = node_df_vaex['y_coord'].astype('float64')

        session[df_name + "_NodeData"] = node_df_vaex
        df_vaex['Measure Type'] = df_vaex.func.where(df_vaex['Measure Type'] == '', None, df_vaex['Measure Type'])
        df_vaex['Partial Period'] = df_vaex.func.where(df_vaex['Partial Period'] == '', 'False',
                                                       df_vaex['Partial Period'])
        # add all variable names without qualifiers to col
        df_vaex['Variable Value'] = df_vaex['Variable Name'] + " " + df_vaex['Variable Name Qualifier']

    if df_name == 'OPG011':
        # TODO: REPLACE VAR HIERARCHY ITERATION HERE
        # list_of_depths = [[], [], []]
        # var_levels = ["Variable Name", "Variable Name Qualifier", "Variable Name Sub Qualifier"]
        # # dff = df[["Variable Value", "Variable Level"]].drop_duplicates()
        # dff_vaex = df_vaex[["Variable Value", "Variable Level"]]
        # unique_value = dff_vaex["Variable Value"].unique()
        # # init the depth lists and replace the value where variable value row equal the unique value to
        # # assign the var_level column values
        # for x in unique_value:
        #     depth_dff = dff_vaex[dff_vaex["Variable Value"] == x]
        #     depth = depth_dff.evaluate("Variable Level")[0]
        #     list_of_depths[depth].append(x)
        #     df_vaex[var_levels[depth]] = df_vaex.func.where(df_vaex["Variable Value"] == x, x,
        #                                                          df_vaex[var_levels[depth]])
        #
        # # begin reverse breadth first traversal, filling hierarchy along the way
        # depth = 3
        # for nodes_at_depth in reversed(list_of_depths):
        #     depth = depth - 1
        #     for node in nodes_at_depth:
        #         parent = get_variable_parent(node, depth)
        #         if parent not in list_of_depths[depth - 1]:
        #             list_of_depths[depth - 1].append(parent)
        #         # insert parent into table
        #         df_vaex[var_levels[depth-1]] = df_vaex.func.where(df_vaex[var_levels[depth]] == node, parent,
        #                                                         df_vaex[var_levels[depth-1]])

        df_vaex['Variable Name Sub Qualifier'] = df_vaex.func.where(df_vaex['Variable Name Sub Qualifier'] == '', None,
                                                                    df_vaex['Variable Name Sub Qualifier'])
        # combine variable hierarchy columns into col for rows with qualifiers
        if df_vaex.data_type(df_vaex['Variable Name Sub Qualifier']) == str:
            df_vaex['Variable Value'] = df_vaex['Variable Name'] + " " + df_vaex['Variable Name Qualifier'] + " " + \
                                        df_vaex['Variable Name Sub Qualifier']
        else:
            df_vaex['Variable Value'] = df_vaex['Variable Name'] + " " + df_vaex['Variable Name Qualifier']

    else:

        df_vaex['Week of Event'] = df_vaex.func.where(df_vaex['Week of Event'] == "", nan, df_vaex['Week of Event'])
        df_vaex['Activity Event Id'] = df_vaex.func.where(df_vaex['Activity Event Id'] == "", nan,
                                                          df_vaex['Activity Event Id'])
        df_vaex['Fiscal Year of Event'] = df_vaex.func.where(df_vaex['Fiscal Year of Event'] == "", nan,
                                                             df_vaex['Fiscal Year of Event'])
        df_vaex['Fiscal Quarter'] = df_vaex.func.where(df_vaex['Fiscal Quarter'] == "", nan,
                                                       df_vaex['Fiscal Quarter'])
        df_vaex['Fiscal Month of Event'] = df_vaex.func.where(df_vaex['Fiscal Month of Event'] == "", nan,
                                                              df_vaex['Fiscal Month of Event'])
        df_vaex['Fiscal Week of Event'] = df_vaex.func.where(df_vaex['Fiscal Week of Event'] == "", nan,
                                                             df_vaex['Fiscal Week of Event'])
        df_vaex['Julian Day'] = df_vaex.func.where(df_vaex['Julian Day'] == "", nan, df_vaex['Julian Day'])
        df_vaex['Week of Event'] = df_vaex['Week of Event'].astype('float64')
        df_vaex['Activity Event Id'] = df_vaex['Activity Event Id'].astype('float64')
        df_vaex['Fiscal Year of Event'] = df_vaex['Fiscal Year of Event'].astype('float64')
        df_vaex['Fiscal Quarter'] = df_vaex['Fiscal Quarter'].astype('float64')
        df_vaex['Fiscal Month of Event'] = df_vaex['Fiscal Month of Event'].astype('float64')
        df_vaex['Fiscal Week of Event'] = df_vaex['Fiscal Week of Event'].astype('float64')
        df_vaex['Julian Day'] = df_vaex['Julian Day'].astype('float64')

        df_vaex['Variable Value'] = df_vaex['Variable Name'] + " " + df_vaex['Variable Name Qualifier']

        # Can be redone to exclude hierarchy one name and to include more levels
        df_vaex.rename('Hierarchy One Top', 'H0')
        df_vaex.rename('Hierarchy One -1', 'H1')
        df_vaex.rename('Hierarchy One -2', 'H2')
        df_vaex.rename('Hierarchy One -3', 'H3')
        df_vaex.rename('Hierarchy One -4', 'H4')
        df_vaex.rename('Hierarchy One Leaf', 'H5')

    df_vaex['OPG Data Set'] = df_vaex.func.where(df_vaex['OPG Data Set'] == '', None, df_vaex['OPG Data Set'])
    df_vaex['H0'] = df_vaex.func.where(df_vaex['H0'] == '', None, df_vaex['H0'])
    df_vaex['H1'] = df_vaex.func.where(df_vaex['H1'] == '', None, df_vaex['H1'])
    df_vaex['H2'] = df_vaex.func.where(df_vaex['H2'] == '', None, df_vaex['H2'])
    df_vaex['H3'] = df_vaex.func.where(df_vaex['H3'] == '', None, df_vaex['H3'])
    df_vaex['H4'] = df_vaex.func.where(df_vaex['H4'] == '', None, df_vaex['H4'])
    df_vaex['H5'] = df_vaex.func.where(df_vaex['H5'] == '', None, df_vaex['H5'])
    df_vaex['Variable Name'] = df_vaex.func.where(df_vaex['Variable Name'] == '', None, df_vaex['Variable Name'])
    df_vaex['Variable Name Qualifier'] = df_vaex.func.where(df_vaex['Variable Name Qualifier'] == '', None,
                                                            df_vaex['Variable Name Qualifier'])
    df_vaex['Variable Name Sub Qualifier'] = df_vaex.func.where(df_vaex['Variable Name Sub Qualifier'] == '', None,
                                                                df_vaex['Variable Name Sub Qualifier'])

    df_vaex['Variable Value'] = df_vaex.func.where(df_vaex['Variable Value'] == '', None, df_vaex['Variable Value'])

    # If we are dealing with links in the future we must format them as follows and edit the table drawer
    # if 'Link' in df.columns:
    #     df.Link = list(map(lambda x: '[Link]({})'.format(x), df.Link))
    if 'Link' in df_vaex.column_names:
        df_vaex.Link = list(map(lambda x: '[Link]({})'.format(x), df.Link))

    logging.debug("dataset {} loaded.".format(df_name))
    return df_vaex


def generate_constants(df_name, session_key):
    """Generates the constants required to be stored for the given dataset."""

    HIERARCHY_LEVELS = ['H{}'.format(i) for i in range(6)]
    df = session[session_key]
    MEASURE_TYPE_VALUES = None

    # secondary hierarchy
    SECONDARY_HIERARCHY_LEVELS = ["Variable Name", "Variable Name Qualifier", "Variable Name Sub Qualifier"]
    Variable_Name = df['Variable Name'].unique()
    Variable_Name_Qualifier = df['Variable Name Qualifier'].unique()
    Variable_Name_Sub_Qualifier = df['Variable Name Sub Qualifier'].unique()

    VARIABLE_LEVEL = 'Variable Value'  # list of variable column names

    COLUMN_NAMES = df.get_column_names()

    if df_name == 'OPG011':
        MEASURE_TYPE_OPTIONS = session["Measure_type_list"][df_name].copy()
        MEASURE_TYPE_VALUES = [get_label(x, df_name + "_Measure_type") for x in MEASURE_TYPE_OPTIONS]
        MEASURE_TYPE_OPTIONS.sort()

        min_date_unf = df['Date of Event'].dt.date.values.min()
        max_date_unf = df['Date of Event'].dt.date.values.max()
        min_date_unf = min_date_unf.astype(datetime)
        max_date_unf = max_date_unf.astype(datetime)

        # New date picker values
        GREGORIAN_MIN_YEAR = int(min_date_unf.year)
        GREGORIAN_YEAR_MAX = int(max_date_unf.year)
        GREGORIAN_QUARTER_MAX_YEAR = int(max_date_unf.year)
        GREGORIAN_QUARTER_FRINGE_MIN = int((min_date_unf.month - 1) // 3 + 1)
        GREGORIAN_QUARTER_FRINGE_MAX = int((max_date_unf.month - 1) // 3 + 1)
        GREGORIAN_MONTH_MAX_YEAR = int(max_date_unf.year)
        GREGORIAN_MONTH_FRINGE_MIN = int(min_date_unf.month)
        GREGORIAN_MONTH_FRINGE_MAX = int(max_date_unf.month)

        GREGORIAN_WEEK_AVAILABLE = True  # not currently used
        GREGORIAN_WEEK_MAX_YEAR = int(max_date_unf.year)
        GREGORIAN_WEEK_FRINGE_MIN = int(min_date_unf.strftime("%W")) + 1
        GREGORIAN_WEEK_FRINGE_MAX = int(max_date_unf.strftime("%W")) + 1

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

        options = []
        variable_option_lists = []

        df = df.to_pandas_df()
        # df['Partial Period'] = df['Partial Period'].transform(lambda x: x == 'Y')
        df['variable_name_qualifier'] = df['Variable Name'] + ' ' + df['Variable Name Qualifier']
        df['variable_name_sub_qualifier'] = df['Variable Name'] + ' ' + df['Variable Name Qualifier'] + ' ' + \
                                            df['Variable Name Sub Qualifier']
        unique_vars = df['Variable Name'].unique().tolist() + df['variable_name_qualifier'].unique().tolist() + df[
            'variable_name_sub_qualifier'].unique().tolist()

        cleaned_list = list(dict.fromkeys([x.strip() for x in unique_vars if str(x) != 'nan']))
        cleaned_list.sort()

        for unique_var in cleaned_list:
            variable_option_lists.append(unique_var)
            options.append(
                {'label': "  " * unique_var.count("|") + str(unique_var).replace('|', ', '), 'value': unique_var})

        VARIABLE_OPTIONS = options
        VARIABLE_OPTION_LISTS = variable_option_lists
        MIN_DATE_UNF = min_date_unf.strftime('%m/%d/%Y')
        MAX_DATE_UNF = max_date_unf.strftime('%m/%d/%Y')
    else:
        MEASURE_TYPE_OPTIONS = df['Measure Type'].unique()
        # New date picker values
        # filtering view of dataframe with rows that equal year
        GREGORIAN_MIN_YEAR = int(df['Year of Event'].min())
        dff = df.filter(df['Calendar Entry Type'] == 'Year')
        GREGORIAN_YEAR_MAX = int(dff['Year of Event'].max())
        dff = df.filter(df['Calendar Entry Type'] == 'Quarter')
        GREGORIAN_QUARTER_MAX_YEAR = int(dff['Year of Event'].max())
        dff = df.filter(df['Year of Event'] == GREGORIAN_MIN_YEAR)
        GREGORIAN_MONTH_FRINGE_MIN = int(df['Month of Event'].min())
        GREGORIAN_QUARTER_FRINGE_MIN = int(dff['Quarter'].min())
        dff = df.filter(df['Year of Event'] == GREGORIAN_QUARTER_MAX_YEAR)
        GREGORIAN_QUARTER_FRINGE_MAX = int(dff['Quarter'].max())
        dff = df.filter(df['Calendar Entry Type'] == 'Month')
        GREGORIAN_MONTH_MAX_YEAR = int(dff['Year of Event'].max())
        dff = df.filter(df['Year of Event'] == GREGORIAN_MONTH_MAX_YEAR)
        GREGORIAN_MONTH_FRINGE_MAX = int(dff['Month of Event'].max())

        dff = df.filter(df['Calendar Entry Type'] == 'Week')
        if int(dff.count(df['Calendar Entry Type']).min()) > 0:
            GREGORIAN_WEEK_AVAILABLE = True  # not currently used
            dff = df.filter(df['Calendar Entry Type'] == 'Week')
            GREGORIAN_WEEK_MAX_YEAR = int(dff['Year of Event'].max())
            dff = df.filter(df['Year of Event'] == GREGORIAN_MIN_YEAR)
            GREGORIAN_WEEK_FRINGE_MIN = int(dff['Week of Event'].min())
            dff = df.filter(df['Year of Event'] == GREGORIAN_WEEK_MAX_YEAR)
            GREGORIAN_WEEK_FRINGE_MAX = int(dff['Week of Event'].max())
        else:
            GREGORIAN_WEEK_AVAILABLE = False  # not currently used, so set fake values
            GREGORIAN_WEEK_MAX_YEAR = 52
            GREGORIAN_WEEK_FRINGE_MIN = 1
            GREGORIAN_WEEK_FRINGE_MAX = 52

        if len(df['Fiscal Year of Event'].unique()) != 1 and df['Fiscal Year of Event'].unique()[0] is not None:
            FISCAL_AVAILABLE = True

            FISCAL_MIN_YEAR = int(df['Fiscal Year of Event'].min())
            # filtering view of dataframe with rows that equal fiscal year
            dff = df.filter(df['Calendar Entry Type'] == 'Fiscal Year')
            FISCAL_YEAR_MAX = int(dff['Fiscal Year of Event'].max())

            dff = df.filter(df['Calendar Entry Type'] == 'Quarter')
            FISCAL_QUARTER_MAX_YEAR = int(dff['Fiscal Year of Event'].max())

            dff = df.filter(df['Fiscal Year of Event'] == FISCAL_MIN_YEAR)
            FISCAL_QUARTER_FRINGE_MIN = int(dff['Fiscal Quarter'].min())
            FISCAL_MONTH_FRINGE_MIN = int(dff['Fiscal Month of Event'].min())
            FISCAL_WEEK_FRINGE_MIN = int(dff['Fiscal Week of Event'].min())

            dff = df.filter(df['Fiscal Year of Event'] == FISCAL_QUARTER_MAX_YEAR)
            FISCAL_QUARTER_FRINGE_MAX = int(dff['Fiscal Quarter'].max())

            dff = df.filter(df['Calender Entry Type'] == 'Month')
            FISCAL_MONTH_MAX_YEAR = int(dff['Fiscal Year of Event'].max())

            dff = df.filter(df['Fiscal Year of Event'] == FISCAL_MONTH_MAX_YEAR)
            FISCAL_MONTH_FRINGE_MAX = int(dff['Fiscal Month of Event'].max())

            dff = df.filter(df['Calendar Entry Type'] == 'Week')
            FISCAL_WEEK_MAX_YEAR = int(dff['Fiscal Year of Event'].max())

            dff = df.filter(df['Fiscal Year of Event'] == FISCAL_WEEK_MAX_YEAR)
            FISCAL_WEEK_FRINGE_MAX = int(dff['Fiscal Week of Event'].max())

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

        MIN_DATE_UNF = df['Date of Event'].dt.date.values.min()
        MAX_DATE_UNF = df['Date of Event'].dt.date.values.max()
        MIN_DATE_UNF = MIN_DATE_UNF.astype(datetime).strftime('%m/%d/%Y')
        MAX_DATE_UNF = MAX_DATE_UNF.astype(datetime).strftime('%m/%d/%Y')

        # replaces all Y in Partial Period with True & False
        # df['Partial Period'] = df['Partial Period'].transform(lambda x: x == 'Y')

        # df['Partial Period'] = df.func.where(df['Partial Period'] == 'F', 'False',
        #                                                df['Partial Period'])
        # df['Partial Period'] = df.func.where(df['Partial Period'] == 'T', 'True',
        #                                      df['Partial Period'])
        # df['Partial Period'] = df['Partial Period'].astype('bool')

        # Sets the Date of Event in the df to be in the correct format for Plotly
        # df['Date of Event'] = df['Date of Event'].transform(
        #     lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))
        options = []
        variable_option_lists = []

        cleaned_list = df[VARIABLE_LEVEL].unique(dropmissing=True)
        cleaned_list.sort()

        for unique_var in cleaned_list:
            variable_option_lists.append(unique_var)
            options.append(
                {'label': "  " * unique_var .count("|") + str(unique_var).replace('|', ', '), 'value': unique_var})

        VARIABLE_OPTIONS = options
        VARIABLE_OPTION_LISTS = variable_option_lists
    storage = {
        'HIERARCHY_LEVELS': HIERARCHY_LEVELS,
        'VARIABLE_LEVEL': VARIABLE_LEVEL,
        'SECONDARY_HIERARCHY_LEVELS': SECONDARY_HIERARCHY_LEVELS,
        'Variable Name': Variable_Name,
        'Variable Name Qualifier': Variable_Name_Qualifier,
        'Variable Name Sub Qualifier': Variable_Name_Sub_Qualifier,
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
        'VARIABLE_OPTIONS': VARIABLE_OPTIONS,
        'VARIABLE_OPTION_LISTS': VARIABLE_OPTION_LISTS,
        "MEASURE_TYPE_VALUES": MEASURE_TYPE_VALUES
    }
    return storage


# ****************************************************DATE FUNCTIONS**************************************************
def last_calender_week(year):
    try:
        date.fromisocalendar(year, 53, 1)
        return 53
    except ValueError:
        return 52


def get_last_day_of_month(day):
    """Given a date returns the last day of the month."""
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


# TODO: not used but can be used for daily data in the future.
def get_week_number(day):
    """Given a date determines the week number."""
    return day.astype('datetime64[W]').astype(int)


def get_last_day_of_week(year, week_number):
    """Given a year and week number determines the last date of the week."""
    first_day_of_week = datetime.strptime(f'{year}-W{int(week_number)}-1', "%Y-W%W-%w").date()
    last_day_of_week = first_day_of_week + timedelta(days=6.9)
    return last_day_of_week


def get_last_day_of_year(year):
    """Returns the last day of a given year."""
    return date(int(year), 12, 31)


def get_month(day):
    """Given a date returns the month."""
    return day.astype('datetime64[M]').astype(int) % 12


# not use anymore
def get_months(days):
    """Given a date returns the month."""
    return days.month % 12


def get_quarter(day):
    """Given a date returns the quarter."""
    return (get_month(day) - 1) // 3 + 1


def get_date_of_quarter(quarter, year):
    """Given a year and quarter returns the last date in the quarter."""
    if quarter == 1:
        return date(year, 3, 31)
    elif quarter == 2:
        return date(year, 6, 30)
    elif quarter == 3:
        return date(year, 9, 30)
    else:
        return date(year, 12, 31)


# **********************************************DATA MANIPULATION FUNCTIONS*******************************************


def data_manipulator(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, df_name,
                     df_const, secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe,
                     fiscal_toggle, num_periods, period_type, arg_values=None, graph_type=None,
                     secondary_state_of_display=None, secondary_hierarchy_toggle=None, secondary_level_dropdown=None,
                     secondary_graph_children=None, secondary_options=None, session_key=None):
    """Returns the filtered/aggregated data frame for visualization."""
    if df_name != 'OPG011':
        filtered_df = data_hierarchy_filter(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown,
                                            hierarchy_graph_children, df_name, df_const, session_key)
        filtered_df = data_time_filter(secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe,
                                       fiscal_toggle, num_periods, period_type, df_const, filtered_df,
                                       session_key)

    else:
        df = session[session_key].copy()
        # initial hierarchy filtering (remove all children of a level to prep for agg)
        if hierarchy_toggle == 'Level Filter' or (
                (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):

            if hierarchy_toggle == 'Level Filter':
                # If anything is in the dropdown
                if hierarchy_level_dropdown:
                    # Take the level and clear the other columns
                    # Ex) H2 picked --> H3, H4, H5 get wiped
                    for i in range(len(df_const[session_key]['HIERARCHY_LEVELS']) -
                                   (int(hierarchy_level_dropdown[1]) + 1)):
                        df[df_const[session_key]['HIERARCHY_LEVELS'][len(df_const[session_key]
                                                                         ['HIERARCHY_LEVELS']) - 1 - i]] \
                           = full(len(df), nan, float64)
                else:
                    # Returns empty data frame with column names
                    df = df[0:0]
            else:
                # Filters out all rows that are less specific than given path length
                for i in range(len(hierarchy_path)):
                    df = df[df[df_const[session_key]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]

        else:
            # Filters out all rows that don't include path member at specific level
            if not hierarchy_path:
                df = df[0:0]
            else:
                for i in range(len(hierarchy_path)):
                    df = df[df[df_const[session_key]['HIERARCHY_LEVELS'][i]] == hierarchy_path[i]]

        if graph_type == "Line" or graph_type == "Scatter" or graph_type == "Bar" or graph_type == "Box_Plot":
            if graph_type == "Box_Plot":
                measure_type = arg_values[0]
            else:
                measure_type = arg_values[1]

            # checking if dataset has been filtered already for the graph types
            if hierarchy_toggle == 'Level Filter':
                if 'simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle +\
                secondary_level_dropdown + timeframe + measure_type + session_key in session and \
                        timeframe == 'all-time':
                    return session['simplified' + hierarchy_toggle + hierarchy_level_dropdown +
                                   secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + measure_type +
                                   session_key]

                elif secondary_type == 'Year' and timeframe == 'select-range' and 'simplified' + hierarchy_toggle + \
                        hierarchy_level_dropdown + secondary_hierarchy_toggle + secondary_level_dropdown + \
                        timeframe + secondary_type + str(start_year) + str(end_year) + measure_type + session_key \
                        in session:
                    return session['simplified' + hierarchy_toggle + hierarchy_level_dropdown +
                                   secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + measure_type + session_key]

                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                            'simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle + \
                            secondary_level_dropdown + timeframe + secondary_type + str(start_year) + str(end_year) + \
                            str(start_secondary) + str(end_secondary) + measure_type + session_key in session:
                    return session['simplified' + hierarchy_toggle + hierarchy_level_dropdown +
                                   secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) +
                                   measure_type + session_key]

                elif 'simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle + \
                        secondary_level_dropdown + timeframe + str(num_periods) + period_type + measure_type + \
                        session_key in session:
                    return session['simplified' + hierarchy_toggle + hierarchy_level_dropdown +
                                   secondary_hierarchy_toggle + secondary_level_dropdown + timeframe +
                                   str(num_periods) + period_type + measure_type + session_key]
            elif hierarchy_toggle == 'Specific Item' and secondary_hierarchy_toggle == 'Level Filter':
                if timeframe == 'all-time' and 'simplified' + hierarchy_toggle + str(hierarchy_path) + \
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle + \
                                   secondary_level_dropdown + timeframe + measure_type + session_key in session:
                    return session['simplified' + hierarchy_toggle + str(hierarchy_path) +
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle +
                                   secondary_level_dropdown + timeframe + measure_type + session_key]

                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                    'simplified' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + \
                    secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + secondary_type + \
                    str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) + measure_type + \
                        session_key in session:
                    return session['simplified' + hierarchy_toggle + str(hierarchy_path) +
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle +
                                   secondary_level_dropdown + timeframe + secondary_type + str(start_year) +
                                   str(end_year) + str(start_secondary) + str(end_secondary) + measure_type +
                                   session_key]

                elif secondary_type == 'Year' and timeframe == 'select-range' and 'simplified' + hierarchy_toggle + \
                    str(hierarchy_path) + str(hierarchy_graph_children) + secondary_hierarchy_toggle + \
                        secondary_level_dropdown + timeframe + secondary_type + str(start_year) + \
                        str(end_year) + measure_type + session_key in session:
                    return session['simplified' + hierarchy_toggle + str(hierarchy_path) +
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle +
                                   secondary_level_dropdown + timeframe + secondary_type + str(start_year) +
                                   str(end_year) + measure_type + session_key]

                elif timeframe == 'to-current' and 'simplified' + hierarchy_toggle + str(hierarchy_path) + \
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle + \
                            secondary_level_dropdown + timeframe + str(num_periods) + period_type + measure_type + \
                            session_key in session:
                    return session['simplified' + hierarchy_toggle + str(hierarchy_path) +
                                   str(hierarchy_graph_children) + secondary_hierarchy_toggle +
                            secondary_level_dropdown + timeframe + str(num_periods) + period_type + measure_type +
                                   session_key]

            filtered_df = data_time_aggregator_simplified(hierarchy_path, secondary_type, end_secondary, end_year,
                                                          start_secondary, start_year, timeframe, fiscal_toggle,
                                                          num_periods, period_type, df_const, arg_values,
                                                          graph_type, df, hierarchy_toggle, hierarchy_level_dropdown,
                                                          hierarchy_graph_children, secondary_state_of_display,
                                                          secondary_hierarchy_toggle, secondary_level_dropdown,
                                                          secondary_graph_children, secondary_options, session_key)
        elif graph_type == 'Bubble':
            # checking if dataset has been filtered already
            if hierarchy_toggle == 'Level Filter':
                if 'bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + session_key in session and \
                        timeframe == 'all-time':
                    return session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + session_key]
                elif secondary_type == 'Year' and timeframe == 'select-range' and 'bubble' + hierarchy_toggle + \
                        hierarchy_level_dropdown + timeframe + secondary_type + str(start_year) + \
                        str(end_year) + session_key in session:
                    return session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + session_key]
                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                            'bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +\
                            str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) + session_key \
                        in session:
                    return session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) +
                                   session_key]
                elif 'bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + str(num_periods) + \
                        period_type + session_key in session:
                    return session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe +
                                   str(num_periods) + period_type + session_key]
            elif hierarchy_toggle == 'Specific Item':
                if 'bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + \
                        timeframe + session_key in session and timeframe == 'all-time':
                    return session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + session_key]
                elif secondary_type == 'Year' and timeframe == 'select-range' and 'bubble' + hierarchy_toggle + \
                        str(hierarchy_path) + str(hierarchy_graph_children) + timeframe + secondary_type + \
                        str(start_year) + str(end_year) + session_key in session:
                    return session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + secondary_type + str(start_year) + str(end_year) + session_key]
                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                        'bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + \
                        timeframe + secondary_type + str(start_year) + str(end_year) + str(start_secondary) + \
                        str(end_secondary) + session_key in session:
                    return session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + secondary_type + str(start_year) + str(end_year) + str(start_secondary) +
                                   str(end_secondary) + session_key]
                elif 'bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe + \
                        str(num_periods) + period_type + session_key in session:
                    return session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + str(num_periods) + period_type + session_key]

            filtered_df = data_time_bubble_aggregator(hierarchy_path, secondary_type, end_secondary, end_year,
                                                      start_secondary, start_year, timeframe, fiscal_toggle,
                                                      num_periods, period_type, df_name, df_const, df, hierarchy_toggle,
                                                      hierarchy_level_dropdown, hierarchy_graph_children, session_key)
        else:
            # checking if dataset has been filtered already
            if hierarchy_toggle == 'Level Filter':
                if 'table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + session_key in session and \
                        timeframe == 'all-time':
                    return session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + session_key]
                elif secondary_type == 'Year' and timeframe == 'select-range' and 'table' + hierarchy_toggle + \
                        hierarchy_level_dropdown + timeframe + secondary_type + str(start_year) + \
                        str(end_year) + session_key in session:
                    return session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + session_key]
                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                            'table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +\
                            str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) + session_key \
                        in session:
                    return session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                                   str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) +
                                   session_key]
                elif 'table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + str(num_periods) + \
                        period_type + session_key in session:
                    return session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe +
                                   str(num_periods) + period_type + session_key]

            elif hierarchy_toggle == 'Specific Item':
                if 'table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + \
                        timeframe in session and timeframe == 'all-time':
                    return session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + session_key]
                elif secondary_type == 'Year' and timeframe == 'select-range' and 'table' + hierarchy_toggle + \
                        str(hierarchy_path) + str(hierarchy_graph_children) + timeframe + secondary_type + \
                        str(start_year) + str(end_year) in session:
                    return session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + secondary_type + str(start_year) + str(end_year) + session_key]
                elif timeframe == 'select-range' and secondary_type != 'Year' and secondary_type is not None and \
                        'table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe + \
                        secondary_type + str(start_year) + str(end_year) + str(start_secondary) + \
                        str(end_secondary) + session_key in session:
                    return session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + secondary_type + str(start_year) + str(end_year) + str(start_secondary) +
                                   str(end_secondary) + session_key]
                elif 'table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe + \
                        str(num_periods) + period_type + session_key in session:
                    return session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                                   timeframe + str(num_periods) + period_type + session_key]

            filtered_df = data_time_aggregator(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary,
                                               start_year, timeframe, fiscal_toggle, num_periods, period_type, df_name,
                                               df_const, df, hierarchy_toggle, hierarchy_level_dropdown,
                                               hierarchy_graph_children, session_key)

    return filtered_df


def data_hierarchy_filter(hierarchy_path, hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, df_name,
                          df_const, session_key):
    """Returns filtered the data frame based on hierarchy selections."""
    # NOTE: This assumes hierarchy path is a list of all previously selected levels

    if hierarchy_toggle == 'Level Filter' or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
        filtered_df = session[session_key]
        if hierarchy_toggle == 'Level Filter':
            # If anything is in the dropdown
            if hierarchy_level_dropdown:
                # Filter based on hierarchy level
                filtered_df = filtered_df.filter(filtered_df[hierarchy_level_dropdown].notna())
                for i in range(len(df_const[session_key]['HIERARCHY_LEVELS']) - (int(hierarchy_level_dropdown[1]) + 1)):
                    filtered_df = filtered_df.filter(filtered_df[df_const[session_key]['HIERARCHY_LEVELS'][
                        len(df_const[session_key]['HIERARCHY_LEVELS']) - 1 - i]].ismissing())
            else:
                # Returns empty data frame with column names
                filtered_df = filtered_df[0:0]
        else:
            # Filters out all rows that are less specific than given path length
            for i in range(len(hierarchy_path)):
                filtered_df = filtered_df.filter(filtered_df[df_const[session_key]
                                                 ['HIERARCHY_LEVELS'][i]] == hierarchy_path[i])
            # Filters out all rows that are more specific than given path length plus one to preserve the child column
            for i in range(len(df_const[session_key]['HIERARCHY_LEVELS']) - (len(hierarchy_path) + 1)):
                filtered_df = filtered_df.filter(filtered_df[df_const[session_key]['HIERARCHY_LEVELS'][
                                                    len(df_const[session_key]['HIERARCHY_LEVELS'])
                                                    - 1 - i]].ismissing())
            filtered_df = filtered_df.filter(filtered_df[df_const[session_key]['HIERARCHY_LEVELS']
                                                                                        [len(hierarchy_path)]].notna())
    else:
        filtered_df = session[df_name]
        # Filters out all rows that don't include path member at specific level
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df.filter(filtered_df[df_const[session_key]['HIERARCHY_LEVELS'][i]] ==
                                             hierarchy_path[i])
        # Filters out all rows that are more specific than given path
        for i in range(len(df_const[session_key]['HIERARCHY_LEVELS']) - len(hierarchy_path)):
            filtered_df = filtered_df.filter(filtered_df[df_const[session_key]['HIERARCHY_LEVELS'][
                len(df_const[session_key]['HIERARCHY_LEVELS']) - 1 - i]].ismissing())

    return filtered_df


def data_time_filter(secondary_type, end_secondary, end_year, start_secondary, start_year, timeframe, fiscal_toggle,
                     num_periods, period_type, df_const, filtered_df, session_key):
    """Returns filtered data frame dependent on date picker selections."""
    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[session_key]['FISCAL_MIN_YEAR']
            end_year = df_const[session_key]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[session_key]['GREGORIAN_MIN_YEAR']
            end_year = df_const[session_key]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

    filtered_df = filtered_df.to_pandas_df()
    date_type = '{}Year of Event'.format(year_prefix)
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
        time_df = filtered_df[filtered_df['Calendar Entry Type'] == current_filter]

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date]
        time_df = time_df[time_df['Date of Event'] <= end_date]

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        # Data frame filtered to be in inputted year range
        time_df = filtered_df[filtered_df[date_type] >= int(start_year)]
        time_df = time_df[time_df[date_type] <= end_year]
        time_df = time_df[time_df['Calendar Entry Type'] == secondary_type]  # Filters out unused calender values

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
            range_df = time_df[time_df[date_type] == start_year]
            range_df = range_df[range_df[division_column] >= start_secondary]

            for i in range(end_year - start_year - 1):
                # Include entirety of in-between years
                range_df = range_df.append(
                    time_df[time_df[date_type] == (start_year + i + 1)])

            # Filter end year below threshold
            time_df = time_df[time_df[date_type] == end_year]
            time_df = time_df[time_df[division_column] < end_secondary]
            range_df = range_df.append(time_df)
            # Update working df
            time_df = range_df
    else:
        # Data frame filtered to be in inputted year range
        time_df = filtered_df[filtered_df[date_type] >= start_year]
        time_df = time_df[time_df[date_type] <= end_year - 1]
        # Filters out month and quarter values (whole year)
        time_df = time_df[time_df['Calendar Entry Type'] == '{}Year'.replace("{}", year_prefix)]

    return time_df


def data_time_bubble_aggregator(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                         timeframe, fiscal_toggle, num_periods, period_type, df_name, df_const, filtered_df,
                         hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, session_key):
    """
    Returns aggregated data frame dependent on date picker selections, hierarchy selection and graph type selection.
    This aggregator does not filter based on measure type.
    """
    filtered_df = filtered_df.to_pandas_df()

    if filtered_df.empty:
        return filtered_df

    measure_types = session["Measure_type_list"][df_name].copy()
    variable_names = df_const[session_key]['VARIABLE_OPTION_LISTS']
    row_list = []

    if hierarchy_toggle == "Level Filter" or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
        if hierarchy_toggle == "Level Filter":
            specific_items = get_hierarchy(hierarchy_level_dropdown)
        else:
            specific_items = get_hierarchy("H" + str(len(hierarchy_path)))
    elif hierarchy_path:
        specific_items = ['specific item']
    else:
        time_df = DataFrame(row_list,
                            columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                     'Variable Value',
                                     'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                     'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                     'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                     'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                     'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        return time_df

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[session_key]['FISCAL_MIN_YEAR']
            end_year = df_const[session_key]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[session_key]['GREGORIAN_MIN_YEAR']
            end_year = df_const[session_key]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

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
        if current_filter != 'Week':
            # Builds data based on all measure types, variable names, hierarchy, and selected time frame
            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = filtered_df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = filtered_df[
                            filtered_df["H" + str(len(hierarchy_path))] == specific_item]
                # Builds data based on all measure types, variable names, and selected time frame
                for measure_type in measure_types:
                    measure_type_name = get_label(measure_type, df_name + "_Measure_type")
                    for variable_name in variable_names:
                        # filter on either the variable name or variable value column
                        if variable_name in df_const[session_key]['Variable Name']:
                            reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                        else:
                            reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                        for z in range(end_date.year - start_date.year + 1):
                            year = start_date.year + z
                            yearly_data = reduced_df[reduced_df["Date of Event"].dt.year == year]
                            if current_filter == "Year":
                                unique_dates = yearly_data["Date of Event"].dt.year.unique()
                            elif current_filter == "Month":
                                unique_dates = yearly_data["Date of Event"].dt.month.unique()
                            else:  # current_filter == "Quarter":
                                yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                                unique_dates = yearly_data["Quarter"].unique()
                            year_of_event = year
                            quarter = nan
                            month_of_event = nan
                            week_of_event = nan
                            for unique_date in unique_dates:
                                if current_filter == 'Year':
                                    unique_data = yearly_data[yearly_data["Date of Event"].dt.year == unique_date]
                                    date_of_event = get_last_day_of_year(year)
                                elif current_filter == 'Quarter':
                                    unique_data = yearly_data[yearly_data["Quarter"] == unique_date]
                                    date_of_event = get_date_of_quarter(unique_date, year)
                                    quarter = unique_date
                                else:
                                    unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_date]
                                    date_of_event = get_last_day_of_month(date(year, int(unique_date), 1))
                                    quarter = get_quarter(unique_date)
                                    month_of_event = unique_date

                                if hierarchy_toggle == "Level Filter" or (
                                        (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                            'graph_children'])):
                                    h0 = unique_data['H0'].values[0]
                                    h1 = unique_data['H1'].values[0]
                                    h2 = unique_data['H2'].values[0]
                                    h3 = unique_data['H3'].values[0]
                                    h4 = unique_data['H4'].values[0]
                                    h5 = unique_data['H5'].values[0]
                                else:
                                    h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                    h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                    h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                    h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                    h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                    h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                                measure_value = unique_data[measure_type].sum()

                                row_list.append(
                                    [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                     h0, h1, h2, h3, h4, h5,
                                     variable_name,
                                     unique_data['Variable Name'].iloc[0],
                                     unique_data['Variable Name Qualifier'].iloc[0],
                                     unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event,
                                     current_filter, year_of_event, quarter, month_of_event, week_of_event, nan,
                                     nan, nan, nan, nan, nan, measure_value,
                                     measure_type_name,
                                     True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Value',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        # Creates a copy of the filtered data frame that just contains the weekly data
        else:  # elif df_name == "OPG011" and current_filter == 'Week':
            # Builds data based on all measure types, variable names, and selected time frame
            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = filtered_df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = filtered_df[
                            filtered_df["H" + str(len(hierarchy_path))] == specific_item]
                for measure_type in measure_types:
                    measure_type_name = get_label(measure_type, df_name + "_Measure_type")
                    for variable_name in variable_names:
                        # filter on either the variable name or variable value column
                        if variable_name in df_const[session_key]['Variable Name']:
                            reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                        else:
                            reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                        for z in range(end_date.year - start_date.year + 1):
                            year = start_date.year + z
                            yearly_data = reduced_df[reduced_df["Date of Event"].dt.year == year]
                            unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                            year_of_event = year
                            for unique_date in unique_dates:
                                unique_secondary = unique_date
                                unique_data = yearly_data[
                                    yearly_data["Date of Event"].dt.isocalendar().week == unique_secondary]
                                date_of_event = get_last_day_of_week(year, unique_secondary)
                                quarter = get_quarter(unique_date)
                                month_of_event = get_month(unique_date)
                                week_of_event = unique_secondary
                                measure_value = unique_data[measure_type].sum()

                                if hierarchy_toggle == "Level Filter" or (
                                        (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                            'graph_children'])):
                                    h0 = unique_data['H0'].values[0]
                                    h1 = unique_data['H1'].values[0]
                                    h2 = unique_data['H2'].values[0]
                                    h3 = unique_data['H3'].values[0]
                                    h4 = unique_data['H4'].values[0]
                                    h5 = unique_data['H5'].values[0]
                                else:
                                    h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                    h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                    h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                    h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                    h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                    h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                                row_list.append(
                                    [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                     h0, h1, h2, h3, h4, h5,
                                     variable_name,
                                     unique_data['Variable Name'].iloc[0],
                                     unique_data['Variable Name Qualifier'].iloc[0],
                                     unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event,
                                     current_filter, year_of_event, quarter, month_of_event, week_of_event,
                                     nan, nan, nan, nan, nan, nan, measure_value, measure_type_name,
                                     True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Value',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= datetime64(start_date.date())]
        time_df = time_df[time_df['Date of Event'] <= datetime64(end_date.date())]

        if hierarchy_toggle == "Level Filter":
            session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe +
                    str(num_periods) + period_type] = time_df
        else:
            session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                    str(num_periods) + period_type] = time_df

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        for specific_item in specific_items:
            if specific_item == "specific item":
                further_filtered_df = filtered_df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = filtered_df[filtered_df["H" + str(len(hierarchy_path))] == specific_item]
            for measure_type in measure_types:
                measure_type_name = get_label(measure_type, df_name + "_Measure_type")
                for variable_name in variable_names:
                    # filter on either the variable name or variable value column
                    if variable_name in df_const[session_key]['Variable Name']:
                        further_reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                    else:
                        further_reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                    for z in range(end_year - start_year + 1):
                        year = start_year + z
                        yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                        if secondary_type == "Month":
                            unique_dates = yearly_data["Date of Event"].dt.month.unique()
                        elif secondary_type == "Week":
                            unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                        else:  # secondary_type == "Quarter"
                            yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                            unique_dates = yearly_data["Quarter"].unique()
                        month = nan
                        week = nan
                        for unique_date in unique_dates:
                            if secondary_type == 'Quarter':
                                secondary = unique_date
                                quarter = secondary
                                unique_data = yearly_data[yearly_data["Quarter"] == secondary]
                                date_of_event = get_date_of_quarter(secondary, year)
                            elif secondary_type == "Week":
                                secondary = unique_date
                                unique_data = yearly_data[
                                    yearly_data["Date of Event"].dt.isocalendar().week == secondary]
                                date_of_event = get_last_day_of_week(year, secondary)
                                quarter = get_quarter(unique_date)
                                month = get_month(unique_date)
                                week = secondary
                            else:
                                secondary = unique_date
                                quarter = get_quarter(unique_date)
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.month == secondary]
                                date_of_event = get_last_day_of_month(date(year, int(secondary), 1))
                                month = secondary

                            measure_value = unique_data[measure_type].sum()

                            if hierarchy_toggle == "Level Filter" or (
                                    (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                        'graph_children'])):
                                h0 = unique_data['H0'].values[0]
                                h1 = unique_data['H1'].values[0]
                                h2 = unique_data['H2'].values[0]
                                h3 = unique_data['H3'].values[0]
                                h4 = unique_data['H4'].values[0]
                                h5 = unique_data['H5'].values[0]
                            else:
                                h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 h0, h1, h2, h3, h4, h5,
                                 variable_name,
                                 unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, secondary_type,
                                 year, quarter, month, week, nan, nan, nan, nan, nan, nan,
                                 measure_value, measure_type_name,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
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
                range_df = pd.concat([range_df, time_df[time_df['{}Year of Event'.format(year_prefix)] ==
                                                                                                (start_year + i + 1)]])

            # Filter end year below threshold
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] == end_year]
            time_df = time_df[time_df[division_column] < end_secondary]
            range_df = pd.concat([range_df, time_df])

            # Update working df
            time_df = range_df

        if hierarchy_toggle == 'Level Filter':
            if timeframe == 'all-time':
                session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe] = time_df
            else:
                session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                        str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary)] = time_df
        else:
            if timeframe == 'all-time':
                session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                        timeframe] = time_df

            else:
                session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                        secondary_type + str(start_year) + str(end_year) + str(start_secondary) +
                        str(end_secondary)] = time_df

    else:
        for specific_item in specific_items:
            if specific_item == "specific item":
                further_filtered_df = filtered_df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = filtered_df[filtered_df["H" + str(len(hierarchy_path))] == specific_item]
            for measure_type in measure_types:
                measure_type_name = get_label(measure_type, df_name+"_Measure_type")
                for variable_name in variable_names:
                    # filter on either the variable name or variable value column
                    if variable_name in df_const[session_key]['Variable Name']:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                    else:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                    unique_secondarys = reduced_df['Date of Event'].dt.year.unique()
                    for unique_secondary in unique_secondarys:
                        secondary = unique_secondary
                        unique_data = reduced_df[reduced_df['Date of Event'].dt.year == secondary]
                        measure_value = unique_data[measure_type].sum()
                        date_of_event = get_last_day_of_year(secondary)

                        if hierarchy_toggle == "Level Filter" or (
                                (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                    'graph_children'])):
                            h0 = unique_data['H0'].values[0]
                            h1 = unique_data['H1'].values[0]
                            h2 = unique_data['H2'].values[0]
                            h3 = unique_data['H3'].values[0]
                            h4 = unique_data['H4'].values[0]
                            h5 = unique_data['H5'].values[0]

                        else:
                            h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                            h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                            h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                            h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                            h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                            h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                        row_list.append(
                            [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                             h0, h1, h2, h3, h4, h5,
                             variable_name,
                             unique_data['Variable Name'].iloc[0],
                             unique_data['Variable Name Qualifier'].iloc[0],
                             unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, "Year",
                             secondary, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                             measure_value, measure_type_name,
                             True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
                                        'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                        'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                        'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                        'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                        'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        if hierarchy_toggle == "Level Filter":
            session['bubble' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                    str(start_year) + str(end_year)] = time_df

        else:
            session['bubble' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                    secondary_type + str(start_year) + str(end_year)] = time_df

    return time_df


def data_time_aggregator(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                         timeframe, fiscal_toggle, num_periods, period_type, df_name, df_const, filtered_df,
                         hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, session_key):
    """
    Returns aggregated data frame dependent on date picker selections, hierarchy selection and graph type selection.
    This aggregator does not filter based on measure type.
    """
    filtered_df = filtered_df.to_pandas_df()

    if filtered_df.empty:
        return filtered_df

    measure_types = session["Measure_type_list"][df_name].copy()
    variable_names = df_const[session_key]['VARIABLE_OPTION_LISTS']
    row_list = []

    if hierarchy_toggle == "Level Filter" or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
        if hierarchy_toggle == "Level Filter":
            specific_items = get_hierarchy(hierarchy_level_dropdown)
        else:
            specific_items = get_hierarchy("H" + str(len(hierarchy_path)))
    elif hierarchy_path:
        specific_items = ['specific item']
    else:
        time_df = DataFrame(row_list,
                            columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                     'Variable Value',
                                     'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                     'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                     'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                     'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                     'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        return time_df

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[session_key]['FISCAL_MIN_YEAR']
            end_year = df_const[session_key]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[session_key]['GREGORIAN_MIN_YEAR']
            end_year = df_const[session_key]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

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
        if current_filter != 'Week':
            # Builds data based on all measure types, variable names, hierarchy, and selected time frame
            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = filtered_df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = filtered_df[
                            filtered_df["H" + str(len(hierarchy_path))] == specific_item]
                # Builds data based on variable names, and selected time frame
                for variable_name in variable_names:
                    # filter on either the variable name or variable value column
                    if variable_name in df_const[session_key]['Variable Name']:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                    else:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        yearly_data = reduced_df[reduced_df["Date of Event"].dt.year == year]
                        if current_filter == "Year":
                            unique_dates = yearly_data["Date of Event"].dt.year.unique()
                        elif current_filter == "Month":
                            unique_dates = yearly_data["Date of Event"].dt.month.unique()
                        else:  # current_filter == "Quarter":
                            yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                            unique_dates = yearly_data["Quarter"].unique()
                        year_of_event = year
                        quarter = nan
                        month_of_event = nan
                        week_of_event = nan
                        for unique_date in unique_dates:
                            if current_filter == 'Year':
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.year == unique_date]
                                date_of_event = get_last_day_of_year(year)
                            elif current_filter == 'Quarter':
                                unique_data = yearly_data[yearly_data["Quarter"] == unique_date]
                                date_of_event = get_date_of_quarter(unique_date, year)
                                quarter = unique_date
                            else:
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_date]
                                date_of_event = get_last_day_of_month(date(year, int(unique_date), 1))
                                quarter = get_quarter(unique_date)
                                month_of_event = unique_date

                            if hierarchy_toggle == "Level Filter" or (
                                    (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                        'graph_children'])):
                                h0 = unique_data['H0'].values[0]
                                h1 = unique_data['H1'].values[0]
                                h2 = unique_data['H2'].values[0]
                                h3 = unique_data['H3'].values[0]
                                h4 = unique_data['H4'].values[0]
                                h5 = unique_data['H5'].values[0]
                            else:
                                h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                            count = unique_data[measure_types[0]].sum()
                            dollar = unique_data[measure_types[1]].sum()
                            duration = unique_data[measure_types[2]].sum()

                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 h0, h1, h2, h3, h4, h5,
                                 variable_name,
                                 unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event,
                                 current_filter, year_of_event, quarter, month_of_event, week_of_event, nan,
                                 nan, nan, nan, nan, nan, count, dollar, duration,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Value',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Count', 'Dollar', 'Duration', 'Partial Period'])

        # Creates a copy of the filtered data frame that just contains the weekly data
        else:  # elif df_name == "OPG011" and current_filter == 'Week':
            # Builds data based on all measure types, variable names, and selected time frame
            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = filtered_df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = filtered_df[
                            filtered_df["H" + str(len(hierarchy_path))] == specific_item]
                for variable_name in variable_names:
                    # filter on either the variable name or variable value column
                    if variable_name in df_const[session_key]['Variable Name']:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                    else:
                        reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        yearly_data = reduced_df[reduced_df["Date of Event"].dt.year == year]
                        unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                        year_of_event = year
                        for unique_date in unique_dates:
                            unique_secondary = unique_date
                            unique_data = yearly_data[
                                yearly_data["Date of Event"].dt.isocalendar().week == unique_secondary]
                            date_of_event = get_last_day_of_week(year, unique_secondary)
                            quarter = get_quarter(unique_date)
                            month_of_event = get_month(unique_date)
                            week_of_event = unique_secondary
                            count = unique_data[measure_types[0]].sum()
                            dollar = unique_data[measure_types[1]].sum()
                            duration = unique_data[measure_types[2]].sum()

                            if hierarchy_toggle == "Level Filter" or (
                                    (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                        'graph_children'])):
                                h0 = unique_data['H0'].values[0]
                                h1 = unique_data['H1'].values[0]
                                h2 = unique_data['H2'].values[0]
                                h3 = unique_data['H3'].values[0]
                                h4 = unique_data['H4'].values[0]
                                h5 = unique_data['H5'].values[0]
                            else:
                                h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 h0, h1, h2, h3, h4, h5,
                                 variable_name,
                                 unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event,
                                 current_filter, year_of_event, quarter, month_of_event, week_of_event,
                                 nan, nan, nan, nan, nan, nan, count, dollar, duration,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Value',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= datetime64(start_date.date())]
        time_df = time_df[time_df['Date of Event'] <= datetime64(end_date.date())]

        if hierarchy_toggle == "Level Filter":
            session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe +
            str(num_periods) + period_type] = time_df
        else:
            session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                    str(num_periods) + period_type + session_key] = time_df

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        for specific_item in specific_items:
            if specific_item == "specific item":
                further_filtered_df = filtered_df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = filtered_df[filtered_df["H" + str(len(hierarchy_path))] == specific_item]
            for variable_name in variable_names:
                # filter on either the variable name or variable value column
                if variable_name in df_const[session_key]['Variable Name']:
                    further_reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                else:
                    further_reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                for z in range(end_year - start_year + 1):
                    year = start_year + z
                    yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                    if secondary_type == "Month":
                        unique_dates = yearly_data["Date of Event"].dt.month.unique()
                    elif secondary_type == "Week":
                        unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                    else:  # secondary_type == "Quarter"
                        yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                        unique_dates = yearly_data["Quarter"].unique()
                    month = nan
                    week = nan
                    for unique_date in unique_dates:
                        if secondary_type == 'Quarter':
                            secondary = unique_date
                            quarter = secondary
                            unique_data = yearly_data[yearly_data["Quarter"] == secondary]
                            date_of_event = get_date_of_quarter(secondary, year)
                        elif secondary_type == "Week":
                            secondary = unique_date
                            unique_data = yearly_data[
                                yearly_data["Date of Event"].dt.isocalendar().week == secondary]
                            date_of_event = get_last_day_of_week(year, secondary)
                            quarter = get_quarter(unique_date)
                            month = get_month(unique_date)
                            week = secondary
                        else:
                            secondary = unique_date
                            quarter = get_quarter(unique_date)
                            unique_data = yearly_data[yearly_data["Date of Event"].dt.month == secondary]
                            date_of_event = get_last_day_of_month(date(year, int(secondary), 1))
                            month = secondary

                        count = unique_data[measure_types[0]].sum()
                        dollar = unique_data[measure_types[1]].sum()
                        duration = unique_data[measure_types[2]].sum()

                        if hierarchy_toggle == "Level Filter" or (
                                (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                    'graph_children'])):
                            h0 = unique_data['H0'].values[0]
                            h1 = unique_data['H1'].values[0]
                            h2 = unique_data['H2'].values[0]
                            h3 = unique_data['H3'].values[0]
                            h4 = unique_data['H4'].values[0]
                            h5 = unique_data['H5'].values[0]
                        else:
                            h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                            h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                            h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                            h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                            h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                            h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                        row_list.append(
                            [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                             h0, h1, h2, h3, h4, h5,
                             variable_name,
                             unique_data['Variable Name'].iloc[0],
                             unique_data['Variable Name Qualifier'].iloc[0],
                             unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, secondary_type,
                             year, quarter, month, week, nan, nan, nan, nan, nan, nan,
                             count, dollar, duration,
                             True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
                                        'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                        'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                        'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                        'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                        'Activity Event Id', 'Count', 'Dollar', 'Duration', 'Partial Period'])

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
                range_df = pd.concat([range_df, time_df[time_df['{}Year of Event'.format(year_prefix)] ==
                                                                                                (start_year + i + 1)]])

            # Filter end year below threshold
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] == end_year]
            time_df = time_df[time_df[division_column] < end_secondary]
            range_df = pd.concat([range_df, time_df])

            # Update working df
            time_df = range_df
        if hierarchy_toggle == 'Level Filter':
            if timeframe == 'all-time':
                session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe] = time_df
            else:
                session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                        str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) +
                        session_key] = time_df
        else:
            if timeframe == 'all-time':
                session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                        timeframe + session_key] = time_df

            else:
                session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                        secondary_type + str(start_year) + str(end_year) + str(start_secondary) +
                        str(end_secondary) + session_key] = time_df

    else:
        for specific_item in specific_items:
            if specific_item == "specific item":
                further_filtered_df = filtered_df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = filtered_df[filtered_df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = filtered_df[filtered_df["H" + str(len(hierarchy_path))] == specific_item]
            for variable_name in variable_names:
                # filter on either the variable name or variable value column
                if variable_name in df_const[session_key]['Variable Name']:
                    reduced_df = further_filtered_df[further_filtered_df['Variable Name'] == variable_name]
                else:
                    reduced_df = further_filtered_df[further_filtered_df['Variable Value'] == variable_name]
                unique_secondarys = reduced_df['Date of Event'].dt.year.unique()
                for unique_secondary in unique_secondarys:
                    secondary = unique_secondary
                    unique_data = reduced_df[reduced_df['Date of Event'].dt.year == secondary]
                    date_of_event = get_last_day_of_year(secondary)
                    count = unique_data[measure_types[0]].sum()
                    dollar = unique_data[measure_types[1]].sum()
                    duration = unique_data[measure_types[2]].sum()

                    if hierarchy_toggle == "Level Filter" or (
                            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                'graph_children'])):
                        h0 = unique_data['H0'].values[0]
                        h1 = unique_data['H1'].values[0]
                        h2 = unique_data['H2'].values[0]
                        h3 = unique_data['H3'].values[0]
                        h4 = unique_data['H4'].values[0]
                        h5 = unique_data['H5'].values[0]

                    else:
                        h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                        h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                        h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                        h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                        h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                        h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                    row_list.append(
                        [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                         h0, h1, h2, h3, h4, h5,
                         variable_name,
                         unique_data['Variable Name'].iloc[0],
                         unique_data['Variable Name Qualifier'].iloc[0],
                         unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, "Year",
                         secondary, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                         count, dollar, duration,
                         True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
                                        'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                        'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                        'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                        'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                        'Activity Event Id', 'Count', 'Dollar', 'Duration', 'Partial Period'])

        if hierarchy_toggle == "Level Filter":
            session['table' + hierarchy_toggle + hierarchy_level_dropdown + timeframe + secondary_type +
                    str(start_year) + str(end_year) + session_key] = time_df

        else:
            session['table' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) + timeframe +
                    secondary_type + str(start_year) + str(end_year) + session_key] = time_df
    return time_df


def data_time_aggregator_simplified(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary,
                                    start_year, timeframe, fiscal_toggle, num_periods, period_type, df_const,
                                    arg_values, graph_type, df, hierarchy_toggle, hierarchy_level_dropdown,
                                    hierarchy_graph_children, secondary_path, secondary_hierarchy_toggle,
                                    secondary_level_dropdown, secondary_graph_children, secondary_options, session_key):
    """
    Returns aggregated data frame dependent on date picker selections, hierarchy selection and graph type selection.
    This aggregator does filter based on measure type to be used for figures that do not require all measure types to
    avoid aggregating unnecessary data.
    """
    df = df.to_pandas_df()

    if df.empty:
        return df

    if secondary_hierarchy_toggle == 'Level Filter':
        variable_names = df_const[session_key][secondary_level_dropdown]
    elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
        variable_names = [option['label'] for option in secondary_options]
    else:
        variable_names = [secondary_path[-1] if secondary_path != [] else None]

    if variable_names[0] is None:
        return df[0:0]
    elif graph_type == "Box_Plot":
        measure_type = arg_values[0]
    else:
        measure_type = arg_values[1]

    row_list = []

    if hierarchy_toggle == "Level Filter":
        specific_items = get_hierarchy(hierarchy_level_dropdown)
    elif hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        specific_items = get_hierarchy("H" + str(len(hierarchy_path)))
    elif hierarchy_path:
        specific_items = ['specific item']
    else:
        time_df = DataFrame(row_list,
                            columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                     'Variable Value',
                                     'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                     'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                     'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                     'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                     'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])
        return time_df

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle == 'Fiscal':
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle == 'Fiscal':
            start_year = df_const[session_key]['FISCAL_MIN_YEAR']
            end_year = df_const[session_key]['FISCAL_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['FISCAL_MONTH_FRINGE_MAX'] + 1
        else:  # year_type == 'Gregorian'
            start_year = df_const[session_key]['GREGORIAN_MIN_YEAR']
            end_year = df_const[session_key]['GREGORIAN_MONTH_MAX_YEAR']
            start_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MIN']
            end_secondary = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MAX'] + 1

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
        if current_filter != 'Week':
            # Builds data based on hierarchy, variable names, and selected time frame

            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = df[df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = df[df["H" + str(len(hierarchy_path))] == specific_item]

                for variable_name in variable_names:

                    # filters on secondary hierarchy
                    if secondary_hierarchy_toggle == "Level Filter":
                        further_reduced_df = further_filtered_df[further_filtered_df[secondary_level_dropdown] ==
                                                                 variable_name]
                    elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == [
                                                                                                    'graph_children']:
                        further_reduced_df = further_filtered_df[
                                further_filtered_df[df_const[session_key]['SECONDARY_HIERARCHY_LEVELS']
                                [len(secondary_path)]] == variable_name]
                    else:
                        further_reduced_df = further_filtered_df[
                                further_filtered_df[df_const[session_key]['SECONDARY_HIERARCHY_LEVELS']
                                [len(secondary_path)-1]] == variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                        if current_filter == "Year":
                            unique_dates = yearly_data["Date of Event"].dt.year.unique()
                        elif current_filter == "Month":
                            unique_dates = yearly_data["Date of Event"].dt.month.unique()
                        else:  # current_filter == "Quarter":
                            yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                            unique_dates = yearly_data["Quarter"].unique()
                        year_of_event = year
                        quarter = nan
                        month_of_event = nan
                        week_of_event = nan
                        for unique_date in unique_dates:
                            if current_filter == 'Year':
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.year == unique_date]
                                date_of_event = get_last_day_of_year(year)
                            elif current_filter == 'Quarter':
                                unique_data = yearly_data[yearly_data["Quarter"] == unique_date]
                                date_of_event = get_date_of_quarter(unique_date, year)
                                quarter = unique_date
                            else:
                                unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_date]
                                date_of_event = get_last_day_of_month(date(year, int(unique_date), 1))
                                quarter = get_quarter(unique_date)
                                month_of_event = unique_date

                            if hierarchy_toggle == "Level Filter" or (
                                    (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                        'graph_children'])):
                                h0 = unique_data['H0'].values[0]
                                h1 = unique_data['H1'].values[0]
                                h2 = unique_data['H2'].values[0]
                                h3 = unique_data['H3'].values[0]
                                h4 = unique_data['H4'].values[0]
                                h5 = unique_data['H5'].values[0]

                            else:
                                h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                            measure_value = unique_data[measure_type].sum()

                            row_list.append(
                                [unique_data['OPG Data Set'].iloc[0], unique_data['Hierarchy One Name'].iloc[0],
                                 h0, h1, h2, h3, h4, h5,
                                 unique_data['Variable Value'].iloc[0],
                                 unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, current_filter,
                                 year_of_event, quarter, month_of_event, week_of_event, nan, nan, nan,
                                 nan, nan, nan, measure_value, measure_type,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                   columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                            'Variable Value',
                                            'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                            'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                            'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                            'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                            'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        # Creates a copy of the filtered data frame that just contains the weekly data
        else:  # elif df_name == "OPG011" and current_filter == 'Week':
            # Builds data based on all measure types, variable names, and selected time frame

            for specific_item in specific_items:
                if specific_item == "specific item":
                    further_filtered_df = df
                elif hierarchy_toggle == "Level Filter":
                    further_filtered_df = df[df[hierarchy_level_dropdown] == specific_item]
                else:
                    further_filtered_df = df[df["H" + str(len(hierarchy_path))] == specific_item]

                for variable_name in variable_names:
                    # filters on secondary hierarchy
                    if secondary_hierarchy_toggle == "Level Filter":
                        further_reduced_df = further_filtered_df[further_filtered_df[secondary_level_dropdown] ==
                                                                 variable_name]
                    elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == \
                                                                                                    ['graph_children']:
                        further_reduced_df = further_filtered_df[
                                further_filtered_df[df_const[session_key]['SECONDARY_HIERARCHY_LEVELS']
                                [len(secondary_path)]] == variable_name]
                    else:
                        further_reduced_df = further_filtered_df[further_filtered_df[df_const[session_key][
                                                    'SECONDARY_HIERARCHY_LEVELS'][len(secondary_path) - 1]] ==
                                                                     variable_name]
                    for z in range(end_date.year - start_date.year + 1):
                        year = start_date.year + z
                        num_weeks = last_calender_week(year)
                        yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                        unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                        year_of_event = year
                        quarter = nan
                        for unique_date in unique_dates:
                            if (num_weeks == 52 and unique_date != 53) or num_weeks == 53:
                                unique_data = yearly_data[
                                    yearly_data["Date of Event"].dt.isocalendar().week == unique_date]
                                date_of_event = get_last_day_of_week(year, unique_date)
                                month_of_event = date_of_event.month
                                week_of_event = unique_date

                                measure_value = unique_data[measure_type].sum()

                                if hierarchy_toggle == "Level Filter" or (
                                        (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                            'graph_children'])):
                                    h0 = unique_data['H0'].values[0]
                                    h1 = unique_data['H1'].values[0]
                                    h2 = unique_data['H2'].values[0]
                                    h3 = unique_data['H3'].values[0]
                                    h4 = unique_data['H4'].values[0]
                                    h5 = unique_data['H5'].values[0]

                                else:
                                    h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                                    h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                                    h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                                    h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                                    h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                                    h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                                row_list.append(
                                [nan, nan,
                                 h0, h1, h2, h3, h4, h5,
                                 unique_data['Variable Value'].iloc[0],
                                 unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, current_filter,
                                 year_of_event, quarter, month_of_event, week_of_event, nan, nan, nan, nan,
                                 nan, nan, measure_value, measure_type,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

            time_df = DataFrame(row_list,
                                       columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4',
                                                'H5', 'Variable Value', 'Variable Name', 'Variable Name Qualifier',
                                                'Variable Name Sub Qualifier', 'Date of Event', 'Calendar Entry Type',
                                                'Year of Event', 'Quarter', 'Month of Event', 'Week of Event',
                                                'Fiscal Year of Event', 'Fiscal Quarter',
                                                'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                                'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        time_df = time_df[time_df['Date of Event'] >= datetime64(start_date.date())]
        time_df = time_df[time_df['Date of Event'] <= datetime64(end_date.date())]

        # caching filtering
        if hierarchy_toggle == "Level Filter" and secondary_hierarchy_toggle == 'Level Filter':
            session['simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle +
                    secondary_level_dropdown + timeframe + str(num_periods) + period_type + measure_type +
                    session_key] = time_df
        elif hierarchy_toggle == "Specific Item" and secondary_hierarchy_toggle == 'Level Filter':
            session['simplified' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                    secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + str(num_periods) +
                    period_type + measure_type + session_key] = time_df

    # If not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':

        for specific_item in specific_items:
            if specific_item == 'specific item':
                further_filtered_df = df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = df[df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = df[df["H" + str(len(hierarchy_path))] == specific_item]

            for variable_name in variable_names:
                # filters on secondary hierarchy
                if secondary_hierarchy_toggle == "Level Filter":
                    further_reduced_df = further_filtered_df[further_filtered_df[secondary_level_dropdown] ==
                                                                                                        variable_name]
                elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
                    further_reduced_df = further_filtered_df[
                            further_filtered_df[df_const[session_key]['SECONDARY_HIERARCHY_LEVELS']
                            [len(secondary_path)]] == variable_name]
                else:
                    further_reduced_df = further_filtered_df[further_filtered_df[df_const[session_key][
                                    'SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)-1]] == variable_name]

                for z in range(end_year - start_year + 1):
                    year = start_year + z
                    yearly_data = further_reduced_df[further_reduced_df["Date of Event"].dt.year == year]
                    if secondary_type == "Month":
                        unique_dates = yearly_data["Date of Event"].dt.month.unique()
                    elif secondary_type == "Week":
                        unique_dates = yearly_data["Date of Event"].dt.isocalendar().week.unique()
                        # secondary_type == "Quarter"
                    else:
                        yearly_data["Quarter"] = yearly_data['Date of Event'].dt.quarter
                        unique_dates = yearly_data["Quarter"].unique()
                    quarter = nan
                    month = nan
                    week = nan
                    for unique_date in unique_dates:
                        if secondary_type == 'Quarter':
                            quarter = unique_date
                            unique_data = yearly_data[yearly_data["Quarter"] == unique_date]
                            date_of_event = get_date_of_quarter(unique_date, year)
                        elif secondary_type == "Week":
                            unique_data = yearly_data[
                                yearly_data["Date of Event"].dt.isocalendar().week == unique_date]
                            date_of_event = get_last_day_of_week(year, unique_date)
                            # quarter = nan
                            # month = nan
                            # week = nan
                            # secondary_type== 'Month'
                        else:
                            # quarter = get_quarter(unique_date)
                            unique_data = yearly_data[yearly_data["Date of Event"].dt.month == unique_date]
                            date_of_event = get_last_day_of_month(date(year, int(unique_date), 1))
                            month = unique_date

                        measure_value = unique_data[measure_type].sum()

                        if hierarchy_toggle == "Level Filter" or (
                                (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == [
                                'graph_children'])):
                            h0 = unique_data['H0'].values[0]
                            h1 = unique_data['H1'].values[0]
                            h2 = unique_data['H2'].values[0]
                            h3 = unique_data['H3'].values[0]
                            h4 = unique_data['H4'].values[0]
                            h5 = unique_data['H5'].values[0]

                        else:
                            h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                            h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                            h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                            h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                            h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                            h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                        row_list.append(
                                [nan, nan,
                                 h0, h1, h2, h3, h4, h5,
                                 unique_data['Variable Value'].iloc[0], unique_data['Variable Name'].iloc[0],
                                 unique_data['Variable Name Qualifier'].iloc[0],
                                 unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, secondary_type,
                                 year, quarter, month, week, nan, nan, nan, nan, nan, nan,
                                 measure_value, measure_type,
                                 True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
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
                range_df = pd.concat([range_df, time_df[
                    time_df['{}Year of Event'.format(year_prefix)] == (start_year + i + 1)]], ignore_index=True)

            # Filter end year below threshold
            time_df = time_df[time_df['{}Year of Event'.format(year_prefix)] == end_year]
            time_df = time_df[time_df[division_column] < end_secondary]
            time_df = pd.concat([range_df, time_df], ignore_index=True)

        if hierarchy_toggle == "Level Filter" and secondary_hierarchy_toggle == 'Level Filter':
            if timeframe == 'all-time':

                session['simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle +
                        secondary_level_dropdown + timeframe + measure_type + session_key] = time_df
            else:
                session['simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle +
                        secondary_level_dropdown + timeframe + secondary_type + str(start_year) + str(end_year) +
                        str(start_secondary) + str(end_secondary) + measure_type + session_key] = time_df
        elif hierarchy_toggle == 'Specific Item' and secondary_hierarchy_toggle == 'Level Filter':
            if timeframe == 'all-time':
                session['simplified' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                        secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + measure_type +
                        session_key] = time_df
            else:
                session['simplified' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                        secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + secondary_type +
                        str(start_year) + str(end_year) + str(start_secondary) + str(end_secondary) + measure_type +
                        session_key] = time_df
    else:

        for specific_item in specific_items:
            if specific_item == 'specific item':
                further_filtered_df = df
            elif hierarchy_toggle == "Level Filter":
                further_filtered_df = df[df[hierarchy_level_dropdown] == specific_item]
            else:
                further_filtered_df = df[df["H" + str(len(hierarchy_path))] == specific_item]
            # len_var = len(variable_names)
            for variable_name in variable_names:
                # filters on secondary hierarchy
                if secondary_hierarchy_toggle == "Level Filter":
                    further_reduced_df = further_filtered_df[further_filtered_df[secondary_level_dropdown] ==
                                                                                                        variable_name]
                elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
                    further_reduced_df = further_filtered_df[further_filtered_df[df_const[session_key]
                        ['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)]] == variable_name]
                else:
                    further_reduced_df = further_filtered_df[further_filtered_df[df_const[session_key][
                                    'SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)-1]] == variable_name]

                unique_secondarys = further_reduced_df['Date of Event'].dt.year.unique()

                for unique_secondary in unique_secondarys:
                    unique_data = further_reduced_df[further_reduced_df['Date of Event'].dt.year == unique_secondary]
                    measure_value = unique_data[measure_type].sum()
                    date_of_event = get_last_day_of_year(unique_secondary)

                    if hierarchy_toggle == "Level Filter" or (
                            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
                        h0 = unique_data['H0'].values[0]
                        h1 = unique_data['H1'].values[0]
                        h2 = unique_data['H2'].values[0]
                        h3 = unique_data['H3'].values[0]
                        h4 = unique_data['H4'].values[0]
                        h5 = unique_data['H5'].values[0]
                    else:
                        h0 = hierarchy_path[0] if len(hierarchy_path) >= 1 else nan
                        h1 = hierarchy_path[1] if len(hierarchy_path) >= 2 else nan
                        h2 = hierarchy_path[2] if len(hierarchy_path) >= 3 else nan
                        h3 = hierarchy_path[3] if len(hierarchy_path) >= 4 else nan
                        h4 = hierarchy_path[4] if len(hierarchy_path) >= 5 else nan
                        h5 = hierarchy_path[5] if len(hierarchy_path) >= 6 else nan

                    row_list.append(
                        [nan, nan,
                         h0, h1, h2, h3, h4, h5,
                         unique_data['Variable Value'].iloc[0],
                         unique_data['Variable Name'].iloc[0],
                         unique_data['Variable Name Qualifier'].iloc[0],
                         unique_data['Variable Name Sub Qualifier'].iloc[0], date_of_event, "Year", unique_secondary,
                         nan, nan, nan, nan, nan, nan, nan, nan, nan, measure_value,
                         measure_type, True if unique_data['Partial Period'].iloc[0] is True else nan])

        time_df = DataFrame(row_list,
                               columns=['OPG Data Set', 'Hierarchy One Name', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5',
                                        'Variable Value',
                                        'Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier',
                                        'Date of Event', 'Calendar Entry Type', 'Year of Event', 'Quarter',
                                        'Month of Event', 'Week of Event', 'Fiscal Year of Event', 'Fiscal Quarter',
                                        'Fiscal Month of Event', 'Fiscal Week of Event', 'Julian Day',
                                        'Activity Event Id', 'Measure Value', 'Measure Type', 'Partial Period'])

        if hierarchy_toggle == "Level Filter" and secondary_hierarchy_toggle == 'Level Filter':
            session['simplified' + hierarchy_toggle + hierarchy_level_dropdown + secondary_hierarchy_toggle +
                    secondary_level_dropdown + timeframe + secondary_type + str(start_year) +
                    str(end_year) + measure_type + session_key] = time_df
        elif hierarchy_toggle == 'Specific Item' and secondary_hierarchy_toggle == 'Level Filter':
            session['simplified' + hierarchy_toggle + str(hierarchy_path) + str(hierarchy_graph_children) +
                    secondary_hierarchy_toggle + secondary_level_dropdown + timeframe + secondary_type +
                    str(start_year) + str(end_year) + measure_type + session_key] = time_df
    return time_df


def customize_menu_filter(dff, measure_type, df_const, secondary_path,
                          secondary_hierarchy_toggle, secondary_level_dropdown, secondary_graph_children,
                          secondary_options, session_key):
    """Filters data frame based on customize menu inputs and returns the filtered data frame."""

    if secondary_hierarchy_toggle == 'Level Filter':
        variable = df_const[session_key][secondary_level_dropdown]
    elif secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
        variable = [option['label'] for option in secondary_options]
    else:
        variable = secondary_path[-1] if secondary_path != [] else None

    if measure_type == 'Link':
        filtered_df = dff[dff['Measure Fcn'] == 'Link']
    else:
        filtered_df = dff[dff['Measure Type'] == measure_type]

    if variable is not None:
        # ensure variable_names is a list of variable values
        if type(variable) is not list:
            variable = [variable]

        aggregate_df = DataFrame()

        # for each selection, add the rows defined by the selection
        for variable_name in variable:
            # Filters based on rows that match the variable name path
            if secondary_hierarchy_toggle == "Level Filter":
                further_filter_df = filtered_df[filtered_df[secondary_level_dropdown] ==
                                                         variable_name]
            else:
                if secondary_hierarchy_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
                    further_filter_df = filtered_df[
                        filtered_df[df_const[session_key]['SECONDARY_HIERARCHY_LEVELS']
                        [len(secondary_path)]] == variable_name]
                else:
                    further_filter_df = filtered_df[filtered_df[df_const[session_key][
                        'SECONDARY_HIERARCHY_LEVELS'][len(secondary_path) - 1]] == variable_name]

            aggregate_df = pd.concat([aggregate_df, further_filter_df])

        filtered_df = aggregate_df
    else:
        filtered_df = filtered_df[0:0]

    return filtered_df


# *********************************************LANGUAGE DATA***********************************************************

def get_label(label, table=None):
    """Given a label returns the appropriate ref_desc from OP_Ref."""
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


# ********************************************DATA FITTING OPERATIONS**************************************************

def linear_regression(df, x, y, ci):
    """
    Creates statistical model from ordinary lease squares method and uses the model return the prediction of a
    linear best fit.
    """
    df_best_fit = DataFrame()
    df_best_fit['timestamp'] = pd.to_datetime(df[x])
    df_best_fit['serialtime'] = [(d - datetime(1970, 1, 1)).days for d in df_best_fit['timestamp']]
    x_axis = sm.add_constant(df_best_fit['serialtime'])
    model = sm.OLS(df[y], x_axis).fit()  # creates statistical model from ordinary lease squares method
    df_best_fit['Best Fit'] = model.fittedvalues

    if ci:
        df_best_fit["Upper Interval"], df_best_fit["Lower Interval"] = confidence_intervals(model)

    return df_best_fit


def polynomial_regression(df, x, y, degree, ci):
    """
    Creates statistical model from ordinary lease squares method and uses the model return the prediction of a
    polynomial best fit.
    """
    df_best_fit = DataFrame()
    df_best_fit['timestamp'] = pd.to_datetime(df[x])
    df_best_fit['serialtime'] = [(d - datetime(1970, 1, 1)).days for d in df_best_fit['timestamp']]
    polynomial_features = PolynomialFeatures(degree=degree)
    xp = polynomial_features.fit_transform(df_best_fit['serialtime'].to_numpy().reshape(-1, 1))
    model = sm.OLS(df[y], xp).fit()  # creates statistical model from ordinary lease squares method
    df_best_fit["Best Fit"] = model.predict(xp)  # creates best fit with generated polynomial

    if ci:
        df_best_fit["Lower Interval"], df_best_fit["Upper Interval"] = confidence_intervals(model)

    return df_best_fit


def confidence_intervals(model):
    """
    Calculates standard deviation and confidence interval for prediction and returns the upper and lower confidence
    interval.
    """
    _, lower, upper = wls_prediction_std(model)
    return lower, upper
