from .materials_utils import Material, apply_porosity, thermal_contact_resistance
from .materials import options as materials_dict
from salt_probe_util.optimizer import OptimParam
from salt_probe_util.thermal_quadrupoles_model import TQProbe
import math

class Probe:
    def __init__(self, name: str, outer_material: str, sensing_OD: float, TQ_params: TQProbe = None):
        """
        Parameters
        ----------
        name : str
            Name of the probe.
        outer_material : str
            Outer material of the probe sheath (for comaptability with crucibles)
        sensing_OD : float
            Outer diameter of the probe sensing region (in meters).
        model_params : dict
            Dictionary containing parameters for the valid simulation models.
        """
        self.name = name
        self.outer_material = outer_material
        self.sensing_OD = sensing_OD
        self.TQ_params = TQ_params

def get_lumped_properties(tc_material1: Material, 
                          tc_material2: Material, 
                          heating_wire_material: Material, 
                          insulation_material: Material,
                          tc1_volume: float,
                          tc2_volume: float,
                          heating_wire_volume: float,
                          insulation_volume: float):
    """
    Calculate the lumped properties of material within wire region radius, based on volume-weights
    """
    total_volume = tc1_volume + tc2_volume + heating_wire_volume + insulation_volume
    
    def volume_weighted_average(property_name: str):
        return (getattr(tc_material1, property_name) * tc1_volume +
                getattr(tc_material2, property_name) * tc2_volume +
                getattr(heating_wire_material, property_name) * heating_wire_volume +
                getattr(insulation_material, property_name) * insulation_volume) / total_volume
    
    k_eff = volume_weighted_average('k')
    alpha_eff = volume_weighted_average('alpha')

    return k_eff, alpha_eff

# =========================================================
# Probe Definitions
# =========================================================

def generate_INL_probe():
    name = "INL Probe"

    # all units SI
    # GEOMETRY =============================================
    # Note that I just made up bounds and prior sigmas 1/8/25
    L = OptimParam(0.1, (0.09, 0.11), 0.005) # length of probe sensing region (m)
    TC_loc = L.current_value/2 # location of thermocouple bead with respect to probe tip (m)
    r_tc_wire1 = 0.094313e-3 # radius of individual thermocouple wire 1 in sensing region
    r_tc_wire2 = r_tc_wire1 # radius of individual thermocouple wire 2 in sensing region
    r_heating_wire = r_tc_wire1 # radius of individual heating wire in sensing region
    r_wire_region_outer = OptimParam(0.485942e-3, (0.48e-3, 0.49e-3), 0.005e-3) # radius of outer edge of wire region from center of probe
    r_wire_region_inner = OptimParam(0.297315e-3, (0.29e-3, 0.30e-3), 0.005e-3) # radius of inner edge of wire region from center of probe
    r_wire_region_mid = r_wire_region_inner.current_value + (r_wire_region_outer.current_value - r_wire_region_inner.current_value)/2 # radius of middle of wire region from center of probe
    r_hw_curve = 4.85942e-4    # Depth of heating wire curve
    dist_tip_HW = 0.002 # Distance between heating wire tip and inner Ni sheath
    r_insulation = OptimParam(0.8293e-3, (r_wire_region_outer.current_value, 0.85e-3), 0.1e-3)
    r_sheath = OptimParam(1.388e-3, (r_insulation.current_value, 1.42e-3), 0.1e-3)
    r_sheath_curve = 0.001 # Depth of Ni Sheath curved tip


    # MATERIALS/THERMAL PROPERTIES ============================
    thermocouple_material = materials_dict["Type K Thermocouple"]
    sheath_material = materials_dict["Nickel 200"]
    insulation_material = apply_porosity(materials_dict["Alumina"], porosity_percent=7.38)  # 7.38% porosity
    heating_wire_material = materials_dict["Chromel"]

    # thermal contact resistance between insulation and sheath
    TCR_insulation_sheath = thermal_contact_resistance(insulation_material.name, sheath_material.name, ignore_warnings=True)

    # generate model parameters dictionary


    return name, sheath_material.name, 2*r_Ni.initial_value, model_dict

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