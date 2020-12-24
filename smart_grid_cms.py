# Smart grid Scenario with active CMS control

import mosaik
from time import process_time
import pandapower as pp
import cosim_mosaik.simulators.Smart_Cms.methods as methods
from cosim_mosaik.simulators.Smart_Home.Model.methods import create_house, read_from_json

sim_config = {
    'PandaPower': {
        'python': 'cosim_mosaik.simulators.pandapower_api.pandapower_api:PandaPower',
    },
    'Collector': {
        'python': 'cosim_mosaik.simulators.mosaik_collector.mosaik_collector:Collector',
    },
    'CmsModel': {
        'python': 'cosim_mosaik.simulators.Smart_Cms.simulator:CmsModel',
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

# Start Simulators
en_sim = world.start('PandaPower', step_size=step_size)
collector = world.start('Collector', step_size=step_size)
wrapper = world.start('CmsModel', step_size=int(step_size/3))
home_wrapper = world.start('HomeModel', step_size=int(step_size/3))

# Starting CSV simulators
line_sim = world.start('CSV', sim_start=START, datafile='data/schedules/line_loading_schedule.csv')
power_sim = world.start('CSV', sim_start=START, datafile='data/schedules/line_power_schedule.csv')
pv_sim = world.start('CSV', sim_start=START, datafile='data/generators/pv1.csv')
load_sim = world.start('CSV', sim_start=START, datafile='data/loads/loads_15min_new.csv')
sgen_sim = world.start('CSV', sim_start=START, datafile='data/generators/sgen.csv')

# Instantiate grid, CMS, Smart home models
grid1 = pp.from_json('data/grids/MV_LV_grid.json')
grid = en_sim.Grid(gridfile='data/grids/MV_LV_grid.json').children
cms = wrapper.Cms(configfile='data/grids/MV_LV_grid.json').children
smart_homes = home_wrapper.HomeModel.create(len(houses), house_list=houses)
monitor = collector.Monitor()

# Instantiate CSV simulator Models
line_values = line_sim.lines.create(1)
line_power_values = power_sim.lines.create(1)
load_values = load_sim.loads.create(1)
pv_values = pv_sim.pv.create(1)
sgen_values = sgen_sim.sgen.create(1)

# Connect models
number_of_profiles = 20


def main():
    idx, idy = 0, 0

    # Mapping Load, Line names to their CMS ids
    cms_load_connections = methods.connect_cms_entities(grid1.load, cms, 'load')
    cms_line_connections = methods.connect_cms_entities(grid1.line, cms, 'line')
    cms_bus_connections = methods.connect_cms_entities(grid1.bus, cms, 'bus')

    # Mapping Load, Line names to their Grid ids
    grid_load_connections = methods.connect_grid_entities(grid1.load, grid, 'load')
    grid_line_connections = methods.connect_grid_entities(grid1.line, grid, 'line')
    # grid_bus_connections = methods.connect_grid_entities(grid1.bus, grid, 'bus')
    grid_sgen_connections = methods.connect_grid_sgen(grid)

    # Smart homes mapped to corresponding CMS entities
    cms_home_dict = methods.connect_homes(cms_load_connections, smart_homes)

    # Smart home loads mapped to corresponding Grid entities
    grid_home_dict = methods.connect_homes(grid_load_connections, smart_homes)

    # Running grid and smart home simulator
    print('\n The smart grid (with CMS/EMS enabled) simulation is now running...')

    # Line loading prediction input to CMS
    for cid, line in cms_line_connections.items():
        world.connect(line_values[0], cms[cid], (line, 'loading_percent'))
        world.connect(line_power_values[0], cms[cid], (line, 'bus_p_mw'))

    # Connect inputs from (EMS) smart homes to CMS (for flex data)
    for cid, home in cms_home_dict.items():  # Creates cyclic dependency
        world.connect(home, cms[cid], 'e_min_flex')
        world.connect(home, cms[cid], 'e_max_flex')
        world.connect(home, cms[cid], 'p_min_flex')
        world.connect(home, cms[cid], 'p_max_flex')

    # Sgen profiles to grid
    for gid, name in grid_sgen_connections.items():
        world.connect(sgen_values[0], grid[gid], (name, 'p_mw'))

    # CSV to smart home connections
    for gid, home in grid_home_dict.items():
        id_str = '{id:02d}'.format(id=idy % number_of_profiles + 1)
        world.connect(load_values[0], home, ('P_H{id}'.format(id=id_str), 'P_Load'))
        world.connect(load_values[0], home, ('Q_H{id}'.format(id=id_str), 'Q_Load'))
        world.connect(pv_values[0], home, ('P_PV{id}'.format(id=id_str), 'P_PV'))
        idy += 1

    # CMS control on smart homes (time-delayed)
    for cid, home in cms_home_dict.items():
        # Power injection into Smart Home
        world.connect(cms[cid], home, ('P_set', 'P_ems'), time_shifted=True, initial_data={'P_set': 0})
        # Toggle value input to Smart Home
        world.connect(cms[cid], home, 'cms_toggle', time_shifted=True, initial_data={'cms_toggle': 0})

    # EMS control action on the grid (Smart homes to grid)
    for gid, home in grid_home_dict.items():
        world.connect(home, grid[gid], ('P_house_out', 'p_mw'))
        world.connect(home, grid[gid], ('Q_house_out', 'q_mvar'))
        # world.connect(home, monitor, 'P_house_out')
        # world.connect(home, monitor, 'cms_toggle')

    # Monitor grid parameters after control action

    # Line results
    # world.connect(grid[324], monitor, 'loading_percent')
    # world.connect(grid[325], monitor, 'loading_percent')

    # Bus Results
    # world.connect(cms[112], monitor, 'p_set')
    # world.connect(cms[112], monitor, 'p_error')
    # world.connect(cms[112], monitor, 'e_min_flex')
    # world.connect(cms[112], monitor, 'p_demand')

    # House Toggle results
    # world.connect(cms[1091], monitor, 'cms_toggle')
    # world.connect(cms[1091], monitor, 'P_set')

    # House results
    # world.connect(smart_homes[40], monitor, 'P_ems')
    # world.connect(smart_homes[40], monitor, 'cms_toggle')
    # world.connect(smart_homes[40], monitor, 'P_Load')
    # world.connect(smart_homes[40], monitor, 'P_house')
    # world.connect(smart_homes[40], monitor, 'P_control')

    # Run Simulation
    world.run(until=END)


if __name__ == '__main__':

    main()
    # Calculate the run-time for the entire simulation
    print("\n Simulation run time was:", process_time() - start_time, "seconds")
