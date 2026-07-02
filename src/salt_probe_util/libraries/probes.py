from .materials_utils import Material, apply_porosity, thermal_contact_resistance
from .materials import options as materials_dict
from salt_probe_util.optimizer import OptimParam
import math

class Probe:
    def __init__(self, name: str, outer_material: str, sensing_diameter: float, model_params: dict):
        """
        Parameters
        ----------
        name : str
            Name of the probe.
        outer_material : str
            Outer material of the probe sheath (for comaptability with crucibles)
        sensing_diameter : float
            Diameter of the probe sensing region (in meters).
        model_params : dict
            Dictionary containing parameters for the valid simulation models.
        """
        self.name = name
        self.outer_material = outer_material
        self.sensing_diameter = sensing_diameter
        self.model_params = model_params

# define type k thermocouple as average of Chromel and Alumel
def build_type_k_tc_material():
    name = "TypeK_Thermocouple"

    # get the thermal properties of Chromel and Alumel
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
        return (cp_alm(T) * rho_alm(T) + cp_chr(T) * rho_chr(T)) / (rho_alm(T) + rho_chr(T))
    
    # valid range is the intersection of the valid ranges of Chromel and Alumel
    valid_range = (
        max(materials_dict["Chromel"].valid_range[0], materials_dict["Alumel"].valid_range[0]),
        min(materials_dict["Chromel"].valid_range[1], materials_dict["Alumel"].valid_range[1])
    )

    ignore_out_of_range = True  # allow extrapolation outside of valid range

    return name, k_func, rho_func, cp_func, valid_range, ignore_out_of_range

# generate thermocouple material (average of two materials)
name, k_func, rho_func, cp_func, valid_range, ignore_out_of_range = build_type_k_tc_material()
type_k_thermocouple = Material(name,
                               valid_range=valid_range,
                               ignore_out_of_range=ignore_out_of_range,
                               k_func=k_func,
                               rho_func=rho_func,
                               cp_func=cp_func)

# =========================================================
# Probe Definitions
# =========================================================

def generate_INL_probe():
    name = "INL Probe"

    # GEOMETRY =============================================
    # Note that I just made up bounds and prior sigmas 1/8/25
    r_tc = OptimParam(0.094313e-3, (0.09e-3, 0.1e-3), 0.005e-3)  # Radius of Thermocouple wires
    r_wires = OptimParam(0.094313e-3, (0.09e-3, 0.1e-3), 0.005e-3)     # Radius of heating wires
    r_wir_o = OptimParam(0.485942e-3, (0.48e-3, 0.49e-3), 0.005e-3)       # radius of outside wires from center of probe
    r_wir_i = OptimParam(0.297315e-3, (0.29e-3, 0.30e-3), 0.005e-3)      # radius of inside wires from center of probe
    r_wir_mid = OptimParam(0.391629e-3, (0.38e-3, 0.40e-3), 0.005e-3)    # radius of middle of wires from center of probe
    TC_loc = OptimParam(0.05, (0.045, 0.055), 0.002)                     # Location of TC Bead w relation to probe tip (5 cm)
    HW_curve = OptimParam(4.85942e-4, (4.5e-4, 5.2e-4), 0.5e-4)       # Depth of heating wire curve
    HW_Ni = OptimParam(0.002, (0.0015, 0.0025), 0.0005)               # Distance between heating wire tip and inner Ni sheath
    r_Al = OptimParam(0.8293e-3, (0.8e-3, 0.85e-3), 0.1e-3)            # Alumina Layer radius (in meters)
    r_Ni = OptimParam(1.388e-3, (1.35e-3, 1.42e-3), 0.1e-3)             # Nickel Sheath radius (in meters)
    Ni_curve = OptimParam(0.001, (0.0005, 0.0015), 0.00025)              # Depth of Ni Sheath curved tip
    samp_probe = OptimParam(-0.001, (-0.01, 0), 0.001)         # Distance between Sample and Probe tip (negative = BELOW probe tip)
    r_samp = OptimParam(0.00207, (0.002, 0.01), 1e-4)            # Sample Radius (in meters) (commented out in original)
    h_max = OptimParam(0.1, (9e-2, 1e-1), 5e-3)                 # Height of Probe (m)

    # Derived values
    h_base = OptimParam(
        initial_value=-0.01 + samp_probe.initial_value,
        bounds=(-0.02, 0),
        prior_sigma=0.001
    )    # total area below probe (Crucible bottom + separation)
    vol_wires = OptimParam(
        initial_value=math.pi * r_wires.initial_value**2 * (h_max.initial_value*2) +
                         (math.pi**2 * r_wires.initial_value**2 * r_wir_mid.initial_value),
        bounds=(0, 1e-3),
        prior_sigma=1e-4
    )  # Volume of heating wires

    L = OptimParam(
        initial_value=(
            h_max.initial_value -
            (r_Ni.initial_value - r_Al.initial_value + HW_Ni.initial_value + HW_curve.initial_value) +
            2 * math.pi * r_wir_mid.initial_value
        ),
        bounds=(0, 1e-1),
        prior_sigma=5e-3
    )

    # MATERIALS/THERMAL PROPERTIES ============================
    thermocouple = type_k_thermocouple
    sheath = materials_dict["Nickel 200"]
    insulation = apply_porosity(materials_dict["Alumina"], porosity_percent=7.38)  # 7.38% porosity
    heating_wires = materials_dict["Chromel"]

    # thermal contact resistance between insulation and sheath
    TCR_insulation_sheath = thermal_contact_resistance(insulation.name, sheath.name, ignore_warnings=True)

    # generate model parameters dictionary


    return name, sheath.name, 2*r_Ni.initial_value, model_dict

INL_probe = Probe(*generate_INL_probe())

########################################################

def generate_BYU_probe_2C_2():
    #### NEEEDS TO BE FILLED OUT STILLL!!!! ######
    name = "??? BYU Probe 2C.2"

    # GEOMETRY =============================================
    # Note that I just made up bounds and prior sigmas 1/8/25
    r_tc = OptimParam(0.094313e-3, (0.09e-3, 0.1e-3), 0.005e-3)  # Radius of Thermocouple wires
    r_wires = OptimParam(0.094313e-3, (0.09e-3, 0.1e-3), 0.005e-3)     # Radius of heating wires
    r_wir_o = OptimParam(0.485942e-3, (0.48e-3, 0.49e-3), 0.005e-3)       # radius of outside wires from center of probe
    r_wir_i = OptimParam(0.297315e-3, (0.29e-3, 0.30e-3), 0.005e-3)      # radius of inside wires from center of probe
    r_wir_mid = OptimParam(0.391629e-3, (0.38e-3, 0.40e-3), 0.005e-3)    # raidus of middle of wires from center of probe
    TC_loc = OptimParam(0.05, (0.045, 0.055), 0.002)                     # Location of TC Bead w relation to probe tip (5 cm)
    HW_curve = OptimParam(4.85942e-4, (4.5e-4, 5.2e-4), 0.5e-4)       # Depth of heating wire curve
    HW_sheath = OptimParam(0.002, (0.0015, 0.0025), 0.0005)               # Distance between heating wire tip and inner Ni sheath
    r_insulation = OptimParam(2.159e-3/2, ((2.159-0.0508)*1e-3/2, (2.159+0.0508)*1e-3/2), 0.1e-3)            # Insulation Layer radius (in meters)
    r_sheath = OptimParam(2.7686e-3 / 2, ((2.7686-0.0254)*1e-3 / 2, (2.7686+0.0254)*1e-3 / 2), 0.1e-3)             # Sheath radius (in meters)
    h_point = OptimParam(0.005, (0.004, 0.006), 0.00025)            # Depth of Sheath pointed tip
    h_max = OptimParam(143e-3, (140e-3, 145e-3), 2e-3)                 # Height of sensing region of Probe (m)

    # Derived values
    # geometry["h_base"] = {
    #     "initial_value": -0.01 + geometry["samp_probe"]["initial_value"],  # Total area below probe (Crucible bottom + separation)
    #     "bounds": (-0.02, 0),
    #     "prior_sigma": 0.001
    # } # total area below probe (Crucible bottom + separation)
    vol_wires = OptimParam(
        initial_value=math.pi * r_wires.initial_value**2 * (h_max.initial_value*2) +
                         (math.pi**2 * r_wires.initial_value**2 * r_wir_mid.initial_value),
        bounds=(0, 1e-3),
        prior_sigma=1e-4
    )  # Volume of heating wires
    L = OptimParam(
        initial_value=(
            h_max.initial_value -
            (r_sheath.initial_value - r_insulation.initial_value + HW_sheath.initial_value + HW_curve.initial_value) +
            2 * math.pi * r_wir_mid.initial_value),
        bounds = (0, 1e-1),
        prior_sigma = 5e-3
    ) # length of wires (Total length - spacing)

    # MATERIALS/THERMAL PROPERTIES ============================
    sheath = materials_dict["Nickel 200"]
    insulation = apply_porosity(materials_dict["Alumina"], porosity_percent=7.38)  # 7.38% porosity
    heating_wires = materials_dict["Chromel"]
    thermocouple = type_k_thermocouple
    
    # thermal contact resistance between insulation and sheath
    TCR_insulation_sheath = thermal_contact_resistance(insulation.name, sheath.name, ignore_warnings=True)

    return name, geometry, thermocouple, heating_wires, insulation, sheath, TCR_insulation_sheath

BYU_probe_2C_2 = Probe(*generate_BYU_probe_2C_2())


########################################################
# Generate probes options dictionary
########################################################

options = {obj.name: obj for name, obj in vars().items() if isinstance(obj, Probe)}