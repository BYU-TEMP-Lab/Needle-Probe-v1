import logging
from dataclasses import dataclass

import numpy as np
from scipy.constants import Stefan_Boltzmann as STEFAN_BOLTZMANN_CONSTANT  # W m^-2 K^-4
from scipy.special import iv as besseli, kv as besselk

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class TQProbe:
    # SI units
    # length of the probe sensing region
    L: float 

    # electrical properties
    R_elec: float # electrical resistance of the heating wire circuit
    power_decay_rate: float # decay rate of the heat source (1/s). Typically 0.

    # core (lumped properties of all material wthin outer radius of wires)
    r_core: float 
    k_eff_core: float
    alpha_eff_core: float

    # insulation (between outer radius of wires and inner radius of sheath)
    r_insulation: float
    k_insulation: float
    alpha_insulation: float

    # thermal contact resistance between insulation and sheath
    tcr_ins_sh: float 

    # sheath
    r_sheath: float
    k_sheath: float
    alpha_sheath: float
    emissivity_sheath: float

@dataclass(frozen=True)
class TQSample:
    k: float
    alpha: float
    rho: float
    cp: float
    rhocp: float
    refractive_index: float
    scattering_coeff: float

@dataclass(frozen=True)
class TQCrucible:
    r_inner: float
    r_outer: float
    k: float
    alpha: float
    emissivity: float

@dataclass(frozen=True)
class TQEnvironment:
    T_amb: float
    h_conv: float
    power: float
    time_array: np.ndarray

def _cylindrical_layer(s, r_in, r_out, k_val, alpha_val, length):
    qi = r_in * np.sqrt(s / alpha_val) # dimensionless inner thermal radius
    qo = r_out * np.sqrt(s / alpha_val) # dimensionless outer thermal radius

    # bessel function solutions
    ## 0th order corresponds to temp, and 1st order to space
    i0i, i0o = besseli(0, qi), besseli(0, qo)
    i1i, i1o = besseli(1, qi), besseli(1, qo)
    k0i, k0o = besselk(0, qi), besselk(0, qo)
    k1i, k1o = besselk(1, qi), besselk(1, qo)

    a = qi * (i0i * k1o + i1o * k0i) # geometric transmission coefficient
    b = (1 / (2 * np.pi * k_val * length)) * (i0o * k0i - i0i * k0o) # thermal impedance of the cylindrical layer
    c = 2 * np.pi * k_val * length * qi * qo * (i1o * k1i - i1i * k1o) # thermal capacitance
    d = qi * (i0o * k1i + i1i * k0o) # heat flux damping coefficient

    return np.array([[a, b], [c, d]], dtype=complex)

def _radiative_transform(m_cyl, R_rad):
    ac, bc, cc, dc = m_cyl[0, 0], m_cyl[0, 1], m_cyl[1, 0], m_cyl[1, 1] # unpack conductive cylindrical layer matrix
    denom = bc + R_rad # conductive and radiative resistances add in parallel
    return np.array(
        [
            [(bc + R_rad * ac) / denom, (bc * R_rad) / denom],
            [(ac + dc + R_rad * cc - 2) / denom, (bc + R_rad * dc) / denom],
        ],
        dtype=complex,
    )

def _laplace_response(s, probe: TQProbe, sample: TQSample, crucible: TQCrucible, environment: TQEnvironment):
    alpha_sample = sample.alpha
    q0_initial = environment.power

    # effective wire region
    q1 = probe.r_core * np.sqrt(s / probe.alpha_eff_core) # thermal wave number for the effective wire region
    c1 = (
        (probe.k_eff_core / probe.alpha_eff_core)
        * np.pi
        * probe.L
        * (probe.r_core**2)
        * s
    ) # thermal capacitance of the effective wire region
    b1 = (
        (1 / (2 * np.pi * probe.k_eff_core * probe.L))
        * (besseli(0, q1) / (q1 * besseli(1, q1)))
        - (1 / c1)
    ) # thermal impedance of the effective wire region
    d1 = (q1 / 2) * (besseli(0, q1) / besseli(1, q1)) # geometric transmission coefficient of effective wire region

    ones_s = np.ones_like(s)
    zeros_s = np.zeros_like(s)
    m1 = np.array([[ones_s, b1], [c1, d1]], dtype=complex)

    # insulation layer
    m2 = _cylindrical_layer(
        s,
        probe.r_core,
        probe.r_insulation,
        probe.k_insulation,
        probe.alpha_insulation,
        probe.L,
    )

    # thermal contact resistance between insulation and sheath
    m_tcr = np.array(
        [[ones_s, probe.tcr_ins_sh * ones_s], [zeros_s, ones_s]],
        dtype=complex,
    )

    # sheath layer
    m3 = _cylindrical_layer(
        s,
        probe.r_insulation,
        probe.r_sheath,
        probe.k_sheath,
        probe.alpha_sheath,
        probe.L,
    )

    # sample layer
    m4_pure = _cylindrical_layer(
        s,
        probe.r_sheath,
        crucible.r_inner,
        sample.k,
        sample.alpha,
        probe.L,
    )
    area_sheath = 2 * np.pi * probe.r_sheath * probe.L
    radiation_resistance = (
        (1 / probe.emissivity_sheath)
        + ((1 / crucible.emissivity) - 1) * (probe.r_sheath / crucible.r_inner)
        + sample.scattering_coeff * (crucible.r_inner - probe.r_sheath) * (probe.r_sheath / crucible.r_inner)
    ) / (4 * (sample.refractive_index**2) * STEFAN_BOLTZMANN_CONSTANT * (environment.T_amb**3) * area_sheath) # linearization of radiative heat transfer around T0
    m4 = _radiative_transform(m4_pure, radiation_resistance) # modify to include radiative heat transfer

    # crucible layer
    m5 = _cylindrical_layer(
        s,
        crucible.r_inner,
        crucible.r_outer,
        crucible.k,
        crucible.alpha,
        probe.L,
    )

    # external (convective) layer (NEGLECTS RADIATIVE HEAT TRANSFER TO AMBIENT)
    c_conv = environment.h_conv * (2 * np.pi * crucible.r_outer * probe.L)
    mconv = np.array([[ones_s, zeros_s], [c_conv * ones_s, ones_s]], dtype=complex)

    # combine all layers into a single system matrix
    system_matrix = m1
    for layer in (m2, m_tcr, m3, m4, m5, mconv):
        system_matrix = np.einsum("ij...,jk...->ik...", system_matrix, layer)

    # return the Laplace-domain temperature response at the thermocouple (T_tc(s) = q0(s) * (A/C))
    return (q0_initial / (s + probe.power_decay_rate)) * (system_matrix[0, 0] / system_matrix[1, 0])

def _de_Hoog_invlap(F_func, t_vec, alpha=0, tol=1e-9):
    """Numerical inversion of a Laplace transform using the de Hoog algorithm.

    Parameters
    ----------
    F_func : callable
        Function that accepts a complex vector/array of Laplace parameters 's'.
    t_vec : array-like
        Strictly positive time vector at which to evaluate the inversion.
    alpha : float, default 0
        The largest pole (singularity) of F(s). Dictates convergence bounds. Typically 0. 
    tol : float, default 1e-9
        Numerical tolerance required for the Fourier series convergence.
    """

    # Force the time input into a 1D flat NumPy array of floats
    all_t = np.asarray(t_vec, dtype=float).ravel()

    # Handle the empty edge case safely
    if all_t.size == 0:
        return np.array([], dtype=float)
    
    # The de Hoog algorithm cannot process t <= 0 (div-by-zero errors)
    if np.any(all_t <= 0):
        raise ValueError("de_Hoog_invlap requires strictly positive times.")

    # Convert all times to log10 space to cluster time vectors by decades
    log_all_t = np.log10(all_t)
    i_min = int(np.floor(np.min(log_all_t)))
    i_max = int(np.ceil(np.max(log_all_t)))

    final_f = []

    # CRITICAL LOOP: Run de Hoog decade-by-decade to prevent catastrophic
    # round-off error when time ranges cover multiple orders of magnitude.
    for i_log in range(i_min, i_max + 1):
        # Isolate times belonging to the current decade (e.g., 10^0 to 10^1)
        mask = (log_all_t >= i_log) & (log_all_t < (i_log + 1))
        t_piece = all_t[mask]

        # Skip to the next decade if no time coordinates exist in this range
        if len(t_piece) == 0:
            continue

        # T dictates the local Fourier period; optimized for this time block
        T = np.max(t_piece) * 2

        # Gamma is the real shifting factor for the Bromwich contour path
        gamma = alpha - np.log(tol) / (2 * T)

        # M defines the number of terms used in the Padé / continued fraction expansion
        M = 20
        run = np.arange(2 * M + 1)

        # Generate complex sampling points along the integration path
        s = gamma + 1j * np.pi * run / T

        # Vectorized evaluation of the user's Laplace-domain function
        a = F_func(s)

        # Correct the first term (DC component) of the Fourier sequence
        a[0] = a[0] / 2.0

        # Initialize the 'e' and 'q' matrices for the Quotient-Difference (QD) algorithm
        e = np.zeros((2 * M + 1, M + 1), dtype=complex)
        q = np.zeros((2 * M, M + 1), dtype=complex)

        # Seed the first column of the 'q' matrix with normalized coefficients
        q[:, 1] = a[1:2 * M + 1] / a[0:2 * M]

        # THE QUOTIENT-DIFFERENCE (QD) ALGORITHM:
        # Recursively builds a lookup table to accelerate convergence of the
        # series by converting the Fourier series into a continued fraction.
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

        # Extract the coefficients 'd' for the continued fraction expansion
        d = np.zeros(2 * M + 1, dtype=complex)
        d[0] = a[0]
        d[1:2 * M:2] = -q[0, 1 : M + 1] # Odd elements from q-matrix
        d[2:2 * M + 1:2] = -e[0, 1 : M + 1] # Even elements from e-matrix

        nt = len(t_piece)

        # Matrices to store numerator (a_vec) and denominator (b_vec) arrays
        # rows = fraction step, columns = individual time steps in t_piece
        a_vec = np.zeros((2 * M + 2, nt), dtype=complex)
        b_vec = np.zeros((2 * M + 2, nt), dtype=complex)

        # Seed initial conditions for the continued fraction recurrence relation
        a_vec[1, :] = d[0]
        b_vec[0:2, :] = 1.0

        # Complex rotation vector (z = e^(i*pi*t/T)) mapping to the unit circle
        z = np.exp(1j * np.pi * t_piece / T)

        # EVALUATE CONTINUED FRACTIONS:
        # Use the 3-term recurrence relation to build up Padé rational
        # approximations simultaneously across all times in this decade block.
        for n in range(2, 2 * M + 2):
            a_vec[n, :] = a_vec[n - 1, :] + d[n - 1] * z * a_vec[n - 2, :]
            b_vec[n, :] = b_vec[n - 1, :] + d[n - 1] * z * b_vec[n - 2, :]

        # Padé remainder approximation to sharpen convergence at the tail end
        h2M = 0.5 * (1.0 + (d[2 * M - 1] - d[2 * M]) * z)
        r2Mz = -h2M * (1.0 - np.sqrt(1.0 + d[2 * M] * z / (h2M**2)))

        # Finalize the rational approximation vectors
        a_final = a_vec[2 * M, :] + r2Mz * a_vec[2 * M - 1, :]
        b_final = b_vec[2 * M, :] + r2Mz * b_vec[2 * M - 1, :]

        # Scale results back into the time-domain using the Bromwich integral multiplier
        f_piece = (1.0 / T) * np.exp(gamma * t_piece) * np.real(a_final / b_final)

        # Append the calculated block into our master results tracking list
        final_f.extend(f_piece.tolist())

    # Return the unified time-domain solution vector
    return np.array(final_f)

def thermal_quadrupoles(probe: TQProbe, sample: TQSample, crucible: TQCrucible, environment: TQEnvironment) -> np.ndarray:
    """
    Solve for temperature vs time for the needle-probe quadrupole model.

    Parameters
    ----------
    probe : TQProbe
        Parameters describing the probe geometry and materials.
    sample : TQSample
        Parameters describing the sample material properties.
    crucible : TQCrucible
        Parameters describing the crucible material properties.
    environment : TQEnvironment
        Parameters describing the test parameters and environment.
    """

    # force the time input into a 1D flat NumPy array of floats
    time = np.asarray(environment.time_array, dtype=float).ravel()

    # Handle the empty edge case safely
    if time.size == 0:
        return np.array([], dtype=float)

    # The thermal quadrupole model is only valid for non-negative times
    if np.any(time < 0):
        raise ValueError("Time values must be non-negative.")

    # remove any leading zero from the time vector for evaluation, but preserve it in the final output
    has_leading_zero = np.isclose(time[0], 0.0)
    evaluation_time = time[1:] if has_leading_zero else time

    # Handle the empty edge case safely after removing leading zero
    if evaluation_time.size == 0:
        return np.array([0.0], dtype=float)

    # Evaluate the Laplace-domain response and invert it to the time domain using de Hoog's method
    response = _de_Hoog_invlap(
        lambda s: _laplace_response(s, probe, sample, crucible, environment),
        evaluation_time,
    )

    # If a leading zero was present in the original time vector, prepend a zero to the response to maintain alignment
    if has_leading_zero:
        response = np.concatenate(([0.0], response))

    # return the time-domain response, preserving the original time vector's shape
    return response

if __name__ == "__main__":
    test_pars = ThermalQuadrupoleParameters(
        k_wire_layer=2,
        alpha_wire_layer=3,
        k_insulation=4,
        alpha_insulation=5,
        thermal_contact_resistance_insulation_sheath=6,
        k_sheath=7,
        alpha_sheath=8,
        ksample=9,
        alpha_sample=10,
        k_crucible=11,
        alpha_crucible=12,
        emissivity1=0.5,
        emissivity2=0.6,
        index=1.5,
        scatter=0.03,
        T0=273,
        V=3.3,
        electrical_resistance=10,
        rwires=0.01,
        rsheath_inner=0.02,
        rsheath=0.03,
        rsample=0.04,
        rcrucible=0.05,
        L=10,
        h_conv=20,
        rhosample=1000,
        cpsample=500,
        rhocp=500000,
        I_val=0.2,
        source_decay_rate=0.01
    )
    t_test = np.linspace(0.0, 10, 100)
    result = thermal_quadrupoles(
        t_test,
        test_pars,
        sample_diffusivity_mode="from_rho_cp",
        power_calculation_mode="direct_current",
    )
    logger.debug("Thermal quadrupole model result: %s", result)