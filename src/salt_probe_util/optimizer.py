
import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

from .libraries.simulations import simulation_options_dict

logger = logging.getLogger(__name__)

@dataclass
class OptimParam:
    initial_value: float
    bounds: tuple
    prior_sigma: float

def build_optim_vectors(resolved_params, user_selections):
    # Build vectors for optimization based on resolved parameters
    candidate_decision_vars = [list(user_selections.decision_vars.keys())[i] for i in user_selections.decision_vars_indx]
    active_decision_vars = []
    
    initial_values = []
    lower_bounds = []
    upper_bounds = []
    prior_sigmas = []

    for var in candidate_decision_vars:
        if var not in resolved_params.keys():
            logger.warning("Decision variable %s not found in resolved parameters.", var)
            continue

        if not isinstance(resolved_params[var], dict) or "initial_value" not in resolved_params[var]:
            logger.warning("Decision variable %s is not a scalar parameter and will be skipped.", var)
            continue

        active_decision_vars.append(var)

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

    # Allow selection of optimizer method from user selections (e.g., 'lm' or 'trf')
    optim_vecs["method"] = getattr(user_selections, "optim_method", "trf")

    return optim_vecs


def get_residuals(x, file_data, simulation_name, initial_model_params, active_decision_vars, x0, priors):
    # get experimental temp curve and filename
    exp_temp_curve = file_data["tempData"]
    filepath = file_data["filepath"]
    
    # create copy of prepared data to modify
    # iter_params = initial_model_params.copy()
    iter_model_params = initial_model_params.copy()

    # update resolved parameters with current optimization values
    for key, val in zip(active_decision_vars, x):
        iter_model_params[key] = val

    # get simulation temp curve
    simulation = simulation_options_dict[simulation_name]
    sim_temp_curve = simulation(iter_model_params, filepath)

    # interpolate simulation to experimental time points
    exp_times = exp_temp_curve[:, 0]
    sim_times = sim_temp_curve[:, 0]
    sim_temps = sim_temp_curve[:, 1]
    sim_temps_interp = np.interp(exp_times, sim_times, sim_temps)

    # residuals
    error_residuals = (sim_temps_interp - exp_temp_curve[:, 1]) / file_data["tempData_std"]
    prior_residuals = (x - x0) / priors

    return np.concatenate((error_residuals, prior_residuals))

def get_solved_values(prepared_file_data):
    # unpack prepared data
    optim_vecs = prepared_file_data["optim_vecs"]
    simulation_name = prepared_file_data["simulation"]
    initial_model_params = prepared_file_data["resolved_params"]
    file_data = prepared_file_data["file_data"]
    active_decision_vars = optim_vecs["active_decision_vars"]
    x0 = optim_vecs["initial_values"]
    bounds = optim_vecs["bounds"]
    priors = optim_vecs["prior_sigmas"]

    # function to compute residuals
    method = prepared_file_data["optim_vecs"].get("method", "trf")

    def _to_unbounded(x, lb, ub, eps=1e-12):
        p = (x - lb) / (ub - lb)
        p = np.clip(p, eps, 1 - eps)
        return np.log(p / (1 - p))

    def _to_bounded(y, lb, ub):
        p = 1.0 / (1.0 + np.exp(-y))
        return lb + (ub - lb) * p

    if method == "lm":
        # Standard LM without bounds
        result = least_squares(
            get_residuals,
            x0,
            method="lm",
            x_scale=priors,
            args=(
                file_data,
                simulation_name,
                initial_model_params,
                active_decision_vars,
                x0,
                priors,
            ),
        )
    elif method == "lm_bounded":
        # Use variable transform to enforce bounds with LM
        lb = bounds[0]
        ub = bounds[1]
        y0 = _to_unbounded(x0, lb, ub)

        def residuals_in_y(y):
            x = _to_bounded(y, lb, ub)
            return get_residuals(x, file_data, simulation_name, initial_model_params, active_decision_vars, x0, priors)

        result = least_squares(
            residuals_in_y,
            y0,
            method="lm",
            x_scale=priors,
            args=(),
        )

        # Map back to original parameter space
        x_sol = _to_bounded(result.x, lb, ub)
        # create a fake result-like object with .x mapped to x_sol for downstream packaging
        class _Res:
            pass

        tmp = _Res()
        tmp.x = x_sol
        tmp.cost = 0.5 * np.sum(result.fun**2)
        tmp.nfev = result.nfev
        tmp.message = result.message
        tmp.success = result.success
        result = tmp
    else:
        result = least_squares(
            get_residuals,
            x0,
            bounds=bounds,
            method="trf",
            x_scale=priors,
            args=(
                file_data,
                simulation_name,
                initial_model_params,
                active_decision_vars,
                x0,
                priors,
            ),
        )
    
    # package results
    solved = {
        "filepath": file_data["filepath"],
        "T_amb_K": file_data["avgT_amb_K"]["initial_value"],
        "solved_values": {},
        "cost": result.cost,
        "iterations": result.nfev,
        "message": result.message,
        "success": result.success
    }

    for key, val in zip(prepared_file_data["optim_vecs"]["active_decision_vars"], result.x):
        solved["solved_values"][key] = val

    # After convergence, generate and save fitted-vs-data plot
    try:
        iter_model_params = initial_model_params.copy()
        for key, val in zip(prepared_file_data["optim_vecs"]["active_decision_vars"], result.x):
            iter_model_params[key] = val

        sim_callable = simulation_options_dict[simulation_name]
        sim_curve = sim_callable(iter_model_params, file_data["filepath"])  # Nx2 array

        # Prepare output directory
        data_path = Path(file_data["filepath"]).resolve()
        plot_dir = data_path.parent / "Plots_initial_model"
        plot_dir.mkdir(parents=True, exist_ok=True)
        out_file = plot_dir / f"{data_path.stem}_fitted.png"

        exp_curve = file_data["tempData"]
        exp_y = exp_curve[:, 1] - exp_curve[:, 1][0]
        sim_y = sim_curve[:, 1] - sim_curve[:, 1][0]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(exp_curve[:, 0], exp_y, s=6, c="tab:blue", alpha=0.6, label="Experimental")
        ax.plot(sim_curve[:, 0], sim_y, c="tab:green", lw=1.5, label="Fitted model")
        ax.set_xscale("log")
        ax.set_xlabel("Time (s)")
        ambient = file_data.get("avgT_amb_K", {}).get("initial_value", None)
        ax.set_ylabel(r"$\Delta T$ relative to start (K)")
        if ambient is not None:
            title = f"{data_path.name} — Fitted model vs data (shifted to T0={ambient:.2f} K)"
        else:
            title = f"{data_path.name} — Fitted model vs data (shifted to initial value)"
        ax.set_title(textwrap.fill(title, width=58), fontsize=10)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_file, dpi=200, bbox_inches="tight")
        plt.close(fig)
        solved["fitted_plot"] = str(out_file)
    except Exception as e:
        solved["fitted_plot"] = None
        logger.warning("Could not create fitted plot: %s", e)

    return solved


if __name__ == "__main__":
    pass