"""
compare_python_matlab.py
Compares Python thermal_quadrupoles_model with MATLAB quadrupoles_model results
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Add src to path before importing package modules
src_path = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_path))

from salt_probe_util.thermal_quadrupoles_model import (
    TQCrucible,
    TQEnvironment,
    TQProbe,
    TQSample,
    thermal_quadrupoles,
)

def build_thermal_model_inputs(
    par_vector,
    time_array,
    sample_diffusivity_mode="from_rho_cp",
    power_calculation_mode="V*I",
):
    """Build the current TQ dataclass objects from the MATLAB-style parameter vector."""
    values = np.asarray(par_vector, dtype=float).ravel()
    if values.size != 31:
        raise ValueError(f"Expected 31 parameter values, received {values.size}")

    p = values

    if sample_diffusivity_mode == "from_rho_cp":
        alpha_sample = p[7] / (p[25] * p[26])
    elif sample_diffusivity_mode == "from_rhocp":
        alpha_sample = p[7] / p[27]
    else:
        alpha_sample = p[8]

    if power_calculation_mode == "V*I":
        power = p[16] * p[28]
    elif power_calculation_mode == "V^2/R":
        power = p[16] ** 2 / p[17]
    else:
        power = p[29]

    probe = TQProbe(
        L=p[23],
        R_elec=p[17],
        power_decay_rate=p[29],
        r_core=p[18],
        k_eff_core=p[0],
        alpha_eff_core=p[1],
        r_insulation=p[19],
        k_insulation=p[2],
        alpha_insulation=p[3],
        tcr_ins_sh=p[4],
        r_sheath=p[20],
        k_sheath=p[5],
        alpha_sheath=p[6],
        emissivity_sheath=p[11],
    )

    sample = TQSample(
        k=p[7],
        alpha=alpha_sample,
        rho=p[25],
        cp=p[26],
        rhocp=p[27],
        refractive_index=p[13],
        scattering_coeff=p[14],
    )

    crucible = TQCrucible(
        r_inner=p[21],
        r_outer=p[22],
        k=p[9],
        alpha=p[10],
        emissivity=p[12],
    )

    environment = TQEnvironment(
        T_amb=p[15],
        h_conv=p[24],
        power=power,
        time_array=np.asarray(time_array, dtype=float).ravel(),
    )

    return probe, sample, crucible, environment


def load_matlab_results(matlab_file=None):
    """Load MATLAB results from a .mat file."""
    if matlab_file is None:
        matlab_file = Path(__file__).resolve().parent / "MATLAB_ONLY" / "matlab_results.mat"
    else:
        matlab_file = Path(matlab_file)

    try:
        from scipy.io import loadmat

        mat_data = loadmat(matlab_file)
        return {
            "t_test": mat_data["t_test"].flatten(),
            "result_matlab": mat_data["result_matlab"].flatten(),
            "par_vec_test": mat_data["par_vec_test"].flatten(),
        }
    except Exception as exc:
        print(f"Could not load MATLAB results: {exc}")
        return None


def plot_comparison(time_array, result_python, result_matlab, output_dir=None):
    """Plot Python and MATLAB outputs along with their absolute difference."""
    time_array = np.asarray(time_array, dtype=float).ravel()
    result_python = np.asarray(result_python, dtype=float).ravel()
    result_matlab = np.asarray(result_matlab, dtype=float).ravel()

    if time_array.size != result_python.size or time_array.size != result_matlab.size:
        min_len = min(time_array.size, result_python.size, result_matlab.size)
        time_array = time_array[:min_len]
        result_python = result_python[:min_len]
        result_matlab = result_matlab[:min_len]

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / "comparison_results.png"
    fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True, constrained_layout=True)

    axes[0].plot(time_array, result_python, label="Python", linewidth=1.5)
    axes[0].plot(time_array, result_matlab, label="MATLAB", linewidth=1.2, linestyle="--")
    axes[0].set_ylabel("Temperature")
    axes[0].set_title("Python vs MATLAB thermal model comparison")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    abs_diff = np.abs(result_python - result_matlab)
    axes[1].plot(time_array, abs_diff, color="C3", linewidth=1.5)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Absolute difference")
    axes[1].set_yscale("log")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Needle Probe Thermal Model Comparison")
    # fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return out_path


def main():
    print("=" * 60)
    print("COMPARING PYTHON vs MATLAB IMPLEMENTATIONS")
    print("=" * 60)

    # Define a more physically plausible parameter vector for the comparison test.
    par_vec_test = np.array([
        15.0, 1.0e-5, 0.18, 7.5e-7, 1.0e-4, 20.0, 4.5e-6, 2.0, 1.7e-6,
        15.0, 6.0e-6, 0.80, 0.80, 1.45, 0.03, 298.15, 3.3, 10.0, 5.0e-4,
        7.0e-4, 1.0e-3, 1.2e-3, 1.5e-3, 1.0e-2, 20.0, 1200.0, 1000.0,
        1.2e6, 0.20, 0.01, 0.0,
    ])

    t_test = np.linspace(0.01, 10, 100)
    sample_diffusivity_mode_test = "from_rho_cp"
    iv_flag_test = 1

    print(f"\nTest Parameters:")
    print(f"  Parameters: {len(par_vec_test)} elements")
    print(f"  Time points: {len(t_test)} (from {t_test[0]:.4f} to {t_test[-1]:.2f} seconds)")
    print(f"  sample_diffusivity_mode: {sample_diffusivity_mode_test}")
    print(f"  iv_flag: {iv_flag_test}")

    print("\nRunning Python implementation...")
    try:
        probe, sample, crucible, environment = build_thermal_model_inputs(
            par_vec_test,
            time_array=t_test,
            sample_diffusivity_mode=sample_diffusivity_mode_test,
            power_calculation_mode="V*I",
        )
        result_python = thermal_quadrupoles(probe, sample, crucible, environment)
        print("Python completed successfully")
        print(f"  Result shape: {result_python.shape}")
        print(f"  Min: {np.min(result_python):.6e}, Max: {np.max(result_python):.6e}")
    except Exception as exc:
        print(f"Python failed: {exc}")
        result_python = None
        return
    
    print("\nLoading MATLAB results...")
    matlab_data = load_matlab_results()
    
    if matlab_data is None:
        print("MATLAB results not available. Run test_quadrupoles_model.m in MATLAB first.")
        return
    
    result_matlab = matlab_data['result_matlab']
    t_matlab = matlab_data['t_test'].flatten()

    print("MATLAB results loaded")
    print(f"  Result shape: {result_matlab.shape}")
    print(f"  Min: {np.min(result_matlab):.6e}, Max: {np.max(result_matlab):.6e}")
    
    if len(result_python) != len(result_matlab):
        min_len = min(len(result_python), len(result_matlab))
        result_python = result_python[:min_len]
        result_matlab = result_matlab[:min_len]
    
    # Calculate differences
    abs_diff = np.abs(result_python - result_matlab)
    rel_diff = np.abs((result_python - result_matlab) / (np.abs(result_matlab) + 1e-10))

    print("\nAbsolute Difference:")
    print(f"  Mean: {np.mean(abs_diff):.6e}")
    print(f"  Median: {np.median(abs_diff):.6e}")
    print(f"  Max: {np.max(abs_diff):.6e}")
    print(f"  Std Dev: {np.std(abs_diff):.6e}")

    print("\nRelative Difference (%):")
    print(f"  Mean: {np.mean(rel_diff) * 100:.6e}%")
    print(f"  Median: {np.median(rel_diff) * 100:.6e}%")
    print(f"  Max: {np.max(rel_diff) * 100:.6e}%")

    plot_path = plot_comparison(
        t_matlab if len(t_matlab) == len(result_matlab) else t_test,
        result_python,
        result_matlab,
        output_dir=Path(__file__).resolve().parent / "output",
    )
    print(f"\nSaved comparison plot to {plot_path}")

if __name__ == "__main__":
    main()
