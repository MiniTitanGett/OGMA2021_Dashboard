import pandas as pd
import numpy as np
import app
import dash_core_components as dcc
import dash_html_components as html
import pyodbc
import json
import plotly.express as px

# graph json layout positions
JSON_GRAPH_TYPE = 0
JSON_GRAPH_OPTIONS = 1
JSON_GRAPH_OPTIONS_XAXIS = 0
JSON_GRAPH_OPTIONS_YAXIS = 1
JSON_GRAPH_OPTIONS_MEASURE = 2
JSON_TIMEFRAME_TYPE = 2
JSON_TIMEFRAME_START = 3
JSON_TIMEFRAME_END = 4
JSON_TIMEFRAME_PERIOD = 5
JSON_TIMEFRAME_PERIOD_START = 6
JSON_TIMEFRAME_PERIOD_END = 7
JSON_HIERARCHY_FILTER = 8
JSON_HIERARCHY_SELECT = 9


# This uses pandas categories to shrink the data
def create_categories(dff, hierarchy_columns):
    to_category = ['Variable Name', 'Calendar Entry Type', 'Measure Type', 'OPG 001 Time Series Measures']
    to_category = hierarchy_columns + to_category
    for i in to_category:
        dff[i] = pd.Categorical(dff[i])
    return dff


df = pd.read_csv('apps/OPG001/test_data/Graphics 1 example dataset V4.csv')

# replaces all strings that are just spaces with NaN
df.replace(to_replace=r'^\s*$', value=np.NaN, regex=True, inplace=True)

# replaces all Y in Partial Period with True & False
df['Partial Period'] = df['Partial Period'].transform(lambda x: x == 'Y')

# Sets the Date of Event in the df to be in the correct format for Plotly
df['Date of Event'] = df['Date of Event'].transform(lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))

# Can be redone to exclude hierarchy one name and to include more levels
df = df.rename(columns={'Hierarchy One Top': 'H1',
                        'Hierarchy One -1': 'H2',
                        'Hierarchy One -2': 'H3',
                        'Hierarchy One -3': 'H4',
                        'Hierarchy One -4': 'H5',
                        'Hierarchy One Leaf': 'H6'})
HIERARCHY_LEVELS = ['H{}'.format(i + 1) for i in range(6)]

# Shrinks Data Size
df = create_categories(df, HIERARCHY_LEVELS)

# list of column names
COLUMN_NAMES = df.columns.values

conn = pyodbc.connect(
    'DRIVER={SQL Server};SERVER=PANDA\\DEV_COLLATION_01;DATABASE=OPEN_Dev_NB;Trusted_Connection=yes',
    autocommit=True);

query = """\
declare @p_result_status varchar(255)
exec dbo.opp_addgeteditdeletefind_clob {}, \'Get\', {}, null, null, null, null, null, null, null, null, null,
@p_result_status output
select @p_result_status as result_status
""".format(297509564, 21876144)

cursor = conn.cursor()
cursor.execute(query)

clob = cursor.fetchone()
cursor.nextset()
results = cursor.fetchone()

j = json.loads(clob.clob_text)

filtered_df = df[df['Variable Name'] == j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_YAXIS]]
filtered_df = filtered_df[filtered_df['Measure Type'] == j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_MEASURE]]

if j[JSON_TIMEFRAME_TYPE] == 'Year':
    filtered_df = filtered_df[filtered_df['Calendar Entry Type'] == 'Year']
    filtered_df = filtered_df[filtered_df['Year of Event'] >= j[JSON_TIMEFRAME_START]]
    filtered_df = filtered_df[filtered_df['Year of Event'] <= j[JSON_TIMEFRAME_END]]
else:  # Fiscal Year
    filtered_df = filtered_df[filtered_df['Calendar Entry Type'] == 'Fiscal Year']
    filtered_df = filtered_df[filtered_df['Fiscal Year of Event'] >= j[JSON_TIMEFRAME_START]]
    filtered_df = filtered_df[filtered_df['Fiscal Year of Event'] <= j[JSON_TIMEFRAME_END]]

app = app.get_app('0004/')

if j[JSON_GRAPH_TYPE] == 'line':
    fig = px.line(data_frame=filtered_df, x='Date of Event', y='Measure Value')
    fig.update_layout(
        xaxis={'title': j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_XAXIS]},
        yaxis={'title': j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_MEASURE]}
    )
    app.layout = html.Div([
        dcc.Graph(figure=fig)
    ])
else:
    fig = px.bar(
        data_frame=filtered_df,
        x='Date of Event',
        y='Measure Value',
        color='Variable Name',
        barmode='group'
    )
    fig.update_layout(
        xaxis={'title': j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_XAXIS]},
        yaxis={'title': j[JSON_GRAPH_OPTIONS][JSON_GRAPH_OPTIONS_MEASURE]}
    )
    app.layout = html.Div([
        dcc.Graph(figure=fig)
    ])

