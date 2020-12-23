"""
This module contains the model types for Pandapower (:class:`Bus`,
:class:`Branch`, and :class:`Generator`).

"""
from __future__ import division

import os.path
import pandapower as pp


def load_case(path, grid_idx, model_keys):
    # Load PandaPower case from *path*
    loaders = {
        "p.": pp.from_pickle,
        ".json": pp.from_json,
        ".xlsx": pp.from_excel,
    }

    try:
        ext = os.path.splitext(path)[-1]
        loader = loaders[ext]
        net = loader(path)
    except KeyError:
        raise ValueError("Don't know how to open '%s'" % path)

    # Initialize an entity map
    entity_map = UniqueKeyDict()

    # Create entities for all pandapower-element-types defined in 'meta'
    for keys in model_keys:
        if keys != "Cms":
            entity_map.update(create_entities(grid_idx, net, keys))

    return net, entity_map


def create_entities(grid_idx, pp_net, etype):
    entity_map = UniqueKeyDict()
    for idx, name in enumerate(pp_net[etype]["name"]):

        eid = make_entity_eid(idx, grid_idx, etype, name)
        obj = {
            "etype": etype,
            "idx": idx,
            "name": name
        }

        if etype == "line":
            obj["loading_percent"] = 0
            obj["from_bus"] = pp_net[etype]["from_bus"].iloc[idx]
            obj["to_bus"] = pp_net[etype]["to_bus"].iloc[idx]
            obj["bus_p_mw"] = 0

        if etype == "load":
            obj["cms_toggle"] = 0
            obj["P_set"] = 0
            obj["zone"] = pp_net[etype]["zone"].iloc[idx]

        if etype == "bus":
            obj["zone"] = pp_net[etype]["zone"].iloc[idx]
            obj["p_mw"] = 0
            obj["q_mvar"] = 0
            obj["p_set"] = 0
            obj["p_demand"] = 0
            obj["p_error"] = 0

            # Initialize Bus flex parameters
            obj["e_min_flex"] = 0
            obj["e_max_flex"] = 0
            obj["p_min_flex"] = 0
            obj["p_max_flex"] = 0

        entity_map[eid] = obj

    return entity_map


def make_cms_eid(name, cms_idx):
    return "%s_%s" % (name, cms_idx)


def make_entity_eid(name, grid_idx, pandatype, ename):
    return '%s-%s_%s,%s' % (grid_idx, pandatype, name, ename)


class UniqueKeyDict(dict):
    """A :class:`dict` that won't let you insert the same key twice."""

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError('Key "%s" already exists in dict.' % key)
        super(UniqueKeyDict, self).__setitem__(key, value)
