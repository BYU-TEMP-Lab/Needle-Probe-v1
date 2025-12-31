from materials_utils import Material, apply_porosity, thermal_contact_resistance
from materials import options as materials_dict
import math

class Probe:
    def __init__(self, name, geometry, TC_props, heating_wire_props, insulation_props, sheath_props, TCR_insulation_sheath):
        self.name = name
        self.geometry = geometry
        self.TC_props = TC_props
        self.heating_wire_props = heating_wire_props
        self.insulation_props = insulation_props
        self.sheath_props = sheath_props
        self.TCR_insulation_sheath = TCR_insulation_sheath


def generate_INL_probe():
    name = "INL Probe"

    # GEOMETRY =============================================
    geometry = {
        "r_tc": 0.094313e-3,          # Radius of Thermocouple wires
        "r_wires": 0.094313e-3,       # Radius of heating wires
        "r_wir_o": 0.485942e-3,       # radius of outside wires from center of probe
        "r_wir_i": 0.297315e-3,       # radius of inside wires from center of probe
        "r_wir_mid": 0.391629e-3,     # raidus of middle of wires from center of probe
        "TC_loc": 0.05,               # Location of TC Bead w relation to probe tip (5 cm)
        "HW_curve": 4.85942e-4,       # Depth of heating wire curve
        "HW_Ni": 0.002,               # Distance between heating wire tip and inner Ni sheath
        "r_Al": 0.8293e-3,            # Alumina Layer radius (in meters)
        "r_Ni": 1.388e-3,             # Nickel Sheath radius (in meters) 
        "Ni_curve": 0.001,            # Depth of Ni Sheath curved tip
        "samp_probe": -0.001,         # Distance between Sample and Probe tip (negative = BELOW probe tip)
        "r_samp": 0.00207,            # Sample Radius (in meters) (commented out in original)
        "r_cruc": 0.0127,             # Radius of Crucible (in meters)
        "h_max": 0.1,                 # Height of Probe (m)
    }

    # Derived values
    geometry["h_base"] = -0.01 + geometry["samp_probe"]  # Total area below probe (Crucible bottom + separation)
    geometry["vol_wires"] = (
        math.pi * geometry["r_wires"]**2 * (geometry["h_max"]*2) +
        (math.pi**2 * geometry["r_wires"]**2 * geometry["r_wir_mid"])
    )  # Volume of heating wires

    geometry["L"] = (
        geometry["h_max"] -
        (geometry["r_Ni"] - geometry["r_Al"] + geometry["HW_Ni"] + geometry["HW_curve"]) +
        2 * math.pi * geometry["r_wir_mid"]
    )  # Length of wires (Total length - spacing)

    # MATERIALS/THERMAL PROPERTIES ============================
    sheath = materials_dict["Nickel 200"]
    insulation = apply_porosity(materials_dict["Alumina"], porosity_percent=7.38)  # 7.38% porosity
    heating_wires = materials_dict["Chromel"]

    # define thermocouple as average of Chromel and Alumel
    def build_tc_funcs():
        k_chr = materials_dict["Chromel"].k_func
        k_alm = materials_dict["Alumel"].k_func
        cp_chr = materials_dict["Chromel"].cp_func
        cp_alm = materials_dict["Alumel"].cp_func
        rho_alm = materials_dict["Alumel"].rho_func
        rho_chr = materials_dict["Chromel"].rho_func

        def k_func(T):
            return (k_chr+k_alm) / 2
        def rho_func(T):
            return (rho_chr+rho_alm) / 2
        def cp_func(T):
            return (cp_alm*rho_alm + cp_chr*rho_chr) / (rho_alm + rho_chr)
        
        return k_func, rho_func, cp_func
    
    tc_k_func, tc_rho_func, tc_cp_func = build_tc_funcs()

    thermocouple = Material(
        name="TypeK_Thermocouple",
        k_func=tc_k_func,
        rho_func=tc_rho_func,
        cp_func=tc_cp_func,
        valid_range=materials_dict["Chromel"].valid_range,
        ignore_out_of_range=True
        )
    
    # thermal contact resistance between insulation and sheath
    TCR_insulation_sheath = thermal_contact_resistance(insulation.name, sheath.name, ignore_warnings=True)

    return name, geometry, thermocouple, heating_wires, insulation, sheath, TCR_insulation_sheath

INL_probe = Probe(*generate_INL_probe())


########################################################

def generate_BYU_probe_2C_2():
    #### NEEEDS TO BE FILLED OUT STILLL!!!! ######
    name = "BYU Probe 2C.2"

    # GEOMETRY =============================================
    geometry = {
        "r_tc": 0.094313e-3,          # Radius of Thermocouple wires
        "r_wires": 0.094313e-3,       # Radius of heating wires
        "r_wir_o": 0.485942e-3,       # radius of outside wires from center of probe
        "r_wir_i": 0.297315e-3,       # radius of inside wires from center of probe
        "r_wir_mid": 0.391629e-3,     # raidus of middle of wires from center of probe
        "TC_loc": 0.05,               # Location of TC Bead w relation to probe tip (5 cm)
        "HW_curve": 4.85942e-4,       # Depth of heating wire curve
        "HW_Ni": 0.002,               # Distance between heating wire tip and inner Ni sheath
        "r_Al": 0.8293e-3,            # Alumina Layer radius (in meters)
        "r_Ni": 1.388e-3,             # Nickel Sheath radius (in meters) 
        "Ni_curve": 0.001,            # Depth of Ni Sheath curved tip
        "samp_probe": -0.001,         # Distance between Sample and Probe tip (negative = BELOW probe tip)
        "r_samp": 0.00207,            # Sample Radius (in meters) (commented out in original)
        "r_cruc": 0.0127,             # Radius of Crucible (in meters)
        "h_max": 0.1,                 # Height of Probe (m)
    }

    # Derived values
    geometry["h_base"] = -0.01 + geometry["samp_probe"]  # Total area below probe (Crucible bottom + separation)
    geometry["vol_wires"] = (
        math.pi * geometry["r_wires"]**2 * (geometry["h_max"]*2) +
        (math.pi**2 * geometry["r_wires"]**2 * geometry["r_wir_mid"])
    )  # Volume of heating wires

    geometry["L"] = (
        geometry["h_max"] -
        (geometry["r_Ni"] - geometry["r_Al"] + geometry["HW_Ni"] + geometry["HW_curve"]) +
        2 * math.pi * geometry["r_wir_mid"]
    )  # Length of wires (Total length - spacing)

    # MATERIALS/THERMAL PROPERTIES ============================
    sheath = materials_dict["Nickel 200"]
    insulation = apply_porosity(materials_dict["Alumina"], porosity_percent=7.38)  # 7.38% porosity
    heating_wires = materials_dict["Chromel"]

    # define thermocouple as average of Chromel and Alumel
    def build_tc_funcs():
        k_chr = materials_dict["Chromel"].k_func
        k_alm = materials_dict["Alumel"].k_func
        cp_chr = materials_dict["Chromel"].cp_func
        cp_alm = materials_dict["Alumel"].cp_func
        rho_alm = materials_dict["Alumel"].rho_func
        rho_chr = materials_dict["Chromel"].rho_func

        def k_func(T):
            return (k_chr+k_alm) / 2
        def rho_func(T):
            return (rho_chr+rho_alm) / 2
        def cp_func(T):
            return (cp_alm*rho_alm + cp_chr*rho_chr) / (rho_alm + rho_chr)
        
        return k_func, rho_func, cp_func
    
    tc_k_func, tc_rho_func, tc_cp_func = build_tc_funcs()

    thermocouple = Material(
        name="TypeK_Thermocouple",
        k_func=tc_k_func,
        rho_func=tc_rho_func,
        cp_func=tc_cp_func,
        valid_range=materials_dict["Chromel"].valid_range,
        ignore_out_of_range=True
        )
    
    # thermal contact resistance between insulation and sheath
    TCR_insulation_sheath = thermal_contact_resistance(insulation.name, sheath.name, ignore_warnings=True)

    return name, geometry, thermocouple, heating_wires, insulation, sheath, TCR_insulation_sheath

BYU_probe_2C_2 = Probe(*generate_BYU_probe_2C_2())


########################################################
# Generate probes options dictionary
########################################################

options = {obj.name: obj for name, obj in vars().items() if isinstance(obj, Probe)}