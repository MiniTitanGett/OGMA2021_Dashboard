######################################################################################################################
"""
hierarchy.py

contains helper functions for, and layout of, the hierarchy filter
"""
######################################################################################################################

# External Packages
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

# Internal Modules
from apps.app0003.data import TREE, HIERARCHY_LEVELS, get_label


def generate_dropdown(tile, state_of_display=None, dropdown_value=None):
    # create a comma delimited string for tree navigation
    if state_of_display is None:
        state_of_display = []
    string_of_names = "root"
    for x in state_of_display:
        string_of_names += (', {}'.format(x['props']['children']))
    if dropdown_value:
        string_of_names += (', {}'.format(dropdown_value))
    # tree navigation logic
    if TREE.get_node(string_of_names).is_leaf():
        options = TREE.parent(TREE.get_node(string_of_names).identifier).data
    else:
        options = TREE.get_node(string_of_names).data
    return dcc.Dropdown(
        id={'type': 'hierarchy_specific_dropdown', 'index': tile},
        options=options,
        multi=False,
        placeholder='{}...'.format('Select'))


def generate_history_button(name, index, tile):
    return html.Button(
        name,
        id={'type': 'button: {}'.replace("{}", str(tile)), 'index': index},
        n_clicks=0,
        style={'background': 'none', 'border': 'none', 'padding': '5px', 'color': '#006699',
               'cursor': 'pointer', 'text-align': 'center', 'text-decoration': 'underline', 'display': 'inline-block'})


def get_hierarchy_layout(tile):
    return html.Div(
        # Hierarchy Filter Div - Wrapper
        style={'textAlign': 'center', 'height': 'auto'},
        children=[
            # Hierarchy level filter vs specific node toggle switch
            html.Div([
                html.P(
                    get_label("Level Filter"),
                    style={'display': 'inline-block', 'position': 'relative', 'bottom': '7px'}),
                daq.BooleanSwitch(
                    id={'type': 'hierarchy-toggle', 'index': tile},
                    on=False,
                    color='#1f77b4',
                    style={'transform': 'scale(0.7)', 'display': 'inline-block'}),
                html.P(
                    get_label("Specific Item"),
                    style={'margin-left': '5px', 'display': 'inline-block', 'position': 'relative', 'bottom': '6px'})],
                style={'margin-left': '15px', 'text-align': 'left'}),
            # Hierarchy Level Filter
            html.Div([
                dcc.Dropdown(
                    id={'type': 'hierarchy_level_dropdown', 'index': tile},
                    options=[{'label': get_label(x), 'value': x} for x in HIERARCHY_LEVELS],
                    multi=False,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center'},
                    placeholder='{}...'.format('Select'))],
                id={'type': 'hierarchy_level_filter', 'index': tile}),
            # Hierarchy Filter
            html.Div([
                html.Div(
                    children=[],
                    id={'type': 'hierarchy_display_button', 'index': tile},
                    style={'display': 'inline-block', 'overflow-x': 'scroll', 'width': '100%', 'whiteSpace': 'nowrap',
                           'height': '60px'}),
                dcc.Checklist(
                    id={'type': 'graph_children_toggle', 'index': tile},
                    options=[{'label': get_label('Graph All in Dropdown'), 'value': 'graph_children'}],
                    value=[],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block'}),
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
                        children=generate_dropdown(tile),
                        id={'type': 'hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})], style={'display': 'flex'})],
                id={'type': 'hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'})
        ])
