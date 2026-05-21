from dataclasses import dataclass

import numpy as np
from scipy.constants import Stefan_Boltzmann as STEFAN_BOLTZMANN_CONSTANT  # W m^-2 K^-4
from scipy.special import iv as besseli, kv as besselk


def _scalar_value(value, default=None):
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get("initial_value", default)
    return value


def _material_alpha(k_val, rho_val, cp_val):
    return k_val / (rho_val * cp_val)


def _resolve_parameter_vector_from_mapping(params):
    """Build the 31-element thermal-quadrupole vector from the resolved parameter mapping."""
    probe = params.get("_probe_obj") or params.get("probe")
    crucible = params.get("_crucible_obj") or params.get("crucible")
    sample = params.get("_sample_obj") or params.get("sample")

    if probe is None or crucible is None or sample is None:
        raise ValueError("Expected resolved mapping with probe, crucible, and sample objects.")

    probe_geom = getattr(probe, "geometry", {})
    sheath = getattr(probe, "sheath_props", None)
    insulation = getattr(probe, "insulation_props", None)
    wire = getattr(probe, "heating_wire_props", None)
    tc = getattr(probe, "TC_props", None)

    if any(x is None for x in (sheath, insulation, wire, tc)):
        raise ValueError("Probe object is missing thermal property groups.")

    # Helper for dict-like material property values
    def g(obj, key):
        return _scalar_value(getattr(obj, key, None))

    # Material temperatures are already resolved, so use initial_value fields
    wire_k = g(wire, "k")
    wire_rho = g(wire, "rho")
    wire_cp = g(wire, "cp")
    ins_k = g(insulation, "k")
    ins_rho = g(insulation, "rho")
    ins_cp = g(insulation, "cp")
    sheath_k = g(sheath, "k")
    sheath_rho = g(sheath, "rho")
    sheath_cp = g(sheath, "cp")
    sample_k = g(sample, "k")
    sample_rho = g(sample, "rho")
    sample_cp = g(sample, "cp")
    crucible_k = g(crucible.material, "k")
    crucible_rho = g(crucible.material, "rho")
    crucible_cp = g(crucible.material, "cp")

    # Geometry and scalar inputs
    r_tc = _scalar_value(probe_geom.get("r_tc"))
    r_wires = _scalar_value(probe_geom.get("r_wires"))
    r_Al = _scalar_value(probe_geom.get("r_Al"))
    r_Ni = _scalar_value(probe_geom.get("r_Ni"))
    r_wir_i = _scalar_value(probe_geom.get("r_wir_i"))
    r_wir_o = _scalar_value(probe_geom.get("r_wir_o"))
    r_wir_mid = _scalar_value(probe_geom.get("r_wir_mid"))
    TC_loc = _scalar_value(probe_geom.get("TC_loc"))
    HW_curve = _scalar_value(probe_geom.get("HW_curve"))
    HW_Ni = _scalar_value(probe_geom.get("HW_Ni", probe_geom.get("HW_sheath")))
    Ni_curve = _scalar_value(probe_geom.get("Ni_curve"))
    samp_probe = _scalar_value(probe_geom.get("samp_probe", probe_geom.get("h_point")))
    h_max = _scalar_value(probe_geom.get("h_max"))
    L = _scalar_value(probe_geom.get("L"))

    T_amb = _scalar_value(params.get("Ambient Temperature"))
    avgQ = _scalar_value(params.get("Power"))
    tcr = _scalar_value(params.get("Thermal Contact Resistance Sheath-Insulation"))
    scatter = _scalar_value(params.get("??? Scatter"), 0.0)
    decay_rate = _scalar_value(params.get("??? Flux Decay"), 0.0)
    decay_point = _scalar_value(params.get("??? Decay Point"), 0.0)
    h_convec = _scalar_value(params.get("Convection Coefficient"), 0.0)

    sheath_emissivity = _scalar_value(sheath.emissivity, 0.5)
    sample_emissivity = _scalar_value(sample.emissivity, 0.5)

    # Keep the model source term in direct-current form by setting I=1 and V=power.
    # The model uses V * I internally.
    V = avgQ
    I_val = 1.0

    return np.array(
        [
            wire_k,
            _material_alpha(wire_k, wire_rho, wire_cp),
            ins_k,
            _material_alpha(ins_k, ins_rho, ins_cp),
            tcr,
            sheath_k,
            _material_alpha(sheath_k, sheath_rho, sheath_cp),
            sample_k,
            _material_alpha(sample_k, sample_rho, sample_cp),
            crucible_k,
            _material_alpha(crucible_k, crucible_rho, crucible_cp),
            sheath_emissivity,
            sample_emissivity,
            1.0,
            scatter,
            T_amb,
            V,
            1.0,
            r_wires,
            r_Al,
            r_Ni,
            _scalar_value(crucible.inner_radius),
            _scalar_value(crucible.outer_radius),
            L,
            h_convec,
            sample_rho,
            sample_cp,
            sample_rho * sample_cp,
            I_val,
            decay_rate,
            decay_point,
        ],
        dtype=float,
    )


@dataclass(frozen=True)
class ThermalQuadrupoleParameters:
    k_eff_wire: float
    alpha_eff_wire: float
    k_insulation: float
    alpha_insulation: float
    thermal_contact_resistance_insulation_sheath: float
    k_sheath: float
    alpha_sheath: float
    ksample: float
    alphasample_input: float
    kcrucible: float
    alphacrucible: float
    emissivity1: float
    emissivity2: float
    index: float
    scatter: float
    T0: float
    V: float
    resistance: float
    rwires: float
    rsheath_inner: float
    rsheath: float
    rsample: float
    rcrucible: float
    L: float
    h_convec: float
    rhosample: float
    cpsample: float
    rhocp: float
    I_val: float
    source_decay_rate: float
    legacy_decay_point: float


def _coerce_parameters(par_vector) -> ThermalQuadrupoleParameters:
    if isinstance(par_vector, dict):
        par_vector = _resolve_parameter_vector_from_mapping(par_vector)
    values = np.asarray(par_vector, dtype=float).ravel()
    if values.size == 30:
        values = np.concatenate([values, [0.0]])
    if values.size != 31:
        raise ValueError(f"Expected 31 parameters, got {values.size}.")
    return ThermalQuadrupoleParameters(*values)


def needle_probe_model(t, par_vector, sample_diffusivity_mode="from_rho_cp", *, heat_source_mode="direct_current"):
    """
    Solve for temperature vs time for the needle-probe quadrupole model.

    Parameters
    ----------
    t : array-like
        Time vector in seconds. A leading zero is allowed and will be preserved
        in the returned delta-T series.
    par_vector : array-like
        31-element parameter vector used by the MATLAB model.
    sample_diffusivity_mode : str
        Selects which sample diffusivity definition to use.
        Supported values: "from_rho_cp", "from_rhocp", "from_alpha".
    heat_source_mode : str, keyword-only
        "direct_current" uses V * I for the heat source.
        "legacy_resistance" uses V^2 / R for the older resistance-based path.
    """
    time = np.asarray(t, dtype=float).ravel()
    parameters = _coerce_parameters(par_vector)

    if time.size == 0:
        return np.array([], dtype=float)

    if np.any(time < 0):
        raise ValueError("Time values must be non-negative.")

    has_leading_zero = np.isclose(time[0], 0.0)
    evaluation_time = time[1:] if has_leading_zero else time

    if evaluation_time.size == 0:
        return np.array([0.0], dtype=float)

    if np.any(evaluation_time <= 0):
        raise ValueError("All time values after any leading zero must be strictly positive.")

    response = invlap(
        lambda s: _laplace_response(s, parameters, sample_diffusivity_mode, heat_source_mode),
        evaluation_time,
    )

    if has_leading_zero:
        response = np.concatenate(([0.0], response))

    return response


def _sample_diffusivity(parameters: ThermalQuadrupoleParameters, sample_diffusivity_mode: str) -> float:
    if sample_diffusivity_mode == "from_rho_cp":
        return parameters.ksample / (parameters.rhosample * parameters.cpsample)
    if sample_diffusivity_mode == "from_rhocp":
        return parameters.ksample / parameters.rhocp
    if sample_diffusivity_mode == "from_alpha":
        return parameters.alphasample_input
    raise ValueError(
        "sample_diffusivity_mode must be 'from_rho_cp', 'from_rhocp', or 'from_alpha'."
    )


def _heat_source_power(parameters: ThermalQuadrupoleParameters, heat_source_mode: str) -> float:
    if heat_source_mode == "direct_current":
        return parameters.V * parameters.I_val
    if heat_source_mode == "legacy_resistance":
        return parameters.V**2 / parameters.resistance
    raise ValueError(
        "heat_source_mode must be 'direct_current' or 'legacy_resistance'."
    )


def _cylindrical_layer(s, r_in, r_out, k_val, alpha_val, length):
    qi = r_in * np.sqrt(s / alpha_val)
    qo = r_out * np.sqrt(s / alpha_val)

    i0i, i0o = besseli(0, qi), besseli(0, qo)
    i1i, i1o = besseli(1, qi), besseli(1, qo)
    k0i, k0o = besselk(0, qi), besselk(0, qo)
    k1i, k1o = besselk(1, qi), besselk(1, qo)

    a = qi * (i0i * k1o + i1o * k0i)
    b = (1 / (2 * np.pi * k_val * length)) * (i0o * k0i - i0i * k0o)
    c = 2 * np.pi * k_val * length * qi * qo * (i1o * k1i - i1i * k1o)
    d = qi * (i0o * k1i + i1i * k0o)

    return np.array([[a, b], [c, d]], dtype=complex)


def _radiative_transform(m_cyl, r_dim):
    ac, bc, cc, dc = m_cyl[0, 0], m_cyl[0, 1], m_cyl[1, 0], m_cyl[1, 1]
    denom = bc + r_dim
    return np.array(
        [
            [(bc + r_dim * ac) / denom, (bc * r_dim) / denom],
            [(ac + dc + r_dim * cc - 2) / denom, (bc + r_dim * dc) / denom],
        ],
        dtype=complex,
    )


def _laplace_response(s, parameters, sample_diffusivity_mode, heat_source_mode):
    alpha_sample = _sample_diffusivity(parameters, sample_diffusivity_mode)
    q0_initial = _heat_source_power(parameters, heat_source_mode)

    area_sheath = 2 * np.pi * parameters.rsheath * parameters.L
    radiation_resistance = (
        (1 / parameters.emissivity1)
        + ((1 / parameters.emissivity2) - 1) * (parameters.rsheath / parameters.rsample)
        + parameters.scatter * (parameters.rsample - parameters.rsheath) * (parameters.rsheath / parameters.rsample)
    ) / (4 * (parameters.index**2) * STEFAN_BOLTZMANN_CONSTANT * (parameters.T0**3) * area_sheath)

    q1 = parameters.rwires * np.sqrt(s / parameters.alpha_eff_wire)
    c1 = (
        (parameters.k_eff_wire / parameters.alpha_eff_wire)
        * np.pi
        * parameters.L
        * (parameters.rwires**2)
        * s
    )
    b1 = (
        (1 / (2 * np.pi * parameters.k_eff_wire * parameters.L))
        * (besseli(0, q1) / (q1 * besseli(1, q1)))
        - (1 / c1)
    )
    d1 = (q1 / 2) * (besseli(0, q1) / besseli(1, q1))

    ones_s = np.ones_like(s)
    zeros_s = np.zeros_like(s)
    m1 = np.array([[ones_s, b1], [c1, d1]], dtype=complex)

    m2 = _cylindrical_layer(
        s,
        parameters.rwires,
        parameters.rsheath_inner,
        parameters.k_insulation,
        parameters.alpha_insulation,
        parameters.L,
    )
    m_tcr = np.array(
        [[ones_s, parameters.thermal_contact_resistance_insulation_sheath * ones_s], [zeros_s, ones_s]],
        dtype=complex,
    )
    m3 = _cylindrical_layer(
        s,
        parameters.rsheath_inner,
        parameters.rsheath,
        parameters.k_sheath,
        parameters.alpha_sheath,
        parameters.L,
    )

    m4_pure = _cylindrical_layer(
        s,
        parameters.rsheath,
        parameters.rsample,
        parameters.ksample,
        alpha_sample,
        parameters.L,
    )
    m4 = _radiative_transform(m4_pure, radiation_resistance)

    m5 = _cylindrical_layer(
        s,
        parameters.rsample,
        parameters.rcrucible,
        parameters.kcrucible,
        parameters.alphacrucible,
        parameters.L,
    )

    c_conv = parameters.h_convec * (2 * np.pi * parameters.rcrucible * parameters.L)
    mconv = np.array([[ones_s, zeros_s], [c_conv * ones_s, ones_s]], dtype=complex)

    system_matrix = m1
    for layer in (m2, m_tcr, m3, m4, m5, mconv):
        system_matrix = np.einsum("ij...,jk...->ik...", system_matrix, layer)

    return (q0_initial / (s + parameters.source_decay_rate)) * (system_matrix[0, 0] / system_matrix[1, 0])


def invlap(F_func, t_vec, alpha=0, tol=1e-9):
    """
    Numerical inversion of a Laplace transform using the de Hoog algorithm.

    Parameters
    ----------
    F_func : callable
        Function that accepts the Laplace parameter s.
    t_vec : array-like
        Strictly positive time vector.
    alpha : float, default 0
        Largest pole of F.
    tol : float, default 1e-9
        Numerical tolerance.
    """
    all_t = np.asarray(t_vec, dtype=float).ravel()
    if all_t.size == 0:
        return np.array([], dtype=float)
    if np.any(all_t <= 0):
        raise ValueError("invlap requires strictly positive times.")

    log_all_t = np.log10(all_t)
    i_min = int(np.floor(np.min(log_all_t)))
    i_max = int(np.ceil(np.max(log_all_t)))

    final_f = []

    for i_log in range(i_min, i_max + 1):
        mask = (log_all_t >= i_log) & (log_all_t < (i_log + 1))
        t_piece = all_t[mask]

        if len(t_piece) == 0:
            continue

        T = np.max(t_piece) * 2
        gamma = alpha - np.log(tol) / (2 * T)
        M = 20
        run = np.arange(2 * M + 1)

        s = gamma + 1j * np.pi * run / T

        a = F_func(s)
        a[0] = a[0] / 2.0

        e = np.zeros((2 * M + 1, M + 1), dtype=complex)
        q = np.zeros((2 * M, M + 1), dtype=complex)

        q[:, 1] = a[1:2 * M + 1] / a[0:2 * M]

        for r in range(1, M + 1):
            limit_r = 2 * (M - r)
            e[0 : limit_r + 1, r] = (
                q[1 : limit_r + 2, r]
                - q[0 : limit_r + 1, r]
                + e[1 : limit_r + 2, r - 1]
            )
            if r < M:
                rq = r + 1
                limit_rq = 2 * (M - rq)
                q[0 : limit_rq + 2, rq] = (
                    q[1 : limit_rq + 3, rq - 1]
                    * e[1 : limit_rq + 3, rq - 1]
                    / e[0 : limit_rq + 2, rq - 1]
                )

        d = np.zeros(2 * M + 1, dtype=complex)
        d[0] = a[0]
        d[1:2 * M:2] = -q[0, 1 : M + 1]
        d[2:2 * M + 1:2] = -e[0, 1 : M + 1]

        nt = len(t_piece)
        a_vec = np.zeros((2 * M + 2, nt), dtype=complex)
        b_vec = np.zeros((2 * M + 2, nt), dtype=complex)

        a_vec[1, :] = d[0]
        b_vec[0:2, :] = 1.0
        z = np.exp(1j * np.pi * t_piece / T)

        for n in range(2, 2 * M + 2):
            a_vec[n, :] = a_vec[n - 1, :] + d[n - 1] * z * a_vec[n - 2, :]
            b_vec[n, :] = b_vec[n - 1, :] + d[n - 1] * z * b_vec[n - 2, :]

        h2M = 0.5 * (1.0 + (d[2 * M - 1] - d[2 * M]) * z)
        r2Mz = -h2M * (1.0 - np.sqrt(1.0 + d[2 * M] * z / (h2M**2)))

        a_final = a_vec[2 * M, :] + r2Mz * a_vec[2 * M - 1, :]
        b_final = b_vec[2 * M, :] + r2Mz * b_vec[2 * M - 1, :]

        f_piece = (1.0 / T) * np.exp(gamma * t_piece) * np.real(a_final / b_final)
        final_f.extend(f_piece.tolist())

    return np.array(final_f)


def run(par_vector, filepath, sample_diffusivity_mode="from_rho_cp", heat_source_mode="direct_current"):
    """
    Adapter used by the simulation dispatch layer.

    Parameters
    ----------
    par_vector : array-like
        Thermal model parameter vector.
    filepath : Path-like
        Experimental data file that provides the time vector.
    sample_diffusivity_mode : str, default "from_rho_cp"
        Sample diffusivity selection.
    heat_source_mode : str, default "direct_current"
        Explicit heating mode for the source term.
    """
    from pathlib import Path

    import pandas as pd

    file_path = Path(filepath)
    data = pd.read_csv(file_path, sep="\t", header=None)
    time = np.asarray(data.iloc[:, 0], dtype=float)
    if time.size == 0:
        return np.empty((0, 2), dtype=float)

    temperatures = needle_probe_model(
        time,
        par_vector,
        sample_diffusivity_mode,
        heat_source_mode=heat_source_mode,
    )

    return np.column_stack((time[: temperatures.size], temperatures))


if __name__ == "__main__":
    par_vec_test = np.array(
        [
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            0.5,
            0.6,
            1.5,
            0.03,
            273,
            3.3,
            10,
            0.01,
            0.02,
            0.03,
            0.04,
            0.05,
            10,
            20,
            1000,
            500,
            500000,
            0.2,
            0.01,
            0,
        ]
    )
    t_test = np.linspace(0.0, 10, 100)
    result = needle_probe_model(
        t_test,
        par_vec_test,
        sample_diffusivity_mode="from_rho_cp",
        heat_source_mode="direct_current",
    )
    print(result)