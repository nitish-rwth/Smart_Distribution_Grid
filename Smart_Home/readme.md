# Smart Home Simulator

This simulator provides a way to simulate multiple types of smart homes using a config file and self-implemented parts of the house, so-called devices/components.
To use this simulator, a HomeModel class object calls the create() and passes a dictionary with house config as an argument. The same object is also implementing the step function for the houses. Finally, mosaik is used to instantiate the smart_homes and connect them further.

## Model - Implementing the Smart home
The Smart_home class needs a ```getparam``` function as well as a ```step``` function. The step function receives a step_size 
and the inputs from mosaik (for an overview of the inputs see the mosaik documentation). It is where the main logic of how the smart home works is implemented.
step() function gets the step_size and the current simulation time and calls energy_manager() of class EMS. This is the power control step of Smart Home.
Smart home devices may participate in this control step based on their respective energy states.

## The config file
The config file is a Json file with the following structure:

```JSON
{
  "housetypes": {
    "house_A": {
      "attrs": {"P_house": 0, "Q_house": 0}, //House attributes
      "num": 10,			     //No of houses of this type
      "components":			     //House devices
      {
        "Battery": {"num": 1, 
	  "params": {"P_in": 1, "max_P": 3.3, "min_P": -3.3, "max_energy": 5,
          "charge_efficiency": 0.9, "discharge_efficiency": 0.9, "soc_min": 0, "soc_max": 100, "soc": 100,
          "flag": 0, "in_service": 1} 	     //Device parameters
        },
        "EV": {"num": 1, "params": {"P_in": 1, "max_P": 22, "max_energy": 50, "charge_efficiency": 0.9,
          "soc_min": 10, "soc_max": 90, "soc": 10, "flag": 0, "in_service": 1}
        },
        "PVCollector": {"num": 1, "params": {"P":5}
        },
        "Load": {"num": 1, "params": {"P": 10, "Q": 5}
        }
      }
    },
```
An example config is given in ```example1.json```

# How to use simulator

## Initialization
First the wrapper has to be initialized using mosaik:  
``` wrapper = world.start('HomeModel', step_size=step_size)``` //step_size can be user defined  

Then the simulators can be created:  
```smart_homes = wrapper.HomeModel.create(len(houses), house_list=houses)```  
 where *len(houses)* is the total amount of houses specified in the config including all housetypes.  

All the created house entities will be in the *smart_homes* list and can be then connected to other simulators using mosaik, for example by using ```world.connect```

# How to run this as a mosaik simulation

Open the file "smart_home_demo.py" in the scenarios folder. If you have already cloned the git repo, set the working directory in your IDE as "./cosim_mosaik.git" with proper file path.
This will automatically adjust all the import paths. Results at the end of the simulation will be available under "cosim_mosaik/simulators/Smart_Home/Simulator/results". This file path is relative to your git repo.
