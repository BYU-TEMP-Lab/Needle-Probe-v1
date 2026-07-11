import numpy as np

from compare_python_matlab import build_thermal_model_inputs


def test_build_thermal_model_inputs_from_matlab_vector():
    par_vec = np.array(
        [
            2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0.5, 0.6, 1.5, 0.03, 273,
            3.3, 10, 0.01, 0.02, 0.03, 0.04, 0.05, 10, 20, 1000, 500, 500000,
            0.2, 0.01, 0,
        ],
        dtype=float,
    )

    probe, sample, crucible, environment = build_thermal_model_inputs(
        par_vec,
        time_array=np.array([0.0, 1.0]),
        sample_diffusivity_mode="from_rho_cp",
        power_calculation_mode="V*I",
    )

    assert probe.r_core == par_vec[18]
    assert probe.k_eff_core == par_vec[0]
    assert sample.refractive_index == par_vec[13]
    assert crucible.r_inner == par_vec[21]
    assert environment.power_avg == par_vec[16] * par_vec[28]
    assert environment.T_amb == par_vec[15]
