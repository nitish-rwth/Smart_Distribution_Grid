"""Simulator class for smart home"""

import mosaik_api
from cosim_mosaik.simulators.Smart_Home.Simulator.model import Smart_home
from cosim_mosaik.simulators.Smart_Home.Model.results import write_to_csv, csv_to_plot

META = {
    'models': {
        'HomeModel': {
            'public': True,
            'params': ['house_list'],
            'attrs': ['P_PV', 'P_control', 'P_Load', 'P_house', 'P_ems', 'P_house_out', 'Q_Load',
                      'Q_house_out', 'cms_toggle', 'e_max_flex', 'e_min_flex', 'p_max_flex', 'p_min_flex',
                      'P_ems_out', 'ems_earning']
        },
    },
}


class HomeModel(mosaik_api.Simulator):

    def __init__(self):
        super().__init__(META)
        self.step_size = None       # desired time-step of the simulation
        self.smart_homes = {}       # dict of houses with their devices and the devices' values
        self.eids = []               # List of smart-home EIDs

    def init(self, sid, step_size):
        self.step_size = step_size
        return self.meta

    def create(self, num, model, house_list):

        entities = []
        """
        Creates num houses according to the config
        Returns an entity dict as specified by mosaik
        
        :param num: no of houses to be created
        :param model: passed by default
        :param house_list: model param needed for mosaik
        :return: dict of entities created
        """

        # Creating the smart_homes as Mosaik models
        for house in house_list:
            eid = house.name
            # List of smart home eids
            self.eids.append(eid)
            # Dict of smart home models mapped to their eids
            self.smart_homes[eid] = Smart_home(house, self.meta["models"]["HomeModel"]["attrs"])
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        """
        :param time: time at which the step should be calculated
        :param inputs: inputs provided by linked entities
        :return: time after the step
        """
        for eid in self.eids:
            if inputs:
                # input_dict = inputs
                # print("\n The input dict is as follows: ")
                # print(input_dict)
                self.smart_homes[eid].step(self.step_size, time, inputs[eid])

        return time + self.step_size

    def get_data(self, outputs):
        """
        Function needed by mosaik, provides interface to get values

        :param outputs: see mosaik specification
        :return: see mosaik specification
        """
        data = {}
        for eid, attrs in outputs.items():
            if eid not in self.eids:
                raise ValueError("No smart home with eid %d found" % eid)
            data[eid] = {}

            for attr in attrs:
                data[eid][attr] = self.smart_homes[eid].getparam(attr)

        return data

    def finalize(self):

        # print("\n Simulation results now being exported as csv and graphical data...")
        # Write the results of all control steps to csv and plot

        # To be disabled when running smart grid scenario
        for eid in self.eids:
            write_to_csv(self.smart_homes[eid].ems, self.smart_homes[eid].results)

        # End of Simulation
        print("\n End of smart home simulation!")
