from materials import options as material_options
from materials_utils import Material
import warnings

class Crucible:
    def __init__(self, name, description, inner_radius, outer_radius, hole_depth, height, indent_height, material: Material, ignore_warnings=False):
        self.name = name
        self.description = description
        self.inner_radius = inner_radius  # in meters
        self.outer_radius = outer_radius  # in meters
        self.hole_depth = hole_depth      # in meters
        self.height = height              # in meters
        self.indent_height = indent_height  # in meters
        self.material = material  # Material object

        if self.material.emissivity_func is None and not ignore_warnings:
            msg = f"\nEmissivity function not defined for material {self.material.name} for crucible {self.name}. \nDefault to 0.5. Radiative heat transfer calculations may be inaccurate."
            warnings.warn(msg)


# ========================================
# Define crucible objects
# ========================================

# The data from 0-7 came from the document "Crucible Dimensions.xlsx" on the box. 
# 0 is the theoretical. 
# No idea what the names mean
# The materials are unknown as of 1/2/26

crucible_0 = Crucible(
    name = "0 (Theoretical)",
    description = "Thesis", 
    inner_radius = 3.97e-3,
    outer_radius = 25.5e-3,
    hole_depth = 110e-3,
    height = 153.4e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_1 = Crucible(
    name = "1 (???)",
    description = "Shiny TriSTripe",
    inner_radius = 4.3e-3,
    outer_radius = 25.47e-3,
    hole_depth = 115.12e-3,
    height = 127.3e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_2 = Crucible(
    name = "2 (???)",
    description = "Dull Goldtop (Teeth)",
    inner_radius = 4.18e-3,
    outer_radius = 25.48e-3,
    hole_depth = 98.42e-3,
    height = 127.18e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_3 = Crucible(
    name = "3 (???)",
    description = "Shiny Greenspecks",
    inner_radius = 4.05e-3,
    outer_radius = 25.59e-3,
    hole_depth = 115.23e-3,
    height = 126.92e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_4 = Crucible(
    name = "4 (???)",
    description = "Dark Grey, Striped",
    inner_radius = 4.12e-3,
    outer_radius = 25.57e-3,
    hole_depth = 115.11e-3,
    height = 127.17e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_5 = Crucible(
    name = "5 (???)",
    description = "Dull Greytop",
    inner_radius = 4.11e-3,
    outer_radius = 25.54e-3,
    hole_depth = 114.78e-3,
    height = 126.88e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_6 = Crucible(
    name = "6 (???)",
    description = "Gold Shiny",
    inner_radius = 4.2e-3,
    outer_radius = 25.35e-3,
    hole_depth = 102.96e-3,
    height = 124.64e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)

crucible_7 = Crucible(
    name = "7 (???)",
    description = "Cutaway",
    inner_radius = 4.16e-3,
    outer_radius = 25.36e-3,
    hole_depth = 117.41e-3,
    height = 127.17e-3,
    indent_height = 0,
    material = material_options["Nickel 200"]
)


# =======================================
# Generate crucible options dictionary
# =======================================

options = {obj.name: obj for name, obj in vars().items() if isinstance(obj, Crucible)}