from pathlib import Path
import csv


def export_probe_calibration(prepared_folder_data, folder_solved_values=None, out_csv=None):
    """Export temperature-dependent probe properties per file to CSV.

    prepared_folder_data: list as returned by prepare_folder_for_optim
    folder_solved_values: list of solved dicts returned by optimizer (optional)
    out_csv: path to output CSV file (defaults to Plots_initial_model/probe_calibration.csv next to first data file)
    """
    if not prepared_folder_data:
        raise ValueError("No prepared data provided")

    first_file = Path(prepared_folder_data[0]["resolved_params"]["filepath"]) if isinstance(prepared_folder_data[0]["resolved_params"].get("filepath"), (str,)) else Path(prepared_folder_data[0]["resolved_params"]["filepath"])
    default_dir = Path(prepared_folder_data[0]["resolved_params"]["filepath"]).parent / "Plots_initial_model"
    out_path = Path(out_csv) if out_csv else (default_dir / "probe_calibration.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build header
    header = [
        "filepath",
        "T_amb_K",
        # Thermocouple
        "TC_k", "TC_rho", "TC_cp",
        # Heating wires
        "Wire_k", "Wire_rho", "Wire_cp",
        # Insulation
        "Ins_k", "Ins_rho", "Ins_cp",
        # Sheath
        "Sheath_k", "Sheath_rho", "Sheath_cp",
        # TCR
        "TCR_insulation_sheath",
    ]

    # Append solved parameter keys if present
    extra_keys = []
    if folder_solved_values:
        # collect union of solved param names
        names = set()
        for s in folder_solved_values:
            names.update(s.get("solved_values", {}).keys())
        extra_keys = sorted(names)
        header.extend(extra_keys)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)

        for i, item in enumerate(prepared_folder_data):
            rp = item["resolved_params"]
            fd = item["file_data"]
            row = [str(fd["filepath"]), fd["avgT_amb_K"]["initial_value"]]

            # Thermocouple
            tc_k = rp.get("Thermocouple k", {}).get("initial_value")
            tc_rho = rp.get("Thermocouple rho", {}).get("initial_value")
            tc_cp = rp.get("Thermocouple cp", {}).get("initial_value")
            row.extend([tc_k, tc_rho, tc_cp])

            # Wire
            w_k = rp.get("Wire k", {}).get("initial_value")
            w_rho = rp.get("Wire rho", {}).get("initial_value")
            w_cp = rp.get("Wire cp", {}).get("initial_value")
            row.extend([w_k, w_rho, w_cp])

            # Insulation
            ins_k = rp.get("Insulation k", {}).get("initial_value")
            ins_rho = rp.get("Insulation rho", {}).get("initial_value")
            ins_cp = rp.get("Insulation cp", {}).get("initial_value")
            row.extend([ins_k, ins_rho, ins_cp])

            # Sheath
            sh_k = rp.get("Sheath k", {}).get("initial_value")
            sh_rho = rp.get("Sheath rho", {}).get("initial_value")
            sh_cp = rp.get("Sheath cp", {}).get("initial_value")
            row.extend([sh_k, sh_rho, sh_cp])

            # TCR
            tcr = rp.get("Thermal Contact Resistance Sheath-Insulation")
            tcr_val = tcr if not isinstance(tcr, dict) else tcr.get("initial_value")
            row.append(tcr_val)

            # Append solved params if present
            if folder_solved_values:
                solved_map = folder_solved_values[i].get("solved_values", {})
                for k in extra_keys:
                    row.append(solved_map.get(k))

            writer.writerow(row)

    return out_path
