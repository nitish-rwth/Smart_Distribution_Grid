# Methods for CMS model
from warnings import warn

e_flex = 392  # (in kWh)
fail_counter = 0


def check_line_loading(loading, line_name, power):

    if loading >= 90:
        warn(str(line_name) + ' is overloaded!!')
        # Power deficit on the receiving bus (in kW)
        P_set = (-1) * ((loading-90)/100) * (power*100/loading) * 1000
        return True, P_set

    elif loading < 80:  # Normal Loading
        # Power surplus on the receiving bus (in kW)
        P_set = ((80 - loading) / 100) * (power * 100 / loading) * 1000
        return False, P_set

    elif 80 <= loading < 90:  # Raise warning but do nothing
        warn(str(line_name) + ' is critical!!')
        return False, None


def power_flex_aggregator(entities, load_dict, bus_name):

    for eid, bus in entities.items():
        if (bus['etype'] == 'bus') and (bus_name == bus['name']):

            # Set bus flex params to 0
            bus['p_min_flex'] = 0
            bus['p_max_flex'] = 0

            # Aggregating flex values for all connected loads
            for eid1, load in entities.items():
                if (load['etype'] == 'load') and (eid1 in load_dict.keys()):
                    bus['p_min_flex'] += load['p_min_flex']
                    bus['p_max_flex'] += load['p_max_flex']

            return bus['p_min_flex'], bus['p_max_flex']


def energy_flex_aggregator(entities, load_dict, bus_name):

    for eid, bus in entities.items():
        if (bus['etype'] == 'bus') and (bus_name == bus['name']):

            # Set bus flex params to 0
            bus['e_min_flex'] = 0
            bus['e_max_flex'] = 0

            # Aggregating flex values for all connected loads
            for eid1, load in entities.items():
                if (load['etype'] == 'load') and (eid1 in load_dict.keys()):
                    bus['e_min_flex'] += load['e_min_flex']
                    bus['e_max_flex'] += load['e_max_flex']

            return bus['e_min_flex'], bus['e_max_flex']


def get_loads(entities, bus_index, net):
    load_bus = None
    dict1 = dict()

    for index, row in net.bus.iterrows():
        if index == bus_index:
            load_bus = row['name']

    for eid, load in entities.items():
        if (load['etype'] == 'load') and (load['zone'] == load_bus):
            dict1[eid] = load['name']

    return dict1, load_bus


def set_load_params(entities, load_dict, flag, cms_power_set):
    P_set = cms_power_set / len(load_dict)

    for eid, entity in entities.items():
        if (entity['etype'] == 'load') and (eid in load_dict.keys()):

            # Congestion detected
            if flag is True:
                entity['cms_toggle'] = 1
                entity['P_set'] = P_set

            # No Congestion detected
            elif flag is False:
                entity['cms_toggle'] = 0
                entity['P_set'] = 0


# Mapping functions for Smart Grid Mosaik Scenario
def get_element_index(element):
    element_dict = {}

    for i in range(0, len(element)):
        # Residential load dict
        if 'Residential' in element[i]:
            element_dict[i] = element[i]

        # Transformer dict
        elif 'MV-LV-Trafo' in element[i]:
            element_dict[i] = element[i]

        # Line dict
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
        warn('Smart homes count is not the same between Grid/CMS and Model!!')
    return map_dict


# CMS specific load mapping functions
def connect_cms_entities(grid_entity, cms, entity_type):

    # Dictionaries for mapping elements
    Dict1 = dict()
    Dict2 = dict()

    Dict1[entity_type] = get_element_index(grid_entity.name)

    # Getting entity indexes from Mosaik entity - 'grid'
    Dict2[entity_type] = get_index_entity(cms, entity_type)

    # Mapping Load, Line names to their Grid ids
    cms_entity_dict = mapping_dict(Dict1[entity_type], Dict2[entity_type])

    return cms_entity_dict


def connect_grid_entities(grid_entity, grid, entity_type):

    # Dictionaries for mapping elements
    Dict1 = dict()
    Dict2 = dict()

    Dict1[entity_type] = get_element_index(grid_entity.name)

    # Getting entity indexes from Mosaik load entity - 'grid'
    Dict2[entity_type] = get_index_entity(grid, entity_type)

    # Mapping Load, Line names to their Grid ids
    grid_entity_dict = mapping_dict(Dict1[entity_type], Dict2[entity_type])

    return grid_entity_dict


def connect_grid_sgen(grid):

    Dict1 = dict()

    for gid, entity in enumerate(grid):
        if entity.type == 'sgen':
            entity_name = entity.eid.partition(',')[2]
            Dict1[gid] = entity_name

    return Dict1


def congestion_manager(entities, attrs, net, step_size, sim_time):

    hours = step_size/3600
    flag, P_set = check_line_loading(attrs['loading_percent'], attrs['name'], attrs['bus_p_mw'])
    P_actual = 0
    p_error = 0
    loads, bus = get_loads(entities, attrs['to_bus'], net)

    # Get bus flex buffer values
    e_min, e_max = energy_flex_aggregator(entities, loads, bus)
    p_min, p_max = power_flex_aggregator(entities, loads, bus)

    if len(loads) > 1:
        if flag is True:  # CMS assumes control of load entities

            # Check power limit violations
            if p_min <= P_set <= p_max:
                P_actual = P_set
            elif P_set < p_min:
                p_error = P_set - p_min
                P_actual = p_min
                warn('Set Power demand by CMS exceeded bus capacity by:' + str(p_error) + 'kW')
                warn('Set power will be reduced to a safe limit')

            # Check Energy Buffer
            E_set = P_actual * hours
            if e_min <= E_set <= e_max:
                pass

            elif E_set < e_min:  # Buffer Violation
                warn('Flex buffer is not enough to participate at bus: ' + str(bus))
                flag = False
                P_actual = 0
                p_error = P_set

                global fail_counter
                fail_counter += 1

            # Initialize/Reset CMS load entities
            set_load_params(entities, loads, flag, P_actual)

        elif (flag is False) and (P_set is not None):  # No critical loading detected, ready for buffer control

            if ((-1) * e_flex) < e_min:  # Charge flex buffer
                warn('Flex buffer is below set minimum')
                # Power necessary to restore buffer
                P_actual = (e_min + e_flex) / hours

                # Line loading violation check
                if P_actual <= P_set:
                    pass
                else:
                    P_actual = P_set

                # Buffer Power limit violation
                if P_actual > p_max:
                    p_error = P_set - p_max
                    P_actual = p_max
                    warn('Power set by CMS exceeded bus capacity by:' + str(p_error) + 'kW')
                    warn('Set power will be reduced to a safe limit')

                flag = True  # CMS ready to assume control of smart homes

            elif ((-1) * e_flex) >= e_min:  # Dont Charge flex buffer
                P_set = 0

            # Initialize/Reset CMS load entities
            set_load_params(entities, loads, flag, P_actual)

        elif (flag is False) and (P_set is None):  # Critical loading, CMS standby
            P_set = 0
            # Initialize/Reset CMS load entities
            set_load_params(entities, loads, flag, P_actual)

    # Update bus power parameters
    for eid, entity in entities.items():
        if (entity['etype'] == 'bus') and (bus == entity['name']):

            # Set bus power params
            entity['p_set'] = P_actual
            entity['p_demand'] = P_set
            entity['p_error'] = p_error

    # if bus == 'MV Bus 2':
    #     e_min, e_max = energy_flex_aggregator(entities, loads, bus)
    #     print('Current energy buffer is:', e_min, 'at step:', sim_time / step_size)
    #     # print('Current flag is:', flag, 'at step:', sim_time / step_size, 'at bus:', bus)
    #     print('Current Bus set power demand is:', P_set)
    #     print('Current fail Counter is:', fail_counter)
