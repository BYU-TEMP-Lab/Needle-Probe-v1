import json
import logging
import textwrap
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .GUI_advanced_settings import AdvancedSettings
from ..libraries.calibrations import options as cal_dict
from ..libraries.materials import options as samples
from ..libraries.probes import options as probes
from ..libraries.crucibles import options as crucibles
from ..libraries.simulations import simulation_options_dict
from ..build_model import model_param_map as decision_vars
from ..bootstrap import setup_logging

logger = logging.getLogger(__name__)

TASK_PROBE_CALIBRATION = "Probe Calibration"
TASK_THERMAL_CONDUCTIVITY = "Thermal Conductivity Measurement"
TASK_SENSITIVITY_ANALYSIS = "Sensitivity Analysis"

## Add functionality to specify whether to save initial data plots

class SimulationOptions(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulation Options")
        self.resizable(False, False)

        # Store option dictionaries.
        self.probes = probes
        self.crucibles = crucibles
        self.samples = samples
        self.simulation_options = simulation_options_dict
        self.decision_vars = decision_vars

        # Simulation-specific cross-section choices can be narrowed later if needed.
        self.cross_section_options_by_simulation = {
            sim_name: {"Axial": "Axial", "Radial": "Radial"}
            for sim_name in self.simulation_options.keys()
        }

        # Defaults file handling.
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.default_file_path = self.BASE_DIR / "config" / "default_options.json"
        self.defaults = {}
        self.load_defaults_file()

        self.override_dur = self.defaults.get("test duration override")
        self.plot_freq = self.defaults.get("plot frequency")
        self.chi2_tol = self.defaults.get("chi2 tolerance")
        self.convection_coeff = self.defaults.get("convection coefficient")

        # Runtime state.
        self.user_cancelled = True
        self.complete = False
        self.calibration = None
        self.perf_calibration = 0
        self.task_mode = TASK_THERMAL_CONDUCTIVITY
        self.data_folder_path = None
        self.adv_settings = None
        self.selected_parameters = []

        self._build_ui()
        self._apply_defaults_to_ui()
        self._update_task_visibility()

    def _build_ui(self):
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.form_frame.columnconfigure(1, weight=10)

        ttk.Label(self.form_frame, text="Simulation Options", font=("Arial", 16)).grid(
            row=0, column=0, columnspan=3, pady=(0, 12)
        )

        # Defaults loader.
        # Defaults loader UI removed for now (can be re-enabled later)
        # self.defaults_label = ttk.Label(
        #     self.form_frame,
        #     text="Defaults: not loaded",
        #     wraplength=320,
        #     justify="left",
        # )
        # self.defaults_label.grid(row=1, column=1, padx=10, pady=(0, 8), sticky="w")
        # ttk.Button(self.form_frame, text="Load Defaults", command=self._load_defaults_via_dialog).grid(
        #     row=1, column=0, padx=10, pady=(0, 8), sticky="e"
        # )

        # Core selections.
        self.probe_var, self.probe_combobox = self.generate_dropdown(
            "Probe:", self.probes, (2, 0), self.defaults.get("probe")
        )
        self.crucible_var, self.crucible_combobox = self.generate_dropdown(
            "Crucible:", self.crucibles, (3, 0), self.defaults.get("crucible")
        )
        self.sample_var, self.sample_combobox = self.generate_dropdown(
            "Sample:", self.samples, (4, 0), self.defaults.get("sample")
        )
        self.simulation_var, self.simulation_combobox = self.generate_dropdown(
            "Physics model:",
            self.simulation_options,
            (5, 0),
            self.defaults.get("simulation"),
        )
        self.simulation_combobox.bind("<<ComboboxSelected>>", self._on_simulation_changed)

        self.cross_section_var, self.cross_section_combobox = self.generate_dropdown(
            "Cross section normal:",
            self._current_cross_section_options(),
            (6, 0),
            self.defaults.get("simulation cross section"),
        )

        # Workflow mode (use generate_dropdown for consistent formatting with other controls)
        self.workflow_var, self.workflow_combobox = self.generate_dropdown(
            "Workflow Mode:",
            {
                TASK_PROBE_CALIBRATION: TASK_PROBE_CALIBRATION,
                TASK_THERMAL_CONDUCTIVITY: TASK_THERMAL_CONDUCTIVITY,
                TASK_SENSITIVITY_ANALYSIS: TASK_SENSITIVITY_ANALYSIS,
            },
            (7, 0),
            self.defaults.get("workflow mode", TASK_THERMAL_CONDUCTIVITY),
        )
        self.workflow_combobox.bind("<<ComboboxSelected>>", lambda _e: self._on_task_changed())

        # Conditional sections (placed in the main form so labels align with dropdowns)
        self.conditional_base_row = 8

        self.calibration_label = ttk.Label(self.form_frame, text="Calibration:")
        self.calibration_var = tk.StringVar(value="Use uncalibrated parameters")
        # Use default combobox sizing so column widths stay consistent
        self.calibration_combobox = ttk.Combobox(
            self.form_frame,
            textvariable=self.calibration_var,
            values=self._calibration_options(),
            state="readonly",
            width=50,
        )
        self.calibration_combobox.bind("<<ComboboxSelected>>", self._on_calibration_changed)
        self.folder_label_title = ttk.Label(self.form_frame, text="Experimental Data Folder:")
        self.folder_label = ttk.Label(
            self.form_frame,
            text="No folder selected",
            wraplength=320,
            justify="left",
        )
        # Place folder button closer to the folder label (smaller padx)
        self.folder_button = ttk.Button(
            self.form_frame,
            text="Select Folder",
            command=self.select_data_folder,
        )

        # Track conditional widgets so we can show/hide them easily
        self._conditional_widgets = [
            self.calibration_label,
            self.calibration_combobox,
            self.folder_label_title,
            self.folder_label,
            self.folder_button,
        ]

        # Advanced settings placed below conditional area to avoid overlap
        self.advanced_button = ttk.Button(
            self.form_frame,
            text="Advanced Settings",
            command=self.open_advanced_settings,
        )
        # place Advanced and Proceed below the maximum possible conditional rows
        self.advanced_button.grid(row=self.conditional_base_row + 4, column=0, columnspan=3, pady=(14, 6))

        # Proceed.
        self.proceed_button = ttk.Button(
            self.form_frame,
            text="Proceed",
            state="disabled",
            command=self.proceed,
        )
        self.proceed_button.grid(row=self.conditional_base_row + 5, column=0, columnspan=3, pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_defaults_to_ui(self):
        if self.defaults.get("probe"):
            self.probe_var.set(self.defaults.get("probe"))
        if self.defaults.get("crucible"):
            self.crucible_var.set(self.defaults.get("crucible"))
        if self.defaults.get("sample"):
            self.sample_var.set(self.defaults.get("sample"))
        if self.defaults.get("simulation"):
            self.simulation_var.set(self.defaults.get("simulation"))
        if self.defaults.get("simulation cross section"):
            self.cross_section_var.set(self.defaults.get("simulation cross section"))
        self.workflow_var.set(self.defaults.get("workflow mode", TASK_THERMAL_CONDUCTIVITY))
        if self.defaults.get("calibration"):
            self.calibration_var.set(self.defaults.get("calibration"))
        self.selected_parameters = self._default_selected_parameters()
        self.decision_vars_indx = self._selected_parameter_indices()

        self.decision_vars_box = None

    def _current_cross_section_options(self):
        sim_name = self.simulation_var.get() if hasattr(self, "simulation_var") else None
        options = self.cross_section_options_by_simulation.get(sim_name)
        if options is None:
            options = {"Axial": "Axial", "Radial": "Radial"}
        return options

    def _default_selected_parameters(self):
        task = self.workflow_var.get() if hasattr(self, "workflow_var") else self.task_mode
        if task == TASK_THERMAL_CONDUCTIVITY:
            return ["Sample k"]
        return list(self.decision_vars.keys())

    def _selected_parameter_indices(self):
        selected = getattr(self, "selected_parameters", []) or self._default_selected_parameters()
        param_names = list(self.decision_vars.keys())
        return [index for index, name in enumerate(param_names) if name in selected]

    def _on_task_changed(self):
        self.selected_parameters = self._default_selected_parameters()
        self.decision_vars_indx = self._selected_parameter_indices()
        self._update_task_visibility()

    def _calibration_options(self):
        probe_name = self.probe_var.get() if hasattr(self, "probe_var") else None
        crucible_name = self.crucible_var.get() if hasattr(self, "crucible_var") else None
        matching = [
            name
            for name, calibration in cal_dict.items()
            if [calibration.probe, calibration.crucible] == [probe_name, crucible_name]
        ]
        matching.sort()
        return matching + ["Use uncalibrated parameters"]

    def _refresh_calibration_options(self):
        options = self._calibration_options()
        current_value = self.calibration_var.get()
        self.calibration_combobox["values"] = options
        if current_value not in options:
            self.calibration_var.set(options[-1] if options else "Use uncalibrated parameters")
        self._apply_selected_calibration()

    def _apply_selected_calibration(self):
        selected = self.calibration_var.get()
        if selected == "Use uncalibrated parameters" or selected not in cal_dict:
            self.calibration = None
            self.perf_calibration = 0
            return

        self.calibration = cal_dict[selected]
        self.perf_calibration = 0

    def _on_calibration_changed(self, _event=None):
        self._apply_selected_calibration()
        self._update_proceed_state()

    def _on_simulation_changed(self, _event=None):
        current_value = self.cross_section_var.get()
        new_options = self._current_cross_section_options()
        self.cross_section_combobox["values"] = list(new_options.keys())
        if current_value not in new_options:
            self.cross_section_var.set(next(iter(new_options.keys()), self.empty_var))
        self._refresh_calibration_options()
        self._update_task_visibility()

    def _update_task_visibility(self):
        self.task_mode = self.workflow_var.get()

        for widget in self._conditional_widgets:
            widget.grid_remove()

        row = 0
        if self.task_mode in (TASK_THERMAL_CONDUCTIVITY, TASK_SENSITIVITY_ANALYSIS):
            self.calibration_label.grid(row=self.conditional_base_row + row, column=0, padx=10, pady=5, sticky="e")
            self.calibration_combobox.grid(row=self.conditional_base_row + row, column=1, padx=10, pady=5, sticky="ew")
            row += 1

        if self.task_mode in (TASK_PROBE_CALIBRATION, TASK_THERMAL_CONDUCTIVITY):
            # Title at left, button to the right, file name displayed below the button
            self.folder_label_title.grid(row=self.conditional_base_row + row, column=0, padx=10, pady=5, sticky="e")
            self.folder_button.grid(row=self.conditional_base_row + row, column=1, padx=10, pady=5, sticky="w")
            self.folder_label.grid(row=self.conditional_base_row + row + 1, column=1, padx=10, pady=(0, 5), sticky="w")
            row += 2

        if self.task_mode == TASK_SENSITIVITY_ANALYSIS:
            self.advanced_button.state(["!disabled"])
            self.advanced_button.configure(text="Advanced Settings (defaults + parameters)")
        else:
            self.advanced_button.state(["!disabled"])
            self.advanced_button.configure(text="Advanced Settings")

        self.update_idletasks()
        self._refresh_calibration_options()
        self._update_proceed_state()

    def _update_proceed_state(self):
        base_ready = all(
            value in mapping
            for value, mapping in [
                (self.probe_var.get(), self.probes),
                (self.crucible_var.get(), self.crucibles),
                (self.sample_var.get(), self.samples),
                (self.simulation_var.get(), self.simulation_options),
                (self.cross_section_var.get(), self._current_cross_section_options()),
            ]
        )

        task = self.workflow_var.get()
        needs_calibration = task in (TASK_THERMAL_CONDUCTIVITY, TASK_SENSITIVITY_ANALYSIS)
        needs_folder = task in (TASK_PROBE_CALIBRATION, TASK_THERMAL_CONDUCTIVITY)

        has_calibration = self.calibration is not None if needs_calibration else True
        has_folder = self.data_folder_path is not None if needs_folder else True

        if base_ready and has_calibration and has_folder:
            self.proceed_button.config(state="normal")
        else:
            self.proceed_button.config(state="disabled")

    def _load_defaults_via_dialog(self):
        selected_file = filedialog.askopenfilename(
            title="Select Default Settings JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=".",
        )
        if selected_file:
            selected_path = Path(selected_file)
            self.load_defaults_file(selected_path)
            self._apply_loaded_defaults_to_ui()

    def _apply_loaded_defaults_to_ui(self):
        self.defaults_label.config(text="Defaults: " + "/".join(self.default_file_path.parts[-2:]))
        self.update_defaults()
        self._update_task_visibility()

    def generate_dropdown(self, title, vars_dict, pos, default_value=None):
        # Title-case the label text so each word starts with a capital letter
        ttk.Label(self.form_frame, text=title.title()).grid(row=pos[0], column=pos[1], padx=10, pady=5, sticky="e")
        var = tk.StringVar(self)
        var.set(default_value if default_value else self.empty_var)
        combobox = ttk.Combobox(
            self.form_frame,
            textvariable=var,
            values=list(vars_dict.keys()),
            state="readonly",
            width=50,
        )
        combobox.grid(row=pos[0], column=pos[1] + 1, padx=10, pady=5, sticky="ew")
        combobox.bind("<<ComboboxSelected>>", lambda _event: self._selection_changed())
        return var, combobox

    def _selection_changed(self):
        self._refresh_calibration_options()
        self._update_proceed_state()

    def update_defaults(self):
        self.probe_var.set(self.defaults.get("probe", self.probe_var.get()))
        self.crucible_var.set(self.defaults.get("crucible", self.crucible_var.get()))
        self.sample_var.set(self.defaults.get("sample", self.sample_var.get()))
        self.simulation_var.set(self.defaults.get("simulation", self.simulation_var.get()))
        self.cross_section_var.set(
            self.defaults.get("simulation cross section", self.cross_section_var.get())
        )
        self.workflow_var.set(self.defaults.get("workflow mode", self.workflow_var.get()))
        self.override_dur = self.defaults.get("test duration override")
        self.plot_freq = self.defaults.get("plot frequency")
        self.chi2_tol = self.defaults.get("chi2 tolerance")
        self.convection_coeff = self.defaults.get("convection coefficient")

    def load_defaults_file(self, filepath=None):
        target_path = Path(filepath or self.default_file_path)
        if target_path.is_file():
            try:
                self.defaults = json.loads(target_path.read_text(encoding="utf-8"))
                logger.info("Settings applied from: %s", "/".join(target_path.parts[-2:]))
            except json.JSONDecodeError as e:
                logger.error("%s is not a valid JSON file: %s", target_path.name, e)
            except Exception as e:
                logger.exception("Unexpected error reading file: %s", e)
        else:
            logger.warning("File not found at %s", target_path.resolve())

    def select_data_folder(self):
        folder = filedialog.askdirectory(
            title="Select an experimental data folder",
            initialdir=".",
        )
        if folder:
            self.data_folder_path = Path(folder)
            self.folder_label.config(text="/".join(self.data_folder_path.parts[-2:]))
        else:
            self.data_folder_path = None
            self.folder_label.config(text="No folder selected")
        self._update_proceed_state()

    def check_for_calibration(self):
        if self.workflow_var.get() not in (TASK_THERMAL_CONDUCTIVITY, TASK_SENSITIVITY_ANALYSIS):
            self.calibration = None
            self.perf_calibration = 0
            return True

        self._apply_selected_calibration()
        return True

    def check_selections(self):
        dropdown_var_vals = [
            self.crucible_var.get(),
            self.probe_var.get(),
            self.sample_var.get(),
            self.simulation_var.get(),
            self.cross_section_var.get(),
        ]
        dropdown_var_dicts = [
            self.crucibles,
            self.probes,
            self.samples,
            self.simulation_options,
            self._current_cross_section_options(),
        ]

        for val, var_dict in zip(dropdown_var_vals, dropdown_var_dicts):
            if val not in list(var_dict.keys()):
                messagebox.showerror(
                    "Error",
                    "Value {val} is not a valid selection. Please select a valid option.".format(val=val),
                )
                return True

        if self.workflow_var.get() in (TASK_PROBE_CALIBRATION, TASK_THERMAL_CONDUCTIVITY):
            if self.data_folder_path is None:
                messagebox.showerror("Error", "Please select a data folder.")
                return True

        if self.workflow_var.get() in (TASK_THERMAL_CONDUCTIVITY, TASK_SENSITIVITY_ANALYSIS):
            if self.calibration_var.get() == self.empty_var:
                messagebox.showerror("Error", "Please select a calibration.")
                return True

            if not self.check_for_calibration():
                messagebox.showerror("Error", "Please select a calibration.")
                return True

        return False

    def open_advanced_settings(self):
        if self.adv_settings is None or not self.adv_settings.winfo_exists():
            self.adv_settings = AdvancedSettings(self)
        else:
            self.adv_settings.lift()

    def proceed(self):
        if self.check_selections():
            return

        self.probe = self.probes[self.probe_var.get()]
        self.crucible = self.crucibles[self.crucible_var.get()]
        self.sample = self.samples[self.sample_var.get()]
        self.simulation_name = self.simulation_var.get()
        self.cross_section = self.cross_section_var.get()
        self.task_mode = self.workflow_var.get()
        if not getattr(self, "selected_parameters", None):
            self.selected_parameters = self._default_selected_parameters()
        self.decision_vars_indx = self._selected_parameter_indices()
        self.override_dur = self._parse_input(self.override_dur, float, "test duration override")
        self.plot_freq = self._parse_input(self.plot_freq, int, "plot frequency")
        self.chi2_tol = self._parse_input(self.chi2_tol, float, "chi2 tolerance")

        if self.calibration is not None:
            calibration_text = self.calibration.name
        else:
            calibration_text = "Use uncalibrated parameters"

        setup_logging(log_dir=self.data_folder_path / "logs")  # Reconfigure logging to write to the selected folder

        msg = f"""
            --------------------------------------------------
            Proceeding with:
            ### Workflow Mode: {self.task_mode}
            ### Probe: {self.probe.name}
            ### Crucible: {self.crucible.name}
            ### Sample: {self.sample.name}
            ### Cross-section: {self.cross_section}
            ### Simulation: {self.simulation_name}
            ### Calibration: {calibration_text}
            ### Overridden Test Duration: {self.override_dur}
            ### Plot Frequency (Iterations): {self.plot_freq}
            ### Chi2 Tolerance: {self.chi2_tol}
            ### Convection Coefficient: {self.convection_coeff}
            ### Data Folder: {self.data_folder_path}
            --------------------------------------------------
        """
        logger.info(textwrap.dedent(msg).strip())

        self.user_cancelled = False
        self.complete = True
        self.destroy()

    def _parse_input(self, value, cast_type, field_name):
        val_str = str(value).strip().lower()
        if val_str in ("", "none", "null", "nan"):
            return None

        try:
            num_val = cast_type(value)
            if isinstance(num_val, float) and abs(num_val) < 1e-12:
                return None
            return num_val
        except (ValueError, TypeError):
            messagebox.showerror("Error", f"Invalid value for {field_name}.")
            return None

    def get_selections_dict(self):
        return {
            "workflow mode": self.task_mode,
            "probe": self.probe,
            "crucible": self.crucible,
            "sample": self.sample,
            "simulation": self.simulation_name,
            "simulation cross section": self.cross_section,
            "calibration": self.calibration,
            "selected calibration name": self.calibration_var.get(),
            "selected parameters": self.selected_parameters,
            "decision variables indices": self.decision_vars_indx,
            "test duration override": self.override_dur,
            "plot frequency": self.plot_freq,
            "chi2 tolerance": self.chi2_tol,
            "convection coefficient": self.convection_coeff,
            "perform new calibration": self.perf_calibration,
            "test data folder": self.data_folder_path,
        }

    def _on_close(self):
        self.user_cancelled = True
        self.destroy()


if __name__ == "__main__":
    main_GUI = SimulationOptions()
    main_GUI.mainloop()
    if getattr(main_GUI, "user_cancelled", True):
        logger.info("User closed the window without proceeding. Exiting program.")
        raise SystemExit(0)

    user_selections = main_GUI.get_selections_dict()
    logger.info("User selections:")
    for key, value in user_selections.items():
        logger.info(" - %s: %s", key, value)
