"""
mosaik API for CMS

"""

from __future__ import division

import os
import sys
import mosaik_api
import cosim_mosaik.simulators.Smart_Cms.methods as methods
from cosim_mosaik.simulators.Smart_Cms import model

META = {
    "models": {
        "Cms": {
            "public": True,
            "params": ["configfile"],  # Name of the file containing the grid topology.
            "attrs": []
        },
        "line": {
            "public": False,
            "params": [],
            "attrs": [
                # Input (net.line)
                "in_service",  # specifies if the line is in service
                "loading_percent",  # line loading [%]
                "from_bus", "to_bus",
                "bus_p_mw"  # Power supplied by line to the receiving bus
            ]
        },
        "load": {
            "public": False,
            "params": [],
            "attrs": [
                "name", "in_service",  # specifies if the load is in service
                "cms_toggle",  # Decides if ems needs to participate or not
                "zone",  # The MV bus which this load will affect
                "P_set",  # Power(kW) set by CMS for each load
                "e_min_flex",  # Total energy(kWh) available for injection by all flexible assets
                "e_max_flex",  # Total energy(kWh) available for absorption by all flexible assets
                "p_max_flex",  # Total power(kW) available for absorption by all flexible assets
                "p_min_flex"   # Total power(kW) available for injection by all flexible assets
            ]
        },
        "trafo": {
            "public": False,
            "params": [],
            "attrs": [
                "loading_percent",  # load utilization relative to rated power [%]
            ],
        },
        "bus": {
                "public": False,
                "params": [],
                "attrs": [
                    "zone",
                    "p_mw",  # resulting active power demand [MW]
                    "q_mvar",  # resulting reactive power demand [Mvar]
                    "p_demand",  # Power demanded by Grid
                    "p_set",  # Power set by CMS
                    "p_error",  # Error between set power and actual power
                    "e_min_flex",  # Total energy(kWh) available for injection at this bus
                    "e_max_flex",  # Total energy(kWh) available for absorption at this bus
                    "p_max_flex",  # Total power(kW) available for absorption at this bus
                    "p_min_flex"   # Total power(kW) available for injection at this bus
                ],
            },
        }
    }


class CmsModel(mosaik_api.Simulator):
    def __init__(self):
        super(CmsModel, self).__init__(META)
        self.step_size = None
        self._entities = {}
        self._net = None
        self._ppcs = []  # Number of CMS instances

    def init(self, sid, step_size, *args, **kwargs):
        self.step_size = step_size
        return self.meta

    def create(self, num, modelname, configfile):
        if modelname != "Cms":
            raise ValueError('Unknown model: "%s"' % modelname)
        if not os.path.isfile(configfile):
            raise ValueError('File "%s" does not exist!' % configfile)

        cms = []
        for _ in range(num):
            cms_idx = len(self._ppcs)
            net, entities = model.load_case(
                configfile, cms_idx, self.meta["models"].keys())

            self._net = net
            self._ppcs.append(net)

            children = []
            for eid, attrs in sorted(entities.items()):
                assert eid not in self._entities
                self._entities[eid] = attrs

                # Get internal pandapower name of the element and add it to the entity
                name = ""
                if "name" in attrs:
                    name = attrs["name"]

                children.append(
                    {"eid": eid, "type": attrs["etype"], "name": name}
                )
            cms.append(
                {
                    "eid": model.make_cms_eid("cms", cms_idx),
                    "type": "Cms",
                    "children": children,
                }
            )
        return cms

    def step(self, time, inputs):
        # commands = {}

        # print('Inputs of CMS are:', inputs)

        # Initialize CMS entities with inputs dict
        for eid, attrs in inputs.items():
            for attr, values in attrs.items():
                for sid, value in values.items():
                    self._entities[eid][attr] = value

                    # if 'HomeModel' in sid:
                    #     commands[eid] = {}
                    #     commands[eid][sid] = {}

        # Run congestion check on MV lines
        for eid, attrs in self._entities.items():
            if 'MV_Line' in eid:
                methods.congestion_manager(self._entities, attrs, self._net, self.step_size, time)

        # Update commands dict for async data exchange
        # for eid, entity in self._entities.items():
        #     if entity['etype'] == 'load':
        #         for sid, value in commands.items():
        #             if eid == sid:
        #                 for did, param in value.items():
        #                     commands[eid][did]['P_ems'] = entity['P_set']
        #                     commands[eid][did]['cms_toggle'] = entity['cms_toggle']

        # print('Command dict is:', commands)
        # yield self.mosaik.set_data(commands)

        # Return new simulation time of CMS
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        # dict of dicts mapping entity IDs (eid) and attribute names (attrs) to their values
        for eid, attrs in outputs.items():
            for attr in attrs:
                val = self._entities[eid][attr]
                data.setdefault(eid, {})[attr] = val
        return data


def main():
    return mosaik_api.start_simulation(CmsModel(), "The mosaik-CMS adapter")


if __name__ == "__main__":
    sys.exit(main())
