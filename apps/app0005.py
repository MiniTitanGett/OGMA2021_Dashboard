import pandas as pd
import numpy as np
import app
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pyodbc
import json
import plotly.express as px
from apps.OPG001.functionality_callbacks import __update_graph

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

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

app = app.get_app('0005/')

app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='year-slider',
        min=df['year'].min(),
        max=df['year'].max(),
        value=df['year'].min(),
        marks={str(year): str(year) for year in df['year'].unique()},
        step=None
    )
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('year-slider', 'value')])
def update_figure(selected_year):
    filtered_df = df[df.year == selected_year]
    traces = []
    for i in filtered_df.continent.unique():
        df_by_continent = filtered_df[filtered_df['continent'] == i]
        traces.append(dict(
            x=df_by_continent['gdpPercap'],
            y=df_by_continent['lifeExp'],
            text=df_by_continent['country'],
            mode='markers',
            opacity=0.7,
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=i
        ))

    return {
        'data': traces,
        'layout': dict(
            xaxis={'type': 'log', 'title': 'GDP Per Capita',
                   'range': [2.3, 4.8]},
            yaxis={'title': 'Life Expectancy', 'range': [20, 90]},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            transition={'duration': 500},
        )
    }
