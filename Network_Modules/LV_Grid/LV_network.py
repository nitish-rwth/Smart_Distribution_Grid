import pandapower as pp
import pandas as pd
# from pandapower.plotting import to_html
# from pandapower.plotting.plotly import simple_plotly


def create_lv_network(net, mv_bus_number):
    # Global variables for storage
    mv_vol = 20

    # Create the low voltage part of the network
    lv_buses = pd.read_csv('lv_buses.csv', sep=';', header=0,
                           decimal=',')
    for _, lv_bus in lv_buses.iterrows():
        pp.create_bus(net, name=lv_bus.bus_name, vn_kv=lv_bus.voltage, type=lv_bus.type, zone=lv_bus.zone,
                      in_service=lv_bus.service)

    # Print network buses
    # print(net.bus)

    mv_bus = pp.get_element_index(net, "bus", "Bus MV-LV_%s.0" % mv_bus_number)
    lv_bus = pp.get_element_index(net, "bus", "Bus LV_%s.0" % mv_bus_number)

    # Create External Grid - Not to be used when connected to MV grid
    pp.create_ext_grid(net, mv_bus, vm_pu=1.02, va_degree=0,
                       name='External grid', s_sc_max_mva=1000, rx_max=0.1, rx_min=0.1)

    # Create lines
    lv_lines = pd.read_csv('lv_lines.csv', sep=';', header=0, decimal=',')
    for _, line in lv_lines.iterrows():
        from_bus = pp.get_element_index(net, "bus", line.from_bus)
        to_bus = pp.get_element_index(net, "bus", line.to_bus)
        pp.create_line(net, from_bus, to_bus, length_km=line.length, std_type=line.std_type, name=line.line_name)

    # Show all lines
    # print("\n These are the transmission lines of the MV-LV grid")
    # print(net.line)

    # Create the MV-LV transformer
    pp.create_transformer_from_parameters(net, mv_bus, lv_bus, sn_mva=.4, vn_hv_kv=mv_vol, vn_lv_kv=0.4,
                                          vkr_percent=1.325,
                                          vk_percent=4, pfe_kw=.95, i0_percent=.2375, tap_side="hv", tap_neutral=0,
                                          tap_min=-2, tap_max=2, tap_step_percent=2.5, tp_pos=0, shift_degree=150,
                                          name='MV-LV-Trafo%s' % mv_bus_number)

    mv_lv_trafo = pp.get_element_index(net, "trafo", 'MV-LV-Trafo%s' % mv_bus_number)

    # show the MV-LV transformer
    # print('\n The LV transformer specs are as follows: ')
    # print(net.trafo)

    # Create Switches
    # Bus-line Switches
    lv_switches = pd.read_csv('lv_switches.csv', sep=';', header=0, decimal=',')

    for _, switch in lv_switches.iterrows():
        bus = pp.get_element_index(net, "bus", switch.bus)
        line = pp.get_element_index(net, "line", switch.element)
        pp.create_switch(net, bus, line, et=switch.et, closed=switch.closed, type=switch.type,
                         name=str(switch.switch_name)+'-%s' % bus)

    # Transformer-line switches
    pp.create_switch(net, mv_bus, mv_lv_trafo, et='t', closed=True, type='LBS',
                     name='Switch MV-LV-Trafo-%s.A' % mv_bus_number)
    pp.create_switch(net, lv_bus, mv_lv_trafo, et='t', closed=True, type='LBS',
                     name='Switch MV-LV-Trafo-%s.B' % mv_bus_number)

    # Show the Low voltage switches
    # print('\n The low voltage switches are :')
    # print(net.switch[net.switch.bus.isin(lv_buses.index)])

    # Create the Loads
    lv_loads = pd.read_csv('lv_loads.csv', sep=';', header=0, decimal=',')
    for _, load in lv_loads.iterrows():
        bus_idx = pp.get_element_index(net, "bus", load.bus)
        pp.create_load(net, bus_idx, p_mw=load.p, q_mvar=load.q, name=load.load_name)

    # Show the low voltage loads
    # print(net.load[net.load.bus.isin(lv_buses.index)])

    # Run a power flow on LV grid - Not to be used when connected to MV grid

    pp.runpp(net)
    # # Bus parameters
    # print("\n The bus parameters will be exported to CSV File!")
    # df1 = pd.DataFrame(net.bus)
    # df2 = pd.DataFrame(net.res_bus)
    # df2.insert(loc=0, column='Bus_Name', value=df1['name'])
    # df2.to_csv('Data/LV/Node_%s/Results/bus_results.csv' % mv_bus_number, sep=';', decimal=',')

    # # Line parameters
    # print("\n The line parameters will be exported to CSV File!")
    # df1 = pd.DataFrame(net.line)
    # df2 = pd.DataFrame(net.res_line)
    # df2.insert(loc=0, column='Line_Name', value=df1['name'])
    # df2.to_csv('Data/LV/Node_%s/Results/line_results.csv' % mv_bus_number, sep=';', decimal=',')
    #
    # # Plotting the network based on power flow results - Not to be used when connected to MV grid
    # simple_plotly(net, figsize=2.1, aspectratio=(16, 10))
    # to_html(net, 'Data/LV/Node_%s/Results/LV_net.html' % mv_bus_number)
    #
    # # Convert this grid to a json file
    pp.to_json(net, "LV_grid.json")

    return mv_bus


if __name__ == '__main__':

    # Create an empty network - Not to be used when connected to MV grid
    network = pp.create_empty_network()
    create_lv_network(network, 14)
