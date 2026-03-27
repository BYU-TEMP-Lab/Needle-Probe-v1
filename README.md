# Needle Probe v1
Description here. 

# Python rewrite
Sudo code:

main.py:
- Define variables based on user selections in GUI
- Perform simple calculations on selected folder data to prepare for optimization
- Set up multi-threading for optimizer (runs files in parallel)

config:
- default_options.json: contains settings auto-filled into GUI. Files formatted the same can be loaded into GUI for convenience
- calibration_data
    - This is where calibration data for various probes is to be stored
    - THIS SHOULD PROBABLY BE MOVED TO "libraries"
- raw_material_data
    - this is where nist properties can be stored
    - THIS SHOULD PROBABLY BE MOVED TO "libraries"

GUI:
- allows user to select probe, sample, calibration, decision variables, etc. 

libraries:
- calibrations.py: organizes calibration data
- crucibles.py: lists and organizes information about various crucibles
- materials_utils.py: various functions used by other files for calculating materials properties
- materials.py: lists and organizes materials properties
- probes.py: lists and organizes probe properties
- simulations.py: lists and organizes the various simulations available

bootstrap.py: configures error messages for readability

build_model.py: 
- maps user inputs and data from libraries to be assigned to variables for use in model and optimizer
- prepare_folder_for_optim():
    - solves for material properties and tolerances at ambient temperature based on library data
        - NOTE: OUR MODEL ASSUMES CONSTANT MATERIAL PROPERTIES THROUGHOUT SIMULATION

flexPDE_model.py:
- run(): runs simulation to get back the time/temp curve
- generates FlexPDE file based on values from build_model.py

optimizer.py:
- optimizes a vector of values to be optimized to match the temp time curve
    - incorporates upper and lower bounds as well as "prior sigmas" for each value to be optimized
        - this just means that there is a "penalty" for straying from initial values based on our certainty in that value

process_data.py:
- reads experimental data from data files
    - stores filepath, temperature curve, std, ambient temperature, and average heat flux supplied by heating wire. 
- get_files_data() stores all of the information into a big list to be handed to the optimizer

thermal_quadrupoles_model.py
- not set up yet, but ideally should be set up to either run the thermal quadrupoles either in python, matlab, or C. 