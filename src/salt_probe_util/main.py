import glob, subprocess, time, os, sys, warnings, json, numpy as np, pandas as pd

import src.salt_probe_util.bootstrap as bootstrap
bootstrap.setup_logging()  # Apply custom warning format

from scipy.interpolate import interp1d
from scipy.optimize import least_squares
from datetime import datetime
from multiprocessing import Pool, cpu_count

from .GUI.GUI_main import SimulationOptions
# import .libraries.materials, .libraries.probes, .optim as optim
# from .libraries.materials import options as material_options
# from .libraries.probes import options as probe_options
# from .libraries.crucibles import options as crucibles_options


# ------------------- User Inputs ------------------- #
def main():
    
    simulation_options_dict = {"FlexPDE": None,
                                   "Thermal Quadrupoles": None}
    cross_section_options_dict = {"Axial": None, 
                               "Radial": None}

    user_input = SimulationOptions(simulation_options_dict, cross_section_options_dict)
    user_input.mainloop()   # waits here until window closes

    if getattr(user_input, "user_cancelled", True):
        print("User closed the window without proceeding. Exiting program.")
        exit(0)
    else:
        selections = user_input.get_selections()
        print(selections)

    # Extract Data
    # Build Initial Model (Get estimated properties/initial values)
    # Choose which vars to optimize based on GUI selections
    # Set bounds
    # Optimize
    ## Run model (FlexPDE)
    ## Compare Model to each Data file (one at a time? all at once?)
    ## Adjust Parameters
    ## Repeat
    # Return Comparison 


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



def properties(crucible, sample, T_amb, MC):
    par_names = ["Thermal Contact Resistance Sheath-Insulation", "cp Insulation"]
    par_vector = np.array([0.005, 800])  # dummy default
    return par_vector, par_names

def run_flexpde(par_vector, par_names, SolvNam, endtime, flexpde_path=r'C:\Program Files\FlexPDE7\FlexPDE7.exe'):
    """
    Generates a full FlexPDE file from parameters, runs FlexPDE, and returns the temp vs time array.
    """
    # --- Geometry & fixed constants ---
    r_tc = 0.094313e-3
    TC_loc = 0.05
    r_wires = 0.094313e-3
    r_wir_o = 0.485942e-3
    r_wir_i = 0.297315e-3
    r_wir_mid = 0.391629E-3
    HW_curve = 4.85942e-4
    HW_Ni = 0.002
    r_Al = 0.8293e-3
    r_Ni = 1.388E-3
    Ni_curve = 0.001
    samp_probe = -0.001
    r_cruc = 0.0127
    h_max = 0.1
    h_base = -0.01 + samp_probe
    vol_wires = np.pi*r_wires**2*(h_max*2) + (np.pi**2 * r_wires**2 * r_wir_mid)
    L = h_max - (r_Ni - r_Al + HW_Ni + HW_curve) + 2*np.pi*r_wir_mid

    # --- Assign parameters ---
    k_Thermocouple = par_vector[0]
    rho_Thermocouple = par_vector[1]
    cp_Thermocouple = par_vector[2]

    k_wire = par_vector[3]
    rho_wire = par_vector[4]
    cp_wire = par_vector[5]

    k_Alumina = par_vector[6]*np.exp((-1.5*(par_vector[20]/100))/(1-(par_vector[20]/100)))
    rho_Alumina = par_vector[7]
    cp_Alumina = par_vector[8]

    k_Sheath = par_vector[9]
    rho_Sheath = par_vector[10]
    cp_Sheath = par_vector[11]
    e_Ni = par_vector[12]

    k_Crucible = par_vector[13]
    rho_Crucible = par_vector[14]
    cp_Crucible = par_vector[15]
    e_Crucible = par_vector[16]

    k_Sample = par_vector[23]
    if 'Sample' in SolvNam:
        rho_cp_Sample = par_vector[26]
        rho_Sample = 1
        cp_Sample = rho_cp_Sample / rho_Sample
    else:
        rho_Sample = par_vector[24]
        cp_Sample = par_vector[25]

    scatter = par_vector[17]
    h_conv = par_vector[18]
    q_gen_wire = par_vector[19]/vol_wires
    rTh_alumina_sheath = par_vector[21]
    rTh_sheath_sample = par_vector[22]
    T_amb = par_vector[27]
    r_samp = par_vector[28]

    # Lumped wire properties
    k_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*k_Alumina + (3.4381e-11 + L*5.5889e-9)*k_wire) / (4.119e-10 + L*8.1652e-8)
    rho_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*rho_Alumina + (3.4381e-11 + L*5.5889e-9)*rho_wire) / (4.119e-10 + L*8.1652e-8)
    cp_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*cp_Alumina + (3.4381e-11 + L*5.5889e-9)*cp_wire) / (4.119e-10 + L*8.1652e-8)
    qgen_Heating_wires = ((3.4381e-11 + L*5.5889e-9)*q_gen_wire) / (4.119e-10 + L*8.1652e-8)

    # --- Generate PDE filename ---
    uniqueID = str(np.random.randint(1000, 9999))
    filename = f"Flex_{uniqueID}.pde"

    # --- PDE content ---
    pde_lines = [
        "TITLE 'Needle Probe Radial X-Section (non-lumped properties)'",
        "COORDINATES YCYLINDER('R','Z')",
        "VARIABLES",
        "temp",
        "DEFINITIONS",
        f"time_end = {endtime:.4f}",
        "t_step = 0.001",
        f"T_amb = {T_amb:.4f}",
        "k", "rho", "cp",
        f"q_gen = 0",
        f"temp_r2 = EVAL(temp,{r_Ni:.6f},0)",
        f"temp_r3 = EVAL(temp,{r_samp:.6f},0)",
        f"q_rad = (5.67e-8*((temp)^4 - temp_r3^4)/(1/{e_Ni:.4f} + (1-{e_Crucible:.4f})/{e_Crucible:.4f} * {r_Ni:.4f}/{r_samp:.4f}))",
        "MATERIALS",
        f'"Crucible" : k={k_Crucible:.4f} rho={rho_Crucible:.4f} cp={cp_Crucible:.4f}',
        f'"Sample" : k={k_Sample:.4f} rho={rho_Sample:.4f} cp={cp_Sample:.4f}',
        f'"Sheath" : k={k_Sheath:.4f} rho={rho_Sheath:.4f} cp={cp_Sheath:.4f}',
        f'"Alumina" : k={k_Alumina:.4f} rho={rho_Alumina:.4f} cp={cp_Alumina:.4f}',
        f'"Heating_wires" : k={k_Heating_wires:.4f} rho={rho_Heating_wires:.4f} cp={cp_Heating_wires:.4f} q_gen={qgen_Heating_wires:.4f}',
        f'"Thermocouple" : k={k_Thermocouple:.4f} rho={rho_Thermocouple:.4f} cp={cp_Thermocouple:.4f}',
        "INITIAL VALUES",
        "temp = T_amb",
        "EQUATIONS",
        "temp: div(k*grad(temp)) + q_gen = (rho*cp)*dt(temp)",
        "TIME",
        "0 BY t_step TO time_end",
        "HISTORIES",
        'History(Temp) AT (0.0, 0.05) export format "#t#r,#i" file="temp.txt"',
        "END"
    ]

    # Write PDE file
    with open(filename, 'w') as f:
        f.write("\n".join(pde_lines))

    # --- Run FlexPDE ---
    command = f'"{flexpde_path}" "{filename}" /r -S'
    subprocess.run(command, shell=True)

    # Wait for temp.txt output
    while not os.path.exists("temp.txt"):
        time.sleep(0.1)

    # Read the FlexPDE output
    temp_tvt = np.loadtxt("temp.txt", delimiter=',', skiprows=8)

    return uniqueID, filename, temp_tvt

def chi2_residuals(x, SolvNam, par_vector, par_names, idx_par_to_Solv, expTvt):
    # Update par_vector with normalized parameters
    for idx_par, idx_solv in idx_par_to_Solv:
        par_vector[idx_par] = x[idx_solv]
    # Run simulation
    _, _, FlexTvt = run_flexpde(par_vector, par_names, SolvNam, expTvt[-1,0])
    # Interpolate FlexPDE data to experimental times
    interp_func = interp1d(FlexTvt[:,0], FlexTvt[:,1], kind='cubic', fill_value="extrapolate")
    T_interp = interp_func(expTvt[:,0])
    residuals = (T_interp - expTvt[:,1]) / expTvt[:,1]  # normalized residuals
    return residuals

def process_file(filepath):
    filename = os.path.basename(filepath)
    print(f"Processing {filename}")
    expTvt, avgT_amb = extract_data(filepath, timewindow)
    par_vector, par_names = properties(crucible, sample, avgT_amb, MC)

    # Map parameters to solve
    idx_par_to_Solv = [(j, SolvNam.index(par)) for j, par in enumerate(par_names) if par in SolvNam]
    idx_par_to_Solv = np.array(idx_par_to_Solv)

    # Initial guess
    for j, (idx_par, idx_solv) in enumerate(idx_par_to_Solv):
        SolvVal[idx_solv] = par_vector[idx_par]

    # Optimize
    res = least_squares(
        chi2_residuals,
        SolvVal,
        bounds=(SolvConstraintsLower, SolvConstraintsUpper),
        args=(SolvNam, par_vector.copy(), par_names, idx_par_to_Solv, expTvt),
        method='trf'
    )
    SolvedParam = res.x
    Chi2_val = np.sum(res.fun**2)
    print(f"Solved parameters: {SolvedParam}, Chi2: {Chi2_val}")
    return avgT_amb, Chi2_val, SolvedParam

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