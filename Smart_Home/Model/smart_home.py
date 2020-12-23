"""Program wrapper to class House and class EMS"""

import pandas as pd
from time import process_time, sleep
from tqdm import tqdm
from cosim_mosaik.simulators.Smart_Home.Model.methods import create_house, read_from_json
from cosim_mosaik.simulators.Smart_Home.Model.ems import EMS
from cosim_mosaik.simulators.Smart_Home.Model.results import write_to_csv, csv_to_plot

smart_homes = []
start_time = process_time()

# Reading power time series data for each house
ems_p = pd.read_csv('data/loads/loads_ems_new.csv', sep=';', header=1)
pv_p = pd.read_csv('data/generators/pv1.csv', sep=';', header=1)
load_p = pd.read_csv('data/loads/loads_15min_new.csv', sep=';', header=1)

# Pandas for result analysis
ems_headers = ['Set_Power (kW)', 'Control_Power (kW)', 'Unbalanced_Power (kW)', 'Intraday_Energy (kWh)', 'Time (hours)']
house_headers = ['P_House (kW)', 'P_Load (kW)', 'P_PV (kW)', 'Time (hours)']

# Simulation run parameters
start = 0
end = 24 * 60  # (hours * minutes)
step_size = 15  # Time in minutes


class Smart_home:
    def __init__(self, home):
        self.name = home.name
        self.number = home.number
        self.house = home
        self.ems = EMS(home)

        # Collecting battery names for csv
        self.battery_headers = []
        self.ev_headers = []

        for battery in self.ems.Batteries:
            self.battery_headers.append(battery.name + '_SOC (%)')
        self.battery_headers.append('Control_Power/Battery (kW)')
        self.battery_headers.append('Time (hours)')

        # Collecting EV names for csv
        for ev in self.ems.EV:
            self.ev_headers.append(ev.name + '_SOC (%)')
        self.ev_headers.append('Control_Power/EV (kW)')
        self.ev_headers.append('Time (hours)')

        EMS_result = pd.DataFrame(columns=ems_headers)
        House_result = pd.DataFrame(columns=house_headers)
        Battery_result = pd.DataFrame(columns=self.battery_headers)
        Ev_result = pd.DataFrame(columns=self.ev_headers)

        self.results = [EMS_result, House_result, Battery_result, Ev_result]
        self.headers = [ems_headers, house_headers, self.battery_headers, self.ev_headers]

    def control_action(self):

        for i in tqdm(range(start, end, step_size)):

            battery_values = []
            ev_values = []
            list_of_results = []

            # Getting data from pandas and house calculations
            P_ems = ems_p['P_H%02d' % self.number]
            P_set = float(P_ems[i]) * ((-1) ** (i % 15))
            P_Load = load_p['P_H%02d' % self.number][i]
            P_PV = pv_p['P_H%02d' % self.number][i]
            P_house = P_Load - P_PV
            P_control = P_set - P_house

            # Collecting Battery SOC
            for battery in self.ems.Batteries:
                battery_values.append(battery.params['soc'])

            for ev in self.ems.EV:
                ev_values.append(ev.params['soc'])

            # Control action on ems
            self.ems.energy_manager(step_size, P_control)

            # Collecting EMS values for results
            ems_values = [P_set, P_control, self.ems.unbalanced_power, self.ems.intraday_e, i / 60]
            house_values = [P_house, P_Load, P_PV, i / 60]
            battery_values.append(self.ems.battery_control)
            battery_values.append(i / 60)
            ev_values.append(self.ems.ev_control)
            ev_values.append(i / 60)

            list_of_values = [ems_values, house_values, battery_values, ev_values]

            for (header, value) in zip(self.headers, list_of_values):
                list_of_results.append(dict(zip(header, value)))

            for j in range(0, len(list_of_results)):
                self.results[j] = self.results[j].append(list_of_results[j], ignore_index=True)

            sleep(0.001)  # Generates a progress bar

        # Write the results of all control steps to csv
        write_to_csv(self.ems, self.results)

        # Plotting results of every EMS and House
        csv_to_plot(self.ems)


# Main program start here
if __name__ == '__main__':

    # Process to create smart homes based on JSON config
    house_dict = read_from_json('cosim_mosaik/simulators/Smart_Home/Model/Data/example1.json')
    houses = create_house(house_dict, 1)

    # Wrap each house as a Smart home (with EMS)
    for house in houses:
        smart_home = Smart_home(house)
        smart_homes.append(smart_home)

    # Running the control step on every EMS
    for smart_home in smart_homes:
        print("\n Running simulation for EMS:", smart_home.ems.name)
        smart_home.control_action()

    # Calculate the run-time for the entire simulation
    print("\n Simulation run time is:", process_time() - start_time, "seconds")
