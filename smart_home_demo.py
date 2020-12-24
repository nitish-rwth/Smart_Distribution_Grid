import mosaik
from time import process_time
from cosim_mosaik.simulators.Smart_Home.Model.methods import create_house, read_from_json

sim_config = {
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

house_dict = read_from_json('cosim_mosaik/simulators/Smart_Home/Model/Data/example1.json')
houses = create_house(house_dict, 1)
start_time = process_time()

START = '01.08.2019 00:00'
END = 24 * 60 * 60  # 1 hour in seconds
granularity = 15  # value in minutes
step_size = granularity * 60  # minutes to seconds

world = mosaik.World(sim_config)

# Start Simulators
collector = world.start('Collector', step_size=step_size)
wrapper = world.start('HomeModel', step_size=step_size)

# Starting CSV simulators
ems_sim = world.start('CSV', sim_start=START, datafile='data/schedules/ems_schedule.csv')
pv_sim = world.start('CSV', sim_start=START, datafile='data/generators/pv1.csv')
load_sim = world.start('CSV', sim_start=START, datafile='data/loads/loads_15min_new.csv')
toggle_sim = world.start('CSV', sim_start=START, datafile='data/schedules/toggle_schedule.csv')

# Instantiate models
monitor = collector.Monitor()
smart_homes = wrapper.HomeModel.create(len(houses), house_list=houses)

# DEFINITION: Loads -> negative power; Generators -> positive power
ems_values = ems_sim.ems.create(1)
load_values = load_sim.loads.create(1)
pv_values = pv_sim.pv.create(1)
toggle_values = toggle_sim.toggle.create(1)
number_of_profiles = 20


def main():

    # Connect models
    for idx, home in enumerate(smart_homes):

        id_str = '{id:02d}'.format(id=idx % number_of_profiles + 1)
        world.connect(load_values[0], home, ('P_H{id}'.format(id=id_str), 'P_Load'))
        world.connect(load_values[0], home, ('Q_H{id}'.format(id=id_str), 'Q_Load'))
        world.connect(pv_values[0], home, ('P_PV{id}'.format(id=id_str), 'P_PV'))
        world.connect(ems_values[0], home, ('profile_{id}'.format(id=id_str), 'P_ems'))
        world.connect(toggle_values[0], home, ('profile_{id}'.format(id=id_str), 'cms_toggle'))

        # Monitoring of results for some houses only (detailed o/p available as csv)
        world.connect(home, monitor, 'P_house')
        world.connect(home, monitor, 'P_Load')
        world.connect(home, monitor, 'P_ems')
        world.connect(home, monitor, 'cms_toggle')

        # world.connect(home, monitor, 'e_max_flex')
        # world.connect(home, monitor, 'e_min_flex')
        # world.connect(home, monitor, 'p_max_flex')
        # world.connect(home, monitor, 'p_min_flex')

    # Run Simulation
    world.run(until=END)


if __name__ == '__main__':

    main()
    # Calculate the run-time for the entire simulation
    print("\n Simulation run time was:", process_time() - start_time, "seconds")

