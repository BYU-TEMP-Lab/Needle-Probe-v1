import logging
import numpy as np
from .bootstrap import setup_logging

logger = logging.getLogger("salt_probe_util")
setup_logging()

from concurrent.futures import ProcessPoolExecutor

try:
    from .GUI.GUI_main import SimulationOptions
    from .process_raw_data import get_folder_data
    from .optimizer import get_solved_values
    from .build_model import prepare_folder_for_optim
    from .plotting import plot_initial_model_vs_data, plot_solved_parameters_vs_temperature
    from .calibration import export_probe_calibration
except Exception as exc:
    logger.error("Failed during module import for main workflow: %s", exc)
    raise

# add uncertainty of thermocouple??? +/- 2.2 C

def main():
    # Overview of main workflow:
    # 1. Get selections from user via GUI
        # probe/crucible
        # sample material
        # physics model
        # k measurement, calibration, or sensitivity analysis
            # If k measurement or sensitivity analysis: ask user to select calibration
            # If k measurement or calibration: ask user to select data folder
    # 2. If sensitity analysis, run sensitivity analysis and save results (including user selections and warnings), then exit.
    # 3. If k measurement or calibration - read in data from experimental data files 
        # If calibration, calculate initial model parameters at ambient temperature for each file (multi-threaded)
    # 4. Plot initial model vs experimental data for inspection
    # 5. For each file, solve for properties at ambient temperature and store results (including user selections and warnings) (multi-threaded)
        # Results may need to be fitted to a temperature curve
    
          
    # ==============================================================================================
    # 1. get user selections
    # ==============================================================================================

    main_GUI = SimulationOptions()
    main_GUI.mainloop()   # waits here until window closes

    if getattr(main_GUI, "user_cancelled", True): # default to True if the attribute doesn't exist
        logger.info("User closed the window without proceeding. Exiting program.")
        exit(0)
    else:
        UI = main_GUI.get_selections_dict()

    task_mode = UI.get("task_mode")

    # ==============================================================================================
    # 2. If sensitivity analysis, run sensitivity analysis and save results (including user selections and warnings), then exit.
    # ==============================================================================================
    if task_mode == "Sensitivity Analysis":
            logger.info("Running sensitivity analysis...")
            logger.info("Sensitivity analysis is not yet implemented. Exiting program.")
            exit(0)

    # ==============================================================================================
    # 3. If k measurement or calibration - read in data from experimental data files 
        # If calibration, calculate initial model parameters at ambient temperature for each file
        # If k measurement, calculate initial sample parameters at ambient temperature for each file
    # ==============================================================================================

    # read in data from experimental data files
    folder_data = get_folder_data(main_GUI.test_folder_path, generate_plots=True) # main_GUI.generate_plots_var.get())

    # end program if no readable files
    if not folder_data:
        logger.warning("No valid data found. Exiting program.")
        return
    
    # solve and store properties for each file in folder_data at ambient temperature (multi-threading requires pickling, which doesn't like nested functions)
    # Note that this means we assume constant properties, heat flux, and ambient temperature during optimization of each file. 
    model_params_list = prepare_folder_for_optim(folder_data, main_GUI)
    
    model_name = UI.get("simulation_name")
    calibration = UI.get("calibration")
    convection_coefficient = UI.get("convection_coeff")
    params = get_model_params(
        task_mode, 
        model_name, 
        calibration, 
        folder_data, 
        convection_coefficient
    )

    # ==============================================================================================
    # 4. Plot initial model vs experimental data for inspection
    # ==============================================================================================
    # plot initial model vs experimental data for inspection
    try:
        plot_initial_model_vs_data(model_params_dict, show=False)
    except Exception as e:
        logger.warning("Plotting initial models failed: %s", e)
    
    # ==============================================================================================
    # 5. For each file, solve for properties at ambient temperature and store results (including user selections and warnings) (multi-threaded)
        # Results may need to be fitted to a temperature curve
    # ==============================================================================================
    # set up multi-threading for running optimization
    with ProcessPoolExecutor() as executor:
        logger.info("Beginning multi-threaded optimization...")
        folder_solved_values = list(executor.map(
            get_solved_values, 
            model_params_dict))

    if getattr(main_GUI, "run_calibration_var", None) is not None and main_GUI.run_calibration_var.get():
        try:
            out_csv = export_probe_calibration(model_params_dict, folder_solved_values)
            logger.info("Saved probe calibration CSV: %s", out_csv)
        except Exception as e:
            logger.warning("Exporting probe calibration failed: %s", e)

        if getattr(main_GUI, "save_summary_plots_var", None) is not None and main_GUI.save_summary_plots_var.get():
            try:
                plot_solved_parameters_vs_temperature(folder_solved_values, show=False)
            except Exception as e:
                logger.warning("Solved-parameter summary plot failed: %s", e)

    if getattr(main_GUI, "save_fit_plots_var", None) is not None and not main_GUI.save_fit_plots_var.get():
        logger.info("Fit plots were requested off in the GUI, but per-file fit plots are created by the optimizer after convergence.")

    # Process results...
    logger.info("Processed %s files.", len(folder_solved_values))
    
    for solved_file in folder_solved_values:
        logger.info(solved_file["message"])



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