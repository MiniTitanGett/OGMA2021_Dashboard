######################################################################################################################
"""
hierarchy.py

Contains helper functions for, and layout of, the hierarchy filter.
"""
######################################################################################################################

# External Packages
import dash_core_components as dcc
import dash_html_components as html

# Internal Modules
from apps.dashboard.data import get_label, session

# ***********************************************HELPER FUNCTIONS****************************************************


def generate_dropdown(tile, df_name, nid_path, df_const):
    """Helper function to generate and return hierarchy drop-down."""
    if df_name:
        # using a subset of our dataframe, turn it into a multiindex df, and access unique values for option
        df = session[df_name][['H0', 'H1', 'H2', 'H3', 'H4', 'H5']]
        hierarchy_nid_list = list(nid_path.split("^||^"))[1:]
        llen = len(hierarchy_nid_list)
        if llen == 6:
            option_list = []
        elif llen != 0:
            # df = df.set_index(['H{}'.format(i) for i in range(llen)])
            # option_list = df.loc[tuple(hierarchy_nid_list)]['H{}'.format(llen)].dropna().unique()
            for i in range(llen):
                level = df_const[df_name]["H"+str(i)][hierarchy_nid_list[i]] if \
                                                                        df_name == "OPG011" else hierarchy_nid_list[i]
                df = df.filter(df['H{}'.format(i)] == level)
                df = df.drop('H{}'.format(i))
            option_list = df['H{}'.format(llen)].unique(dropmissing=True)
        else:
            option_list = df['H0'].unique()
        if df_name == "OPG011":
            options = [{'label': i, 'value': i} for i in option_list]
        else:
            options = [{'label': i, 'value': i} for i in option_list]
        options = sorted(options, key=lambda k: k['label'])

        return dcc.Dropdown(
            id={'type': 'hierarchy_specific_dropdown', 'index': tile},
            options=options,
            multi=False,
            placeholder='{}...'.format(get_label('LBL_Select')))
    else:
        return dcc.Dropdown(
            id={'type': 'hierarchy_specific_dropdown', 'index': tile},
            options=[],
            multi=False,
            placeholder='{}...'.format(get_label('LBL_Select')))


def generate_history_button(name, index, tile, df_name, df_const):
    """helper function to generate and return a hierarchy button for the hierarchy path."""
    return html.Button(
        df_const[df_name]["CATEGORICAL_DATA"]["H" + str(index)]["labels"]
        [name] if isinstance(name, int) else name,
        id={'type': 'button: {}'.replace("{}", str(tile)), 'index': index},
        n_clicks=0,
        style={'background': 'none', 'border': 'none', 'padding': '5px', 'color': '#006699',
               'cursor': 'pointer', 'text-align': 'center', 'text-decoration': 'underline', 'display': 'inline-block',
               'margin-left': str(index * 30) + 'px'})

# ***********************************************LAYOUT***************************************************************


def get_hierarchy_layout(tile, df_name, hierarchy_toggle, level_value, graph_all_toggle, nid_path, df_const):
    """Gets and returns the hierarchy layout."""
    if df_name is not None and df_const is not None:
        hierarchy_nid_list = nid_path.split("^||^")
        hierarchy_button_path = []
        for nid in hierarchy_nid_list:
            if nid == "root":
                continue
            button = generate_history_button(nid, len(hierarchy_button_path), tile, df_name, df_const)
            hierarchy_button_path.append(button)
        return [
            html.Div(
                children=[
                    html.H6(
                        "{}:".format('Hierarchy'),
                        className='date-picker-option-title'),
                    html.I(
                        html.Span(
                            get_label("LBL_Hierarchy_Info"),
                            className='save-symbols-tooltip'),
                        className='fa fa-question-circle-o',
                        id={'type': 'hierarchy-info', 'index': tile},
                        style={'position': 'relative'})],
                id={'type': 'hierarchy-info-wrapper', 'index': tile}
            ),
            # Hierarchy level filter vs specific node toggle switch
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Level_Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("LBL_Specific_Item")), value='Specific Item')],
                id={'type': 'hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'hierarchy_level_dropdown', 'index': tile},
                    options=[{'label': get_label('LBL_' + x, df_name), 'value': x} for x in
                             df_const[df_name]['HIERARCHY_LEVELS']],
                    multi=False,
                    value=level_value,
                    clearable=False,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center', 'margin-top': '10px'},
                    placeholder='{}...'.format(get_label('LBL_Select')))],
                id={'type': 'hierarchy_level_filter', 'index': tile},
                style={} if hierarchy_toggle == 'Level Filter' else {'display': 'none'}),
            # Hierarchy Specific Filter Menu
            html.Div([
                html.Div(
                    children=hierarchy_button_path if hierarchy_button_path else [],
                    id={'type': 'hierarchy_display_button', 'index': tile},
                    style={'display': '', 'overflow': 'scroll', 'width': '100%',
                           'height': '100px', 'padding left': '5px'}),
                dcc.Checklist(
                    id={'type': 'graph_children_toggle', 'index': tile},
                    options=[{'label': get_label('LBL_Graph_All_In_Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('LBL_Top'),
                            id={'type': 'hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'}),
                        html.Button(
                            get_label('LBL_Back'),
                            id={'type': 'hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_dropdown(tile, df_name, nid_path, df_const),
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
                className='date-picker-option-title'),
            # Hierarchy level filter vs specific node toggle switch
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Level_Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("LBL_Specific_Item")), value='Specific Item')],
                id={'type': 'hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'hierarchy_level_dropdown', 'index': tile},
                    options=[],
                    multi=False,
                    value=level_value,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center', 'margin-top': '10px'},
                    placeholder='{}...'.format(get_label('LBL_Select')))],
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
                    options=[{'label': get_label('LBL_Graph_All_In_Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('LBL_Top'),
                            id={'type': 'hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0  0 0'}),
                        html.Button(
                            get_label('LBL_Back'),
                            id={'type': 'hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_dropdown(tile, df_name, nid_path, df_const),
                        id={'type': 'hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})],
                    style={'display': 'flex'})],
                id={'type': 'hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'} if hierarchy_toggle == 'Level Filter' else {})
        ]
