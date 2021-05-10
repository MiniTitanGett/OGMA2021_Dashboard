######################################################################################################################
"""
saving_functions.py

stores all functions used for saving graph layouts
"""
######################################################################################################################
# External Packages
import os
import json
import pyodbc

# Internal Packages
import config

# dict to save all of the saved graphs
saved_layouts = {}


# maps the name of the graph to the attributes you want to store
def save_graph_state(name, attributes):
    """
    :param attributes: list of all of the attributes that defines the unique layout to be saved
    :param name: the title of the layout (graph title)
    """
    saved_layouts[name] = attributes
    # print(saved_graphs)  # delete when done testing


# loads the saved graphs into a dictionary
def load_saved_graphs():
    """
    loads the saved layouts into the saved_layouts dictionary upon dashboard startup
    """
    if os.stat('apps/app0003/saved_layouts.json').st_size != 0:
        with open('apps/app0003/saved_layouts.json') as json_file:
            saved_graphs_temp = json.load(json_file)
            for key in saved_graphs_temp:
                save_graph_state(key, saved_graphs_temp[key])
        json_file.close()


load_saved_graphs()


# saves the graph layout to the saved layouts file
def save_layout_to_file(layouts):
    """
    saves the layouts to the json file
    :param layouts: the dictionary containing all of the saved layouts
    """
    j = json.dumps(layouts, sort_keys=True)
    with open('apps/app0003/saved_layouts.json', 'w') as file:
        file.write(j)
        file.close()


def save_layout_to_db(graph_title):

    if config.CONNECTION_STRING is None:
        return

    conn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=PANDA\\DEV_COLLATION_01;DATABASE=OPEN_Dev_NB;Trusted_Connection=yes',
        autocommit=True);
    j = json.dumps(saved_layouts[graph_title], sort_keys=True)
    report_name = 'Report_Ext_' + graph_title.replace(' ', '_')

    query = """\
    declare @p_parent_char_id int
    declare @p_result_status varchar(255)
    exec dbo.opp_char_ancestors_popt2 {}, \'{}\', 1, \'{}\', \'{}\', @p_parent_char_id output, @p_result_status output
    select @p_parent_char_id as parent_char_id, @p_result_status as result_status
    """.format(297509564, 'Create',
               'LocalSystemChar|System||SystemChar|Templates||Templates|TemplatesReportDesigner||TemplatesReportDesigner|CustomReports||CustomReports|' + report_name + '||',
               'PYTHON_DASH')

    cursor = conn.cursor()
    cursor.execute(query)

    results = cursor.fetchone()

    # ignore result status for now

    parent_char_id = results.parent_char_id

    query = """\
    declare @p_char_id int
    declare @p_result_status varchar(255)
    exec dbo.opp_create_char {}, @p_char_id output, {}, null, null, 1, null, 1,
    \'{}\', \'{}\', null, \'{}\', \'{}\', null, null, null, null, null, null, null, null, null, null, null, \'{}\',
    @p_result_status output
    select @p_char_id as char_id, @p_result_status as result_status
    """.format(297509564, parent_char_id, report_name, 'layoutFile', 'Dash', report_name + '.xml', 'PYTHON_DASH')

    cursor.execute(query)

    results = cursor.fetchone()

    # ignore result status for now

    char_id = results.char_id

    query = """\
    declare @p_result_status varchar(255)
    exec dbo.opp_addgeteditdeletefind_clob {}, \'Add\', {}, \'{}\', \'application/json\', \'{}\', null, null, null, null, null, null,
    @p_result_status output
    select @p_result_status as result_status
    """.format(297509564, char_id, report_name + '.xml', j)

    cursor.execute(query)

    results = cursor.fetchone()

    # ignore result status for now

    cursor.close()
    del cursor


#  function for deleting line from text file
def delete_layout(key, layouts):
    """
    removes selected layouts from the json file
    :param key: the title of the graph, this is the key in the dictionary of saved layouts
    :param layouts: the dictionary containing all of the saved layouts
    """
    if os.stat('apps/app0003/saved_layouts.json').st_size != 0:
        with open('apps/app0003/saved_layouts.json', 'r') as file:
            saved_graphs_temp = json.load(file)
            del saved_graphs_temp[key]
            del layouts[key]
            file.close()
        with open('apps/app0003/saved_layouts.json', 'w') as file:
            j = json.dumps(saved_graphs_temp, sort_keys=True)
            file.write(j)
            file.close()
