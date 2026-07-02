from __future__ import annotations

import csv
import logging
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .libraries.simulations import simulation_options_dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SensitivityResult:
    filepath: Path
    ambient_temperature_K: float
    parameter_name: str
    time_s: np.ndarray
    sensitivity_percent: np.ndarray


def _shift_to_initial(curve: np.ndarray) -> np.ndarray:
    if curve.size == 0:
        return curve
    shifted = curve.copy()
    shifted[:, 1] = shifted[:, 1] - shifted[0, 1]
    return shifted


def _get_param_value(resolved_params: dict, param_name: str):
    value = resolved_params.get(param_name)
    if isinstance(value, dict):
        return value.get("initial_value")
    return value


def _set_param_value(resolved_params: dict, param_name: str, value):
    updated = resolved_params.copy()
    current = updated.get(param_name)
    if isinstance(current, dict) and "initial_value" in current:
        new_entry = current.copy()
        new_entry["initial_value"] = float(value)
        updated[param_name] = new_entry
    else:
        updated[param_name] = float(value)
    return updated


def _compute_sensitivity_for_param(prepared_item: dict, param_name: str, perturbation: float = 0.95):
    simulation_name = prepared_item["simulation"]
    sim_callable = simulation_options_dict.get(simulation_name)
    if sim_callable is None:
        raise ValueError(f"No simulation callable registered for '{simulation_name}'.")

    file_data = prepared_item["file_data"]
    resolved = prepared_item["resolved_params"]
    filepath = Path(file_data["filepath"])
    ambient = file_data["avgT_amb_K"]["initial_value"]

    base_value = _get_param_value(resolved, param_name)
    if base_value is None:
        raise ValueError(f"Parameter '{param_name}' not found in resolved parameters for {filepath.name}.")

    varied_value = base_value * perturbation

    base_curve = _shift_to_initial(sim_callable(resolved, filepath))
    varied_curve = _shift_to_initial(sim_callable(_set_param_value(resolved, param_name, varied_value), filepath))

    if base_curve.size == 0 or varied_curve.size == 0:
        raise ValueError(f"Empty simulation output for {filepath.name}.")

    t = base_curve[:, 0]
    if t.size < 3:
        raise ValueError(f"Not enough time points for sensitivity analysis in {filepath.name}.")

    if np.isclose(t[0], 0.0) or t[0] <= 0:
        t_eval = t[1:]
        base_y = base_curve[:, 1][1:]
    else:
        t_eval = t
        base_y = base_curve[:, 1]

    if varied_curve.shape[0] != base_curve.shape[0] or not np.allclose(varied_curve[:, 0], t):
        varied_y = np.interp(t_eval, varied_curve[:, 0], varied_curve[:, 1])
    else:
        varied_y = varied_curve[:, 1][1:] if t_eval.shape[0] != varied_curve.shape[0] else varied_curve[:, 1]

    log_t = np.log(t_eval)
    dy = np.diff(base_y) / np.diff(log_t)
    dy_varied = np.diff(varied_y) / np.diff(log_t)

    with np.errstate(divide="ignore", invalid="ignore"):
        sensitivity_percent = 100.0 * (dy_varied - dy) / dy

    return SensitivityResult(
        filepath=filepath,
        ambient_temperature_K=ambient,
        parameter_name=param_name,
        time_s=t_eval[1:],
        sensitivity_percent=sensitivity_percent,
    )


def run_sensitivity_analysis(
    prepared_folder_data: list[dict],
    parameter_names: list[str],
    *,
    perturbation: float = 0.95,
    out_dir: str | Path | None = None,
    save_csv: bool = True,
    save_plots: bool = True,
):
    """Run a MATLAB-style sensitivity analysis across prepared files.

    Computes sensitivity for all (file, parameter) pairs and produces:
    - Individual per-parameter plots (one per file × parameter pair)
    - A summary bar chart showing which parameters have the biggest overall effect
    - A heatmap showing sensitivity magnitude across all files and parameters
    - A consolidated CSV with all results

    Returns a list of SensitivityResult objects.
    """
    results: list[SensitivityResult] = []
    csv_rows = []

    if not prepared_folder_data:
        raise ValueError("No prepared folder data supplied.")

    first_file = Path(prepared_folder_data[0]["file_data"]["filepath"]).resolve()
    plot_dir = Path(out_dir) if out_dir else first_file.parent / "Sensitivity_Plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    # Compute sensitivity for all (file, param) pairs
    for item in prepared_folder_data:
        for param_name in parameter_names:
            result = _compute_sensitivity_for_param(item, param_name, perturbation=perturbation)
            results.append(result)

            csv_rows.append(
                {
                    "filepath": str(result.filepath),
                    "ambient_temperature_K": result.ambient_temperature_K,
                    "parameter_name": result.parameter_name,
                    "time_s_start": float(result.time_s[0]),
                    "time_s_end": float(result.time_s[-1]),
                    "sensitivity_mean_percent": float(np.nanmean(result.sensitivity_percent)),
                    "sensitivity_median_percent": float(np.nanmedian(result.sensitivity_percent)),
                    "sensitivity_max_percent": float(np.nanmax(result.sensitivity_percent)),
                    "sensitivity_magnitude_percent": float(np.nanmean(np.abs(result.sensitivity_percent))),
                }
            )

            if save_plots:
                fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
                ax.semilogx(result.time_s, result.sensitivity_percent, lw=1.8)
                ax.axhline(0.0, color="black", linestyle=":", linewidth=1)
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Relative change of dT/dlog(t) (%)")
                title = (
                    f"SA for {result.filepath.name} | {param_name} | T0={result.ambient_temperature_K:.2f} K"
                )
                ax.set_title(textwrap.fill(title, width=56), fontsize=10, pad=12)
                ax.grid(True, alpha=0.3)
                fig.subplots_adjust(top=0.88)
                out_file = plot_dir / f"SA_{result.filepath.stem}_{param_name.replace(' ', '_')}.png"
                fig.savefig(out_file, dpi=200, bbox_inches="tight")
                plt.close(fig)

    if save_csv:
        csv_path = plot_dir / "sensitivity_summary.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

        logger.info("Saved sensitivity summary CSV: %s", csv_path)

    # Generate summary visualizations
    if save_plots and csv_rows:
        _plot_sensitivity_summary(csv_rows, parameter_names, plot_dir)

    return results


def _plot_sensitivity_summary(csv_rows: list[dict], parameter_names: list[str], plot_dir: Path):
    """Generate summary visualizations of sensitivity analysis results."""

    # Aggregate by parameter: mean absolute sensitivity magnitude
    param_magnitudes = {}
    for row in csv_rows:
        pname = row["parameter_name"]
        magnitude = row["sensitivity_magnitude_percent"]
        if pname not in param_magnitudes:
            param_magnitudes[pname] = []
        param_magnitudes[pname].append(magnitude)

    # Average magnitude per parameter
    param_avg_magnitude = {
        pname: np.mean(mags) for pname, mags in param_magnitudes.items()
    }

    # Sort by magnitude (descending)
    sorted_params = sorted(param_avg_magnitude.items(), key=lambda x: x[1], reverse=True)
    param_names_sorted = [p[0] for p in sorted_params]
    magnitudes_sorted = [p[1] for p in sorted_params]

    # Bar chart: sensitivity magnitude by parameter
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(param_names_sorted)))
    ax.barh(range(len(param_names_sorted)), magnitudes_sorted, color=colors)
    ax.set_yticks(range(len(param_names_sorted)))
    ax.set_yticklabels(param_names_sorted, fontsize=9)
    ax.set_xlabel("Mean Absolute Sensitivity Magnitude (%)", fontsize=10)
    ax.set_title("Sensitivity Analysis: Parameter Ranking", fontsize=11, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    out_file = plot_dir / "SA_Parameter_Ranking.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved parameter ranking chart: %s", out_file)

    # Heatmap: sensitivity magnitude across files and parameters
    unique_files = sorted(set(row["filepath"] for row in csv_rows))
    file_stems = [Path(f).stem for f in unique_files]

    # Build matrix: rows=parameters, cols=files, values=mean sensitivity magnitude
    heatmap_data = np.zeros((len(param_names_sorted), len(unique_files)))
    for i, pname in enumerate(param_names_sorted):
        for j, fpath in enumerate(unique_files):
            vals = [
                row["sensitivity_magnitude_percent"]
                for row in csv_rows
                if row["parameter_name"] == pname and row["filepath"] == fpath
            ]
            heatmap_data[i, j] = np.mean(vals) if vals else 0.0

    fig, ax = plt.subplots(figsize=(max(8, len(unique_files) * 0.6), max(6, len(param_names_sorted) * 0.4)), constrained_layout=True)
    im = ax.imshow(heatmap_data, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(unique_files)))
    ax.set_xticklabels(file_stems, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(param_names_sorted)))
    ax.set_yticklabels(param_names_sorted, fontsize=9)
    ax.set_ylabel("Parameter", fontsize=10)
    ax.set_xlabel("File", fontsize=10)
    ax.set_title("Sensitivity Heatmap: All Parameters × Files", fontsize=11, fontweight="bold")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Mean Sensitivity Magnitude (%)", fontsize=9)

    # Annotate cells with values
    for i in range(len(param_names_sorted)):
        for j in range(len(unique_files)):
            val = heatmap_data[i, j]
            text_color = "white" if val > heatmap_data.max() * 0.6 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=text_color, fontsize=7)

    out_file = plot_dir / "SA_Heatmap_All_Parameters.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved sensitivity heatmap: %s", out_file)
