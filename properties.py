import numpy as np
from scipy.interpolate import interp1d

import numpy as np
from scipy.interpolate import interp1d
import warnings

class Material:
    """
    Stores material properties with temperature dependence.
    Supports hybrid approach: each property can be either key-point data or a function.
    -   ignore_out_of_range: if True, will warn instead of erroring when T is outside valid_range
    Requires properties in standard SI units:
        T: K
        k: W/m-K
        cp: J/kg-K
        rho: kg/m^3
    """

    def __init__(self, name, valid_range=None, ignore_out_of_range=False,
                 T_points=None, k_points=None, cp_points=None, rho_points=None, alpha_points=None,
                 k_func=None, cp_func=None, rho_func=None, alpha_func=None):
        self.name = name
        self.ignore_out_of_range = ignore_out_of_range

        if all(x is None for x in [k_points, k_func]):
            raise ValueError(f"Material {name} must have k defined either by points or function")
        if all(x is None for x in [cp_points, cp_func]):
            raise ValueError(f"Material {name} must have cp defined either by points or function")
        if all(x is None for x in [rho_points, rho_func]):
            raise ValueError(f"Material {name} must have rho defined either by points or function")

        # Determine property sources
        self.k_source = 'func' if k_func is not None else 'points'
        self.cp_source = 'func' if cp_func is not None else 'points'
        self.rho_source = 'func' if rho_func is not None else 'points'
        self.alpha_source = 'func' if alpha_func is not None else 'points'

        # Create interpolators if key points are provided
        if T_points is not None:
            self.T_points = np.array(T_points)
            if k_points is not None:
                self.k_interp = interp1d(T_points, k_points, fill_value="extrapolate")
            if cp_points is not None:
                self.cp_interp = interp1d(T_points, cp_points, fill_value="extrapolate")
            if rho_points is not None:
                self.rho_interp = interp1d(T_points, rho_points, fill_value="extrapolate")
            if alpha_points is not None:
                self.alpha_interp = interp1d(T_points, alpha_points, fill_value="extrapolate")

        # Store functions if provided
        self.k_func = k_func
        self.cp_func = cp_func
        self.rho_func = rho_func
        self.alpha_func = alpha_func

        # Set valid range
        if valid_range is not None:
            self.valid_range = valid_range
        elif T_points is not None:
            self.valid_range = (min(T_points), max(T_points))
        else:
            self.valid_range = (None, None)  # No range provided

    def _check_range(self, T):
        Tmin, Tmax = self.valid_range
        msg = f"Temperature {T} K is outside valid range for material {self.name}: ({Tmin}, {Tmax})"
        if Tmin is not None and Tmax is not None:
            if not (Tmin <= T <= Tmax):
                if self.ignore_out_of_range:
                    warnings.warn(msg)
                else:
                    raise ValueError(msg)
        else:
            warnings.warn(f"({Tmin}, {Tmax}) is an incomplete or invalid range defined for material {self.name}.")

    def properties_at_T(self, T):
        self._check_range(T)

        k = float(self.k_func(T)) if self.k_source == 'func' else float(self.k_interp(T))
        cp = float(self.cp_func(T)) if self.cp_source == 'func' else float(self.cp_interp(T))
        rho = float(self.rho_func(T)) if self.rho_source == 'func' else float(self.rho_interp(T))

        # Compute alpha automatically if not provided
        if self.alpha_source == 'func':
            alpha = float(self.alpha_func(T))
        elif hasattr(self, 'alpha_interp'):
            alpha = float(self.alpha_interp(T))
        else:
            alpha = k / (rho * cp)

        return {'k': k, 'cp': cp, 'rho': rho, 'alpha': alpha}


def apply_porosity(material: Material, porosity_percent: float, model="Zivcoca") -> Material:
    """
    Returns a new Material object with thermal conductivity adjusted for porosity.
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
            name=f"{material.name}_porous",
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
            name=f"{material.name}_porous",
            k_func=k_func_porosity,
            cp_func=material.cp_func,
            rho_func=material.rho_func
        )
    
    else:
        raise ValueError("Material object does not have k_points or k_func defined.")
    

def build_probe_materials(Temp: float):
    """Returns a dictionary of all probe materials"""

    # ========================================
    # Nickel 200
    # ========================================
    Nickel200 = Material("Nickel200", 
                    T_points = [173, 673, 1273],
                    k_points = [76.12, 40.62, 40.62],
                    cp_points = [292.88, 418.4, 418.4],
                    rho_points = [8964, 8964, 8964],
                    ignore_out_of_range = True)


    # ========================================
    # Chromel
    # ========================================
    def k_Chromel(T):
        if 100 <= T < 450:
            return 13.1709 - 0.02474581*T + 2.79175E-4*T**2 - 6.862022E-7*T**3 + 6.09438E-10*T**4
        else:
            return 13.1709 - 0.02474581*T + 2.79175E-4*T**2 - 6.862022E-7*T**3 + 6.09438E-10*T**4

    def cp_Chromel(T):
        if 100 <= T < 450:
            return -169.134351 + 5.88577506*T - 0.0235877058*T**2 + 0.0000447834022*T**3 - 0.0000000321153924*T**4
        else:
            return -169.134351 + 5.88577506*T - 0.0235877058*T**2 + 0.0000447834022*T**3 - 0.0000000321153924*T**4

    def rho_Chromel(T):
        return 8670

    Chromel = Material("Chromel", k_func=k_Chromel, cp_func=cp_Chromel, rho_func=rho_Chromel, valid_range=(100, 450), ignore_out_of_range=True)


    # ========================================
    # Alumel
    # ========================================
    # VALID UP TO 450K (177C) (ASSUMPTIONS ALLOW USAGE BEYOND 450K)
    def k_Alumel(T):
        if 100 <= T < 400:
            return 9.346236 + 0.1204046*T - 2.33021E-4*T**2 + 1.774554E-7*T**3
        elif 400 <= T < 773:
            return 39.91124 - 0.08021887*T + 1.89707E-4*T**2 - 1.037644E-7*T**3
        else:
            return 39.91124 - 0.08021887*T + 1.89707E-4*T**2 - 1.037644E-7*T**3

    def cp_Alumel(T):
        if 100 <= T < 410:
            return -120.397194 + 4.83234846*T - 0.0141451249*T**2 + 0.0000151245324*T**3
        elif 410 <= T < 450:
            return 4215.99923 - 16.6533325*T + 0.018666665*T**2
        else:
            return 4215.99923 - 16.6533325*T + 0.018666665*T**2

    Alumel = Material("Alumel", k_func=k_Alumel, cp_func=cp_Alumel, rho_func=lambda T: 8600, valid_range=(100, 450), ignore_out_of_range=True)


    # ========================================
    # ALumina
    # ========================================
    Alumina = Material("Alumina", 
                       T_points = [293, 873],
                       k_points = [37.17, 9.12],
                       cp_points = [782, 1214],
                       rho_points = [3900, 3900],
                       ignore_out_of_range=True)
    


    # ========================================
    # Porous Alumina (using Zivcoca model)
    # ========================================
    # Apply 7.38% porosity
    PorousAlumina = apply_porosity(Alumina, porosity_percent=7.38)
    


    # ========================================
    # Air
    # ========================================
    def k_Air(T):
        return 1e-11*T**3 - 5e-8*T**2 + 1e-4*T + 0.0003

    def cp_Air(T):
        return 1e-10*T**4 - 6e-7*T**3 + 0.001*T**2 - 0.3867*T + 1050

    def rho_Air(T):
        return 355.1 * T**-1.001

    Air = Material("Air", k_func=k_Air, cp_func=cp_Air, rho_func=rho_Air, ignore_out_of_range=True)


    # ========================================
    # Water
    # ========================================
    def k_Water(T):
        if 273 <= T < 533:
            return -0.869083936 + 0.00894880345*T - 1.58366345e-5*T**2 + 7.97543259e-9*T**3
        else:
            return -0.869083936 + 0.00894880345*T - 1.58366345e-5*T**2 + 7.97543259e-9*T**3  # Placeholder

    def cp_Water(T):
        if 273 <= T < 533:
            return 12010.1471 - 80.4072879*T + 0.309866854*T**2 - 5.38186884e-4*T**3 + 3.62536437e-7*T**4
        else:
            return 12010.1471 - 80.4072879*T + 0.309866854*T**2 - 5.38186884e-4*T**3 + 3.62536437e-7*T**4  # Placeholder

    def rho_Water(T):
        if 273 <= T < 293:
            return 0.000063092789034*T**3 - 0.060367639882855*T**2 + 18.9229382407066*T - 950.704055329848
        elif 293 <= T < 373:
            return 0.000010335053319*T**3 - 0.013395065634452*T**2 + 4.96928883265516*T + 432.257114008512
        else:
            return 0.000010335053319*T**3 - 0.013395065634452*T**2 + 4.96928883265516*T + 432.257114008512  # Placeholder

    Water = Material("Water", k_func=k_Water, cp_func=cp_Water, rho_func=rho_Water, valid_range=(273, 373), ignore_out_of_range=True)



    # ========================================
    # Argon
    # ========================================
    def k_Argon(T):
        if 273 <= T < 750:
            return 0.0002678*T**0.7401
        else:
            return 0.03594  # Placeholder

    def cp_Argon(T):
        return 525  # Constant for all T in the MATLAB code

    def rho_Argon(T):
        return 1.77  # Constant for all T

    Argon = Material("Argon", k_func=k_Argon, cp_func=cp_Argon, rho_func=rho_Argon, valid_range=(273, 750), ignore_out_of_range=True)



    # ========================================
    # NaNO3
    # ========================================
    def rho_NaNO3(T):
        return (1847.4-1878.6)/(360-320) * (T-(320+273)) + 1878.6
    
    NaNO3 = Material(
        "NaNO3",
        T_points=[590, 625, 650, 675, 700],
        k_points=[0.517, 0.513, 0.510, 0.507, 0.503],
        cp_points=[1805, 1805, 1805, 1805, 1805],
        rho_func=rho_NaNO3,  # approximate linear trend
        ignore_out_of_range=True
    )


    # ========================================
    # Propylene Glycol
    # ========================================
    def k_PropyleneGlycol(T):
        # Thermal conductivity (W/mK) valid 294–354 K
        return 0.1549 + 1e-4*T

    def cp_PropyleneGlycol(T):
        # Heat capacity (J/kgK) valid 253–373 K
        return 764.977874 + 5.85389298*T

    def rho_PropyleneGlycol(T):
        # Density (kg/m^3) valid 273–393 K
        return 1352.128 - 1.775134*T + 0.003661077*T**2 - 4.338143e-6*T**3

    PropyleneGlycol = Material(
        "PropyleneGlycol",
        k_func=k_PropyleneGlycol,
        cp_func=cp_PropyleneGlycol,
        rho_func=rho_PropyleneGlycol,
        valid_range=(294, 354),
        ignore_out_of_range=True
    )


    # ========================================
    # Potassium Nitrate (KNO3)
    # ========================================
    def k_KNO3(T):
        # Thermal conductivity (W/mK) valid 610–710 K
        return 0.4303 - 0.000422*(T-610.15)

    def cp_KNO3(T):
        # Heat capacity constant (J/kgK)
        return 1518

    def rho_KNO3(T):
        # Density (kg/m^3) valid 610–730 K
        return (1.865 - 0.000723*((T-273.15)-337))*1000

    KNO3 = Material(
        "KNO3",
        k_func=k_KNO3,
        cp_func=cp_KNO3,
        rho_func=rho_KNO3,
        valid_range=(610, 710),
        ignore_out_of_range=True
    )


    # ========================================
    # FLiNaK (LiF-NaF-KF eutectic)
    # ========================================
    def k_FLiNaK(T):
        # Weighted thermal conductivity by molar composition
        k_LiF = 1.9 - 0.0004*T
        k_KF = 0.86 - 0.00025*T
        k_NaF = 1.3 - 0.00028*T
        return 0.465*k_LiF + 0.42*k_KF + 0.115*k_NaF

    def cp_FLiNaK(T):
        # Heat capacity from Rogers et al.
        return (40.3 + 0.0439*T)/0.0412911

    def rho_FLiNaK(T):
        # Density from Cibulkova et al.
        return (2.5793 - 6.24e-4*T)*1000

    FLiNaK = Material(
        "FLiNaK",
        k_func=k_FLiNaK,
        cp_func=cp_FLiNaK,
        rho_func=rho_FLiNaK,
        valid_range=(273, 910),
        ignore_out_of_range=True
    )


    # ========================================
    # FLiBe (LiF-BeF2 eutectic)
    # ========================================
    def k_FLiBe(T):
        # Gheribi et al
        k_LiF = 1.88 - 3.99e-4*T
        k_BeF2 = 0.801 - 2.12e-6*T
        # Weighted by molar fraction
        return 0.67*k_LiF + 0.33*k_BeF2

    def cp_FLiBe(T):
        # Heat capacity weighted by components
        # MSTDB-TC, synthetic
        cp_LiF = 64.183/0.0259394
        cp_BeF2 = (51.1 + 3.46e-2)/0.047009
        return 0.67*cp_LiF + 0.33*cp_BeF2

    def rho_FLiBe(T):
        # Density from Cantor et al.
        return 1000*(2.41 - 4.88e-4*T)

    FLiBe = Material(
        "FLiBe",
        k_func=k_FLiBe,
        cp_func=cp_FLiBe,
        rho_func=rho_FLiBe,
        valid_range=(273, 1070),
        ignore_out_of_range=True
    )


    # ========================================
    # FMgNaK (MgF2-KF-NaF eutectic)
    # ========================================
    def k_FMgNaK(T):
        k_NaF = 1.3 - 0.00028*T
        k_KF = 0.86 - 0.00025*T
        k_MgF2 = 0.87 - 0.00014*T
        return 0.345*k_NaF + 0.59*k_KF + 0.065*k_MgF2

    def cp_FMgNaK(T):
        # eutectic average of unaries form MSTDB
        cp_NaF = 68.62
        cp_KF = 70.6
        cp_MgF2 = 94.43
        return 0.345*cp_NaF + 0.59*cp_KF + 0.065*cp_MgF2

    def rho_FMgNaK(T):
        return -0.6318*T + 2711

    FMgNaK = Material(
        "FMgNaK",
        k_func=k_FMgNaK,
        cp_func=cp_FMgNaK,
        rho_func=rho_FMgNaK,
        valid_range=(273, 1070),
        ignore_out_of_range=True
    )


    # ========================================
    # LiCl-KCl eutectic
    # ========================================
    def k_LiCl_KCl(T):
        # Nagasaka et al.
        k_LiCl = 0.8821 - 2.9e-4*T
        k_KCl = 0.5663 - 1.7e-4*T
        return 0.582*k_LiCl + 0.418*k_KCl

    def cp_LiCl_KCl(T):
        # MSTDB-TC
        cp_LiCl = 1/0.042394*(73.3832 - 0.0094726*T)
        cp_KCl = 73.59656/0.0745513
        return 0.582*cp_LiCl + 0.418*cp_KCl

    def rho_LiCl_KCl(T):
        # Duemmler et al.
        return 2008.2 - 0.5133*T

    LiCl_KCl = Material(
        "LiCl-KCl",
        k_func=k_LiCl_KCl,
        cp_func=cp_LiCl_KCl,
        rho_func=rho_LiCl_KCl,
        valid_range=(273, 1070),
        ignore_out_of_range=True
    )

    # ========================================
    # NaCl-KCl eutectic
    # ========================================
    def k_NaCl_KCl(T):
        # Nagasaka et al.
        k_NaCl = 0.7121 - 1.8e-4*T
        k_KCl = 0.5663 - 1.704e-4*T
        return 0.5123*k_NaCl + 0.4877*k_KCl

    def cp_NaCl_KCl(T):
        # MTSDB-TC
        cp_NaCl = 1/0.0584428*(77.7638 - 0.0075312*T)
        cp_KCl = 73.59656/0.0745513
        return 0.5123*cp_NaCl + 0.4877*cp_KCl

    def rho_NaCl_KCl(T):
        # Van Artsdalen et al.
        return (2.13 - 5.68e-4*T)*1000

    NaCl_KCl = Material(
        "NaCl-KCl",
        k_func=k_NaCl_KCl,
        cp_func=cp_NaCl_KCl,
        rho_func=rho_NaCl_KCl,
        valid_range=(273, 1023),
        ignore_out_of_range=True
    )

    # ========================================
    # LiF-NaF (60-40) eutectic
    # ========================================
    def k_LiF_NaF(T):
        # Gheribi et al
        k_LiF = 1.88 - 3.99e-4*T
        k_NaF = 1.26 - 2.8e-4*T
        return 0.6*k_LiF + 0.4*k_NaF

    def cp_LiF_NaF(T):
        # Powers et al.
        return (125.1 - 0.06661*T)/0.0323589

    def rho_LiF_NaF(T):
        return (2.533 - 5.552e-4*T)*1000

    LiF_NaF = Material(
        "LiF-NaF",
        k_func=k_LiF_NaF,
        cp_func=cp_LiF_NaF,
        rho_func=rho_LiF_NaF,
        valid_range=(273, None),
        ignore_out_of_range=True
    )

    # ========================================
    # LiCl-NaCl eutectic
    # ========================================
    def k_LiCl_NaCl(T):
        # Nagasaka et al.
        k_LiCl = 0.882 - 2.9e-4*T
        k_NaCl = 0.7121 - 1.8e-4*T
        return 0.72*k_LiCl + 0.28*k_NaCl

    def cp_LiCl_NaCl(T):
        # MTSDB-TC
        cp_LiCl = 1/0.042394*(73.3832 - 0.0094726*T)
        cp_NaCl = 1/0.0584428*(77.7638 - 0.0075312*T)
        return 0.72*cp_LiCl + 0.28*cp_NaCl

    # Density- LiCl-NaCl DO NOT USE FOR ACCURATE CP MEASUREMENTS
    def rho_LiCl_NaCl(T):
        # Van Artsdalen et al.
        rho_LiCl = (1.88 - 4.33e-4*T)*1000
        rho_NaCl = (2.41 - 5.43e-4*T)*1000
        return 0.72*rho_LiCl + 0.28*rho_NaCl

    LiCl_NaCl = Material(
        "LiCl-NaCl",
        k_func=k_LiCl_NaCl,
        cp_func=cp_LiCl_NaCl,
        rho_func=rho_LiCl_NaCl,
        valid_range=(273, 1023),
        ignore_out_of_range=True
    )

    # ========================================
    # KCl-ZnCl2 eutectic
    # ========================================
    def k_KCl_ZnCl2(T):
        k_ZnCl2 = 3.05 # Kornwell, maybe actually Turnbull1961
        k_KCl = 0.5663 - 1.704e-4*T # Nagasaka et al.
        return 0.547*k_ZnCl2 + 0.453*k_KCl

    def cp_KCl_ZnCl2(T):
        # cp_ZnCl2 = 24.1  # cal/mole, allegedly constant. Cubicciotti et al
        cp_ZnCl2 = 739.6  # J/kg·K
        cp_KCl = 73.59656/0.0745513 # MSTDB-TC
        return 0.547*cp_ZnCl2 + 0.453*cp_KCl

    def rho_KCl_ZnCl2(T):
        rho_ZnCl2 = 2683 - 0.511*T # Smith and Smith
        rho_KCl = 2140 - 0.583*T # Va Atrsdalen et al.
        return 0.547*rho_ZnCl2 + 0.453*rho_KCl

    KCl_ZnCl2 = Material(
        "KCl-ZnCl2",
        k_func=k_KCl_ZnCl2,
        cp_func=cp_KCl_ZnCl2,
        rho_func=rho_KCl_ZnCl2,
        valid_range=(273, 1023),
        ignore_out_of_range=True
    )


    # Return dictionary
    materials = {
        "Nickel200": Nickel200,
        "Wire": Chromel,
        "Alumina": Alumina,
    }

    return materials


def thermal_contact_resistance(mat1: str, mat2: str) -> float:
    """
    Returns thermal contact resistance (TCR) in m^2*K/W
    between two materials. Extend dictionary as needed.
    """
    TCR_values = {
        ("Alumina", "Nickel200"): 0.0052,
        ("Nickel200", "Sample"): 0.001,
    }
    
    key = (mat1, mat2)
    if key in TCR_values:
        return TCR_values[key]
    elif (mat2, mat1) in TCR_values:  # allow reverse order
        return TCR_values[(mat2, mat1)]
    else:
        raise ValueError(f"No TCR value defined for {mat1}-{mat2}")
