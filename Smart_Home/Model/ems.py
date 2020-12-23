"""This is the program to create EMS's in the grid for each smart home"""

# from warnings import warn
from cosim_mosaik.simulators.Smart_Home.Model.methods import read_from_json, create_house


class EMS:
    def __init__(self, home):

        self.name = "EMS_%s" % home.name
        self.house_name = home.name
        self.PVCollector = home.PV
        self.Load = home.Load
        self.Batteries = home.batteries
        self.EV = home.EV
        self.intraday_e = 0  # Total energy imbalance after simulation has finished
        self.unbalanced_power = 0  # Power imbalance for each time-step
        self.battery_control = 0  # Power to be adjusted by storage batteries
        self.ev_control = 0  # Power to be adjusted by ev batteries
        self.injected_power = 0
        self.absorbed_power = 0

    def report_energy_flex(self):

        battery_flex_max = 0
        battery_flex_min = 0
        ev_flex = 0

        for Battery in self.Batteries:
            if Battery.params['in_service'] is 1:
                battery_flex_max += ((Battery.soc - Battery.params['soc_min'])/100) * Battery.params['max_energy']
                battery_flex_min += ((Battery.params['soc_max'] - Battery.soc) / 100) * Battery.params['max_energy']

        for ev in self.EV:
            if ev.params['in_service'] is 1:
                ev_flex += ((ev.params['soc_max'] - ev.params["soc"]) / 100) * ev.params['max_energy']

        min_flex = (-1) * battery_flex_max  # Max energy that can be discharged by smart home
        max_flex = battery_flex_min + ev_flex  # Max energy that can be absorbed by smart home

        return max_flex, min_flex

    def report_power_flex(self):

        battery_flex_max = 0
        battery_flex_min = 0
        ev_flex = 0

        for Battery in self.Batteries:
            if Battery.params['in_service'] is 1:
                battery_flex_max += Battery.params['max_P']
                battery_flex_min += Battery.params['min_P']

        min_flex = battery_flex_min  # Max power that can be discharged by smart home (-ve)
        max_flex = battery_flex_max  # Max power that can be absorbed by smart home (+ve)

        return max_flex, min_flex

    def energy_manager(self, step_size, control_power):
        """

        :param control_power: power imbalance to be adjusted
        :param step_size: step size in minutes
        :return: actual battery power; deviation between scheduled and actual power; scheduled LEM power
        """
        residual_power = 0
        injected_power = 0
        absorbed_power = 0
        self.battery_control = 0
        self.ev_control = 0
        # hours = step_size / 60

        # Surplus power balancing step
        if control_power > 0:

            battery_flags = []
            # First priority for balancing step - Home Battery
            for Battery in self.Batteries:
                if (Battery.params.get('in_service', 0) is 1) and (Battery.params.get('flag', 0) is not 1):
                    self.battery_control = control_power/len(self.Batteries)
                    absorbed_power += Battery.charge_battery(step_size, self.battery_control)
                    # print('Absorbed power is: ', absorbed_power)
                    # print("\n Executed control step for Battery:", Battery.name)

                elif Battery.params.get('flag', 0) is 1:
                    # warn(Battery.name + " is fully charged!! ")
                    battery_flags.append(Battery.params['flag'])

                    if len(battery_flags) == len(self.Batteries):  # All batteries fully charged
                        # Second priority for power surplus is invoked - EV batteries
                        if len(self.EV) is not 0:
                            for EV in self.EV:
                                # Check if EV battery is operational
                                if (EV.params.get('in_service', 0) is 1) and (EV.params.get('flag', 0) is not 1):
                                    self.ev_control = control_power/len(self.EV)
                                    absorbed_power += EV.ev_controller(step_size, self.ev_control)
                                    # print("\n Executed control step for EV:", EV.name)

                                elif EV.params.get('in_service', 0) is 0:
                                    # warn(EV.name + " is not in service!!")
                                    residual_power += control_power / len(self.EV)

                                elif EV.params.get('flag', 0) is 1:
                                    # warn(EV.name + ' is also fully-charged!!')
                                    self.ev_control = 0
                                    residual_power += control_power/len(self.EV)

                        # No EV's are available
                        elif len(self.EV) is 0:
                            # warn('No electric vehicles were detected!!')
                            residual_power += control_power / len(self.Batteries)

                # Battery not in service
                elif Battery.params.get('in_service', 0) is 0:
                    # warn(Battery.name + " is not in service!!")
                    # A diagnostic function can be inserted here
                    residual_power += control_power / len(self.Batteries)

            self.absorbed_power = absorbed_power
            # print('Absorbed power per time step is: ', absorbed_power)
            # print('Returned Absorbed power is: ', self.absorbed_power)

        # Deficit power balancing step
        elif control_power < 0:  # (-ve) control value

            for Battery in self.Batteries:
                # Deficit power balancing step
                if (Battery.params.get('flag', 0) is not -1) and (Battery.params.get('in_service', 0) is 1):
                    self.battery_control = control_power/len(self.Batteries)
                    injected_power += Battery.discharge_battery(step_size, self.battery_control)

                elif Battery.params.get('flag', 0) is -1:
                    # warn('Battery.name + " cannot discharge more, only reserve charge left!!')
                    self.battery_control = 0
                    residual_power += control_power / len(self.Batteries)

            self.injected_power = injected_power

        elif control_power == 0:
            # Nothing to do for EMS
            pass


if __name__ == '__main__':
    house_dict = read_from_json('C:/Users/bansal/Documents/cosim_mosaik.git/cosim_mosaik/simulators/Smart_Home'
                                '/Model/Data/example1.json')
    houses = create_house(house_dict, 1)

    ems_list = []

    # Create EMS for all houses
    for house in houses:
        ems = EMS(house)
        ems_list.append(ems)
