"""
compare_python_matlab.py
Compares Python thermal_quadrupoles_model with MATLAB quadrupoles_model results
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from salt_probe_util.thermal_quadrupoles_model import needle_probe_model

def load_matlab_results(matlab_file='MATLAB_ONLY/matlab_results.mat'):
    """Load MATLAB results from .mat file"""
    try:
        from scipy.io import loadmat
        mat_data = loadmat(matlab_file)
        return {
            't_test': mat_data['t_test'].flatten(),
            'result_matlab': mat_data['result_matlab'].flatten(),
            'par_vec_test': mat_data['par_vec_test'].flatten()
        }
    except Exception as e:
        print(f"Could not load MATLAB results: {e}")
        return None

def main():
    print("=" * 60)
    print("COMPARING PYTHON vs MATLAB IMPLEMENTATIONS")
    print("=" * 60)
    
    # Define test parameters (same as both Python and MATLAB tests)
    par_vec_test = np.array([ 
        2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0.5, 0.6, 1.5, 0.03, 273, 
        3.3, 10, 0.01, 0.02, 0.03, 0.04, 0.05, 10, 20, 1000, 500, 500000, 0.2, 0.01, 0
    ])
    
    t_test = np.linspace(0.01, 10, 100)
    sample_diffusivity_mode_test = "from_rho_cp"
    iv_flag_test = 1
    
    print(f"\nTest Parameters:")
    print(f"  Parameters: {len(par_vec_test)} elements")
    print(f"  Time points: {len(t_test)} (from {t_test[0]:.4f} to {t_test[-1]:.2f} seconds)")
    print(f"  sample_diffusivity_mode: {sample_diffusivity_mode_test}")
    print(f"  iv_flag: {iv_flag_test}")
    
    # Run Python implementation
    print(f"\nRunning Python implementation...")
    try:
        result_python = needle_probe_model(
            t_test,
            par_vec_test,
            sample_diffusivity_mode_test,
            heat_source_mode="direct_current",
        )
        print(f"✓ Python completed successfully")
        print(f"  Result shape: {result_python.shape}")
        print(f"  Min: {np.min(result_python):.6e}, Max: {np.max(result_python):.6e}")
    except Exception as e:
        print(f"✗ Python failed: {e}")
        result_python = None
        return
    
    # Try to load MATLAB results
    print(f"\nLoading MATLAB results...")
    matlab_data = load_matlab_results()
    
    if matlab_data is None:
        print("⚠ MATLAB results not available. Run test_quadrupoles_model.m in MATLAB first.")
        print("\nPython Results (first 10 points):")
        print("Time(s)\t\tTemp(K)")
        for i in range(min(10, len(t_test))):
            print(f"{t_test[i]:.6f}\t{result_python[i]:.6e}")
        return
    
    result_matlab = matlab_data['result_matlab']
    t_matlab = matlab_data['t_test'].flatten()
    
    print(f"✓ MATLAB results loaded")
    print(f"  Result shape: {result_matlab.shape}")
    print(f"  Min: {np.min(result_matlab):.6e}, Max: {np.max(result_matlab):.6e}")
    
    # Compare results
    print(f"\n" + "=" * 60)
    print("COMPARISON ANALYSIS")
    print("=" * 60)
    
    if len(result_python) != len(result_matlab):
        print(f"⚠ WARNING: Different lengths! Python: {len(result_python)}, MATLAB: {len(result_matlab)}")
        min_len = min(len(result_python), len(result_matlab))
        result_python = result_python[:min_len]
        result_matlab = result_matlab[:min_len]
    
    # Calculate differences
    abs_diff = np.abs(result_python - result_matlab)
    rel_diff = np.abs((result_python - result_matlab) / (np.abs(result_matlab) + 1e-10))
    
    print(f"\nAbsolute Difference:")
    print(f"  Mean: {np.mean(abs_diff):.6e}")
    print(f"  Median: {np.median(abs_diff):.6e}")
    print(f"  Max: {np.max(abs_diff):.6e}")
    print(f"  Std Dev: {np.std(abs_diff):.6e}")
    
    print(f"\nRelative Difference (%):")
    print(f"  Mean: {np.mean(rel_diff)*100:.6e}%")
    print(f"  Median: {np.median(rel_diff)*100:.6e}%")
    print(f"  Max: {np.max(rel_diff)*100:.6e}%")
    
    # Detailed comparison at selected points
    print(f"\n" + "=" * 80)
    print(f"{'Time(s)':>12} | {'Python(K)':>20} | {'MATLAB(K)':>20} | {'Abs Diff':>15} | {'Rel Diff(%)':>12}")
    print("=" * 80)
    
    indices = [0, len(t_test)//4, len(t_test)//2, 3*len(t_test)//4, -1]
    for idx in indices:
        if idx < 0:
            idx = len(t_test) + idx
        if idx < len(t_test):
            py_val = result_python[idx]
            ml_val = result_matlab[idx]
            abs_d = abs_diff[idx]
            rel_d = rel_diff[idx] * 100
            print(f"{t_test[idx]:>12.6f} | {py_val:>20.6e} | {ml_val:>20.6e} | {abs_d:>15.6e} | {rel_d:>12.6e}")
    
    # Overall assessment
    print(f"\n" + "=" * 60)
    max_rel_diff_pct = np.max(rel_diff) * 100
    if max_rel_diff_pct < 0.01:
        status = "✓ EXCELLENT - Implementations match perfectly"
    elif max_rel_diff_pct < 0.1:
        status = "✓ GOOD - Implementations match very closely"
    elif max_rel_diff_pct < 1.0:
        status = "⚠ ACCEPTABLE - Small differences detected"
    else:
        status = "✗ SIGNIFICANT - Implementations differ substantially"
    
    print(status)
    print("=" * 60)

    plt.figure(figsize=(10, 8))

    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(t_test, result_python, label="Python", linewidth=2)
    ax1.plot(t_matlab, result_matlab, label="MATLAB", linestyle="--", linewidth=2)
    ax1.set_ylabel("Temperature (K)")
    ax1.set_title("Python vs MATLAB Needle Probe Model")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.plot(t_test, result_python - result_matlab, color="tab:red", linewidth=1.5)
    ax2.axhline(0.0, color="black", linestyle=":", linewidth=1)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Python - MATLAB")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
