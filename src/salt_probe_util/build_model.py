from .optimizer import build_optim_vectors

# mapping of model parameter names to their source paths in file data or user selections
model_param_map = {
        "Ambient Temperature": ("file_data", "avgT_amb_K"), # K
        "Power": ("file_data", "avgQ"), # W

        "Thermocouple k": ("user_input", "probe", "TC_props", "k"), # W/(m*k)
        "Thermocouple rho": ("user_input", "probe", "TC_props", "rho"), # kg/m^3
        "Thermocouple cp": ("user_input", "probe", "TC_props", "cp"), #J/(kg*K)

        "Wire k": ("user_input", "probe", "heating_wire_props", "k"), 
        "Wire rho": ("user_input", "probe", "heating_wire_props", "rho"), # kg/m^3
        "Wire cp": ("user_input", "probe", "heating_wire_props", "cp"), # J/(kg*K)

        "Insulation k": ("user_input", "probe", "insulation_props", "k"), # W/(m*K)
        "Insulation rho": ("user_input", "probe", "insulation_props", "rho"), # kg/m^3
        "Insulation cp": ("user_input", "probe", "insulation_props", "cp"), # J/(kg*K)

        "Sheath k": ("user_input", "probe", "sheath_props", "k"), # W/(m*K)
        "Sheath rho": ("user_input", "probe", "sheath_props", "rho"), # kg/m^3
        "Sheath cp": ("user_input", "probe", "sheath_props", "cp"), # J/(kg*K)
        "Sheath Emissivity": ("user_input", "probe", "sheath_props", "emissivity"), # unitless

        "Probe Geometry": ("user_input", "probe", "geometry"), # dict of probe geometry parameters since it's more complex
        
        "Crucible k": ("user_input", "crucible", "material", "k"), # W/(m*K)
        "Crucible rho": ("user_input", "crucible", "material", "rho"), # kg/m^3
        "Crucible cp": ("user_input", "crucible", "material", "cp"), # J/(kg*K)
        "Crucible Emissivity ": ("user_input", "crucible", "material", "emissivity"),
        "Crucible inner radius": ("user_input", "crucible", "inner_radius"), # m
        "Crucible hole depth": ("user_input", "crucible", "hole_depth"), # m
        
        "Sample k": ("user_input", "sample", "k"),
        "Sample rho": ("user_input", "sample", "rho"),
        "Sample cp": ("user_input", "sample", "cp"),
        
        "Thermal Contact Resistance Sheath-Insulation": ("user_input", "probe", "TCR_insulation_sheath"), # K/W
        "??? Thermal Contact Resistance Sheath-Sample": 1, 

        "??? Scatter": 1, # unitless
        "??? Flux Decay": 1,
        "??? Decay Point": 1,
        "Convection Coefficient": ("user_input", "convection_coeff"), # W/(m^2*K)

        "filepath": ("file_data", "filepath")
    }


def resolve_params_at_T(file_data, user_selections):
    T_amb = file_data["avgT_amb_K"]["initial_value"]
    print(f"# Resolving parameters for file {file_data['filepath'].name} at T_amb = {T_amb} K...")

    # update all material properties at ambient temperature
    user_selections.probe.TC_props.update_properties_at_T(T_amb)
    user_selections.probe.heating_wire_props.update_properties_at_T(T_amb)
    user_selections.probe.insulation_props.update_properties_at_T(T_amb)
    user_selections.probe.sheath_props.update_properties_at_T(T_amb)
    user_selections.crucible.material.update_properties_at_T(T_amb)
    user_selections.sample.update_properties_at_T(T_amb)

    # initialize prepared data dictionary
    resolved_params = {}

    #dynamically set initial values, bounds, prior sigmas from model_param_map
    for key, path in model_param_map.items():
        # handle hardcoded values
        if not isinstance(path, tuple):
            resolved_params[key] = {
                "initial_value": path,
                "bounds": (path * 0.5, path * 1.5), # Default 50% swing
                "prior_sigma": path * 0.2           # Default 20% uncertainty
            }
            continue

        if isinstance(path, dict):
            resolved_params[key] = path
            continue
        
        # determine root source (folder_data or user_input)
        source_root = path[0]
        attr_path = path[1:]

        # navigate the path
        current_obj = user_selections if source_root == "user_input" else file_data

        try:
            for attr in attr_path:
                # If current_obj is a dict, use get(); if object, use getattr()
                if isinstance(current_obj, dict):
                    current_obj = current_obj[attr]
                else:
                    current_obj = getattr(current_obj, attr)

            # Now current_obj should be the dict: {"initial_value": x, "bounds": y, ...}
            # OR numeric value
            # OR probe dictionary (for geometry)
            if isinstance(current_obj, dict):
                resolved_params[key] = current_obj.copy()
            elif isinstance(current_obj, (float, int)):
                val = float(current_obj)
                # DEFAULT BOUNDS AND PRIOR SIGMA (can be customized later)
                resolved_params[key] = {
                    "initial_value": val,
                    "bounds": (val * 0.5, val * 1.5),
                    "prior_sigma": val * 0.2
                }
            else:
                # Handle cases where the path led to an object instead of a value
                print(f"Warning: Could not resolve {key} to a numeric value.")
                
        except (KeyError, AttributeError):
            print(f"Warning: Could not resolve path for {key}")

    # Append probe geometry parameters individually (different geometry for different probes/models)
    for key, value in resolved_params["Probe Geometry"].items():
        resolved_params[key] = value

    del resolved_params["Probe Geometry"]  # remove the composite entry

    # build optimization vectors
    optim_vecs = build_optim_vectors(resolved_params, user_selections)

    # flatten resolved params
    for key, value, in resolved_params.items():
        if "initial_value" in value:
            resolved_params[key] = value["initial_value"]

    return resolved_params, optim_vecs