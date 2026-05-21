"""Demo of multi-parameter sensitivity analysis summary plots."""
import sys
from pathlib import Path
import csv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import matplotlib.pyplot as plt


def demo_sensitivity_summary_plots():
    """Generate summary plots from sensitivity analysis data."""
    print("Demonstrating multi-parameter sensitivity summary plots...\n")

    # Example data: simulate results from 10 parameters across 1 file at different temps
    parameters = [
        "Sample k",
        "Sample rho",
        "Sample cp",
        "Thermocouple k",
        "Wire k",
        "Sheath k",
        "Insulation k",
        "Crucible k",
        "Convection Coefficient",
        "Radiation View Factor",
    ]

    # Simulate sensitivity magnitudes (Sample k should be highest since we're measuring it)
    param_magnitudes = {
        "Sample k": 85.5,  # HIGH - this is what we're measuring
        "Sample rho": 2.1,
        "Sample cp": 3.4,
        "Thermocouple k": 45.2,  # Medium
        "Wire k": 12.3,
        "Sheath k": 18.7,
        "Insulation k": 5.2,
        "Crucible k": 8.9,
        "Convection Coefficient": 22.4,
        "Radiation View Factor": 1.8,
    }

    # Create output directory
    out_dir = Path(__file__).parent / ".automation" / "sensitivity_summary_demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Bar chart: parameter ranking
    print("✓ Generating parameter ranking chart...")
    sorted_params = sorted(param_magnitudes.items(), key=lambda x: x[1], reverse=True)
    param_names_sorted = [p[0] for p in sorted_params]
    magnitudes_sorted = [p[1] for p in sorted_params]

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(param_names_sorted)))
    
    # Highlight Sample k in bold
    bar_colors = ["darkred" if "Sample k" in name else colors[i] for i, name in enumerate(param_names_sorted)]
    
    bars = ax.barh(range(len(param_names_sorted)), magnitudes_sorted, color=bar_colors)
    ax.set_yticks(range(len(param_names_sorted)))
    ax.set_yticklabels(param_names_sorted, fontsize=10)
    ax.set_xlabel("Mean Absolute Sensitivity Magnitude (%)", fontsize=11, fontweight="bold")
    ax.set_title("Sensitivity Analysis: Parameter Ranking\n(Dark red = Sample k - main measurement target)", 
                 fontsize=12, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, magnitudes_sorted)):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2, f"{val:.1f}%", 
                va="center", fontsize=9)
    
    out_file = out_dir / "SA_Parameter_Ranking.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {out_file}")

    # Save CSV summary
    print("✓ Saving sensitivity summary to CSV...")
    csv_path = out_dir / "sensitivity_ranking.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Rank", "Parameter", "Sensitivity_Magnitude_Percent"])
        writer.writeheader()
        for rank, (param, mag) in enumerate(sorted_params, 1):
            writer.writerow({"Rank": rank, "Parameter": param, "Sensitivity_Magnitude_Percent": f"{mag:.2f}"})
    print(f"  → {csv_path}")

    print("\n📊 Summary:")
    print(f"  Parameters analyzed: {len(parameters)}")
    print(f"  Top 3 most sensitive parameters:")
    for i, (param, mag) in enumerate(sorted_params[:3], 1):
        marker = "🎯 SAMPLE K" if param == "Sample k" else ""
        print(f"    {i}. {param}: {mag:.1f}% {marker}")
    
    print(f"\n✓ Demo complete! Check {out_dir} for plots.")


if __name__ == "__main__":
    demo_sensitivity_summary_plots()
