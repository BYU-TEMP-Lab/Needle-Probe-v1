import numpy as np
from scipy.interpolate import interp1d
import warnings

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
                 k_func=None, cp_func=None, rho_func=None, alpha_func=None, emissivity_func=None):
        self.name = name
        self.ignore_out_of_range = ignore_out_of_range

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
            self.valid_range = (None, None)  # No range provided

    def _check_range(self, T):
        Tmin, Tmax = self.valid_range
        msg2 = f"Temperature {T} K is outside valid range for material {self.name}: ({Tmin}, {Tmax}) K"
        if Tmin is not None and Tmax is not None:
            if not (Tmin <= T <= Tmax):
                if self.ignore_out_of_range:
                    warnings.warn(msg2)
                else:
                    raise ValueError(msg2)
        else:
            warnings.warn(f"({Tmin}, {Tmax}) K is an incomplete or invalid range defined for material {self.name}.")

    def properties_at_T(self, T):
        """
        Takes temperature T (in Kelvin).
        Returns a dictionary with keys: k, cp, rho, alpha, emissivity
        """
        self._check_range(T)

        k = float(self.k_func(T)) if self.k_source == 'func' else float(self.k_interp(T))
        cp = float(self.cp_func(T)) if self.cp_source == 'func' else float(self.cp_interp(T))
        rho = float(self.rho_func(T)) if self.rho_source == 'func' else float(self.rho_interp(T))
        emissivity = float(self.emissivity_func(T)) if self.emissivity_source == 'func' else (float(self.emissivity_interp(T)) if hasattr(self, 'emissivity_interp') else 0.5)

        # Compute alpha automatically if not provided
        if self.alpha_source == 'func':
            alpha = float(self.alpha_func(T))
        elif hasattr(self, 'alpha_points_interp'):
            alpha = float(self.alpha_points_interp(T))
        else:
            alpha = k / (rho * cp)

        return {'k': k, 'cp': cp, 'rho': rho, 'alpha': alpha, 'emissivity': emissivity}
    

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
            rho_points=material.rho_points
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
    
