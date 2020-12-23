"""This is the program to create smart homes in the grid based on JSON data"""

from copy import deepcopy


# Base class for house objects
class House:
    def __init__(self, house_no, dictionary, components):
        self.name = "Smart_Home_%s" % house_no
        self.number = house_no
        # Each smart home has house devices as class attributes
        self.batteries = []
        battery_dict = components.get('Battery', None)
        for num in range(1, battery_dict['num']+1):
            battery = Battery(house_no, deepcopy(battery_dict), num)
            self.batteries.append(battery)

        self.EV = []
        ev_dict = components.get('EV', None)
        for num in range(1, ev_dict['num']+1):
            ev = EV(house_no, deepcopy(ev_dict), num)
            self.EV.append(ev)

        self.PV = PV(house_no, components.get('PVCollector', None))
        self.Load = Load(house_no, components.get('Load', None))
        # Setting attributes specific only to class House
        for key in dictionary:
            setattr(self, key, dictionary[key])


# Base class for house storage battery objects
class Battery:
    def __init__(self, house_no, dictionary, battery_no):

        self.name = "Storage_Battery_%s.%s" % (house_no, battery_no)
        self.params = dictionary['params']
        self.unbalanced_power = 0  # Power imbalance due to battery power limits violation
        self.adjusted_power = 0  # Power adjusted by the battery as per EMS demand
        self.excess_power = 0  # Power imbalance due to battery SOC limits violation

        # Getting battery attributes from parameters dictionary
        self.soc = self.params['soc']
        self.battery_flag = self.params['flag']

    def charge_battery(self, step_size, residual):

        hours = step_size / 60  # minutes into hours
        scheduled_p = residual  # Power imbalance as per EMS

        # Check for Battery power limits violation
        if scheduled_p > self.params['max_P']:
            # print('\n Home battery Charging power limit exceeded!!')
            self.unbalanced_power += scheduled_p - self.params['max_P']
            self.unbalanced_power = round(self.unbalanced_power, 2)
            # print('Supplied Power is being reset to battery power limits!')
            battery_p = self.params['max_P']

        else:
            battery_p = scheduled_p

        # Battery charging and check for soc violation
        if (battery_p > 0) and (self.battery_flag is not 1):
            # Get battery SOC and SOE
            energy2charge = battery_p * hours * self.params['charge_efficiency']
            energy_capacity = ((self.params['soc_max'] - self.soc) / 100) * self.params['max_energy']

            if self.soc == self.params['soc_max']:  # Battery flag fail-safe
                self.battery_flag = 1  # Set flag as 1 to show fully charged state
                self.unbalanced_power += battery_p
                # print('\n Home Battery is fully charged!! Cannot do power balancing!')

            elif energy2charge <= energy_capacity:
                # Check if maximum energy of the battery is reached -> Adjust power if necessary
                self.soc += energy2charge / self.params['max_energy'] * 100
                self.adjusted_power = energy2charge / hours
                self.battery_flag = 0  # Set flag as ready to charge

            elif energy2charge >= energy_capacity:  # Fully-charged
                self.adjusted_power = energy_capacity / hours
                # energy_surplus = energy2charge - energy_capacity
                # self.excess_power += energy_surplus / hours  # Power that remains to be stored
                # warn('\n Home Battery is fully charged!! Cannot store more energy!')
                self.soc = self.params['soc_max']
                self.battery_flag = 1  # Set flag as 1 to show fully charged state

        self.soc = round(self.soc, 3)
        self.params["soc"] = self.soc
        self.params["flag"] = self.battery_flag  # Set flag as (0,1,-1)

        # Collect unadjusted power the entire time-step
        # control_error = self.unbalanced_power + self.excess_power
        adjusted_power = self.adjusted_power / self.params['charge_efficiency']
        self.unbalanced_power, self.excess_power, self.adjusted_power = 0, 0, 0
        # print('Absorbed power is: ', adjusted_power)
        return adjusted_power  # Total power absorbed for this time-step

    def discharge_battery(self, step_size, residual):

        hours = step_size / 60  # minutes into hours
        # Power imbalance/battery as per EMS (-ve)
        scheduled_p = residual

        if scheduled_p < self.params['min_P']:
            # print('\n Maximum demanded power is more than maximum home battery discharging power!!')
            self.unbalanced_power += scheduled_p - self.params['min_P']
            self.unbalanced_power = round(self.unbalanced_power, 2)
            # print('Demanded Power is being reset to home battery power limits!')
            battery_p = self.params['min_P']

        else:
            battery_p = scheduled_p

        # Battery discharging and check for soc violation
        if (battery_p < 0) and (self.battery_flag is not -1):
            # Get battery SOC and SOE
            energy2discharge = battery_p * hours  # (-ve)
            energy_capacity = ((self.soc - self.params['soc_min'])/100) * self.params['max_energy']

            if self.soc == self.params['soc_min']:  # Battery flag fail-safe
                self.battery_flag = -1  # Set flag as -1 to show fully discharged state
                self.unbalanced_power += battery_p
                self.adjusted_power = 0
                # print('\n Home Battery is fully discharged!! Cannot do power balancing!')

            elif ((-1) * energy2discharge) < energy_capacity:
                # Check if minimum energy of the battery is reached -> Adjust power if necessary
                self.soc += energy2discharge / self.params['max_energy'] * 100
                self.adjusted_power = (energy2discharge * self.params['discharge_efficiency']) / hours
                self.battery_flag = 0  # Set flag as ready to discharge

            elif ((-1) * energy2discharge) >= energy_capacity:  # Full-discharge Case
                self.adjusted_power = (-1) * (energy_capacity * self.params['discharge_efficiency']) / hours
                # warn('\n Home Battery is fully discharged!! Cannot deliver more energy!')
                self.soc = self.params['soc_min']
                self.battery_flag = -1  # Set flag as 1 to show fully discharged state

        self.soc = round(self.soc, 3)
        self.params["soc"] = self.soc
        self.params["flag"] = self.battery_flag  # Set flag as (0,1,-1)

        # Collect unadjusted power the entire time-step
        adjusted_power = self.adjusted_power
        self.unbalanced_power, self.excess_power, self.adjusted_power = 0, 0, 0
        return adjusted_power  # Total power adjusted for this time-step (+ve)


# Base class for house EV battery objects
class EV:

    def __init__(self, house_no, dictionary, ev_num):

        self.name = "EV_Battery_%s.%s" % (house_no, ev_num)
        self.params = dictionary['params']
        self.unbalanced_power = 0  # Power imbalance due to battery power limits violation
        self.excess_power = 0  # Power imbalance due to battery SOC limits violation
        self.battery_flag = self.params['flag']
        self.adjusted_power = 0

    def ev_controller(self, step_size, residual):

        # Getting battery attributes from parameters dictionary
        soc = self.params['soc']

        # Battery power balancing action based om EMS data
        # print('\n The battery soc before control step is : ', soc, '%')
        hours = step_size / 60  # minutes into hours
        scheduled_p = residual  # Power imbalance as per EMS

        # Check for Battery power limits violation
        if scheduled_p > self.params['max_P']:
            # print('\n EV battery Charging power limit exceeded!!')
            self.unbalanced_power += scheduled_p - self.params['max_P']
            self.unbalanced_power = round(self.unbalanced_power, 2)
            # print("Initial Power imbalance for this step : ", self.unbalanced_power, "kW")
            # print('Supplied Power is being reset to battery power limits!')
            battery_p = self.params['max_P']

        # Feature disabled for now
        # elif scheduled_p < self.params['min_P']:
        #     print('\n Maximum demanded power is more than maximum home battery discharging power!!')
        #     self.unbalanced_power += scheduled_p - self.params['min_P']
        #     self.unbalanced_power = round(self.unbalanced_power, 2)
        #     # print("Power imbalance for this step : ", self.unbalanced_power, "kW")
        #     # print('Demanded Power is being reset to home battery power limits!')
        #     battery_p = self.params['min_P']

        else:
            battery_p = scheduled_p

        # Battery charging and check for soc violation
        if (battery_p > 0) and (self.battery_flag is not 1):
            # Get battery SOC and SOE
            energy2charge = battery_p * hours * self.params['charge_efficiency']
            energy_capacity = ((self.params['soc_max'] - soc) / 100) * self.params['max_energy']

            if soc == self.params['soc_max']:  # Battery flag fail-safe
                self.battery_flag = 1  # Set flag as 1 to show fully charged state
                self.unbalanced_power += battery_p
                # warn('\n EV Battery is fully charged!! Cannot do power balancing!')

            elif energy2charge <= energy_capacity:
                # Check if maximum energy of the battery is reached -> Adjust power if necessary
                soc += energy2charge / self.params['max_energy'] * 100
                self.adjusted_power = battery_p
                self.battery_flag = 0  # Set flag as ready to charge

            elif energy2charge >= energy_capacity:  # Fully-charged
                self.adjusted_power = energy_capacity / hours
                # energy_surplus = energy2charge - energy_capacity
                # self.excess_power += energy_surplus / hours  # Power that remains to be stored
                # warn('\n EV Battery is fully charged!! Cannot store more energy!')
                soc = self.params['soc_max']
                self.battery_flag = 1  # Set flag as 1 to show fully charged state

        # Feature disabled for now
        # Battery discharging and check for soc violation
        # elif (battery_p < 0) and (self.battery_flag is not -1):
        #     # print('Battery Power for discharging will be: ', battery_p, 'kW')
        #     energy2discharge = battery_p * hours * self.params['discharge_efficiency'] * -1
        #     energy_capacity = (soc/100) * self.params['max_energy']
        #
        #     if soc == self.params['soc_min']:  # Battery flag fail-safe
        #         self.battery_flag = -1  # Set flag as 1 to show fully charged state
        #         self.unbalanced_power += battery_p
        #         print('\n Home Battery is fully discharged!! Cannot do power balancing!')
        #
        #     elif energy2discharge < energy_capacity:
        #         # Check if minimum energy of the battery is reached -> Adjust power if necessary
        #         soc -= energy2discharge / self.params['max_energy'] * 100
        #         self.battery_flag = 0  # Set flag as ready to discharge
        #
        #     elif energy2discharge >= energy_capacity:  # Fully-discharged
        #         energy_deficit = energy_capacity - energy2discharge
        #         self.excess_power += energy_deficit / hours  # Power that remains to be supplied
        #         print('\n Home Battery is fully discharged!! Cannot deliver more energy!')
        #         soc = self.params['soc_min']
        #         self.battery_flag = -1  # Set flag as 1 to show fully charged state

        soc = round(soc, 3)
        self.params["soc"] = soc
        self.params["flag"] = self.battery_flag  # Set flag as (0,1,-1)

        # Collect unadjusted power the entire time-step
        # control_error = self.unbalanced_power + self.excess_power
        # control_error = round(control_error, 2)
        adjusted_power = self.adjusted_power
        self.unbalanced_power, self.excess_power, self.adjusted_power = 0, 0, 0
        return adjusted_power  # Total power absorbed for this time-step


# Base class for house PV collector objects
class PV:
    def __init__(self, house_no, dictionary):
        for pv in range(1, dictionary['num'] + 1):
            self.name = "PV_Collector_%s.%s" % (house_no, pv)
            parameters = dictionary['params']
            for key in parameters:
                setattr(self, key, parameters[key])


# Base class for house load objects
class Load:
    def __init__(self, house_no, dictionary):
        for load in range(1, dictionary['num'] + 1):
            self.name = "Load_%s.%s" % (house_no, load)
            parameters = dictionary['params']
            for key in parameters:
                setattr(self, key, parameters[key])
