from .materials_utils import Material, thermal_contact_resistance, apply_porosity, load_nist_fluid_properties
from pathlib import Path

# List of materials available for use in simulations
# SORTED ALPHABETICALLY BY MATERIAL NAME
# ALL PROPERTIES IN SI UNITS (k in W/m·K, cp in J/kg·K, rho in kg/m³, alpha in m²/s, emissivity unitless)
# Also I left most of the uncertainties out because they are not being used and most don't have sources. they can be found in the old Properties.m file.


# ========================================
# Air
# ========================================
def k_Air(T):
    # Made from data from engineeringtoolbox.com
    return 1e-11*T**3 - 5e-8*T**2 + 1e-4*T + 0.0003 

def cp_Air(T):
    # Made from data from engineersedge.com
    return 1e-10*T**4 - 6e-7*T**3 + 0.001*T**2 - 0.3867*T + 1050

def rho_Air(T):
    # Made from data from engineeringtoolbox.com
    return 355.1 * T**-1.001

Air = Material("Air", k_func=k_Air, cp_func=cp_Air, rho_func=rho_Air, ignore_out_of_range=True)


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
    
def alpha_Alumel(T):
    if 100 <= T < 175:
        return 2.777243e-5 - 3.26281e-7*T + 1.773714e-9*T**2 - 3.253333e-12*T**3
    elif 175 <= T < 422:
        return 9.912174e-6 - 2.568489e-8*T + 8.732857e-11*T**2 - 1.005653e-13*T**3
    elif 422 <= T < 450:
        return -7.507129e-5 + 3.614333e-7*T - 3.952381e-10*T**2
    elif T >= 450:
        # Placeholder for T out of COMSOL range
        return -7.507129e-5 + 3.614333e-7*T - 3.952381e-10*T**2
    else:
        return -7.507129e-5 + 3.614333e-7*T - 3.952381e-10*T**2

Alumel = Material("Alumel", k_func=k_Alumel, cp_func=cp_Alumel, rho_func=lambda T: 8600, valid_range=(100, 450), ignore_out_of_range=True)


# ========================================
# ALumina
# ========================================
T_points_Alumina = [293, 298, 300, 373, 400, 473, 500, 600, 673, 700, 873]
k_points_Alumina = [37.1754, 37.1754, 36.9601, 30.2503, 27.209, 22.5099, 20.93, 16.3045, 13.1378, 12.558, 9.1211]
cp_points_Alumina = [782.218, 782.218, 785.025, 901.3683, 942.03, 1016.802, 1046.7, 1109.502, 1148.873, 1148.873, 1214.92]
rho_points_Alumina = [3900]*len(T_points_Alumina)  # kg/m³, constant

Alumina = Material("Alumina", 
                    T_points = T_points_Alumina,
                    k_points = k_points_Alumina, 
                    cp_points = cp_points_Alumina,
                    rho_points = rho_points_Alumina,
                    valid_range= (293, 873),
                    ignore_out_of_range=True)

# 7.38% porosity seems to be of interest. Can calculate properties with the apply_porosity function (zivoca model) in meterials_funcs.py


# ========================================
# Argon
# ========================================
# From NIST (https://webbook.nist.gov/cgi/cbook.cgi?ID=7440-37-1)
# Eric W. Lemmon, Ian H. Bell, Marcia L. Huber, and Mark O. McLinden, "Thermophysical Properties of Fluid Systems" in NIST Chemistry WebBook, NIST Standard Reference Database Number 69, Eds. P.J. Linstrom and W.G. Mallard, National Institute of Standards and Technology, Gaithersburg MD, 20899, https://doi.org/10.18434/T4D303, (retrieved January 8, 2026).

argon_data_path = Path(__file__).parent / "raw_material_data" / "argon nist fluid properties - 0-1700C - 1 atm.txt"
k_Argon, cp_Argon, rho_Argon = load_nist_fluid_properties(argon_data_path)

Argon = Material(
    name="Argon", 
    k_func=k_Argon, 
    k_perc_uncertainty=0.02, # 2% uncertainty
    cp_func=cp_Argon, 
    cp_perc_uncertainty=0.002, # 0.2% uncertainty
    rho_func=rho_Argon, 
    rho_perc_uncertainty=0.003, # 0.03% uncertainty
    valid_range=(273, 1973), 
    ignore_out_of_range=False
    )

# OLD POLYNOMIAL FITS FOR ARGON VVVVVVV (REPLACED BY NIST DATA ABOVE)
# def k_Argon(T):
#     # Aggarwal, Springer, 1979
#     if T >= 273 and T < 473:
#         return -1.3127E-08*T^2 + 5.3488E-05*T + 3.1611E-03
#     elif T >= 473 and T < 673:
#         return -1.52385E-08*T^2 + 5.52618E-05*T + 2.90397E-03
#     else:
#         return -1.3127E-08*T^2 + 5.3488E-05*T + 3.1611E-03; 

# def cp_Argon(T):
#     # Heat Capacity- Argon: Tegeler, Ch.; Span, R.; Wagner, W., A New Equation of State for Argon Covering the Fluid Region for Temperatures from the Melting Line to 700 K at Pressures up to 1000 MPa, J. Phys. Chem. Ref. Data, 1999, 28, 3, 779-850, https://doi.org/10.1063/1.556037 . [all data]
#     if T >= 273 and T < 473:
#         return -3.5705E-14*T^5 + 1.3617E-10*T^4 - 2.0614E-07*T^3 + 1.5592E-04*T^2 - 5.9846E-02*T + 5.3000E+02
#     elif T >= 473 and T < 673:
#         return -8.80430E-14*T^5 + 2.79446E-10*T^4 - 3.58934E-07*T^3 + 2.35173E-04*T^2 - 7.98606E-02*T + 5.31985E+02
#     else: 
#         return -3.5705E-14*T^5 + 1.3617E-10*T^4 - 2.0614E-07*T^3 + 1.5592E-04*T^2 - 5.9846E-02*T + 5.3000E+02

# def rho_Argon(T):
#     # Density- Argon: Tegeler, Ch.; Span, R.; Wagner, W., A New Equation of State for Argon Covering the Fluid Region for Temperatures from the Melting Line to 700 K at Pressures up to 1000 MPa, J. Phys. Chem. Ref. Data, 1999, 28, 3, 779-850, https://doi.org/10.1063/1.556037 . [all data]
#     if T >= 273 and T < 473:
#         return 4.8953E+02*T^(-1.0005)
#     elif T >= 473 and T < 673:
#         return 4.88954E+02*T^(-1.00033)
#     else:
#         return 4.8953E+02*T^(-1.0005)


# Argon = Material("Argon", k_func=k_Argon, cp_func=cp_Argon, rho_func=rho_Argon, valid_range=(273, 673), ignore_out_of_range=True)


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

def alpha_Chromel(T):
    if 100 <= T < 175:
        return 3.466e-5 - 6.301667e-7*T + 5.119333e-9*T**2 - 1.893333e-11*T**3 + 2.666667e-14*T**4
    elif 175 <= T < 450:
        return 6.607453e-6 - 1.986064e-8*T + 6.038939e-11*T**2 - 5.155141e-14*T**3
    else:
        # Placeholder for T out of COMSOL range
        return 6.607453e-6 - 1.986064e-8*T + 6.038939e-11*T**2 - 5.155141e-14*T**3

Chromel = Material("Chromel", 
                   k_func=k_Chromel, 
                   cp_func=cp_Chromel, 
                   rho_func=rho_Chromel, 
                   alpha_func=alpha_Chromel, 
                   valid_range=(100, 450), 
                   ignore_out_of_range=True)


# ========================================
# FLiBe (LiF-BeF2 eutectic)
# ========================================
def k_FLiBe(T):
    # Gheribi et al 1118.5-1900K
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
# FMgNaK (MgF2-KF-NaF eutectic)
# ========================================
# Valid up to 1070K (797C)
def k_FMgNaK(T):
    k_NaF = 1.3 - 0.00028*T
    k_KF = 0.86 - 0.00025*T
    k_MgF2 = 0.87 - 0.00014*T
    return 0.345*k_NaF + 0.59*k_KF + 0.065*k_MgF2 # eutectic average of unaries from MSTDB

def cp_FMgNaK(T):
    # eutectic average of unaries form MSTDB
    cp_NaF = 68.62
    cp_KF = 70.6
    cp_MgF2 = 94.43
    return 0.345*cp_NaF + 0.59*cp_KF + 0.065*cp_MgF2

def rho_FMgNaK(T):
    return -0.6318*T + 2711

# uncertainty_k_FMgNaK = 0.05*k_FMgNaK(Temp)
# uncertainty_alpha_FMgNaK = 0.05*alpha_FMgNaK(Temp)

FMgNaK = Material(
    "FMgNaK",
    k_func=k_FMgNaK,
    cp_func=cp_FMgNaK,
    rho_func=rho_FMgNaK,
    valid_range=(273, 1070),
    ignore_out_of_range=True
)


# ========================================
# H2O (see Water)
# ========================================


# ========================================
# Inconel 625
# ========================================
def k_Inconel625(T):
    if 316 <= T < 1093:
        return 0.2435*T + 339.27

def cp_Inconel625(T):
    if 316 <= T < 1093:
        return 0.0163*T + 4.23

def rho_Inconel625(T):
    return 8440

def emissivity_Inconel625(T):
    if T < 473:
        return 0.35
    else:
        return 0.35 # placeholder

Inconel625 = Material(
    "Inconel 625",
    k_func=k_Inconel625,
    cp_func=cp_Inconel625,
    rho_func=rho_Inconel625,
    emissivity_func=emissivity_Inconel625,
    valid_range=(316, 1093),
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

# uncertainties
# u_k_LiCl = .2*k_LiCl; %Nagasaka et al
# uncertainty_kLiCl_NaCl = sqrt((.72*u_k_LiCl)^2 + (.28*u_k_NaCl)^2)/k_LiCl_NaCl;%Propagation of uncertainty
# u_k_NaCl = .08*k_NaCl; %Nagasaka et al
# u_rho_LiCl = .01*rho_LiCl; %Van Arstdalen et al.
# u_rho_NaCl = .01*rho_NaCl; %Van Arsdalen et al

LiCl_NaCl = Material(
    "LiCl-NaCl",
    k_func=k_LiCl_NaCl,
    cp_func=cp_LiCl_NaCl,
    rho_func=rho_LiCl_NaCl,
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
    # Janz et al.
    return (2.533 - 5.552e-4*T)*1000

# uncertainties
# u_cp_LiF_NaF = .10; %Powers et al
# u_rho_LiF_NaF = .01

LiF_NaF = Material(
    "LiF-NaF",
    k_func=k_LiF_NaF,
    cp_func=cp_LiF_NaF,
    rho_func=rho_LiF_NaF,
    valid_range=(273, None),
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
# NaNO3-KNO3
# ========================================
# Valid up to 690K (417C)

def k_NaNO3_KNO3(T):
    return 0.0002001993*T + 0.5535004504

def cp_NaNO3_KNO3(T):
    # Joohyun 2024
    if T < 585.15:
        return 1.31192E-03*(T-273.15) + 1139.51
    elif T >= 585.15:
        return 3.88350E-05*(T-273.15) + 1542.22
    else:
        return 3.88350E-05*(T-273.15) + 1542.22 # placeholder
        
def rho_NaNO3_KNO3(T):
    if T < 498.15:
        return -0.51151382*(T-273.15) + 2270.22748425 # Schinke 1960, from Bonk, A., & Bauer, T. (2021). Report on thermo-physical properties of binary NaNO3-KNO3
    elif T >= 498.15:
        # mixtures in a range of 59-61 wt% NaNO3.
        return 2106.0-6.6795E-01*(T-273.15)  # Janz extrap. 1972, from Bonk, A., & Bauer, T. (2021). Report on thermo-physical properties of binary NaNO3-KNO3
    

NaNO3_KNO3 = Material("NaNO3-KNO3",
                        k_func = k_NaNO3_KNO3,
                        cp_func = cp_NaNO3_KNO3,
                        rho_func = rho_NaNO3_KNO3,
                        valid_range = (573, 690),
                        ignore_out_of_range = True)


# ========================================
# 0.5% np-NaNO3-KNO3
# ========================================
# REUSES k AND rho FROM NaNO3-KNO3!!!!

def cp_0_5npNaNO3_KNO3(T):
    # Heat capacity (J/kgK), Joohyun 2024
    if T < 585.15:
        return 1.31192E-03*(T-273.15) + 1139.51
    else:
        return 3.88350E-05*(T-273.15) + 1542.22

np0_5NaNO3_KNO3_T2 = Material(
    "0.5%np-NaNO3-KNO3",
    k_func=k_NaNO3_KNO3,
    cp_func=cp_0_5npNaNO3_KNO3,
    rho_func=rho_NaNO3_KNO3,
    valid_range=(573, 690),
    ignore_out_of_range=True
)


# ========================================
# 1% np-NaNO3-KNO3
# ========================================
# Valid up to 690K (417C)
# REUSES k AND rho FROM NaNO3-KNO3!!!!

def cp_1npNaNO3_KNO3(T):
    return 1540.4+3.0924E-02*(T-273.15) # Bonk, A., & Bauer, T. (2021). Report on thermo-physical properties of binary NaNO3-KNO3 mixtures in a range of 59-61 wt% NaNO3.

np1NaNO3_KNO3 = Material("1%np-NaNO3-KNO3",
                        k_func = k_NaNO3_KNO3,
                        cp_func = cp_1npNaNO3_KNO3,
                        rho_func = rho_NaNO3_KNO3,
                        valid_range = (573, 690),
                        ignore_out_of_range = True)



# ========================================
# 1% np-SiO2-NaNO3-KNO3
# ========================================
# REUSES k AND rho FROM NaNO3-KNO3!!!!

def cp_1npNaNO3_KNO3(T):
    # Heat capacity (J/kgK), Joohyun 2024
    if T < 593.15:
        return 2.29435E-03*(T-273.15) + 1072.02
    else:
        return 2.23927E-03*(T-273.15) + 819.466

# Material objects
np1NaNO3_KNO3 = Material(
    "1%np-NaNO3-KNO3",
    k_func=k_NaNO3_KNO3,
    cp_func=cp_1npNaNO3_KNO3,
    rho_func=rho_NaNO3_KNO3,
    valid_range=(573, 690),
    ignore_out_of_range=True
)


# ========================================
# Nickel 200
# ========================================
def k_Ni(T):
    if T >= 173 and T < 673:
        return 76.12158+0.02717507*T**1-2.126458E-4*T**2+1.876168E-7*T**3
    elif T >= 673 and T <= 1273:
        return 40.623+0.02201643*T**1-3.571429E-7*T**2
    else:
        return 40.623+0.02201643*T**1-3.571429E-7*T**2 # placeholder
    
def cp_Ni(T):
    if T >= 293 and T < 633:
        return 292.88+0.50208*T**1
    elif T >= 633 and T < 1726:
        return 418.4+0.1284488*T**1
    else:
        return 418.4+0.1284488*T**1 # placeholder
def rho_Ni(T):
    return 8964.214-0.1681755*T**1-3.536041E-4*T**2+2.01714E-7*T**3-4.919056E-11*T**4; # 73 to 1373 K

def alpha_Ni(T):
    if T >= 293 and T < 633:
        return 3.044717E-5-5.149323E-8*T**1+3.129624E-11*T**2
    elif T >= 633 and T < 676:
        return 4.81462E-5-1.036816E-7*T**1+7.54384E-11*T**2
    elif T >= 676 and T <= 1273:
        return 1.087891E-5+2.600264E-9*T**1-2.279477E-13*T**2
    else:
        return 1.087891E-5+2.600264E-9*T**1-2.279477E-13*T**2 # placeholder
            

Nickel200 = Material(
                "Nickel 200", 
                T_points=[473, 1144],
                emissivity_points=[0.35, 0.86], # 0.86 is maximum emissivity of Nickel Oxide found in literature
                k_func=k_Ni, 
                cp_func=cp_Ni,
                rho_func=rho_Ni,
                alpha_func=alpha_Ni,
                valid_range= (293, 1273),
                ignore_out_of_range = True)


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
    "Propylene Glycol",
    k_func=k_PropyleneGlycol,
    cp_func=cp_PropyleneGlycol,
    rho_func=rho_PropyleneGlycol,
    valid_range=(294, 354),
    ignore_out_of_range=True
)


# ========================================
# Stainless Steel 316 (SOLID/POLISHED/OXIDIZED)
# ========================================
# Valid up to 1220 K
def k_Steel316(T):
    if 4 <= T < 9:
        return -0.9611905 + 0.5776587*T - 0.08547619*T**2 + 0.004722222*T**3
    elif 9 <= T < 135:
        return -0.575597 + 0.1484296*T + 1.184549e-5*T**2 - 6.696619e-6*T**3 + 2.25279e-8*T**4
    elif 135 <= T < 1220:
        return 7.956002 + 0.02084122*T - 4.706772e-6*T**2 + 6.271478e-10*T**3 - 1.240772e-12*T**4
    else:
        return 7.956002 + 0.02084122*T - 4.706772e-6*T**2 + 6.271478e-10*T**3 - 1.240772e-12*T**4 # placeholder

def cp_Steel316(T):
    if 4 <= T < 18:
        return 0.363452365 + 0.26377074*T + 0.0493134608*T**2 - 0.0038147097*T**3 + 1.19554913e-4*T**4
    elif 18 <= T < 50:
        return -14.0795868 + 2.9024659*T - 0.153359541*T**2 + 0.004588802*T**3 - 3.66629778e-5*T**4
    elif 50 <= T < 140:
        return -20.5016084 - 0.832746541*T + 0.0955618906*T**2 - 7.74522415e-4*T**3 + 1.944414e-6*T**4
    elif 140 <= T < 300:
        return -75.5829977 + 5.00692586*T - 0.0164947547*T**2 + 2.02748649e-5*T**3
    elif 300 <= T < 1500:
        return 235.650788 + 1.30084242*T - 0.00189052617*T**2 + 1.34841366e-6*T**3 - 3.43379416e-10*T**4
    else:
        return 235.650788 + 1.30084242*T - 0.00189052617*T**2 + 1.34841366e-6*T**3 - 3.43379416e-10*T**4 # placeholder

def rho_Steel316(T):
    if 4 <= T < 114:
        return 8042.496 - 0.01245121*T + 3.834401e-5*T**2 - 7.363868e-6*T**3
    elif 114 <= T < 1273:
        return 8058.746 - 0.1963973*T - 4.830884e-4*T**2 + 4.114383e-7*T**3 - 1.337946e-10*T**4
    else:
        return 8058.746 - 0.1963973*T - 4.830884e-4*T**2 + 4.114383e-7*T**3 - 1.337946e-10*T**4 # placeholder

def emissivity_Steel316(T):
    if T < 660:
        return 0.38
    elif 660 <= T < 1138:
        return 0.0005*T + 0.0569
    else:  # T >= 1138
        return 0.6

Steel316 = Material(
    "Steel 316",
    k_func=k_Steel316,
    cp_func=cp_Steel316,
    rho_func=rho_Steel316,
    emissivity_func=emissivity_Steel316,
    valid_range=(4, 1220),
    ignore_out_of_range=True
)


# ========================================
# Toluene
# ========================================
# Valid up to 360 K
def k_Toluene(T):
    if T >= 230 and T <360:
        return 0.2205 - 3.0e-4*T # 230 to 360 K
    else:
        return 0.2205 - 3.0e-4*T # placeholder
    
def cp_Toluene(T):
    if T >= 179 and T < 505:
        return 1377.31548 + 2.58418568*T - 0.0272810691*T**2 + 9.87628598e-5*T**3 - 1.20802791e-8*T**4 - 3.3656506e-10*T**5 + 3.59255687e-13*T**6
    elif T >= 505 and T < 565:
        return 6310522.18 - 48043.826*T + 137.240472*T**2 - 0.174290378*T**3 + 8.30421074e-5*T**4
    else:
        return 6310522.18 - 48043.826*T + 137.240472*T**2 - 0.174290378*T**3 + 8.30421074e-5*T**4 # placeholder

def rho_Toluene(T):
    if T >= 263 and T < 383:
        return 1065.619 - 0.4713105*T - 7.132867E-4*T**2  # 263 to 383 K
    else:
        return 1065.619 - 0.4713105*T - 7.132867E-4*T**2 # placeholder
    
def alpha_Toluene(T):
    if T >= 263 and T < 383:
        return 1.816021E-7 - 3.457821E-10*T + 1.203682E-13*T**2 # 263 to 360 K
    else:
        return 1.816021E-7 - 3.457821E-10*T + 1.203682E-13*T**2 # placeholder

Toluene = Material("Toluene", k_func=k_Toluene, cp_func=cp_Toluene, rho_func=rho_Toluene, alpha_func=alpha_Toluene, valid_range=(263, 360), ignore_out_of_range=True)


# ========================================
# Water (H2O)
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
# Generate material options dictionary
# ========================================

options = {obj.name: obj for name, obj in vars().items() if isinstance(obj, Material)}