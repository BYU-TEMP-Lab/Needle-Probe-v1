from materials import options as material_options
from materials_utils import Material
import warnings

class Crucible:
    def __init__(self, id, description, inner_radius, outer_radius, hole_depth, height, indent_height, material: Material):
        self.id = id
        self.description = description
        self.inner_radius = inner_radius  # in meters
        self.outer_radius = outer_radius  # in meters
        self.hole_depth = hole_depth      # in meters
        self.height = height              # in meters
        self.indent_height = indent_height  # in meters
        self.material = material  # Material object

        if self.material.emissivity_func is None:
            msg = f"Emissivity function not defined for crucible material {self.material.name}. Radiative heat transfer calculations may be inaccurate."
            warnings.warn(msg)

# ========================================

crucible_10 = Crucible(
    id = "10",
    description = "10 mm ID, 12.7 mm OD, 25.4 mm Height Alumina Crucible",
    inner_radius = 0.0050,
    outer_radius = 0.00635,
    hole_depth = 0.0254,
    height = 0.0254,
    indent_height = 0.0025,
    material = material_options["Alumina"]
)

# =======================================
# Generate crucible options dictionary
# =======================================

options = {obj.id: obj for name, obj in vars().items() if isinstance(obj, Crucible)}