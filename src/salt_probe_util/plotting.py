from pathlib import Path
import math
import textwrap
import matplotlib.pyplot as plt
from .libraries.simulations import simulation_options_dict


def _normalize_to_initial(y_values):
    y_values = list(y_values)
    if not y_values:
        return y_values
    y0 = y_values[0]
    return [y - y0 for y in y_values]


def plot_initial_model_vs_data(prepared_list, show=False, out_dir=None):
    """Plot initial model (resolved params) against experimental data for each prepared file.

    - prepared_list: list of dicts returned by `prepare_folder_for_optim`
    - show: if True, call `plt.show()` for each figure
    - out_dir: optional Path where to write plots; if None, saves next to each data file
    """
    for item in prepared_list:
        file_data = item["file_data"]
        resolved = item["resolved_params"]
        sim_name = item.get("simulation")

        sim_callable = simulation_options_dict.get(sim_name)
        if sim_callable is None:
            print(f"No simulation callable found for '{sim_name}', skipping plot for {file_data['filepath'].name}")
            continue

        # run simulation with the resolved (initial) parameters
        try:
            sim_curve = sim_callable(resolved, file_data["filepath"])
        except Exception as e:
            print(f"Simulation {sim_name} failed for {file_data['filepath'].name}: {e}")
            continue

        time_exp = file_data["tempData"][:, 0]
        temp_exp = file_data["tempData"][:, 1]

        time_sim = sim_curve[:, 0]
        temp_sim = sim_curve[:, 1]

        # Plot both curves relative to their own initial value so the start is at 0
        temp_exp_plot = temp_exp - temp_exp[0]
        temp_sim_plot = temp_sim - temp_sim[0]

        # prepare output folder
        data_path = Path(file_data["filepath"]).resolve()
        save_dir = Path(out_dir) if out_dir else data_path.parent / "Plots_initial_model"
        save_dir.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(time_exp, temp_exp_plot, s=6, c="tab:blue", alpha=0.6, label="Experimental")
        ax.plot(time_sim, temp_sim_plot, c="tab:orange", lw=1.5, label="Initial model")
        ax.set_xscale("log")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(r"$\Delta T$ relative to start (K)")
        ambient = file_data.get("avgT_amb_K", {}).get("initial_value", None)
        if ambient is not None:
            title = f"{data_path.name} — Initial model vs data (T_amb={ambient:.2f} K)"
        else:
            title = f"{data_path.name} — Initial model vs data"
        ax.set_title(textwrap.fill(title, width=58), fontsize=10)
        ax.legend()

        out_file = save_dir / f"{data_path.stem}_initial_model.png"
        fig.tight_layout()
        fig.savefig(out_file, dpi=200, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved initial-model plot: {out_file}")

        if show:
            img = plt.imread(out_file)
            plt.imshow(img)
            plt.axis('off')
            plt.show()


def plot_solved_parameters_vs_temperature(folder_solved_values, show=False, out_dir=None):
    """Plot solved parameters against ambient temperature across all files."""
    if not folder_solved_values:
        print("No solved values available for summary plot.")
        return None

    param_names = set()
    temp_solved_pairs = []
    for solved in folder_solved_values:
        if solved.get("T_amb_K") is None:
            continue
        temp_solved_pairs.append((solved["T_amb_K"], solved))
        param_names.update(solved.get("solved_values", {}).keys())

    if not temp_solved_pairs or not param_names:
        print("Insufficient solved values to build summary plot.")
        return None

    sorted_pairs = sorted(temp_solved_pairs, key=lambda pair: pair[0])
    solved_sorted = [pair[1] for pair in sorted_pairs]

    plot_dir = Path(out_dir) if out_dir else Path(solved_sorted[0]["filepath"]).resolve().parent / "Plots_calibration"
    plot_dir.mkdir(parents=True, exist_ok=True)
    out_file = plot_dir / "solved_parameters_vs_temperature.png"

    param_names = sorted(param_names)
    n_params = len(param_names)
    ncols = 2
    nrows = math.ceil(n_params / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4 * nrows), squeeze=False)

    for idx, param in enumerate(param_names):
        ax = axes[idx // ncols][idx % ncols]
        values = []
        plot_temps = []
        for solved in solved_sorted:
            val = solved.get("solved_values", {}).get(param)
            if val is None:
                continue
            plot_temps.append(solved["T_amb_K"])
            values.append(val)

        if values:
            ax.plot(plot_temps, values, marker="o", lw=1.5)
        ax.set_title(param)
        ax.set_xlabel("Ambient temperature (K)")
        ax.set_ylabel("Solved value")
        ax.grid(True, alpha=0.3)

    for idx in range(n_params, nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")

    fig.suptitle("Solved parameters vs ambient temperature", y=1.01)
    fig.tight_layout()
    fig.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved solved-parameter summary plot: {out_file}")

    if show:
        img = plt.imread(out_file)
        plt.imshow(img)
        plt.axis('off')
        plt.show()

    return out_file
