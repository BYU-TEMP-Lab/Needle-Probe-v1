import glob, subprocess, time, os, sys, warnings, json, itertools, numpy as np, pandas as pd
from .bootstrap import setup_logging
setup_logging()  # Apply custom warning format

from scipy.interpolate import interp1d
from scipy.optimize import least_squares
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

from .GUI.GUI_main import SimulationOptions
from .process_data import get_files_data
from .flexPDE_model import run as run_flex_model
from .thermal_quadrupoles_model import run as run_therm_quad_model
from .optimizer import run as run_optimizer, prepare_for_pickling

# import .libraries.materials, .libraries.probes, .optim as optim
# from .libraries.materials import options as material_options
# from .libraries.probes import options as probe_options
# from .libraries.crucibles import options as crucibles_options

# Generate simulation options dictionaries
simulation_options_dict = {"FlexPDE": run_flex_model, "Thermal Quadrupoles": run_therm_quad_model}
cross_section_options_dict = {"Axial": None, "Radial": None}

# function to be multi threaded
def get_solved_values(prepared_file_data, model_template):
    return run_optimizer(prepared_file_data, model_template)


def main():

    # get user selections
    main_GUI = SimulationOptions(
        simulation_options_dict, 
        cross_section_options_dict)
    main_GUI.mainloop()   # waits here until window closes

    if getattr(main_GUI, "user_cancelled", True): # default to True if the attribute doesn't exist
        print("User closed the window without proceeding. Exiting program.")
        exit(0)
    else:
        user_selections = main_GUI.get_selections_dict()
    # else:
    #     selections = main_GUI.get_selections_dict()
    #     print(selections)

    # read in data from experimental data files
    folder_data = get_files_data(main_GUI.test_folder_path)

    # end program if no readable files
    if not folder_data:
        print("No valid data found. Exiting program.")
        return
    
    # solve and store properties for each file in folder_data at ambient temperature (multi-threading requires pickling, which doesn't like nested functions)
    # Note that this means we assume constant properties during optimization at each temperature, and that the ambient temperature is representative of the entire test
    prepared_folder_data = prepare_for_pickling(folder_data, main_GUI)

    def get_model_template(main_GUI):
        return 2

    # set up model template for optimization runs
    model_template = get_model_template(main_GUI)
    
    # set up multi-threading for running optimization
    with ProcessPoolExecutor() as executor:
        print("Beginning multi-threaded optimization...")
        folder_solved_values = list(executor.map(
            get_solved_values, 
            prepared_folder_data,
            itertools.repeat(model_template)))

    # Process results...
    print(f"Processed {len(folder_solved_values)} files.")
    print(f"RESULT: {folder_solved_values}")



# testfolder = input("Enter experimental data folder path: ")
# crucible = "Nickel200"
# sample = "Argon"
# SolvNam = ["Thermal Contact Resistance Sheath-Insulation", "cp Insulation"]
# SolvVal = np.array([0.0052, 780], dtype=float)
# SolvConstraintsLower = np.array([0.0001, 300])
# SolvConstraintsUpper = np.array([2, 1400])
# cross_section = "radial"
# timewindow = (0, 4)
# MC = 0
# Chi2_tolerance = 1e-4

# output_folder = os.path.join(testfolder, 'Output')
# os.makedirs(output_folder, exist_ok=True)

# %Scatter and Index of Refraction%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# index_of_refraction = 1.462 - (1.4e-4)*T; %Solar salts (citation needed)
# scatter = 0;
# % Convection coefficient
# h_convection = 10; %just an assumption

# TCR_sheath_sample = thermal_contact_resistance(Sheath.name, "Generic Sample", ignore_warnings=True)


# ------------------- Helper Functions ------------------- #


# is this garbage? vvvv
def properties(crucible, sample, T_amb, MC):
    par_names = ["Thermal Contact Resistance Sheath-Insulation", "cp Insulation"]
    par_vector = np.array([0.005, 800])  # dummy default
    return par_vector, par_names


# # ------------------- Main Parallel Loop ------------------- #
# files = [f for f in glob.glob(os.path.join(testfolder, '*')) if os.path.isfile(f)]
# with Pool(processes=min(cpu_count(), len(files))) as pool:
#     results = pool.map(process_file, files)

# # Store results in DataFrame
# ParamTemp = pd.DataFrame(columns=['T_amb_K', 'Chi_Squared'] + SolvNam)
# for res in results:
#     avgT_amb, Chi2_val, SolvedParam = res
#     row = [avgT_amb, Chi2_val] + list(SolvedParam)
#     ParamTemp.loc[len(ParamTemp)] = row

# # Save CSV
# date_str = datetime.now().strftime("%Y%m%d")
# ParamTemp.to_csv(os.path.join(output_folder, f'Parameters_{date_str}.csv'), index=False)

if __name__ == "__main__":
    # app = SimulationOptions()
    # app.mainloop()

    # selections = app.get_selections()
    # print(selections)
    main()