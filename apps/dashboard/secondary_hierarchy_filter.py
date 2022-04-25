######################################################################################################################
"""
secondary_hierarchy_filter.py

Contains helper functions for, and layout of, the secondary hierarchy filter.
"""
######################################################################################################################

# External Packages
import dash_core_components as dcc
import dash_html_components as html

# Internal Modules
from apps.dashboard.data import get_label, session

# ***********************************************HELPER FUNCTIONS****************************************************


def generate_secondary_dropdown(tile, df_name, nid_path, df_const):
    """Helper function to generate and return document type hierarchy drop-down."""
    if df_name:
        # using a subset of our dataframe, turn it into a multiindex df, and access unique values for option
        hierarchy_level = df_const[df_name]['SECONDARY_HIERARCHY_LEVELS']
        df = session[df_name][['Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier']]
        hierarchy_nid_list = list(nid_path.split("^||^"))[1:]
        llen = len(hierarchy_nid_list)
        if llen == 3:
            option_list = []
        elif llen != 0:
            # df = df.set_index(['H{}'.format(i) for i in range(llen)])
            # option_list = df.loc[tuple(hierarchy_nid_list)]['H{}'.format(llen)].dropna().unique()
            for i in range(llen):
                level = hierarchy_nid_list[i]
                df = df.filter(df[hierarchy_level[i]] == level)
                df = df.drop(hierarchy_level[i])
            option_list = df[hierarchy_level[llen]].unique(dropmissing=True, dropnan=True)
        else:
            option_list = df['Variable Name'].unique()

        # check if the hierarchy level has none variables and assigns to a option list
        if df_name == "OPG010":
            options = [{'label': i, 'value': i} for i in option_list if
                       len(df_const[df_name][hierarchy_level[llen]]) >= 1 and df_const[df_name][hierarchy_level
                       [llen]][0] != ""]
        else:
            options = [{'label': i, 'value': i}
                       for i in option_list if
                       len(df_const[df_name][hierarchy_level[llen]]) >= 1 and df_const[df_name]
                       [hierarchy_level[llen]] != ""]

        options = sorted(options, key=lambda k: k['label'])

        return dcc.Dropdown(
            id={'type': 'secondary_hierarchy_specific_dropdown', 'index': tile},
            options=options,
            optionHeight=30,
            multi=False,
            style={'font-size': '13px'},
            placeholder='{}...'.format(get_label('LBL_Select')))
    else:
        return dcc.Dropdown(
            id={'type': 'secondary_hierarchy_specific_dropdown', 'index': tile},
            options=[],
            optionHeight=30,
            multi=False,
            style={'font-size': '13px'},
            placeholder='{}...'.format(get_label('LBL_Select')))


def generate_secondary_history_button(name, index, tile, df_name, df_const):
    """helper function to generate and return a hierarchy button for the hierarchy path."""
    hierarchy_level = ['Variable Name', 'Variable Name Qualifier', 'Variable Name Sub Qualifier']
    return html.Button(
        name,
        id={'type': 'button: {}'.replace("{}", str(tile)), 'index': index},
        n_clicks=0,
        style={'background': 'none', 'border': 'none', 'padding': '5px', 'color': '#006699',
               'cursor': 'pointer', 'text-align': 'center', 'text-decoration': 'underline', 'display': 'inline-block',
               'margin-left': str(index * 30) + 'px'})

# ***********************************************LAYOUT***************************************************************


def get_secondary_hierarchy_layout(tile, df_name=None, hierarchy_toggle='Level Filter', level_value='Variable Name',
                                          graph_all_toggle=None, nid_path="root", df_const=None):
    """Gets and returns the hierarchy layout."""
    if df_name is not None and df_const is not None:
        hierarchy_nid_list = nid_path.split("^||^")
        hierarchy_button_path = []
        hierarchy_level = df_const[df_name]['SECONDARY_HIERARCHY_LEVELS']
        for nid in hierarchy_nid_list:
            if nid == "root":
                continue
            button = generate_secondary_history_button(nid, len(hierarchy_button_path), tile, df_name, df_const)
            hierarchy_button_path.append(button)
        return [
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Level_Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("LBL_Specific_Item")), value='Specific Item')],
                id={'type': 'secondary_hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'secondary_hierarchy_level_dropdown', 'index': tile},
                    # check if the hierarchy level has none variables and assigns to a option list
                    options=[{'label': get_label('LBL_' + x.replace(' ', '_'), df_name) + " ({0})".format(len(
                        df_const[df_name][x])), 'value': x} for x in hierarchy_level if len(
                        df_const[df_name][x]) >= 1 and df_const[df_name][x][0] is not None ],
                    multi=False,
                    clearable=False,
                    optionHeight=30,
                    value=level_value,
                    style={'color': 'black', 'textAlign': 'center', 'margin-top': '10px', 'font-size': '13px'},
                    placeholder='{}...'.format(get_label('LBL_Select')))],
                id={'type': 'secondary_hierarchy_level_filter', 'index': tile},
                style={} if hierarchy_toggle == 'Level Filter' else {'display': 'none'}),
            # Hierarchy Specific Filter Menu
            html.Div([
                html.Div(
                    children=hierarchy_button_path if hierarchy_button_path else [],
                    id={'type': 'secondary_hierarchy_display_button', 'index': tile},
                    style={'display': '', 'overflow': 'scroll', 'height': '100px', 'padding left': '5px',
                           'max-width': '260px'}),
                dcc.Checklist(
                    id={'type': 'secondary_hierarchy_children_toggle', 'index': tile},
                    options=[{'label': get_label('LBL_Graph_All_In_Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('LBL_Top'),
                            id={'type': 'secondary_hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'}),
                        html.Button(
                            get_label('LBL_Back'),
                            id={'type': 'secondary_hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_secondary_dropdown(tile, df_name, nid_path, df_const),
                        id={'type': 'secondary_hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})],
                    style={'display': 'flex'})],
                id={'type': 'secondary_hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'} if hierarchy_toggle == 'Level Filter' else {})
        ]
    else:
        return [
            # Hierarchy level filter vs specific node toggle switch
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Level_Filter")), value='Level Filter'),
                dcc.Tab(label="{}".format(get_label("LBL_Specific_Item")), value='Specific Item')],
                id={'type': 'secondary_hierarchy-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=hierarchy_toggle,
                style={'display': 'block'}),
            # Hierarchy Level Filter Menu
            html.Div([
                dcc.Dropdown(
                    id={'type': 'secondary_hierarchy_level_dropdown', 'index': tile},
                    options=[],
                    multi=False,
                    optionHeight=30,
                    value=level_value,
                    style={'color': 'black', 'width': '100%', 'textAlign': 'center', 'margin-top': '10px',
                           'font-size': '13px'},
                    placeholder='{}...'.format(get_label('LBL_Select')))],
                id={'type': 'secondary_hierarchy_level_filter', 'index': tile},
                style={} if hierarchy_toggle == 'Level Filter' else {'display': 'none'}),
            # Hierarchy Specific Filter Menu
            html.Div([
                html.Div(
                    children=[],
                    id={'type': 'secondary_hierarchy_display_button', 'index': tile},
                    style={'display': 'inline-block', 'overflow-x': 'scroll', 'width': '100%', 'whiteSpace': 'nowrap',
                           'height': '60px'}),
                dcc.Checklist(
                    id={'type': 'secondary_hierarchy_children_toggle', 'index': tile},
                    options=[{'label': get_label('LBL_Graph_All_In_Dropdown'),
                              'value': 'graph_children'}],
                    value=graph_all_toggle if graph_all_toggle else [],
                    style={'color': 'black', 'width': '100%', 'display': 'inline-block', 'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Button(
                            get_label('LBL_Top'),
                            id={'type': 'secondary_hierarchy_to_top', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0  0 0'}),
                        html.Button(
                            get_label('LBL_Back'),
                            id={'type': 'secondary_hierarchy_revert', 'index': tile},
                            n_clicks=0,
                            style={'min-width': '45px', 'display': 'inline-block', 'padding': '0 0 0 0'})],
                        style={'height': '0px', 'display': 'inline-block'}),
                    html.Div(
                        children=generate_secondary_dropdown(tile, df_name, nid_path, df_const),
                        id={'type': 'secondary_hierarchy_specific_dropdown_container', 'index': tile},
                        style={'color': 'black', 'flex-grow': '1', 'textAlign': 'center', 'display': 'inline-block'})],
                    style={'display': 'flex'})],
                id={'type': 'secondary_hierarchy_specific_filter', 'index': tile},
                style={'display': 'none'} if hierarchy_toggle == 'Level Filter' else {})
        ]
