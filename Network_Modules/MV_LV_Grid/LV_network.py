import pandapower as pp
import pandas as pd
from pandapower.plotting import to_html
# from pandapower.plotting.plotly import simple_plotly


def create_lv_network(net):
    # Global variables for storage
    BATTERY_MAX_P = 0.0034  # (Value in MW)
    BATTERY_MIN_P = -0.0034  # (Value in MW)
    MV_VOL = 20

    # Create the low voltage part of the network
    pp.create_bus(net, name='Bus MV0', vn_kv=MV_VOL, type='n')
    pp.create_bus(net, name='Bus LV0', vn_kv=0.4, type='n')

    mv_bus = pp.get_element_index(net, "bus", "Bus MV0")
    lv_bus = pp.get_element_index(net, "bus", "Bus LV0")

    for i in range(1, 4):
        for j in range(1, 5):
            pp.create_bus(net, name='Bus LV%s.%s' % (i, j), vn_kv=0.4, type='m')

    # show the LV buses
    # print(net.bus)

    # Create External Grid - Not to be used when connected to MV grid
    # pp.create_ext_grid(net, pp.get_element_index(net, "bus", 'Bus MV0'), vm_pu=1.03, va_degree=0,
    #                    name='External grid', s_sc_max_mva=1000, rx_max=0.1, rx_min=0.1)

    # Create lines
    lv_lines = pd.read_csv('Data/lv_lines.csv', sep=';', header=0, decimal=',')
    for _, lv_line in lv_lines.iterrows():
        from_bus = pp.get_element_index(net, "bus", lv_line.from_bus)
        to_bus = pp.get_element_index(net, "bus", lv_line.to_bus)
        pp.create_line(net, from_bus, to_bus, length_km=lv_line.length, std_type=lv_line.std_type,
                       name=lv_line.line_name)

    # Show all lines
    # print("\n These are the transmission lines of the MV-LV grid")
    # print(net.line)

    # Create the MV-LV transformer

    pp.create_transformer_from_parameters(net, mv_bus, lv_bus, sn_mva=.4, vn_hv_kv=MV_VOL, vn_lv_kv=0.4,
                                          vkr_percent=1.325,
                                          vk_percent=4, pfe_kw=.95, i0_percent=.2375, tap_side="hv", tap_neutral=0,
                                          tap_min=-2, tap_max=2, tap_step_percent=2.5, tp_pos=0, shift_degree=150,
                                          name='MV-LV-Trafo')

    mv_lv_trafo = pp.get_element_index(net, "trafo", 'MV-LV-Trafo')

    # show the MV-LV transformer
    # print('\n The LV transformer specs are as follows: ')
    # print(net.trafo)

    # Create Switches
    lv_buses = net.bus[net.bus.vn_kv == 0.4]
    # Bus-line Switches
    lv_ls = net.line[(net.line.from_bus.isin(lv_buses.index)) & (net.line.to_bus.isin(lv_buses.index))]
    for _, line in lv_ls.iterrows():
        pp.create_switch(net, line.from_bus, line.name, et='l', closed=True, type='LBS', name='Switch %s - %s' % (
            net.bus.name.at[line.from_bus], line['name']))
        pp.create_switch(net, line.to_bus, line.name, et='l', closed=True, type='LBS', name='Switch %s - %s' % (
            net.bus.name.at[line.to_bus], line['name']))

    # Transformer-line switches
    pp.create_switch(net, mv_bus, mv_lv_trafo, et='t', closed=True, type='LBS', name='Switch MV0 - MV-LV-Trafo')
    pp.create_switch(net, lv_bus, mv_lv_trafo, et='t', closed=True, type='LBS', name='Switch LV0 - MV-LV-Trafo')

    # Show the Low voltage switches
    # print('\n The low voltage switches are :')
    # print(net.switch[net.switch.bus.isin(lv_buses.index)])

    # Create the Loads
    lv_loads = pd.read_csv('Data/lv_loads.csv', sep=';', header=0, decimal=',')
    for _, load in lv_loads.iterrows():
        bus_idx = pp.get_element_index(net, "bus", load.bus)
        pp.create_load(net, bus_idx, p_mw=load.p, q_mvar=load.q, name=load.load_name)

    # Show the low voltage loads
    # print(net.load[net.load.bus.isin(lv_buses.index)])

    # Create PV Panels/static generators at load buses
    lv_sgens = pd.read_csv('Data/lv_sgens.csv', sep=';', header=0, decimal=',')
    for _, sgen in lv_sgens.iterrows():
        bus_idx = pp.get_element_index(net, "bus", sgen.bus)
        pp.create_sgen(net, bus_idx, p_mw=sgen.p, q_mvar=sgen.q, sn_mva=sgen.sn, type=sgen.type, name=sgen.sgen_name)

    # Show LV static generators
    # print('\n The placement of solar PV systems is as follows: ')
    # print(net.sgen)

    # Create Battery elements
    lv_battery = pd.read_csv('Data/lv_battery.csv', sep=';', header=0, decimal=',')
    for _, battery in lv_battery.iterrows():
        bus_idx = pp.get_element_index(net, "bus", battery.bus)
        pp.create_storage(net, bus=bus_idx, p_mw=battery.pnom, max_e_mwh=battery.max_cap, sn_mva=battery.snom,
                          name=battery.name, type=battery.type, max_p_mw=BATTERY_MAX_P, min_p_mw=BATTERY_MIN_P,
                          controllable=1)

    # Show Battery/Storage elements
    # print('\n The battery systems are connected as follows :')
    # print(net.storage[net.storage.bus.isin(lv_buses.index)])

    # Run a power flow on LV grid - Not to be used when connected to MV grid

    # pp.runpp(net)
    # print(net.res_bus)
    # print(net.res_line)

    # Plotting the network based on power flow results - Not to be used when connected to MV grid
    # simple_plotly(net)
    to_html(net, 'Data/LV_net.html')

    # Convert this grid to a json file
    pp.to_json(net, "Data/LV_grid.json")


if __name__ == '__main__':

    # Create an empty network - Not to be used when connected to MV grid
    network = pp.create_empty_network()
    create_lv_network(network)
