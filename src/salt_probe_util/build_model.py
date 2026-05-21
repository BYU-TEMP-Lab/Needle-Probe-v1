from .optimizer import build_optim_vectors


# UI-facing labels for available parameters.
# This stays here because the GUI consumes it directly.
model_param_map = {
    "Ambient Temperature": ("file_data", "avgT_amb_K"),
    "Power": ("file_data", "avgQ"),
    "Thermocouple k": ("user_input", "probe", "TC_props", "k"),
    "Thermocouple rho": ("user_input", "probe", "TC_props", "rho"),
    "Thermocouple cp": ("user_input", "probe", "TC_props", "cp"),
    "Wire k": ("user_input", "probe", "heating_wire_props", "k"),
    "Wire rho": ("user_input", "probe", "heating_wire_props", "rho"),
    "Wire cp": ("user_input", "probe", "heating_wire_props", "cp"),
    "Insulation k": ("user_input", "probe", "insulation_props", "k"),
    "Insulation rho": ("user_input", "probe", "insulation_props", "rho"),
    "Insulation cp": ("user_input", "probe", "insulation_props", "cp"),
    "Sheath k": ("user_input", "probe", "sheath_props", "k"),
    "Sheath rho": ("user_input", "probe", "sheath_props", "rho"),
    "Sheath cp": ("user_input", "probe", "sheath_props", "cp"),
    "Sheath Emissivity": ("user_input", "probe", "sheath_props", "emissivity"),
    "Probe Geometry": ("user_input", "probe", "geometry"),
    "Crucible k": ("user_input", "crucible", "material", "k"),
    "Crucible rho": ("user_input", "crucible", "material", "rho"),
    "Crucible cp": ("user_input", "crucible", "material", "cp"),
    "Crucible Emissivity": ("user_input", "crucible", "material", "emissivity"),
    "Crucible inner radius": ("user_input", "crucible", "inner_radius"),
    "Crucible hole depth": ("user_input", "crucible", "hole_depth"),
    "Sample k": ("user_input", "sample", "k"),
    "Sample rho": ("user_input", "sample", "rho"),
    "Sample cp": ("user_input", "sample", "cp"),
    "Thermal Contact Resistance Sheath-Insulation": (
        "user_input",
        "probe",
        "TCR_insulation_sheath",
    ),
    "??? Thermal Contact Resistance Sheath-Sample": 1,
    "??? Scatter": 1,
    "??? Flux Decay": 1,
    "??? Decay Point": 1,
    "Convection Coefficient": ("user_input", "convection_coeff"),
}


def _make_parameter_entry(value, lower_factor=0.5, upper_factor=1.5, sigma_factor=0.2):
    value = float(value)
    return {
        "initial_value": value,
        "bounds": (lower_factor * value, upper_factor * value),
        "prior_sigma": sigma_factor * value,
    }


def _copy_parameter_dict(parameter_dict):
    return {
        key: value.copy() if isinstance(value, dict) else value
        for key, value in parameter_dict.items()
    }


def _update_materials_at_ambient_temperature(user_selections, ambient_temperature):
    user_selections.probe.TC_props.update_properties_at_T(ambient_temperature)
    user_selections.probe.heating_wire_props.update_properties_at_T(ambient_temperature)
    user_selections.probe.insulation_props.update_properties_at_T(ambient_temperature)
    user_selections.probe.sheath_props.update_properties_at_T(ambient_temperature)
    user_selections.crucible.material.update_properties_at_T(ambient_temperature)
    user_selections.sample.update_properties_at_T(ambient_temperature)


def _flatten_model_parameters(resolved_params):
    for key, value in list(resolved_params.items()):
        if isinstance(value, dict) and "initial_value" in value:
            resolved_params[key] = value["initial_value"]


def prepare_folder_for_optim(folder_data, user_selections):
    prepared_list = []

    for file_data in folder_data:
        resolved_params, optim_vecs = resolve_params_at_T(file_data, user_selections)

        prepared_list.append(
            {
                "file_data": file_data,
                "resolved_params": resolved_params,
                "simulation": user_selections.simulation_name,
                "optim_vecs": optim_vecs,
            }
        )

    return prepared_list


def resolve_params_at_T(file_data, user_selections):
    ambient_temperature = file_data["avgT_amb_K"]["initial_value"]
    print(
        f"# Resolving parameters for file {file_data['filepath'].name} at T_amb = {ambient_temperature} K..."
    )

    _update_materials_at_ambient_temperature(user_selections, ambient_temperature)

    probe = user_selections.probe
    crucible = user_selections.crucible
    sample = user_selections.sample

    resolved_params = {
        "_probe_obj": probe,
        "_crucible_obj": crucible,
        "_sample_obj": sample,
        "Ambient Temperature": _copy_parameter_dict(file_data["avgT_amb_K"]),
        "Power": _copy_parameter_dict(file_data["avgQ"]),
        "Thermocouple k": _copy_parameter_dict(probe.TC_props.k),
        "Thermocouple rho": _copy_parameter_dict(probe.TC_props.rho),
        "Thermocouple cp": _copy_parameter_dict(probe.TC_props.cp),
        "Wire k": _copy_parameter_dict(probe.heating_wire_props.k),
        "Wire rho": _copy_parameter_dict(probe.heating_wire_props.rho),
        "Wire cp": _copy_parameter_dict(probe.heating_wire_props.cp),
        "Insulation k": _copy_parameter_dict(probe.insulation_props.k),
        "Insulation rho": _copy_parameter_dict(probe.insulation_props.rho),
        "Insulation cp": _copy_parameter_dict(probe.insulation_props.cp),
        "Sheath k": _copy_parameter_dict(probe.sheath_props.k),
        "Sheath rho": _copy_parameter_dict(probe.sheath_props.rho),
        "Sheath cp": _copy_parameter_dict(probe.sheath_props.cp),
        "Sheath Emissivity": _copy_parameter_dict(probe.sheath_props.emissivity),
        "Probe Geometry": _copy_parameter_dict(probe.geometry),
        "Crucible k": _copy_parameter_dict(crucible.material.k),
        "Crucible rho": _copy_parameter_dict(crucible.material.rho),
        "Crucible cp": _copy_parameter_dict(crucible.material.cp),
        "Crucible Emissivity": _copy_parameter_dict(crucible.material.emissivity),
        "Crucible inner radius": _make_parameter_entry(crucible.inner_radius),
        "Crucible hole depth": _make_parameter_entry(crucible.hole_depth),
        "Sample k": _copy_parameter_dict(sample.k),
        "Sample rho": _copy_parameter_dict(sample.rho),
        "Sample cp": _copy_parameter_dict(sample.cp),
        "Thermal Contact Resistance Sheath-Insulation": _make_parameter_entry(
            probe.TCR_insulation_sheath
        ),
        "??? Thermal Contact Resistance Sheath-Sample": _make_parameter_entry(1.0),
        "??? Scatter": _make_parameter_entry(0.0),
        "??? Flux Decay": _make_parameter_entry(1.0),
        "??? Decay Point": _make_parameter_entry(1.0),
        "Convection Coefficient": _make_parameter_entry(user_selections.convection_coeff),
    }

    for key, value in resolved_params["Probe Geometry"].items():
        resolved_params[key] = value

    optim_vecs = build_optim_vectors(resolved_params, user_selections)

    del resolved_params["Probe Geometry"]
    _flatten_model_parameters(resolved_params)
    resolved_params["filepath"] = file_data["filepath"]

    return resolved_params, optim_vecs