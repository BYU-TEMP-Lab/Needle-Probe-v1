import probes

decision_var_options = {
        "k Thermocouple": 1, # W/(m*k)
        "rho Thermocouple": 1, # kg/m^3
        "cp Thermocouple": 1, #j/(kg*K)

        "k Wire": 1, 
        "rho Wire": 1,
        "cp Wire": 1,

        "k Insulation": 1,
        "rho Insulation": 1,
        "cp Insulation": 1,
        "Porosity Insulation": 1, # unitless (ratio)

        "k Sheath": 1,
        "rho Sheath": 1,
        "cp Sheath": 1,
        "Emissivity Sheath": 1, # unitless

        "k Crucible": 1,
        "rho Crucible": 1,
        "cp Crucible": 1,
        "Emissivity Crucible": 1,

        "k Sample": 1,
        "rho Sample": 1,
        "cp Sample": 1,
        "radius Sample": 1, # m

        "Thermal Contact Resistance Sheath-Insulation": 1, # K/W
        "Thermal Contact Resistance Sheath-Sample": 1,

        "Ambient Temperature": 1, # K
        "Scatter": 1, # unitless
        "Flux Decay": 1,
        "Decay Point": 1,
        "Convection": 1, # W/(m^2*K)
        "Power": 1 # W
    }

def build_decision_vars():
    return

if __name__ == "__main__":
    build_decision_vars()