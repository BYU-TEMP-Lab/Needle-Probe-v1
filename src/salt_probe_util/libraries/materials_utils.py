import warnings, numpy as np, pandas as pd
from scipy.interpolate import interp1d
from pathlib import Path

class Material:
    """
    Stores material properties with temperature dependence (Kelvin).
    Supports hybrid approach: each property can be either key-point data or a function.
    -   ignore_out_of_range: if True, will warn instead of erroring when T is outside valid_range
    Requires properties in standard SI units:
        T: K
        k: W/m-K
        cp: J/kg-K
        rho: kg/m^3
    """

    def __init__(self, name, valid_range=None, ignore_out_of_range=False,
                 T_points=None, k_points=None, cp_points=None, rho_points=None, alpha_points=None, emissivity_points=None,
                 k_func=None, cp_func=None, rho_func=None, alpha_func=None, emissivity_func=None,
                 k_perc_uncertainty=0.2, cp_perc_uncertainty=0.1, rho_perc_uncertainty=0.1, alpha_perc_uncertainty=None, emissivity_perc_uncertainty=0.1):
        self.name = name
        self.ignore_out_of_range = ignore_out_of_range
        self.k_perc_uncertainty = k_perc_uncertainty
        self.cp_perc_uncertainty = cp_perc_uncertainty
        self.rho_perc_uncertainty = rho_perc_uncertainty
        self.alpha_perc_uncertainty = alpha_perc_uncertainty
        self.emissivity_perc_uncertainty = emissivity_perc_uncertainty

        msg1 = lambda name, x: f"Material {name} must have {x} defined either by points or function"
        if all(x is None for x in [k_points, k_func]):
            raise ValueError(msg1(self.name, 'k'))
        if all(x is None for x in [cp_points, cp_func]):
            raise ValueError(msg1(self.name, 'cp'))
        if all(x is None for x in [rho_points, rho_func]):
            raise ValueError(msg1(self.name, 'rho'))

        # Determine property sources
        self.k_source = 'func' if k_func is not None else 'points'
        self.cp_source = 'func' if cp_func is not None else 'points'
        self.rho_source = 'func' if rho_func is not None else 'points'
        self.alpha_source = 'func' if alpha_func is not None else 'points'
        self.emissivity_source = 'func' if emissivity_func is not None else 'points'

        # Create interpolators if key points are provided
        if T_points is not None:
            self.T_points = np.array(T_points)
            # create loop to iterate over names
            names = ["k_points", "cp_points", "rho_points", "alpha_points", "emissivity_points"]
            for name, var in zip(names, (k_points, cp_points, rho_points, alpha_points, emissivity_points)):
                if var is not None:
                    setattr(self, name, np.array(var))
                    setattr(self, f"{name}_interp", interp1d(T_points, var, fill_value="extrapolate"))

        # Store functions if provided
        self.k_func = k_func
        self.cp_func = cp_func
        self.rho_func = rho_func
        self.alpha_func = alpha_func
        self.emissivity_func = emissivity_func

        # Set valid range
        if valid_range is not None:
            self.valid_range = valid_range
        elif T_points is not None:
            self.valid_range = (min(T_points), max(T_points))
        else:
            self.valid_range = (None, None)  # No range provided :(

    def _check_range(self, T):
        Tmin, Tmax = self.valid_range
        eps = 1e-5  # 0.00001 K buffer for floating point stability

        # 1. CRITICAL DATA CHECK: Warn if no range is defined at all
        if Tmin is None and Tmax is None:
            warnings.warn(f"WARNING: No valid temperature range defined for {self.name}. "
                        f"Property calculations at {T:.2f} K may be physically invalid.")
            return # Exit early since we can't perform the numerical check

        # 2. PERFORM NUMERICAL CHECK: Handle partial or full ranges
        is_low = (Tmin is not None) and (T < Tmin - eps)
        is_high = (Tmax is not None) and (T > Tmax + eps)

        if is_low or is_high:
            msg = (f"Temperature {T:.3f} K is outside valid range for {self.name}: "
                f"({Tmin if Tmin is not None else '-inf'}, "
                f"{Tmax if Tmax is not None else 'inf'}) K")
            
            if self.ignore_out_of_range:
                warnings.warn(msg)
            else:
                # Hard stop if data is out of range and user hasn't opted-out
                raise ValueError(msg)

    def update_properties_at_T(self, T):
        """
        Takes temperature T (in Kelvin).
        Returns a dictionary with keys: k, cp, rho, alpha, emissivity
        """
        self._check_range(T)

        k = float(self.k_func(T)) if self.k_source == 'func' else float(self.k_points_interp(T))
        cp = float(self.cp_func(T)) if self.cp_source == 'func' else float(self.cp_points_interp(T))
        rho = float(self.rho_func(T)) if self.rho_source == 'func' else float(self.rho_points_interp(T))
        emissivity = float(self.emissivity_func(T)) if self.emissivity_source == 'func' else (float(self.emissivity_points_interp(T)) if hasattr(self, 'emissivity_points_interp') else 0.5)

        # Compute alpha automatically if not provided
        if self.alpha_source == 'func':
            alpha = float(self.alpha_func(T))
        elif hasattr(self, 'alpha_points_interp'):
            alpha = float(self.alpha_points_interp(T))
        else:
            alpha = k / (rho * cp)

        # compute uncertainty of alpha if not provided
        if self.alpha_perc_uncertainty is None or not hasattr(self, 'alpha_perc_uncertainty'):
            self.alpha_perc_uncertainty = alpha * np.sqrt(
                (self.k_perc_uncertainty/k)**2 +
                (self.rho_perc_uncertainty/rho)**2 +
                (self.cp_perc_uncertainty/cp)**2
            )

        # setup output dictionary at T
        self.k = {
            "initial_value": k,
            "bounds": (0.9 * k, 1.1 * k),
            "prior_sigma": self.k_perc_uncertainty * k
        }
        self.cp = {
            "initial_value": cp,
            "bounds": (0.9 * cp, 1.1 * cp),
            "prior_sigma": self.cp_perc_uncertainty * cp
        }
        self.rho = {
            "initial_value": rho,
            "bounds": (0.9 * rho, 1.1 * rho),
            "prior_sigma": self.rho_perc_uncertainty * rho
        }
        self.alpha = {
            "initial_value": alpha,
            "bounds": (0.9 * alpha, 1.1 * alpha),
            "prior_sigma": self.alpha_perc_uncertainty * alpha
        }
        self.emissivity = {
            "initial_value": emissivity,
            "bounds": (0.9 * emissivity, 1.1 * emissivity),
            "prior_sigma": self.emissivity_perc_uncertainty * emissivity
        }
    

def load_nist_fluid_properties(filepath: Path):
    """
    Loads NIST fluid properties from a text file (tab delimited)
    Expects columns: Temperature (K), k (W/m-K), cp (J/kg-K), rho (kg/m^3)
    Returns functions for k, cp, rho.
    """

    # data = np.loadtxt(filepath, skiprows=1, delimiter="\t")  # Skip header row
    # T = data[:, 0] + 273.15  # Convert from C to K
    # rho = data[:, 2]
    # cp = data[:, 8] * 1000 # Convert from J/g-K to J/kg-K
    # k = data[:, 12]

    df = pd.read_csv(filepath, sep="\t")
    # df.columns = df.columns.str.strip()
    target_columns = ["Temperature (C)", "Therm. Cond. (W/m*K)", "Cp (J/g*K)", "Density (kg/m3)"]
    df_clean = df.dropna(subset=target_columns)

    T = df_clean["Temperature (C)"].values + 273.15  # Convert from C to K
    k = df_clean["Therm. Cond. (W/m*K)"].values
    cp = df_clean["Cp (J/g*K)"].values * 1000 # Convert from J/g-K to J/kg-K
    rho = df_clean["Density (kg/m3)"].values

    k_func = interp1d(T, k, fill_value="extrapolate")
    cp_func = interp1d(T, cp, fill_value="extrapolate")
    rho_func = interp1d(T, rho, fill_value="extrapolate")

    return k_func, cp_func, rho_func
    

def thermal_contact_resistance(mat1: str, mat2: str, ignore_warnings=False) -> float:
    """
    Returns thermal contact resistance (TCR) in m^2*K/W
    between two materials. Extend dictionary as needed.
    - Alumina-Nickel200: 0.0052 (no source, needs verification)
    - Nickel200-Generic Sample: 0.001 (no source, needs verification)
    - Generic Sample-Generic Crucible: 1e-8 (no source, needs verification)
    """
    TCR_values = {
        ("Alumina", "Nickel 200"): 0.0052, # these numbers don't currently appear to have sources
        ("Porous Alumina", "Nickel 200"): 0.0052,
        ("Nickel 200", "Generic Sample"): 0.001,
        ("Generic Sample", "Generic Crucible"): 1e-8
    }
    
    key = (mat1, mat2)
    if key in TCR_values:
        return TCR_values[key]
    elif (mat2, mat1) in TCR_values:  # allow reverse order
        return TCR_values[(mat2, mat1)]
    else:
        msg = f"No TCR value defined for {mat1}-{mat2}. Default to 0."
        if ignore_warnings:
            warnings.warn(msg)
            return 0.0  # Default to 0 if not found
        else:
            raise ValueError(msg)

def apply_porosity(material: Material, porosity_percent: float, model="Zivcoca") -> Material:
    """
    Returns a new Material object with thermal conductivity (NOT OTHER PROPERTIES YET) adjusted for porosity.
    Currently supports the Zivcoca model (Z. Zivcoca et al, 2009) for Alumina.
    
    Parameters:
        material: Material object
        porosity_percent: Fraction of voids (0-100)
        model: Porosity model to apply (currently only "Zivcoca" implemented)
    
    Returns:
        New Material object with adjusted k_points / k_func
    """
    phi = porosity_percent / 100  # Convert to fraction
    
    if material.name.lower() != "alumina" and model == "Zivcoca":
        raise ValueError("Zivcoca model is only valid for Alumina.")
    
    # If material uses discrete points
    if hasattr(material, "k_points") and material.k_points is not None:
        k_new = material.k_points * np.exp(-1.5 * phi / (1 - phi))
        return Material(
            name=f"Porous {material.name}",
            T_points=material.T_points,
            k_points=k_new,
            cp_points=material.cp_points,
            rho_points=material.rho_points,
            ignore_out_of_range=material.ignore_out_of_range
        )
    
    # If material uses functions
    elif hasattr(material, "k_func") and material.k_func is not None:
        def k_func_porosity(T):
            return material.k_func(T) * np.exp(-1.5 * phi / (1 - phi))
        return Material(
            name=f"Porous{material.name}",
            k_func=k_func_porosity,
            cp_func=material.cp_func,
            rho_func=material.rho_func
        )
    
    else:
        raise ValueError("Material object does not have k_points or k_func defined.")
    
