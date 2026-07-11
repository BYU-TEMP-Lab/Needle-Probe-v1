from pathlib import Path

import numpy as np

import compare_python_matlab as cmp


def test_plot_comparison_creates_difference_plot(tmp_path):
    time = np.array([0.1, 0.2, 0.3])
    python = np.array([1.0, 1.5, 2.0])
    matlab = np.array([1.0, 1.4, 2.1])

    out_path = cmp.plot_comparison(time, python, matlab, output_dir=tmp_path)

    assert out_path.exists()
    assert out_path.name.startswith("comparison_")
