"""This is the program to encapsulate smart homes as a mosaik compatible model"""

import pandas as pd
import re
from cosim_mosaik.simulators.Smart_Home.Model.ems import EMS
from warnings import warn

# Pandas for result analysis
ems_headers = ['P_demand', 'Reward', 'Toggle value', 'P_adjusted', 'Time (hours)']
house_headers = ['P_House', 'P_Set', 'P_PV', 'P_res', 'Time (hours)', 'P_load']

# Electricity prices for reward model
unit_price = 0.08  # euros/kWh
buy_price = 0.07  # euros/kWh
sell_price = 0.09  # euros/kWh
P_set = 4  # Power set by EMS for most optimal power demand


class Smart_home:
    def __init__(self, home, params):
        self.params = {}
        self.name = home.name
        self.number = home.number
        self.house = home
        self.ems = EMS(home)
        self.consumption = 0

        # Collecting battery names for csv
        self.battery_headers = []
        self.ev_headers = []

        for battery in self.ems.Batteries:
            self.battery_headers.append('SOC')
        self.battery_headers.append('Control_Power')
        self.battery_headers.append('Time (hours)')

        # Collecting EV names for csv
        for ev in self.ems.EV:
            self.ev_headers.append('SOC')
        self.ev_headers.append('Control_Power')
        self.ev_headers.append('Time (hours)')

        for param in params:
            self.params[param] = 0

        EMS_result = pd.DataFrame(columns=ems_headers)
        House_result = pd.DataFrame(columns=house_headers)
        Battery_result = pd.DataFrame(columns=self.battery_headers)
        Ev_result = pd.DataFrame(columns=self.ev_headers)

        self.results = [EMS_result, House_result, Battery_result, Ev_result]
        self.headers = [ems_headers, house_headers, self.battery_headers, self.ev_headers]

    def getparam(self, param):
        return self.params[param]

    def step(self, step_size, time, inputs=None):

        battery_values = []
        ev_values = []
        list_of_results = []
        hours = step_size/3600
        self.params['P_control'] = 0
        self.ems.battery_control = 0
        p_reward = 0

        # Getting model attributes values from input dictionary
        # print('Current simulation time is:', time)
        # print('\n The input dict is as follows:')
        # print(inputs)

        for attr, simulator in inputs.items():
            for name, value in simulator.items():
                # Parameters coming from CSV simulator only
                if re.search('loads', name):
                    self.params[attr] = value
                elif re.search('pv', name):
                    self.params[attr] = value

                # Parameters coming from CMS simulator
                elif re.search('ems', attr):
                    self.params[attr] = value
                elif re.search('toggle', name) or re.search('toggle', attr):
                    self.params[attr] = int(value)

        # Collecting Battery SOC
        for battery in self.ems.Batteries:
            battery_values.append(battery.params['soc'])

        for ev in self.ems.EV:
            ev_values.append(ev.params['soc'])

        # Flex Parameters
        self.params["e_max_flex"], self.params["e_min_flex"] = self.ems.report_energy_flex()
        self.params["p_max_flex"], self.params["p_min_flex"] = self.ems.report_power_flex()

        # Smart Home only Scenario
        # self.params["P_house"] = self.params["P_Load"]  # House with load only
        self.params["P_house"] = self.params["P_Load"] - self.params["P_PV"]
        P_res = self.params["P_house"]
        P_excess = self.params["P_PV"] - self.params["P_Load"]

        # EMS only Scenarios
        if self.params['cms_toggle'] == 0:
            self.params['P_ems'] = 0

            # if P_excess > 0:
            #     # Power absorbed due to excess solar
            #     self.ems.energy_manager(step_size / 60, P_excess)
            #     self.params["P_control"] = self.ems.absorbed_power

            if P_res > P_set:
                # Power delivered due to insufficient solar
                self.ems.energy_manager(step_size / 60, (-1) * (P_res-P_set))
                self.params["P_control"] = self.ems.injected_power

            elif P_res < P_set:
                # Power absorbed due to lean loading
                self.ems.energy_manager(step_size / 60, (P_set-P_res))
                self.params["P_control"] = self.ems.absorbed_power

        # CMS + EMS Scenarios (CMS command takes precedence)
        elif self.params['cms_toggle'] == 1:

            if P_excess > 0:
                # Power produced due to excess solar
                self.params["P_ems"] = self.params["P_ems"] + P_excess

            # Control action by house EMS
            self.ems.energy_manager(step_size/60, self.params["P_ems"])

            if self.params["P_ems"] < 0:  # Inject power in the bus
                self.params["P_control"] = self.ems.injected_power
                self.params['P_ems_out'] = round(self.ems.injected_power / 1000, 4)
                self.params['ems_earning'] += (-1) * self.ems.injected_power * sell_price * hours

            elif self.params["P_ems"] > 0:  # Absorb power from the bus
                self.params["P_control"] = self.ems.absorbed_power
                self.params['P_ems_out'] = round(self.ems.absorbed_power / 1000, 4)
                self.params['ems_earning'] += self.ems.absorbed_power * buy_price * hours

            p_reward = self.params["P_control"]

        else:
            warn('Toggle value undefined by CMS !!')

        # Adjusting house power demand after EMS action
        self.params["P_house"] = P_res + self.params["P_control"]
        self.consumption += self.params["P_house"] * unit_price * hours

        # House Power input to the grid
        self.params['P_house_out'] = round(self.params["P_house"] / 1000, 4)
        self.params['Q_house_out'] = round(self.params["Q_Load"] / 1000, 4)

        # To be disabled in smart grid connection
        # Generating output of EMS control action

        plot_scaling = time / 3600  # Converting time to hours
        ems_values = [self.params["P_ems"], self.params["ems_earning"], int(self.params["cms_toggle"]),
                      p_reward, plot_scaling]
        house_values = [self.params["P_house"], P_set, self.params["P_PV"], P_res,
                        plot_scaling, self.params["P_Load"]]
        battery_values.append(self.ems.battery_control)
        battery_values.append(plot_scaling)
        ev_values.append(self.ems.ev_control)
        ev_values.append(plot_scaling)

        # Preparing results CSV
        list_of_values = [ems_values, house_values, battery_values, ev_values]

        for (header, value) in zip(self.headers, list_of_values):
            list_of_results.append(dict(zip(header, value)))

        for j in range(0, len(list_of_results)):
            self.results[j] = self.results[j].append(list_of_results[j], ignore_index=True)
