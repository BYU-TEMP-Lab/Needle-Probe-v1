
import numpy as np
from scipy.optimize import least_squares
from .build_model import resolve_params_at_T
from .main import simulation_options_dict


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


def prepare_folder_for_optim(folder_data, user_selections):
    # initialize list to hold prepared data for all files
    prepared_list = []

    # solve for values at ambient temperature to plug into model
    for file in folder_data:
        resolved_params, optim_vecs = resolve_params_at_T(file, user_selections)
        
        prepared_list.append({
            "file_data": file,
            "resolved_params": resolved_params,
            "simulation": user_selections.simulation,
            "optim_vecs": optim_vecs
        })

    return prepared_list


def get_residuals(x, initial_model_params, active_decision_vars, x0, priors):
    # create copy of prepared data to modify
    # iter_params = initial_model_params.copy()
    iter_model_params = initial_model_params.copy()

    # update resolved parameters with current optimization values
    for key, val in zip(active_decision_vars, x):
        iter_model_params[key] = val

    # get simulation temp curve
    simulation = simulation_options_dict[iter_model_params["simulation"]]
    sim_temp_curve = simulation(iter_model_params)

    # get experimental temp curve
    exp_temp_curve = iter_model_params["file_data"]["tempData"]

    # interpolate simulation to experimental time points
    exp_times = exp_temp_curve[:, 0]
    sim_times = sim_temp_curve[:, 0]
    sim_temps = sim_temp_curve[:, 1]
    sim_temps_interp = np.interp(exp_times, sim_times, sim_temps)

    # residuals
    error_residuals = (sim_temps_interp - exp_temp_curve[:, 1]) / iter_model_params["file_data"]["tempData_std"]
    prior_residuals = (x - x0) / priors

    return np.concatenate((error_residuals, prior_residuals))

def get_solved_values(prepared_file_data):
    # unpack prepared data
    optim_vecs = prepared_file_data["optim_vecs"]
    initial_model_params = prepared_file_data["resolved_params"]
    active_decision_vars = optim_vecs["active_decision_vars"]
    x0 = optim_vecs["initial_values"]
    bounds = optim_vecs["bounds"]
    priors = optim_vecs["prior_sigmas"]

    # function to compute residuals
    result = least_squares(
        get_residuals, x0, 
        bounds=bounds,
        method = 'trf',
        x_scale = priors,
        args = (
            initial_model_params, 
            active_decision_vars,
            x0,
            priors
            )
    )
    
    # package results
    solved = {
        "filepath": prepared_file_data["filepath"],
        "solved_values": {}
    }

    for key, val in zip(prepared_file_data["optim_vecs"]["active_decision_vars"], result.x):
        solved["solved_values"][key] = val

    return solved


if __name__ == "__main__":
    pass