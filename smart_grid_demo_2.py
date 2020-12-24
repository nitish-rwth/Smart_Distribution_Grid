# Smart grid Scenario with CMS/EMS control

import mosaik
from time import process_time
import pandapower as pp
import cosim_mosaik.simulators.Smart_Home.Simulator.methods as methods
from cosim_mosaik.simulators.Smart_Home.Model.methods import create_house, read_from_json


sim_config = {
    'PandaPower': {
        'python': 'cosim_mosaik.simulators.pandapower_api.pandapower_api:PandaPower',
    },
    'Collector': {
        'python': 'cosim_mosaik.simulators.mosaik_collector.mosaik_collector:Collector',
    },
    'HomeModel': {
        'python': 'cosim_mosaik.simulators.Smart_Home.Simulator.simulator:HomeModel',
    },
    'CSV': {
        'python': 'cosim_mosaik.simulators.mosaik_csv.mosaik_csv:CSV'
    },
}

# Function to create smart homes based on JSON config
house_dict = read_from_json('cosim_mosaik/simulators/Smart_Home/Model/Data/example2.json')
houses = create_house(house_dict, 1)

start_time = process_time()

# Simulation parameters
START = '01.08.2019 00:00'
END = 24 * 60 * 60  # 1 hour in seconds
granularity = 15  # value in minutes
step_size = granularity * 60  # minutes to seconds

world = mosaik.World(sim_config)

# Connect profiles to smart homes
number_of_profiles = 20

# Dictionaries for mapping elements
Dict1 = dict()
Dict2 = dict()

# Start Simulators
en_sim = world.start('PandaPower', step_size=step_size)
collector = world.start('Collector', step_size=step_size)
wrapper = world.start('HomeModel', step_size=step_size)

# Starting CSV simulators
ems_sim = world.start('CSV', sim_start=START, datafile='data/loads/loads_ems_new.csv')
pv_sim = world.start('CSV', sim_start=START, datafile='data/generators/pv1.csv')
load_sim = world.start('CSV', sim_start=START, datafile='data/loads/loads_15min_new.csv')

# Instantiate models
grid = en_sim.Grid(gridfile='data/grids/MV_LV_grid.json').children
grid1 = pp.from_json('data/grids/MV_LV_grid.json')
monitor = collector.Monitor()
smart_homes = wrapper.HomeModel.create(len(houses), house_list=houses)

# DEFINITION: Loads -> negative power; Generators -> positive power
ems_values = ems_sim.ems.create(1)
load_values = load_sim.loads.create(1)
pv_values = pv_sim.pv.create(1)


def main():

    # Connect smart homes to Grid/ Automatic element mapping
    # Getting indexes from pandapower network
    Dict1['load'] = methods.get_element_index(grid1.load.name)
    Dict1['trafo'] = methods.get_element_index(grid1.trafo.name)
    Dict1['line'] = methods.get_element_index(grid1.line.name)
    Dict1['bus'] = methods.get_element_index(grid1.bus.name)

    # Getting entity indexes from Mosaik load entity - 'grid'
    Dict2['load'] = methods.get_index_entity(grid, 'load')
    Dict2['trafo'] = methods.get_index_entity(grid, 'trafo')
    Dict2['line'] = methods.get_index_entity(grid, 'line')
    Dict2['bus'] = methods.get_index_entity(grid, 'bus')

    # Mapping Load, line names to their Grid ids
    load_dict = methods.mapping_dict(Dict1['load'], Dict2['load'])
    # trafo_dict = mapping_dict(Dict1['trafo'], Dict2['trafo'])
    line_dict = methods.mapping_dict(Dict1['line'], Dict2['line'])
    bus_dict = methods.mapping_dict(Dict1['bus'], Dict2['bus'])

    # Smart home loads mapped to corresponding Grid entities
    home_dict = methods.connect_homes(load_dict, smart_homes)

    # Running grid and smart home simulator
    profile_id = 0
    print('\n The smart home (with CMS/EMS) and grid simulations are now running...')

    for gids, home in home_dict.items():

        id_str = '{id:02d}'.format(id=profile_id % number_of_profiles + 1)

        # Smart home connections
        world.connect(load_values[0], home, ('P_H{id}'.format(id=id_str), 'P_Load'))
        world.connect(load_values[0], home, ('Q_H{id}'.format(id=id_str), 'Q_Load'))
        world.connect(pv_values[0], home, ('P_PV{id}'.format(id=id_str), 'P_PV'))
        # world.connect(ems_values[0], home, ('P_H{id}'.format(id=id_str), 'P_ems'))

        # Smart home to grid connections
        world.connect(home, grid[gids], ('P_house_out', 'p_mw'))
        world.connect(home, grid[gids], ('Q_house_out', 'q_mvar'))

        profile_id += 1

        # Connect collectors to Grid Trafos/Lines
        for gid in line_dict.keys():
            # world.connect(grid[gid], monitor, 'p_from_mw')
            world.connect(grid[gid], monitor, 'loading_percent')

        # for gid in bus_dict.keys():
        #     world.connect(grid[gid], monitor, 'p_mw')

    # Run Simulation
    world.run(until=END)


if __name__ == '__main__':

    main()
    # Calculate the run-time for the entire simulation
    print("\n Simulation run time was:", process_time() - start_time, "seconds")
