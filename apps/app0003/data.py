######################################################################################################################
"""
data.py

contains arbitrary constants, data constants, and data manipulation functions
"""
######################################################################################################################

# External Packages
import pandas as pd
import numpy as np
from treelib import Tree
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# *******************************************DATAFRAME INITIALIZATION************************************************

DF = pd.read_csv('apps/app0003/test_data/Graphics 1 example dataset V4.csv')

# ***********************************************ARBITRARY CONSTANTS*************************************************

GRAPH_OPTIONS = ['Line', 'Bar', 'Scatter', 'Table', 'Box Plot']

X_AXIS_OPTIONS = ['Time']

CLR = {'text1': 'black',
       'text2': '#EED5DD',
       'black': 'black',
       'white': 'white',
       'background1': '#760024',
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
DATA_CONTENT_HIDE = {'flex-grow': '0', 'background-color': CLR['sidebar-initial'],
                     'border-right': '1px solid {}'.format(CLR['lightgray']),
                     'display': 'none'}

# ********************************************DATE-PICKER CONSTANTS**************************************************

GREGORIAN_MIN_YEAR = int(DF['Year of Event'].min())
GREGORIAN_YEAR_MAX = int(DF['Year of Event'][DF['Calendar Entry Type'] == 'Year'].max())
GREGORIAN_QUARTER_MAX_YEAR = int(DF['Year of Event'][DF['Calendar Entry Type'] == 'Quarter'].max())
GREGORIAN_QUARTER_FRINGE_MIN = int(DF['Quarter'][DF['Year of Event'] == GREGORIAN_MIN_YEAR].min())
GREGORIAN_QUARTER_FRINGE_MAX = int(DF['Quarter'][DF['Year of Event'] == GREGORIAN_QUARTER_MAX_YEAR].max())
GREGORIAN_MONTH_MAX_YEAR = int(DF['Year of Event'][DF['Calendar Entry Type'] == 'Month'].max())
GREGORIAN_MONTH_FRINGE_MIN = int(DF['Month of Event'][DF['Year of Event'] == GREGORIAN_MIN_YEAR].min())
GREGORIAN_MONTH_FRINGE_MAX = int(DF['Month of Event'][DF['Year of Event'] == GREGORIAN_MONTH_MAX_YEAR].max())
GREGORIAN_WEEK_MAX_YEAR = 2020  # int(DF['Year of Event'][DF['Calendar Entry Type'] == 'Week'].max())
GREGORIAN_WEEK_FRINGE_MIN = 12  # int(DF['Week of Event'][DF['Year of Event'] == GREGORIAN_MIN_YEAR].min())
GREGORIAN_WEEK_FRINGE_MAX = 42  # int(DF['Week of Event'][DF['Year of Event'] == GREGORIAN_WEEK_MAX_YEAR].max())

FISCAL_MIN_YEAR = int(DF['Fiscal Year of Event'].min())
FISCAL_YEAR_MAX = int(DF['Fiscal Year of Event'][DF['Calendar Entry Type'] == 'Fiscal Year'].max())
FISCAL_QUARTER_MAX_YEAR = int(DF['Fiscal Year of Event'][DF['Calendar Entry Type'] == 'Quarter'].max())
FISCAL_QUARTER_FRINGE_MIN = int(DF['Fiscal Quarter'][DF['Fiscal Year of Event'] == FISCAL_MIN_YEAR].min())
FISCAL_QUARTER_FRINGE_MAX = int(DF['Fiscal Quarter'][DF['Fiscal Year of Event'] == FISCAL_QUARTER_MAX_YEAR].max())
FISCAL_MONTH_MAX_YEAR = int(DF['Fiscal Year of Event'][DF['Calendar Entry Type'] == 'Month'].max())
FISCAL_MONTH_FRINGE_MIN = int(DF['Fiscal Month of Event'][DF['Fiscal Year of Event'] == FISCAL_MIN_YEAR].min())
FISCAL_MONTH_FRINGE_MAX = int(DF['Fiscal Month of Event'][DF['Fiscal Year of Event'] == FISCAL_MONTH_MAX_YEAR].max())
FISCAL_WEEK_MAX_YEAR = 2021  # int(DF['Fiscal Year of Event'][DF['Calendar Entry Type'] == 'Week'].max())
FISCAL_WEEK_FRINGE_MIN = 37  # int(DF['Fiscal Week of Event'][DF['Fiscal Year of Event'] == FISCAL_MIN_YEAR].min())
FISCAL_WEEK_FRINGE_MAX = 8  # int(DF['Fiscal Week of Event'][DF['Fiscal Year of Event'] == FISCAL_WEEK_MAX_YEAR].max())

MIN_DATE_UNF = datetime.strptime(str(DF.loc[DF['Date of Event'].idxmin(), 'Date of Event']), '%Y%m%d')
MAX_DATE_UNF = datetime.strptime(str(DF.loc[DF['Date of Event'].idxmax(), 'Date of Event']), '%Y%m%d')


# **********************************************DATA MANIPULATION FUNCTIONS*******************************************

def data_filter(hierarchy_path, dropdown_value, secondary_type, end_secondary, end_year, start_secondary, start_year,
                timeframe, fiscal_toggle, num_periods, period_type, hierarchy_toggle, hierarchy_level_dropdown,
                hierarchy_graph_children, arg_value):
    # NOTE: This assumes hierarchy path is a list of all previously selected levels

    if not hierarchy_toggle or (arg_value and (hierarchy_toggle and hierarchy_graph_children == ['graph_children'])):
        filtered_df = DF.copy()

        if not hierarchy_toggle:
            # If anything is in the drop down
            if hierarchy_level_dropdown:
                # Filter based on hierarchy level
                filtered_df.dropna(subset=[hierarchy_level_dropdown], inplace=True)
                for i in range(len(HIERARCHY_LEVELS) - int(hierarchy_level_dropdown[1])):
                    bool_series = pd.isnull(filtered_df[HIERARCHY_LEVELS[len(HIERARCHY_LEVELS) - 1 - i]])
                    filtered_df = filtered_df[bool_series]
            else:
                # Returns empty data frame with column names
                filtered_df = filtered_df[0:0]
        else:
            # Filters out all rows that are less specific than given path length
            for i in range(len(hierarchy_path)):
                filtered_df = filtered_df[filtered_df[HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
            # Filters out all rows that are more specific than given path length plus one to preserve the child column
            for i in range(len(HIERARCHY_LEVELS) - (len(hierarchy_path) + 1)):
                bool_series = pd.isnull(filtered_df[HIERARCHY_LEVELS[len(HIERARCHY_LEVELS) - 1 - i]])
                filtered_df = filtered_df[bool_series]
            filtered_df.dropna(subset=[HIERARCHY_LEVELS[len(hierarchy_path)]], inplace=True)
    else:
        filtered_df = DF.copy()
        if dropdown_value:
            hierarchy_path.append(dropdown_value)
        # Filters out all rows that don't include path member at specific level
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df[filtered_df[HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
        # Filters out all rows that are more specific than given path
        for i in range(len(HIERARCHY_LEVELS) - len(hierarchy_path)):
            bool_series = pd.isnull(filtered_df[HIERARCHY_LEVELS[len(HIERARCHY_LEVELS) - 1 - i]])
            filtered_df = filtered_df[bool_series]

    # account for date type (Gregorian vs Fiscal)
    if fiscal_toggle:
        year_prefix = 'Fiscal '
    else:  # year_type is 'gregorian-dates'
        year_prefix = ''

    # account for special timeframe case 'all-time'
    if timeframe == 'all-time':
        secondary_type = 'Month'
        if fiscal_toggle:
            start_year = FISCAL_MIN_YEAR
            end_year = FISCAL_MONTH_MAX_YEAR
            start_secondary = FISCAL_MONTH_FRINGE_MIN
            end_secondary = FISCAL_MONTH_FRINGE_MAX + 1
        else:  # year_type == 'Gregorian'
            start_year = GREGORIAN_MIN_YEAR
            end_year = GREGORIAN_MONTH_MAX_YEAR
            start_secondary = GREGORIAN_MONTH_FRINGE_MIN
            end_secondary = GREGORIAN_MONTH_FRINGE_MAX + 1

    # account for special timeframe case 'to-current'
    if timeframe == 'to-current':
        end_date = datetime.today()
        if period_type == 'last-years':
            start_date = end_date - relativedelta(years=int(num_periods))
            current_filter = '{}Year'.replace("{}", year_prefix)
        elif period_type == 'last-quarters':
            start_date = end_date - relativedelta(months=3 * int(num_periods))
            current_filter = 'Quarter'
        elif period_type == 'last-months':
            start_date = end_date - relativedelta(months=int(num_periods))
            current_filter = 'Month'
        else:  # period_type == 'last-weeks'
            start_date = end_date - timedelta(weeks=int(num_periods))
            current_filter = 'Week'

        # Filters out unused calender values
        time_df = filtered_df.copy()
        time_df = time_df[time_df['Calendar Entry Type'] == current_filter]

        # Filter all dates inside range (inclusive)
        time_df = time_df[time_df['Date of Event'] >= start_date]
        time_df = time_df[time_df['Date of Event'] <= end_date]

    # if not in year tab, filter using secondary selections
    elif not secondary_type == 'Year':
        # Data frame filtered to be in inputted year range
        time_df = filtered_df[filtered_df['{}Year of Event'.format(year_prefix)] >= start_year]
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
def customize_menu_filter(dff, measure_type, variable_names):
    filtered_df = dff[dff['Measure Type'] == measure_type]
    if type(variable_names) is not list:
        variable_names = [variable_names]
    temp_df = pd.DataFrame()
    for i in variable_names:
        temp_df = temp_df.append(filtered_df[filtered_df['Variable Name'] == i])
    filtered_df = temp_df
    return filtered_df


# Helper function for the tree generator
def filter_list(hierarchy_path):
    # Filters out all rows that don't include path member at specific level
    filtered_df = DF
    for i in range(len(hierarchy_path)):
        filtered_df = filtered_df[filtered_df[HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
    return filtered_df


# Takes in a dataframe with the hierarchy structure and returns a tree
def generate_tree(hierarchy_levels_tree):
    # This line assumes the hierarchy is the beginning columns
    hierarchy_names = list(DF)[2:hierarchy_levels_tree]  # Holds the headers of each of the hierarchy levels

    generated_tree = Tree()

    # Creates root node and its children
    first_level = DF[hierarchy_names[0]].unique()
    first_level_data = [{'label': i, 'value': i} for i in first_level]
    generated_tree.create_node('ROOT', 'root', data=first_level_data)

    # Stores full ids for each level
    all_level_ids = [['root']]

    # Iterate through each hierarchy column
    for i in range(1, hierarchy_levels_tree):
        # List of ids for new level
        next_level_ids = []
        for parent_id in all_level_ids[i - 1]:
            # Grabs node and its children
            parent_node = generated_tree.get_node(parent_id)
            members = parent_node.data
            if members is not None:
                for this_member in members:
                    # Uses parent id to make id
                    new_node = this_member['value']
                    new_id = '{}, {}'.format(parent_id, new_node)
                    next_level_ids.append(new_id)
                    if i != len(hierarchy_names):
                        if i != 1:
                            # Turns hierarchy path into list, uses that to get children
                            hierarchy_path = new_id.split(", ")
                            hierarchy_path.remove('root')
                            filtered_df = filter_list(hierarchy_path)
                            children = filtered_df[hierarchy_names[i]].dropna().unique()
                        else:
                            # For the first level no filtering is required
                            children = DF[hierarchy_names[i]].dropna().unique()
                        children_data = [{'label': j, 'value': j} for j in children]
                        generated_tree.create_node(
                            tag=new_node,
                            identifier=new_id,
                            parent=parent_id,
                            data=children_data)
                    else:
                        # If leaf level, no children exist
                        generated_tree.create_node(
                            tag=new_node,
                            identifier=new_id,
                            parent=parent_id)
        all_level_ids.append(next_level_ids)
    for x in generated_tree.all_nodes_itr():
        options = [{'label': i.tag, 'value': i.tag} for i in generated_tree.children(x.identifier)]
        x.data = options
    return generated_tree


# This uses pandas categories to shrink the data
def create_categories(dff, hierarchy_columns):
    to_category = ['Variable Name', 'Calendar Entry Type', 'Measure Type', 'OPG 001 Time Series Measures']
    to_category = hierarchy_columns + to_category
    for i in to_category:
        dff[i] = pd.Categorical(dff[i])
    return dff


def get_table_columns(dff):
    df = dff.drop(
        ['OPG 001 Time Series Measures', 'Calendar Entry Type', 'Year of Event',
         'Month of Event'], axis=1)
    df = df.dropna(how='all', axis=1)
    return df.columns


# *********************************************LANGUAGE DATA***********************************************************

def get_label(key):
    key_row = language_data[language_data['Key'] == key]
    key_row = key_row[key_row['Language'] == LANGUAGE]
    if len(key_row) != 1:
        return 'Key Error: {}'.format(key)
    return key_row.iloc[0]['Displayed Text']


language_data = pd.read_csv('apps/app0003/test_data/Language Data.csv')
# Apparently will be passed in via the server (en/fr)
LANGUAGE = 'en'


# *********************************************DATAFRAME OPERATIONS***************************************************

# replaces all strings that are just spaces with NaN
DF.replace(to_replace=r'^\s*$', value=np.NaN, regex=True, inplace=True)

# replaces all Y in Partial Period with True & False
DF['Partial Period'] = DF['Partial Period'].transform(lambda x: x == 'Y')

# Sets the Date of Event in the df to be in the correct format for Plotly
DF['Date of Event'] = DF['Date of Event'].transform(lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))

# Can be redone to exclude hierarchy one name and to include more levels
DF = DF.rename(columns={'Hierarchy One Top': 'H1',
                        'Hierarchy One -1': 'H2',
                        'Hierarchy One -2': 'H3',
                        'Hierarchy One -3': 'H4',
                        'Hierarchy One -4': 'H5',
                        'Hierarchy One Leaf': 'H6'})
HIERARCHY_LEVELS = ['H{}'.format(i + 1) for i in range(6)]

# If we are dealing with links in the future we must format them as follows and edit the table drawer
# dataframe_table.Link = list(map(lambda x: '[Link]({})'.format(x), dataframe_table.Link))


# Shrinks Data Size
DF = create_categories(DF, HIERARCHY_LEVELS)

# list of column names
COLUMN_NAMES = DF.columns.values

# Generate Tree for hierarchy filter to use
TREE = generate_tree(len(HIERARCHY_LEVELS) + 2)

# Used in defining the graph menu items
DATA_OPTIONS = DF['Variable Name'].unique().tolist()
MEASURE_TYPE_OPTIONS = DF['Measure Type'].dropna().unique().tolist()
