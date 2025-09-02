import materials
from materials import Material, apply_porosity, thermal_contact_resistance
import math

materials_dict = {name: obj for name, obj in vars(materials).items() if isinstance(obj, Material)}

def generate_Nickel200_crucible1():
    
    crucible = materials_dict["Nickel200"]
