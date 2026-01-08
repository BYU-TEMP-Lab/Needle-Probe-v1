
# do we need bounds? If so LM doesn't support that. Trust Region Reflective might also work.

decision_var_options = {
        "Thermocouple k": 1, # W/(m*k)
        "Thermocouple rho": 1, # kg/m^3
        "Thermocouple cp": 1, #J/(kg*K)

        "Wire k": 1, 
        "Wire rho": 1,
        "Wire cp": 1,

        "Insulation k": 1,
        "Insulation rho": 1,
        "Insulation cp": 1,
        "Insulation Porosity ": 1, # unitless (ratio)

        "Sheath k": 1,
        "Sheath rho": 1,
        "Sheath cp": 1,
        "Sheath Emissivity ": 1, # unitless

        "Crucible k": 1,
        "Crucible rho": 1,
        "Crucible cp": 1,
        "Crucible Emissivity ": 1,

        "Sample k": 1,
        "Sample rho": 1,
        "Sample cp": 1,
        "Sample radius": 1, # m

        "Thermal Contact Resistance Sheath-Insulation": 1, # K/W
        "Thermal Contact Resistance Sheath-Sample": 1,

        "Ambient Temperature": 1, # K
        "Scatter": 1, # unitless
        "Flux Decay": 1,
        "Decay Point": 1,
        "Convection": 1, # W/(m^2*K)
        "Power": 1 # W
    }

# 1. SWITCH STATEMENT: Calculate values of ALL decision vars EITHER 
#    a. from calibration at temp OR
#    b. from material/crucible/probe properties at temp
# 2. Create vector of 
#    a. decision vars to be optimized (specified by user input). 
#    b. their initial values (calculated in step 1)
#    c. define bounds?
# 3. Pass to 1/2 to model/optimizer and return optimized vector back


def build_decision_vars_ICs(user_selections, file_data):
    probe = user_selections.probe
    crucible = user_selections.crucible
    sample = user_selections.sample

    T_ambient = file_data["avgT_amb_K"]

    for key in decision_var_options.keys():
        if user_selections["calibration"][key]:
            func = user_selections["calibration"][key]
            decision_var_options[key] = func(T_ambient)
            continue

        match key:
            case "Thermocouple k":
                func = probe.thermocouple_k
            case "Crucible k":
                func = crucible.material.k
            case _:
                func = lambda x: None
                print(f"No function found for decision variable {key}")

# TRY THIS INSTEAD VVVVVVVV

# # A mapping of variable names to object attributes
# property_map = {
#     "Thermocouple k": ("probe", "thermocouple_k"),
#     "Crucible k": ("crucible", "material", "k"),
#     "Sample k": ("sample", "material", "k"),
#     # ... etc
# }

# ALSO CONSIDER USING THIS STRUCTURE VVVVVVV
# ALSO CUT DOWN THE NUMBER OF VARIABLES!!!!!
# decision_var_metadata = {
#     "Sample k": {
#         "initial_guess": 1.0, 
#         "bounds": (0.01, 10.0), 
#         "prior_sigma": 0.05, # For Bayesian Penalty
#         "scale": 1.0         # For TRF x_scale
#     },
#     "Thermal Contact Resistance": {
#         "initial_guess": 0.001,
#         "bounds": (0, 0.5),
#         "prior_sigma": 0.1,
#         "scale": 0.001       # Scaling helps the optimizer handle tiny numbers
#     }
# }

# def build_decision_vars_ICs(user_selections, file_data):
#     T_amb = file_data["avgT_amb_K"]
#     ics = {}

#     for key, path in property_map.items():
#         # Check calibration first as you did
#         if user_selections["calibration"].get(key):
#             ics[key] = user_selections["calibration"][key](T_amb)
#         else:
#             # Dynamically traverse the object (e.g., user_selections.probe.thermocouple_k)
#             obj = user_selections
#             for attr in path:
#                 obj = getattr(obj, attr)
#             # Assuming 'obj' is now the function/property
#             ics[key] = obj(T_amb) if callable(obj) else obj
#     return ics
            




    return

# %% [code]
# Is this garbage? vvvvvvv
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

def run(x, y):
    return 2

if __name__ == "__main__":
    build_decision_vars_ICs()