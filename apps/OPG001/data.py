######################################################################################################################
"""
data.py

contains arbitrary constants, data constants, and data manipulation functions
"""
######################################################################################################################

# External Packages
import pandas as pd
import numpy as np
import math
from treelib import Tree
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Contents:
#   ARBITRARY CONSTANTS
#       - GRAPH_OPTIONS
#       - X_AXIS_OPTIONS
#       - CLR
#   STYLE RETURNS FOR CALLBACKS
#       - VIEW_CONTENT_SHOW
#       - VIEW_CONTENT_HIDE
#       - CUSTOMIZE_CONTENT_SHOW
#       - CUSTOMIZE_CONTENT_HIDE
#       - LAYOUT_CONTENT_SHOW
#       - LAYOUT_CONTENT_HIDE
#       - DATA_CONTENT_SHOW
#       - DATA_CONTENT_HIDE
#   DATASET CLASS
#       - DataSet
#             - __init__()
#             - filter_list()
#             - generate_tree()
#   DATA MANIPULATION FUNCTIONS
#       - data_filter()
#       - customize_menu_filter()
#       - create_categories()
#       - get_table_columns()
#   LANGUAGE DATA
#       - get_label()
#       - LANGUAGE_DF
#       - LANGUAGE
#   DATAFRAME OPERATIONS
#       - DATA_SETS
#       - LOADED_DFS


# ***********************************************ARBITRARY CONSTANTS*************************************************

GRAPH_OPTIONS = ['Line', 'Bar', 'Scatter', 'Box Plot', 'Table', 'Sankey']

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

# TODO : replace with session memory
# dict to save all of the saved graphs
saved_layouts = {}

# dict to save all of the saved dashboards
saved_dashboards = {}

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


# ********************************************DATASET CLASS************************************************************

class DataSet:
    def __init__(self, df_name):
        # print("hello world")

        if df_name.find('.csv') > -1:
            # df = pd.DataFrame(None)
            df = pd.read_csv('apps/OPG001/test_data/{}'.format(df_name),
                             #  chunks = pd.read_csv('apps/OPG001/test_data/{}'.format(df_name),
                             parse_dates=['Date of Event'],
                             # infer_datetime_format=True,
                             # chunksize=50_000,
                             dtype={
                                 "Variable Name": object,
                                 "Variable Name Qualifier": object,
                                 "Variable Name Sub Qualifier": object
                             })
            # for chunk in chunks:
            #    df = df.append(chunk, ignore_index=True)
        elif df_name.find('.xlsx') > -1:
            df = pd.read_excel('apps/OPG001/test_data/{}'.format(df_name),
                               dtype={
                                   "Variable Name": object,
                                   "Variable Name Qualifier": object,
                                   "Variable Name Sub Qualifier": object
                               })
        elif df_name.find('.json') > -1:
            df = pd.read_json('apps/OPG001/test_data/{}'.format(df_name),
                              orient='records',
                              lines=True)
        else:
            raise Exception('Unknown file type: ', df_name)

        # add all variable names without qualifiers to col
        col = pd.Series(df['Variable Name'][df['Variable Name Qualifier'].isna()])
        # combine variable hierarchy columns into col for rows with qualifiers
        col = col.append(
            pd.Series(
                df['Variable Name'][df['Variable Name Qualifier'].notna()]
                + "|"
                + df['Variable Name Qualifier'][df['Variable Name Qualifier'].notna()]))
        df['Variable Name'] = col

        # replaces all strings that are just spaces with NaN
        df.replace(to_replace=r'^\s*$', value=np.NaN, regex=True, inplace=True)

        # Can be redone to exclude hierarchy one name and to include more levels
        df = df.rename(columns={'Hierarchy One Top': 'H1',
                                'Hierarchy One -1': 'H2',
                                'Hierarchy One -2': 'H3',
                                'Hierarchy One -3': 'H4',
                                'Hierarchy One -4': 'H5',
                                'Hierarchy One Leaf': 'H6'})

        self.HIERARCHY_LEVELS = ['H{}'.format(i + 1) for i in range(6)]

        # If we are dealing with links in the future we must format them as follows and edit the table drawer
        # dataframe_table.Link = list(map(lambda x: '[Link]({})'.format(x), dataframe_table.Link))

        # list of variable column names
        self.VARIABLE_LEVEL = 'Variable Name'

        # list of column names
        self.COLUMN_NAMES = df.columns.values

        # list of measure type options
        self.MEASURE_TYPE_OPTIONS = df['Measure Type'].dropna().unique().tolist()

        # New date picker values

        self.GREGORIAN_MIN_YEAR = int(df['Year of Event'].min())
        self.GREGORIAN_YEAR_MAX = int(df['Year of Event'][df['Calendar Entry Type'] == 'Year'].max())
        self.GREGORIAN_QUARTER_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Quarter'].max())
        self.GREGORIAN_QUARTER_FRINGE_MIN = int(df['Quarter'][df['Year of Event'] == self.GREGORIAN_MIN_YEAR].min())
        self.GREGORIAN_QUARTER_FRINGE_MAX = \
            int(df['Quarter'][df['Year of Event'] == self.GREGORIAN_QUARTER_MAX_YEAR].max())
        self.GREGORIAN_MONTH_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Month'].max())
        self.GREGORIAN_MONTH_FRINGE_MIN = \
            int(df['Month of Event'][df['Year of Event'] == self.GREGORIAN_MIN_YEAR].min())
        self.GREGORIAN_MONTH_FRINGE_MAX = \
            int(df['Month of Event'][df['Year of Event'] == self.GREGORIAN_MONTH_MAX_YEAR].max())

        if len(df[df['Calendar Entry Type'] == 'Week']) > 0:
            self.GREGORIAN_WEEK_AVAILABLE = True  # not currently used
            self.GREGORIAN_WEEK_MAX_YEAR = int(df['Year of Event'][df['Calendar Entry Type'] == 'Week'].max())
            self.GREGORIAN_WEEK_FRINGE_MIN = int(
                df['Week of Event'][df['Year of Event'] == self.GREGORIAN_MIN_YEAR].min())
            self.GREGORIAN_WEEK_FRINGE_MAX = int(
                df['Week of Event'][df['Year of Event'] == self.GREGORIAN_WEEK_MAX_YEAR].max())
        else:
            self.GREGORIAN_WEEK_AVAILABLE = False  # not currently used, so set fake values
            self.GREGORIAN_WEEK_MAX_YEAR = 52
            self.GREGORIAN_WEEK_FRINGE_MIN = 1
            self.GREGORIAN_WEEK_FRINGE_MAX = 52

        if len(df['Fiscal Year of Event'].unique()) != 1 and df['Fiscal Year of Event'].unique()[0] is not None:
            self.FISCAL_AVAILABLE = True

            self.FISCAL_MIN_YEAR = int(df['Fiscal Year of Event'].min())
            self.FISCAL_YEAR_MAX = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Fiscal Year'].max())
            self.FISCAL_QUARTER_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Quarter'].max())
            self.FISCAL_QUARTER_FRINGE_MIN = \
                int(df['Fiscal Quarter'][df['Fiscal Year of Event'] == self.FISCAL_MIN_YEAR].min())
            self.FISCAL_QUARTER_FRINGE_MAX = int(
                df['Fiscal Quarter'][df['Fiscal Year of Event'] == self.FISCAL_QUARTER_MAX_YEAR].max())
            self.FISCAL_MONTH_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Month'].max())
            self.FISCAL_MONTH_FRINGE_MIN = \
                int(df['Fiscal Month of Event'][df['Fiscal Year of Event'] == self.FISCAL_MIN_YEAR].min())
            self.FISCAL_MONTH_FRINGE_MAX = int(
                df['Fiscal Month of Event'][df['Fiscal Year of Event'] == self.FISCAL_MONTH_MAX_YEAR].max())
            self.FISCAL_WEEK_MAX_YEAR = int(df['Fiscal Year of Event'][df['Calendar Entry Type'] == 'Week'].max())
            self.FISCAL_WEEK_FRINGE_MIN = int(df['Fiscal Week of Event'][df['Fiscal Year of Event']
                                                                         == self.FISCAL_MIN_YEAR].min())
            self.FISCAL_WEEK_FRINGE_MAX = int(df['Fiscal Week of Event'][df['Fiscal Year of Event']
                                                                         == self.FISCAL_WEEK_MAX_YEAR].max())
        else:
            self.FISCAL_AVAILABLE = False

        # self.MIN_DATE_UNF = datetime.strptime(str(df.loc[df['Date of Event'].idxmin(), 'Date of Event']), '%Y%m%d')
        # self.MAX_DATE_UNF = datetime.strptime(str(df.loc[df['Date of Event'].idxmax(), 'Date of Event']), '%Y%m%d')

        # this is a hack until we get the data delivered from the database
        try:
            self.MIN_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(),
                                                         'Date of Event'], '%Y/%m/%d')
        except:
            self.MIN_DATE_UNF = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmin(), 'Date of Event']
            # self.MIN_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64').idxmin(),  # at
            #                                            'Date of Event'], '%Y/%m/%d')

        try:
            self.MAX_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(),
                                                         'Date of Event'], '%Y/%m/%d')
        except:
            self.MAX_DATE_UNF = df.loc[df['Date of Event'].astype('datetime64[ns]').idxmax(), 'Date of Event']
            # self.MAX_DATE_UNF = datetime.strptime(df.loc[df['Date of Event'].astype('datetime64').idxmax(),  # at
            #                                            'Date of Event'], '%Y/%m/%d')

        # replaces all Y in Partial Period with True & False
        df['Partial Period'] = df['Partial Period'].transform(lambda x: x == 'Y')

        # Sets the Date of Event in the df to be in the correct format for Plotly
        # df['Date of Event'] = df['Date of Event'].transform(
        #     lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))

        # Shrinks Data Size
        df = create_categories(df, self.HIERARCHY_LEVELS)

        self.DF = df

        self.TREE = None
        self.VARIABLE_OPTIONS = None

    # Helper function for the tree generator
    def filter_list(self, hierarchy_path):
        # Filters out all rows that don't include path member at specific level
        filtered_df = self.DF
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df[filtered_df[self.HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
        return filtered_df

    # Takes in a dataframe with the hierarchy structure and returns a tree
    def generate_tree(self, hierarchy_levels_tree, first_col_index):
        # Holds the headers of each of the hierarchy levels
        hierarchy_names = list(self.DF)[first_col_index:(hierarchy_levels_tree + first_col_index)]

        generated_tree = Tree()

        # Creates root node and its children
        first_level = self.DF[hierarchy_names[0]].unique()
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
                        # new_id = '{}, {}'.format(parent_id, new_node)
                        new_id = '{}^||^{}'.format(parent_id, new_node)
                        next_level_ids.append(new_id)
                        if i != len(hierarchy_names):
                            if i != 1:
                                # Turns hierarchy path into list, uses that to get children
                                # hierarchy_path = new_id.split(", ")
                                hierarchy_path = new_id.split("^||^")
                                hierarchy_path.remove('root')
                                filtered_df = self.filter_list(hierarchy_path)
                                children = filtered_df[hierarchy_names[i]].dropna().unique()
                            else:
                                # For the first level no filtering is required
                                children = self.DF[hierarchy_names[i]].dropna().unique()
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

    def get_visual_hierarchy(self):

        options = []

        unique_vars = self.DF[self.VARIABLE_LEVEL].unique()
        cleaned_list = [x for x in unique_vars if str(x) != 'nan']
        cleaned_list.sort()

        for unique_var in cleaned_list:
            options.append(
                {'label': "  " * unique_var.count("|") + str(unique_var).replace('|', ', '), 'value': unique_var})

        self.VARIABLE_OPTIONS = options


# **********************************************DATA MANIPULATION FUNCTIONS*******************************************

def data_filter(hierarchy_path, secondary_type, end_secondary, end_year, start_secondary, start_year,
                timeframe, fiscal_toggle, num_periods, period_type, hierarchy_toggle, hierarchy_level_dropdown,
                hierarchy_graph_children, df_name):
    # NOTE: This assumes hierarchy path is a list of all previously selected levels

    if hierarchy_toggle == 'Level Filter' or (
            (hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children'])):
        filtered_df = LOADED_DFS[df_name].DF.copy()

        if hierarchy_toggle == 'Level Filter':
            # If anything is in the drop down
            if hierarchy_level_dropdown:
                # Filter based on hierarchy level
                filtered_df.dropna(subset=[hierarchy_level_dropdown], inplace=True)
                for i in range(len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - int(hierarchy_level_dropdown[1])):
                    bool_series = pd.isnull(filtered_df[LOADED_DFS[df_name].HIERARCHY_LEVELS[
                        len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - 1 - i]])
                    filtered_df = filtered_df[bool_series]
            else:
                # Returns empty data frame with column names
                filtered_df = filtered_df[0:0]
        else:
            # Filters out all rows that are less specific than given path length
            for i in range(len(hierarchy_path)):
                filtered_df = filtered_df[filtered_df[LOADED_DFS[df_name].HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
            # Filters out all rows that are more specific than given path length plus one to preserve the child column
            for i in range(len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - (len(hierarchy_path) + 1)):
                bool_series = pd.isnull(filtered_df[LOADED_DFS[df_name].HIERARCHY_LEVELS[
                    len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - 1 - i]])
                filtered_df = filtered_df[bool_series]
            filtered_df.dropna(subset=[LOADED_DFS[df_name].HIERARCHY_LEVELS[len(hierarchy_path)]], inplace=True)
    else:
        filtered_df = LOADED_DFS[df_name].DF
        # Filters out all rows that don't include path member at specific level
        for i in range(len(hierarchy_path)):
            filtered_df = filtered_df[filtered_df[LOADED_DFS[df_name].HIERARCHY_LEVELS[i]] == hierarchy_path[i]]
        # Filters out all rows that are more specific than given path
        for i in range(len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - len(hierarchy_path)):
            bool_series = pd.isnull(filtered_df[LOADED_DFS[df_name].HIERARCHY_LEVELS[
                len(LOADED_DFS[df_name].HIERARCHY_LEVELS) - 1 - i]])
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
            start_year = LOADED_DFS[df_name].FISCAL_MIN_YEAR
            end_year = LOADED_DFS[df_name].FISCAL_MONTH_MAX_YEAR
            start_secondary = LOADED_DFS[df_name].FISCAL_MONTH_FRINGE_MIN
            end_secondary = LOADED_DFS[df_name].FISCAL_MONTH_FRINGE_MAX + 1
        else:  # year_type == 'Gregorian'
            start_year = LOADED_DFS[df_name].GREGORIAN_MIN_YEAR
            end_year = LOADED_DFS[df_name].GREGORIAN_MONTH_MAX_YEAR
            start_secondary = LOADED_DFS[df_name].GREGORIAN_MONTH_FRINGE_MIN
            end_secondary = LOADED_DFS[df_name].GREGORIAN_MONTH_FRINGE_MAX + 1

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
def customize_menu_filter(dff, df_name, measure_type, variable_names):
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
                filtered_df[filtered_df[LOADED_DFS[df_name].VARIABLE_LEVEL] == variable_name])

        filtered_df = aggregate_df

    return filtered_df


# This uses pandas categories to shrink the data
def create_categories(dff, hierarchy_columns):
    to_category = ['Calendar Entry Type', 'Measure Type', 'OPG Data Set']
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

def get_label(key):
    key_row = LANGUAGE_DF[LANGUAGE_DF['Key'] == key]
    key_row = key_row[key_row['Language'] == LANGUAGE]
    if key is None:
        return None
    if len(key_row) != 1:
        return 'Key Error: {}'.format(key)
    return key_row.iloc[0]['Displayed Text']


LANGUAGE_DF = pd.read_csv('apps/OPG001/test_data/Language Data JG.csv')
# Apparently will be passed in via the server
# 'en' = English
# 'fr' = French
LANGUAGE = 'en'

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
DATA_SETS = ['OPG001_2016-17_Week_v3.csv', 'OPG010 Sankey Data.xlsx']

LOADED_DFS = {}

for i in DATA_SETS:
    # Load data frame and extract data
    LOADED_DFS[i] = DataSet(i)
    # Build hierarchy tree
    LOADED_DFS[i].TREE = LOADED_DFS[i].generate_tree(len(LOADED_DFS[i].HIERARCHY_LEVELS), 2)
    # Build variable tree
    LOADED_DFS[i].get_visual_hierarchy()
