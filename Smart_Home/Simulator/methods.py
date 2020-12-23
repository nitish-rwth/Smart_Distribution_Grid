# Mapping functions for Smart Grid Mosaik Scenario
from warnings import warn


def get_element_index(element):
    element_dict = {}

    for i in range(0, len(element)):
        # Residential load dict
        if 'Residential' in element[i]:
            element_dict[i] = element[i]

        # Transformer dict
        elif 'MV-LV-Trafo' in element[i]:
            element_dict[i] = element[i]

        # Transformer dict
        elif 'MV_Line' in element[i]:
            element_dict[i] = element[i]

        # Bus dict
        elif 'MV Bus' in element[i]:
            element_dict[i] = element[i]

    return element_dict


def get_index_entity(grid, etype):
    element_dict = dict()

    for i in range(0, len(grid)):
        entity_name = grid[i].eid.partition(',')[2]
        entity_type = grid[i].type

        if 'Residential' in entity_name and entity_type == etype == 'load':
            element_dict[i] = entity_name
        elif 'MV-LV' in entity_name and entity_type == etype == 'trafo':
            element_dict[i] = entity_name
        elif 'MV_Line' in entity_name and entity_type == etype == 'line':
            element_dict[i] = entity_name
        elif 'MV Bus' in entity_name and entity_type == etype == 'bus':
            element_dict[i] = entity_name

    return element_dict


def mapping_dict(a, b):
    map_dict = {}
    if len(a) == len(b):
        for key, value in a.items():
            for key1, value1 in b.items():
                if value == value1:
                    map_dict.update({key1: value})
    else:
        warn('Element/Entity count is not the same between Pandapower and Mosaik!!')
    return map_dict  # Returns a dict of Grid ids mapped to their entity names


def connect_homes(a, b):
    map_dict = {}
    i = 0
    if len(a) == len(b):
        for key, value in a.items():
            map_dict.update({key: b[i]})
            i += 1
    else:
        warn('Smart homes count is not the same between Grid and Model!!')
    return map_dict
