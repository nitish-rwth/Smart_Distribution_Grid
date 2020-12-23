import json
from copy import deepcopy
from cosim_mosaik.simulators.Smart_Home.Model.house import House

list_of_houses = []


# Reading the JSON File with house configs
def read_from_json(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
        houses = data['housetypes']
        return houses


def create_house(houses, counter):
    no_of_houses = 0

    # Counting total no of houses of all possible configurations
    for home in houses.items():
        no_of_houses += home[1]['num']
    # print('The total number of houses are', no_of_houses)

    # Creating objects for class House
    for home in houses.items():
        if counter <= no_of_houses:
            for j in range(0, home[1]['num']):  # Create smart homes with each specific house type
                smart_home = House(counter, deepcopy(home[1]['attrs']), deepcopy(home[1]['components']))
                list_of_houses.append(smart_home)
                counter += 1

    return list_of_houses


if __name__ == '__main__':
    house_dict = read_from_json('C:/Users/bansal/Documents/cosim_mosaik.git/cosim_mosaik/simulators/Smart_Home'
                                '/Model/Data/example1.json')
    homes = create_house(house_dict, 1)
