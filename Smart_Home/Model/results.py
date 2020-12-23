# Plotting results of all control steps for one Smart Home

from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
from numpy import arange

# Plot configured for 24 hour control action
scale = list(arange(0, 24, .25))
scale1 = list(arange(0, 24.1, 1))
list_of_files = ['EMS_Results.csv', 'House_Results.csv', 'Battery_Results.csv', 'EV_Results.csv']
figure_names = ['Figure_%s' % i for i in range(1, 12)]
figure_titles = ['EMS Parameters', 'House Parameters', 'Storage Devices']
house_titles = ['Power demanded by House', 'Cumulative House Load', 'PV Generation', 'Electricity Costs (in €)']
ems_titles = ['P_set (from CMS)', 'Total_Earnings (in €)', 'CMS_Toggle', 'P_settled (by EMS)']


# Writing results of all control steps for one EMS
def write_to_csv(ems, list_of_results):

    # Writing Output of control step to a csv file
    output_dir = Path('cosim_mosaik/simulators/Smart_Home/Simulator/results/%s' % ems.name)
    output_dir.mkdir(parents=True, exist_ok=True)

    for (a, b) in zip(list_of_results, list_of_files):
        a.to_csv(output_dir/b, index=False, header=True, mode='w', sep=';')


# Individual plots for all parameters
def csv_to_plot():

    series = []
    figures = []
    figure_axes = []
    count = 0

    # Getting Output of control step from csv files
    output_dir = Path('cosim_mosaik/simulators/Smart_Home/Simulator/results/EMS_Smart_Home_1/Scenario 2')
    for b in list_of_files:
        series.append(pd.read_csv(output_dir/b, sep=';', header=0))

    for i in range(0, 12):
        figure, axes = plt.subplots(1, 1, figsize=(12, 6))
        figures.append(figure), figure_axes.append(axes)

    for axis in figure_axes:
        axis.margins(x=0)
        axis.tick_params(axis='x')
        axis.axhline(y=0, color='r', linestyle='--')

    # for (figure, title) in zip(figures, figure_titles):
    #     figure.suptitle('%s' % title, x=0.51, y=1.0, size='large', weight='bold')

    # Plotting results of the control step for EMS
    for i in range(0, 4):
        series[0].plot('Time (hours)', y=series[0].columns[i], xticks=scale1, title=ems_titles[i],
                       ax=figure_axes[i], fontsize=14)

    # Plotting results of the control step for house
    for i in range(0, 4):
        series[1].plot('Time (hours)', y=series[1].columns[i], xticks=scale1, title=house_titles[i],
                       ax=figure_axes[i+4], fontsize=14)

    # Plotting results of the control step for batteries
    for i in range(0, 2):
        series[2].plot('Time (hours)', y=series[2].columns[i], xticks=scale1, ax=figure_axes[i+8],
                       title='Battery_' + str(i+1), fontsize=14)

    for i in range(0, 1):
        series[3].plot('Time (hours)', y=series[3].columns[i], xticks=scale1, ax=figure_axes[i+10],
                       title='EV_' + str(i+1), fontsize=14)

    # Save figures to folder
    for (figure, name) in zip(figures, figure_names):
        figure.tight_layout()
        figure.savefig(output_dir/name, dpi=300)
        plt.close(figure)


# Comparison plots for all parameters
def compare_plots():

    series = []
    figures = []
    figure_axes = []
    twin_axes = []

    # Getting Output of control step from csv files
    output_dir = Path('cosim_mosaik/simulators/Smart_Home/Simulator/results/EMS_Smart_Home_1')
    for b in list_of_files:
        series.append(pd.read_csv(output_dir/b, sep=';', header=0))

    for i in range(0, 12):
        figure, axes = plt.subplots(1, 1, figsize=(12, 5))
        figures.append(figure), figure_axes.append(axes)

    for axis in figure_axes:
        axis.margins(x=0)
        axis.tick_params(axis='x')
        # axis.axhline(y=0, color='r', linestyle='--')

    # Duplicate axis for double plotting
    # for axis in twin_axes:
    #     axis.margins(x=0)
    #     axis.tick_params(axis='y', labelsize=14)

    # for (figure, title) in zip(figures, figure_titles):
    #     figure.suptitle('%s' % title, x=0.51, y=1.0, size='large', weight='bold')

    # Plotting results of the control step for EMS
    # House power curve vs res curve
    series[1].plot('Time (hours)', y=(series[1].columns[0]), xticks=scale1,
                   ax=figure_axes[0], fontsize=16, linestyle='-')
    series[1].plot('Time (hours)', y=(series[1].columns[1]), xticks=scale1,
                   ax=figure_axes[0], fontsize=16, linestyle=':', color='g')
    series[1].plot('Time (hours)', y=(series[1].columns[3]), xticks=scale1,
                   ax=figure_axes[0], fontsize=14, linestyle='--')
    figure_axes[0].set_ylabel('Power (in kW)', fontsize=16)
    figure_axes[0].axhline(y=0, color='r', linestyle='--')
    # figure_axes[0].axhline(y=5, color='g', linestyle='--')

    # Battery Performance
    twin_axes_1 = figure_axes[1].twinx()
    series[2].plot('Time (hours)', y=(series[2].columns[0]), xticks=scale1,
                   ax=figure_axes[1], fontsize=16, linestyle='-', color='orange')

    series[2].plot('Time (hours)', y=(series[2].columns[2]), xticks=scale1,
                   ax=twin_axes_1, fontsize=14, linestyle='--')
    figure_axes[1].legend(loc='lower left')
    figure_axes[1].set_ylabel('SOC (in %)', fontsize=16)
    twin_axes_1.legend(loc='lower center')
    twin_axes_1.set_ylabel('Power (in kW)', fontsize=16)
    twin_axes_1.axhline(y=0, color='r', linestyle=':')

    # Reward performance
    twin_axes_2 = figure_axes[2].twinx()
    series[0].plot('Time (hours)', y=(series[0].columns[1]), xticks=scale1,
                   ax=twin_axes_2, fontsize=16, linestyle='-', color='orange')
    series[0].plot('Time (hours)', y=(series[0].columns[3]), xticks=scale1,
                   ax=figure_axes[2], fontsize=14, linestyle='--')
    figure_axes[2].legend(loc='upper left')
    figure_axes[2].set_ylabel('Power (in kW)', fontsize=16)
    twin_axes_2.legend(loc='lower left', bbox_to_anchor=(0, 0.1))
    twin_axes_2.set_ylabel('incentive (in €)', fontsize=16)
    figure_axes[2].axhline(y=0, color='r', linestyle=':')

    # EV performance
    twin_axes_3 = figure_axes[3].twinx()
    series[3].plot('Time (hours)', y=(series[3].columns[0]), xticks=scale1,
                   ax=figure_axes[3], fontsize=16, linestyle='-', color='orange')
    series[3].plot('Time (hours)', y=(series[3].columns[1]), xticks=scale1,
                   ax=twin_axes_3, fontsize=14, linestyle='--')
    figure_axes[3].legend(loc='upper left')
    figure_axes[3].set_ylabel('SOC (in %)', fontsize=16)
    twin_axes_3.legend(loc='upper center')
    twin_axes_3.set_ylabel('Power (in kW)', fontsize=16)
    twin_axes_3.axhline(y=0, color='r', linestyle=':')

    # House power curve vs demand curve
    series[1].plot('Time (hours)', y=(series[1].columns[0]), xticks=scale1,
                   ax=figure_axes[4], fontsize=16, linestyle='-', lw=2)
    series[1].plot('Time (hours)', y=(series[1].columns[1]), xticks=scale1,
                   ax=figure_axes[4], fontsize=16, linestyle=':', color='g')
    series[0].plot('Time (hours)', y=(series[0].columns[0]), xticks=scale1,
                   ax=figure_axes[4], fontsize=14, linestyle='--', color='r')

    figure_axes[4].set_ylabel('Power (in kW)', fontsize=16)
    figure_axes[4].legend(loc='lower left')
    # figure_axes[4].axhline(y=0, color='r', linestyle=':')

    # House load Demand
    series[1].plot('Time (hours)', y=(series[1].columns[5]), xticks=scale1,
                   ax=figure_axes[5], fontsize=16, linestyle='-', legend='P_Load')
    figure_axes[5].set_ylabel('Power (in kW)', fontsize=16)
    figure_axes[5].axhline(y=0, color='r', linestyle='--')

    # House PV generation
    series[1].plot('Time (hours)', y=(series[1].columns[2]), xticks=scale1,
                   ax=figure_axes[6], fontsize=16, linestyle='-')
    figure_axes[6].set_ylabel('Power (in kW)', fontsize=16)

    # House load vs P_res
    series[1].plot('Time (hours)', y=(series[1].columns[5]), xticks=scale1,
                   ax=figure_axes[7], fontsize=16, linestyle='--', color='orange')
    figure_axes[7].set_ylabel('Power (in kW)', fontsize=16)
    figure_axes[7].axhline(y=0, color='r', linestyle='--')

    series[1].plot('Time (hours)', y=(series[1].columns[3]), xticks=scale1,
                   ax=figure_axes[7], fontsize=16, linestyle='-')

    # Save figures to folder
    for (figure, name) in zip(figures, figure_names):
        figure.tight_layout()
        figure.savefig(output_dir/name, dpi=300)
        plt.close(figure)


def main():
    # csv_to_plot()
    compare_plots()


if __name__ == '__main__':
    main()
