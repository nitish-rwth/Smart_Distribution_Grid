from Connections.MV_network import create_mv_network
from Connections.LV_network import create_lv_network
import pandapower as pp
import pandas as pd
from pandapower.plotting import to_html
from pandapower.plotting.plotly import simple_plotly


network = pp.create_empty_network()
create_mv_network(network)
create_lv_network(network)

# MV-LV Line

ext_bus = pp.get_element_index(network, "bus", "MV Bus 14")
mv_bus = pp.get_element_index(network, "bus", "Bus MV0")
pp.create_line(network, ext_bus, mv_bus, length_km=1.0, std_type='OHL_CIGRE_MV', name='MV-LV Line')
mv_lv_line = pp.get_element_index(network, "line", "MV-LV Line")

# MV-LV Line switches
pp.create_switch(network, ext_bus, mv_lv_line, et='l', closed=True, type='LBS', name='Switch MV-LV S0')
pp.create_switch(network, mv_bus, mv_lv_line, et='l', closed=True, type='LBS', name='Switch MV-LV S1')

# pp.runpp(network)
# print(net.bus)
# print("\n The bus parameters are :")
# print(network.res_bus)
# print("\n The line parameters are :")
# print(network.res_line)

# Bus geo data

# network.bus_geodata = pd.read_json(
#     """{"x":{"0":7.0,"1":4.0,"2":4.0,"3":4.0,"4":2.5,"5":1.0,"6":1.0,"7":8.0,"8":8.0,"9":6.0,
#     "10":4.0,"11":4.0,"12":10.0,"13":10.0,"14":10.0},"y":{"0":16,"1":15,"2":13,"3":11,"4":9,
#     "5":7,"6":3,"7":3,"8":5,"9":5,"10":5,"11":7,"12":15,"13":11,"14":5}}""")
# # network.bus_geodata_lv = pd.read_json(
#     """{"x":{"15":10.0,"16":10,"17":9,"18":8,"19":7,"20":6,"21":11,"22":12,"23":13,"24":14,
#     "25":10,"26":10,"27":10.0,"28":10.0},"y":{"15":4,"16":3,"17":3,"18":3,"19":3,
#     "20":3,"21":3,"22":3,"23":3,"24":3,"25":2,"26":1,"27":0,"28":-1}}""")

# Match bus.index
# network.bus_geodata = network.bus_geodata.loc[network.bus.index]

# Plotting the network based on power flow results
simple_plotly(network, figsize=2.1, aspectratio=(16, 10))
# Plot results and network diagram in a HTML file
to_html(network, 'Data/MV_LV_net.html')

# Convert this grid to a json file
# pp.to_json(network, "Data/MV_LV_grid.json")
