
import numpy as np
# do we need bounds? If so LM doesn't support that. Trust Region Reflective might also work.

model_param_map = {
        "Thermocouple k": ("user_input", "probe", "TC_props", "k"), # W/(m*k)
        "Thermocouple rho": ("user_input", "probe", "TC_props", "rho"), # kg/m^3
        "Thermocouple cp": ("user_input", "probe", "TC_props", "cp"), #J/(kg*K)

        "Wire k": ("user_input", "probe", "heating_wire_props", "k"), 
        "Wire rho": ("user_input", "probe", "heating_wire_props", "rho"), # kg/m^3
        "Wire cp": ("user_input", "probe", "heating_wire_props", "cp"), # J/(kg*K)

        "Insulation k": ("user_input", "probe", "insulation_props", "k"), # W/(m*K)
        "Insulation rho": ("user_input", "probe", "insulation_props", "rho"), # kg/m^3
        "Insulation cp": ("user_input", "probe", "insulation_props", "cp"), # J/(kg*K)

        "Sheath k": ("user_input", "probe", "sheath_props", "k"), # W/(m*K)
        "Sheath rho": ("user_input", "probe", "sheath_props", "rho"), # kg/m^3
        "Sheath cp": ("user_input", "probe", "sheath_props", "cp"), # J/(kg*K)
        "Sheath Emissivity": ("user_input", "probe", "sheath_props", "emissivity"), # unitless
        
        "Crucible k": ("user_input", "crucible", "material", "k"), # W/(m*K)
        "Crucible rho": ("user_input", "crucible", "material", "rho"), # kg/m^3
        "Crucible cp": ("user_input", "crucible", "material", "cp"), # J/(kg*K)
        "Crucible Emissivity ": ("user_input", "crucible", "material", "emissivity"),
        "Crucible inner radius": ("user_input", "crucible", "inner_radius"), # m
        
        "Sample k": ("user_input", "sample", "k"),
        "Sample rho": ("user_input", "sample", "rho"),
        "Sample cp": ("user_input", "sample", "cp"),
        
        "Thermal Contact Resistance Sheath-Insulation": ("user_input", "probe", "TCR_insulation_sheath"), # K/W
        "??? Thermal Contact Resistance Sheath-Sample": 1, 

        "Ambient Temperature": ("file_data", "avgT_amb_K"), # K

        "??? Scatter": 1, # unitless
        "??? Flux Decay": 1,
        "??? Decay Point": 1,
        "??? Convection Coefficient": ("user_input", "convection_coeff"), # W/(m^2*K)
        "Power": ("file_data", "avgQ") # W
    }

def resolve_params_at_T(file_data, user_selections):
    T_amb = file_data["avgT_amb_K"]["initial_value"]
    print(f"# Resolving parameters for file {file_data['filepath'].name} at T_amb = {T_amb} K...")
    user_selections.probe.TC_props.update_properties_at_T(T_amb)
    user_selections.probe.heating_wire_props.update_properties_at_T(T_amb)
    user_selections.probe.insulation_props.update_properties_at_T(T_amb)
    user_selections.probe.sheath_props.update_properties_at_T(T_amb)
    user_selections.crucible.material.update_properties_at_T(T_amb)
    user_selections.sample.update_properties_at_T(T_amb)

    # initialize prepared data dictionary
    resolved_params = {}

    #dynamically set initial values, bounds, prior sigmas
    for key, path in model_param_map.items():
        # handle hardcoded values
        if not isinstance(path, tuple):
            resolved_params[key] = {
                "initial_value": path,
                "bounds": (path * 0.5, path * 1.5), # Default 50% swing
                "prior_sigma": path * 0.2           # Default 20% uncertainty
            }
            continue

        if isinstance(path, dict):
            resolved_params[key] = path
            continue
        
        # determine root source (folder_data vs user_input)
        source_root = path[0]
        attr_path = path[1:]

        # navigate the path
        current_obj = user_selections if source_root == "user_input" else file_data

        try:
            for attr in attr_path:
                # If current_obj is a dict, use get(); if object, use getattr()
                if isinstance(current_obj, dict):
                    current_obj = current_obj[attr]
                else:
                    current_obj = getattr(current_obj, attr)

            # Now current_obj should be the dict: {"initial_value": x, "bounds": y, ...}
            if isinstance(current_obj, dict):
                resolved_params[key] = current_obj.copy()
            elif isinstance(current_obj, (float, int)):
                val = float(current_obj)
                resolved_params[key] = {
                    "initial_value": val,
                    "bounds": (val * 0.5, val * 1.5),
                    "prior_sigma": val * 0.2
                }
            else:
                # Handle cases where the path led to an object instead of a value
                print(f"Warning: Could not resolve {key} to a numeric value.")
                
        except (KeyError, AttributeError):
            print(f"Warning: Could not resolve path for {key}")
    
    return resolved_params


def build_optim_vectors(resolved_params, user_selections):
    # Build vectors for optimization based on resolved parameters
    active_decision_vars = [list(user_selections.decision_vars.keys())[i] for i in user_selections.decision_vars_indx]
    
    initial_values = []
    lower_bounds = []
    upper_bounds = []
    prior_sigmas = []

    for var in active_decision_vars:
        if var not in resolved_params.keys():
            print(f"Warning: Decision variable {var} not found in resolved parameters.")
            continue

        initial_values.append(resolved_params[var]["initial_value"])
        lower_bounds.append(resolved_params[var]["bounds"][0])
        upper_bounds.append(resolved_params[var]["bounds"][1])
        prior_sigmas.append(resolved_params[var]["prior_sigma"])
        
    optim_vecs = {
        "active_decision_vars": active_decision_vars,
        "initial_values": np.array(initial_values),
        "bounds": (np.array(lower_bounds), np.array(upper_bounds)),
        "prior_sigmas": np.array(prior_sigmas)
    }

    return optim_vecs


def prepare_for_pickling(folder_data, user_selections):
    # initialize list to hold prepared data for all files
    prepared_list = []

    # solve for values at ambient temperature to plug into model
    for file in folder_data:
        resolved_params = resolve_params_at_T(file, user_selections)

        # build vectors for optimization
        optim_vecs = build_optim_vectors(resolved_params, user_selections)
        filepath = file["filepath"]
        prepared_list.append({
            "filepath": filepath,
            "resolved_params": resolved_params,
            "optim_vecs": optim_vecs
        })
    return prepared_list

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