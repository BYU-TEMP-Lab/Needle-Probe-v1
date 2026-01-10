from .materials_utils import Material, apply_porosity, thermal_contact_resistance
from .materials import options as materials_dict
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
    # Note that I just made up bounds and prior sigmas 1/8/25
    geometry = {
        "r_tc": {                     
            "initial_value": 0.094313e-3, # Radius of Thermocouple wires
            "bounds": (0.09e-3, 0.1e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wires": {
            "initial_value": 0.094313e-3,       # Radius of heating wires
            "bounds": (0.09e-3, 0.1e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_o": {
            "initial_value": 0.485942e-3,       # radius of outside wires from center of probe
            "bounds": (0.48e-3, 0.49e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_i": {
            "initial_value": 0.297315e-3,       # radius of inside wires from center of probe
            "bounds": (0.29e-3, 0.30e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_mid": {
            "initial_value": 0.391629e-3,     # raidus of middle of wires from center of probe
            "bounds": (0.38e-3, 0.40e-3),
            "prior_sigma": 0.005e-3
        },
        "TC_loc": {
            "initial_value": 0.05,               # Location of TC Bead w relation to probe tip (5 cm)
            "bounds": (0.045, 0.055),
            "prior_sigma": 0.002
        },
        "HW_curve": {
            "initial_value": 4.85942e-4,       # Depth of heating wire curve
            "bounds": (4.5e-4, 5.2e-4),
            "prior_sigma": 0.5e-4
        },
        "HW_Ni": {
            "initial_value": 0.002,               # Distance between heating wire tip and inner Ni sheath
            "bounds": (0.0015, 0.0025),
            "prior_sigma": 0.0005
        },
        "r_Al": {
            "initial_value": 0.8293e-3,            # Alumina Layer radius (in meters)
            "bounds": (0.8e-3, 0.85e-3),
            "prior_sigma": 0.1e-3
        },
        "r_Ni": {
            "initial_value": 1.388e-3,             # Nickel Sheath radius (in meters) 
            "bounds": (1.35e-3, 1.42e-3),
            "prior_sigma": 0.1e-3
        },
        "Ni_curve": {
            "initial_value": 0.001,            # Depth of Ni Sheath curved tip
            "bounds": (0.0005, 0.0015),
            "prior_sigma": 0.00025
        },
        "samp_probe": {
            "initial_value": -0.001,         # Distance between Sample and Probe tip (negative = BELOW probe tip)
            "bounds": (-0.01, 0),
            "prior_sigma": 0.001
        },
        "r_samp": {
            "initial_value": 0.00207,            # Sample Radius (in meters) (commented out in original)
            "bounds": (0.002, 0.01),
            "prior_sigma": 1e-4
        },
        "h_max": {
            "initial_value": 0.1,                 # Height of Probe (m)
            "bounds": (9e-2, 1e-1),
            "prior_sigma": 5e-3
        }
    }

    # Derived values
    geometry["h_base"] = {
        "initial_value": -0.01 + geometry["samp_probe"]["initial_value"],  # Total area below probe (Crucible bottom + separation)
        "bounds": (-0.02, 0),
        "prior_sigma": 0.001
    } # total area below probe (Crucible bottom + separation)
    geometry["vol_wires"] = {
        "initial_value": math.pi * geometry["r_wires"]["initial_value"]**2 * (geometry["h_max"]["initial_value"]*2) +
                         (math.pi**2 * geometry["r_wires"]["initial_value"]**2 * geometry["r_wir_mid"]["initial_value"]),
        "bounds": (0, 1e-3),
        "prior_sigma": 1e-4
    }  # Volume of heating wires

    geometry["L"] = {
        "initial_value": (
        geometry["h_max"]["initial_value"] -
        (geometry["r_Ni"]["initial_value"] - geometry["r_Al"]["initial_value"] + geometry["HW_Ni"]["initial_value"] + geometry["HW_curve"]["initial_value"]) +
        2 * math.pi * geometry["r_wir_mid"]["initial_value"]
        ),  # Length of wires (Total length - spacing)
        "bounds": (0, 1e-1),
        "prior_sigma": 5e-3
    }

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
        
        return {"k_func": k_func, "rho_func": rho_func, "cp_func": cp_func}
    
    # generate thermocouple material (average of two materials)
    tc_dict = build_tc_funcs()

    thermocouple = Material(
        name="TypeK_Thermocouple",
        k_func=tc_dict["k_func"],
        rho_func=tc_dict["rho_func"],
        cp_func=tc_dict["cp_func"],
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
    name = "??? BYU Probe 2C.2"

    # GEOMETRY =============================================
    # GEOMETRY =============================================
    # Note that I just made up bounds and prior sigmas 1/8/25
    geometry = {
        "r_tc": {                     
            "initial_value": 0.094313e-3, # Radius of Thermocouple wires
            "bounds": (0.09e-3, 0.1e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wires": {
            "initial_value": 0.094313e-3,       # Radius of heating wires
            "bounds": (0.09e-3, 0.1e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_o": {
            "initial_value": 0.485942e-3,       # radius of outside wires from center of probe
            "bounds": (0.48e-3, 0.49e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_i": {
            "initial_value": 0.297315e-3,       # radius of inside wires from center of probe
            "bounds": (0.29e-3, 0.30e-3),
            "prior_sigma": 0.005e-3
        },
        "r_wir_mid": {
            "initial_value": 0.391629e-3,     # raidus of middle of wires from center of probe
            "bounds": (0.38e-3, 0.40e-3),
            "prior_sigma": 0.005e-3
        },
        "TC_loc": {
            "initial_value": 0.05,               # Location of TC Bead w relation to probe tip (5 cm)
            "bounds": (0.045, 0.055),
            "prior_sigma": 0.002
        },
        "HW_curve": {
            "initial_value": 4.85942e-4,       # Depth of heating wire curve
            "bounds": (4.5e-4, 5.2e-4),
            "prior_sigma": 0.5e-4
        },
        "HW_sheath": {
            "initial_value": 0.002,               # Distance between heating wire tip and inner Ni sheath
            "bounds": (0.0015, 0.0025),
            "prior_sigma": 0.0005
        },
        "r_insulation": {
            "initial_value": 2.159e-3/2,            # Insulation Layer radius (in meters)
            "bounds": ((2.159-0.0508)*1e-3/2, (2.159+0.0508)*1e-3/2),
            "prior_sigma": 0.1e-3
        },
        "r_sheath": {
            "initial_value": 2.7686e-3 / 2,             # Sheath radius (in meters) 
            "bounds": ((2.7686-0.0254)*1e-3 / 2, (2.7686+0.0254)*1e-3 / 2),
            "prior_sigma": 0.1e-3
        },
        "h_point": {
            "initial_value":0.005,            # Depth of Sheath pointed tip
            "bounds": (0.004, 0.006),
            "prior_sigma": 0.00025
        },
        "h_max": {
            "initial_value": 143e-3,                 # Height of sensing region of Probe (m)
            "bounds": (140e-3, 145e-3),
            "prior_sigma": 2e-3
        }
    }

    # Derived values
    # geometry["h_base"] = {
    #     "initial_value": -0.01 + geometry["samp_probe"]["initial_value"],  # Total area below probe (Crucible bottom + separation)
    #     "bounds": (-0.02, 0),
    #     "prior_sigma": 0.001
    # } # total area below probe (Crucible bottom + separation)
    geometry["vol_wires"] = {
        "initial_value": math.pi * geometry["r_wires"]["initial_value"]**2 * (geometry["h_max"]["initial_value"]*2) +
                         (math.pi**2 * geometry["r_wires"]["initial_value"]**2 * geometry["r_wir_mid"]["initial_value"]),
        "bounds": (0, 1e-3),
        "prior_sigma": 1e-4
    }  # Volume of heating wires

    geometry["L"] = {
        "initial_value": (
        geometry["h_max"]["initial_value"] -
        (geometry["r_sheath"]["initial_value"] - geometry["r_insulation"]["initial_value"] + geometry["HW_sheath"]["initial_value"] + geometry["HW_curve"]["initial_value"]) +
        2 * math.pi * geometry["r_wir_mid"]["initial_value"]
        ),  # Length of wires (Total length - spacing)
        "bounds": (0, 1e-1),
        "prior_sigma": 5e-3
    }

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
            return (k_chr(T) + k_alm(T)) / 2
        def rho_func(T):
            return (rho_chr(T) + rho_alm(T)) / 2
        def cp_func(T):
            return (cp_alm(T)*rho_alm(T) + cp_chr(T)*rho_chr(T)) / (rho_alm(T) + rho_chr(T))
        
        return {"k_func": k_func, "rho_func": rho_func, "cp_func": cp_func}
    
    # generate thermocouple material (average of two materials)
    tc_dict = build_tc_funcs()

    max_temp = min(materials_dict["Chromel"].valid_range[1], materials_dict["Alumel"].valid_range[1])
    min_temp = max(materials_dict["Chromel"].valid_range[0], materials_dict["Alumel"].valid_range[0])

    thermocouple = Material(
        name="TypeK_Thermocouple",
        k_func=tc_dict["k_func"],
        rho_func=tc_dict["rho_func"],
        cp_func=tc_dict["cp_func"],
        valid_range=(min_temp, max_temp),
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