decision_var_options = {
        "Thermocouple k": 1, # W/(m*k)
        "Thermocouple rho": 1, # kg/m^3
        "Thermocouple cp": 1, #j/(kg*K)

        "Wire k": 1, 
        "Wire rho": 1,
        "Wire cp": 1,

        "Insulation k": 1,
        "Insulation rho": 1,
        "Insulation cp": 1,
        "Porosity Insulation": 1, # unitless (ratio)

        "Sheath k": 1,
        "Sheath rho": 1,
        "Sheath cp": 1,
        "Emissivity Sheath": 1, # unitless

        "Crucible k": 1,
        "Crucible rho": 1,
        "Crucible cp": 1,
        "Emissivity Crucible": 1,

        "Sample k": 1,
        "Sample rho": 1,
        "Sample cp": 1,
        "Sample radius": 1, # m

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