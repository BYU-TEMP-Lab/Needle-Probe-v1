from ..flexPDE_model import run as run_flex_model
from ..thermal_quadrupoles_model import run as run_therm_quad_model

simulation_options_dict = {"FlexPDE": run_flex_model, "Thermal Quadrupoles": run_therm_quad_model}
cross_section_options_dict = {"Axial": None, "Radial": None}