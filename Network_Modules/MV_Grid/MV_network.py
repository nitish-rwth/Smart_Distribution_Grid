import pandas as pd
import pandapower as pp
from pandapower.plotting import to_html
from pandapower.plotting.plotly import simple_plotly

net = pp.create_cigre_network_mv(with_der=False)

def create_mv_network(net_cigre_mv):
    # Line-data
    line_data = {'c_nf_per_km': 151.1749, 'r_ohm_per_km': 0.501, 'x_ohm_per_km': 0.716, 'max_i_ka': 0.145, 'type': 'cs'}
    pp.create_std_type(net_cigre_mv, line_data, name='CABLE_CIGRE_MV', element='line')

    line_data = {'c_nf_per_km': 10.09679, 'r_ohm_per_km': 0.510, 'x_ohm_per_km': 0.366, 'max_i_ka': 0.195, 'type': 'ol'}
    pp.create_std_type(net_cigre_mv, line_data, name='OHL_CIGRE_MV', element='line')

    # Buses
    bus0 = pp.create_bus(net_cigre_mv, name='MV Bus 0', vn_kv=110, type='b', zone='CIGRE_MV')
    buses = pp.create_buses(net_cigre_mv, 14, name=['MV Bus %i' % i for i in range(1, 15)], vn_kv=20, type='b',
                            zone='CIGRE_MV')

    # Ext-Grid
    pp.create_ext_grid(net_cigre_mv, bus0, vm_pu=1.05, va_degree=0.0, s_sc_max_mva=5000, s_sc_min_mva=5000, rx_max=0.1,
                       rx_min=0.1)

    # Lines
    mv_lines = pd.read_csv('Data/MV/mv_lines.csv', sep=';', header=0, decimal=',')
    for _, mv_line in mv_lines.iterrows():
        from_bus = pp.get_element_index(net_cigre_mv, "bus", mv_line.from_bus)
        to_bus = pp.get_element_index(net_cigre_mv, "bus", mv_line.to_bus)
        pp.create_line(net_cigre_mv, from_bus, to_bus, length_km=mv_line.length, std_type=mv_line.std_type,
                       name=mv_line.line_name)
    # print(net_cigre_mv.line)

    # Trafos
    trafo0 = pp.create_transformer_from_parameters(net_cigre_mv, bus0, buses[0], sn_mva=25, vn_hv_kv=110, vn_lv_kv=20,
                                                   vkr_percent=0.16, vk_percent=12.00107, pfe_kw=0, i0_percent=0,
                                                   shift_degree=30.0, name='Trafo 0-1')
    trafo1 = pp.create_transformer_from_parameters(net_cigre_mv, bus0, buses[11], sn_mva=25, vn_hv_kv=110, vn_lv_kv=20,
                                                   vkr_percent=0.16, vk_percent=12.00107, pfe_kw=0, i0_percent=0,
                                                   shift_degree=30.0, name='Trafo 0-12')

    # Switches
    mv_switches = pd.read_csv('Data/MV/mv_switches.csv', sep=';', header=0, decimal=',')
    for _, switch in mv_switches.iterrows():
        pp.create_switch(net_cigre_mv, switch.bus, pp.get_element_index(net_cigre_mv, "line", str(switch.element)),
                         et='l', closed=switch.closed, type=switch.type, name=switch.switch_name)
    # print(net_cigre_mv.switch)

    # Trafo switches
    pp.create_switch(net_cigre_mv, bus0, trafo0, et='t', closed=True, type='CB', name='MV_Trafo_SW_A')
    pp.create_switch(net_cigre_mv, bus0, trafo1, et='t', closed=True, type='CB', name='MV_Trafo_SW_B')

    # Residential and Commercial / Industrial Loads
    mv_loads = pd.read_csv('Data/MV/mv_loads.csv', sep=';', header=0, decimal=',')
    for _, load in mv_loads.iterrows():
        pp.create_load_from_cosphi(net_cigre_mv, load.bus, sn_mva=load.sn, cos_phi=load.pf, mode=load.load_mode,
                                   name=load.load_name)
    # print(net_cigre_mv.load)

    # Optional distributed energy resources
    mv_sgens = pd.read_csv('Data/MV/mv_sgens.csv', sep=';', header=0, decimal=',')
    for _, sgen in mv_sgens.iterrows():
        pp.create_sgen(net_cigre_mv, sgen.bus, p_mw=sgen.p, q_mvar=sgen.q, sn_mva=sgen.sn, type=sgen.type,
                       name=sgen.sgen_name)
    # print(net_cigre_mv.sgen)

    # # Bus geo data
    # net_cigre_mv.bus_geodata = pd.read_json(
    #     """{"x":{"0":7.0,"1":4.0,"2":4.0,"3":4.0,"4":2.5,"5":1.0,"6":1.0,"7":8.0,"8":8.0,"9":6.0,
    #     "10":4.0,"11":4.0,"12":10.0,"13":10.0,"14":10.0},"y":{"0":16,"1":15,"2":13,"3":11,"4":9,
    #     "5":7,"6":3,"7":3,"8":5,"9":5,"10":5,"11":7,"12":15,"13":11,"14":5}}""")
    #
    # # Match bus.index
    # net_cigre_mv.bus_geodata = net_cigre_mv.bus_geodata.loc[net_cigre_mv.bus.index]

    # Run a power flow on MV grid - Not to be used when connected to MV grid

    # pp.runpp(net_cigre_mv)
    # print("\n The bus parameters are :")
    # df1 = pd.DataFrame(net_cigre_mv.bus)
    # df2 = pd.DataFrame(net_cigre_mv.res_bus)
    # df2.insert(loc=0, column='Bus_Name', value=df1['name'])
    # df2.to_csv('Data/bus_results.csv', sep=';', decimal=',')
    # print("\n The line parameters are :")
    # df1 = pd.DataFrame(net_cigre_mv.line)
    # df2 = pd.DataFrame(net_cigre_mv.res_line)
    # df2.insert(loc=0, column='Line_Name', value=df1['name'])
    # df2.to_csv('Data/line_results.csv', sep=';', decimal=',')

    # # Plotting the network based on power flow results - Not to be used when connected to MV grid
    # simple_plotly(net_cigre_mv, figsize=2.1, aspectratio=(16, 10))
    # to_html(net_cigre_mv, 'Data/MV/MV_net.html')
    #
    # # Convert this grid to a json file
    # pp.to_json(net_cigre_mv, "Data/MV/MV_grid.json")


if __name__ == '__main__':

    # Create an empty network - Not to be used when connected to LV grid
    network = pp.create_empty_network()
    create_mv_network(network)
