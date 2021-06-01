######################################################################################################################
"""
hierarchy.py

contains helper functions for, and layout of, the hierarchy filter
"""
######################################################################################################################

# External Packages
import time

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

# Internal Modules
from apps.OPG001.data import get_label, session, CLR


# Contents:
#   HELPER FUNCTIONS
#       - generate_dropdown()
#       - generate_history_button()
#   LAYOUT
#       - get_hierarchy_layout()


# ***********************************************HELPER FUNCTIONS****************************************************

# helper function to generate hierarchy dropdown
def generate_dropdown(tile, df_name, nid_path):
    if df_name:
        # using a subset of our dataframe, turn it into a multiindex df, and access unique values for option
        df = session[df_name][['H1', 'H2', 'H3', 'H4', 'H5', 'H6']]
        hierarchy_nid_list = list(nid_path.split("^||^"))[1:]
        l = len(hierarchy_nid_list)
        if l == 6:
            option_list = []
        elif l != 0:
            df = df.set_index(['H{}'.format(i + 1) for i in range(l)])
            option_list = df.loc[tuple(hierarchy_nid_list)]['H{}'.format(l + 1)].dropna().unique()
        else:
            option_list = df['H1'].unique()
        options = [{'label': i, 'value': i} for i in option_list]

        return dcc.Dropdown(
            id={'type': 'hierarchy_specific_dropdown', 'index': tile},
            options=options,
            multi=False,
            placeholder='{}...'.format(get_label('Select')))
    else:
        return dcc.Dropdown(
            id={'type': 'hierarchy_specific_dropdown', 'index': tile},
            options=None,
            multi=False,
            placeholder='{}...'.format(get_label('Select')))


# helper function to generate a hierarchy button for hierarchy path
def generate_history_button(name, index, tile):
    return html.Button(
        name,
        id={'type': 'button: {}'.replace("{}", str(tile)), 'index': index},
        n_clicks=0,
        style={'background': 'none', 'border': 'none', 'padding': '5px', 'color': '#006699',
               'cursor': 'pointer', 'text-align': 'center', 'text-decoration': 'underline', 'display': 'inline-block'})


# ***********************************************LAYOUT***************************************************************

# get hierarchy layout
def get_hierarchy_layout(tile, df_name, hierarchy_toggle, level_value, graph_all_toggle, nid_path, df_const):
    if df_name and df_const is not None:
        hierarchy_nid_list = nid_path.split("^||^")
        hierarchy_button_path = []
        for nid in hierarchy_nid_list:
            if nid == "root":
                continue
            button = generate_history_button(nid, len(hierarchy_button_path), tile)
            hierarchy_button_path.append(button)
        return [
            html.H6(
                "{}:".format('Hierarchy'),
                style={'color': CLR['text1'], 'margin-top': '20px', 'display': 'inline-block', 'text-align': 'none'}),
            # Hierarchy level filter vs specific node toggle switch
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("Level Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("Specific Item")), value='Specific Item')],
                id={'type': 'hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'hierarchy_level_dropdown', 'index': tile},
                    options=[{'label': get_label(x), 'value': x} for x in df_const[df_name]['HIERARCHY_LEVELS']],
                    multi=False,
                    value=level_value,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center', 'margin-top': '10px'},
                    placeholder='{}...'.format(get_label('Select')))],
                id={'type': 'hierarchy_level_filter', 'index': tile},
                style={} if hierarchy_toggle == 'Level Filter' else {'display': 'none'}),
            # Hierarchy Specific Filter Menu
            html.Div([
                html.Div(
                    children=hierarchy_button_path if hierarchy_button_path else [],
                    id={'type': 'hierarchy_display_button', 'index': tile},
                    style={'display': 'inline-block', 'overflow-x': 'scroll', 'width': '100%', 'whiteSpace': 'nowrap',
                           'height': '60px'}),
                dcc.Checklist(
                    id={'type': 'graph_children_toggle', 'index': tile},
                    options=[{'label': get_label('Graph All in Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('Top'),
                            id={'type': 'hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'}),
                        html.Button(
                            get_label('Back'),
                            id={'type': 'hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_dropdown(tile, df_name, nid_path),
                        id={'type': 'hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})],
                    style={'display': 'flex'})],
                id={'type': 'hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'} if hierarchy_toggle == 'Level Filter' else {})
        ]
    else:
        return [
            html.H6(
                "{}:".format('Hierarchy'),
                style={'color': CLR['text1'], 'margin-top': '20px', 'display': 'inline-block', 'text-align': 'none'}),
            # Hierarchy level filter vs specific node toggle switch
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("Level Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("Specific Item")), value='Specific Item')],
                id={'type': 'hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'hierarchy_level_dropdown', 'index': tile},
                    options=None,
                    multi=False,
                    value=level_value,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center', 'margin-top': '10px'},
                    placeholder='{}...'.format(get_label('Select')))],
                id={'type': 'hierarchy_level_filter', 'index': tile},
                style={} if hierarchy_toggle == 'Level Filter' else {'display': 'none'}),
            # Hierarchy Specific Filter Menu
            html.Div([
                html.Div(
                    children=[],
                    id={'type': 'hierarchy_display_button', 'index': tile},
                    style={'display': 'inline-block', 'overflow-x': 'scroll', 'width': '100%', 'whiteSpace': 'nowrap',
                           'height': '60px'}),
                dcc.Checklist(
                    id={'type': 'graph_children_toggle', 'index': tile},
                    options=[{'label': get_label('Graph All in Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('Top'),
                            id={'type': 'hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'}),
                        html.Button(
                            get_label('Back'),
                            id={'type': 'hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_dropdown(tile, df_name, nid_path),
                        id={'type': 'hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})],
                    style={'display': 'flex'})],
                id={'type': 'hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'} if hierarchy_toggle == 'Level Filter' else {})
        ]