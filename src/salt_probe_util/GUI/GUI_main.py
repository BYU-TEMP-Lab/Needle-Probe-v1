import json, os, tkinter as tk, textwrap
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .GUI_advanced_settings import AdvancedSettings
from .GUI_calibration_menu import CalibrationMenu
from ..libraries.materials import options as samples
from ..libraries.probes import options as probes
from ..libraries.crucibles import options as crucibles
from ..libraries.calibrations import options as cal_dict
from ..optim import decision_var_options as decision_vars
  

class SimulationOptions(tk.Tk):
    def __init__(self, simulation_options_dict, cross_section_options_dict):
        super().__init__()
        
        # Store option dictionaries
        self.probes = probes
        self.crucibles = crucibles
        self.samples = samples
        self.simulation_options = simulation_options_dict
        self.cross_sections = cross_section_options_dict
        self.decision_vars = decision_vars

        # Load the defaultsettings from the JSON file
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.default_file_path = self.BASE_DIR / "config" / "default_options.json"
        self.load_defaults_file()

        self.override_dur = self.defaults.get("test duration override")
        self.plot_freq = self.defaults.get("plot frequency")
        self.chi2_tol = self.defaults.get("chi2 tolerance")

        # build UI
        self._build_ui()
        

    def _build_ui(self):
        self.title("Simulation Options")
        self.resizable(False, False)

        # --- Container for centering ---
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(expand=True)

        # --- Title ---
        ttk.Label(self.form_frame, text="Simulation Options", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        # --- Dropdowns for Probe, Crucible, Sample, Simulation Cross Section, Simulation ---
        self.empty_var = "Select..."

        self.probe_var, self.probe_combobox = self.generate_dropdown("Probe", probes, (1, 0), self.defaults.get("probe"))
        self.crucible_var, self.crucible_combobox = self.generate_dropdown("Crucible", crucibles, (2, 0), self.defaults.get("crucible"))
        self.sample_var, self.sample_combobox = self.generate_dropdown("Sample", samples, (3, 0))
        self.simulation_var, self.simulation_combobox = self.generate_dropdown("Simulation", self.simulation_options, (4, 0), self.defaults.get("simulation"))
        self.cross_section_var, self.cross_section_combobox = self.generate_dropdown("Simulation Cross-section", self.cross_sections, (5, 0), self.defaults.get("simulation cross section"))

        # --- Decision Variables ---
        ttk.Label(self.form_frame, text="Decision Variables:").grid(row=6, column=0, padx=10, pady=5, sticky="e")
        self.decision_vars_box = tk.Listbox(self.form_frame, selectmode=tk.MULTIPLE, exportselection=False) # selectmode can be SINGLE, BROWSE, MULTIPLE, or EXTENDED
        self.decision_vars_box.grid(row=6, column=1, padx=10, pady=5, sticky="w")

        for x in decision_vars.keys():
            self.decision_vars_box.insert(tk.END, x)

        # Select the default decision variables
        for indx, x in enumerate(self.decision_vars.keys()):
            if x in self.defaults.get("decision variables", []):
                self.decision_vars_box.selection_set(indx)

        # --- Data Folder Selection ---
        ttk.Label(self.form_frame, text="Experimental Data Folder:").grid(row=7, column=0, padx=10, pady=5, sticky="e")
        self.folder_label = ttk.Label(self.form_frame, text="No folder selected", wraplength=250, justify="left")
        self.folder_label.grid(row=8, column=1, padx=10, pady=5, sticky="w")
        ttk.Button(self.form_frame, text="Select Folder", command=self.select_data_folder).grid(row=7, column=1, padx=10, pady=5, sticky="w")

        # --- Advanced Settings Button ---
        self.adv_settings = None
        ttk.Button(self.form_frame, text="Advanced Settings", command=self.open_advanced_settings).grid(row=9, column=0, columnspan=2, pady=10)

        # --- Proceed Button ---
        self.proceed_button = ttk.Button(self.form_frame, text="Proceed", state="disabled", command=self.proceed)
        self.proceed_button.grid(row=10, column=0, columnspan=2, pady=15)
        self.test_folder_path = None

        # --- Initialize Calibration Menu ---
        self.cal_menu = None


    def generate_dropdown(self, title, vars_dict, pos, default_value = None):
        ttk.Label(self.form_frame, text=title).grid(row=pos[0], column=pos[1], padx=10, pady=5, sticky="e")
        var = tk.StringVar(self)

        if not default_value:
            var.set(self.empty_var)
        else:
            var.set(default_value)

        combobox = ttk.Combobox(self.form_frame, textvariable=var, values=list(vars_dict.keys()), state="readonly")
        combobox.grid(row=pos[0], column=pos[1]+1, padx=10, pady=5, sticky="w")
        return var, combobox
    

    def update_defaults(self):
        self.probe_var.set(self.defaults.get("probe"))
        self.crucible_var.set(self.defaults.get("crucible"))
        self.simulation_var.set(self.defaults.get("simultion"))
        self.cross_section_var.set(self.defaults.get("simulation cross section"))

        # Select the default decision variables
        ## Clear current selection first
        self.decision_vars_box.selection_clear(0, tk.END)
        for indx, x in enumerate(self.decision_vars.keys()):
            if x in self.defaults.get("decision variables", []):
                self.decision_vars_box.selection_set(indx)
        
        self.override_dur = self.defaults.get("test duration override")
        self.plot_freq = self.defaults.get("plot frequency")
        self.chi2_tol = self.defaults.get("chi2 tolerance")


    def load_defaults_file(self, filepath=None):
        """Read the JSON config and update UI/Data using pathlib """
        # 1. Fallback to self.default_file_path if no path provided
        # 2. Ensure filepath is a Path object even if a string was passed
        target_path = Path(filepath or self.default_file_path)

        # .is_file() is more specific than .exists() (it ensures it's not a folder)
        if target_path.is_file():
            try:
                data = target_path.read_text(encoding='utf-8')
                self.defaults = json.loads(data)
                print(f"Settings applied from: {"/".join(target_path.parts[-2:])}")
                
            except json.JSONDecodeError as e:
                print(f"Error: {target_path.name} is not a valid JSON file. {e}")
            except Exception as e:
                print(f"Unexpected error reading file: {e}")
        else:
            # Use .resolve() to show the full absolute path in the warning
            # This helps you debug exactly where Python is looking
            print(f"Warning: File not found at {target_path.resolve()}")

            
    def select_data_folder(self):
        self.test_folder_path = filedialog.askdirectory(title="Select an experimental data folder", initialdir=".")
        if self.test_folder_path:
            self.test_folder_path = Path(self.test_folder_path)
            self.folder_label.config(text="/".join(self.test_folder_path.parts[-2:]))
            self.proceed_button.config(state="normal")
        else:
            self.folder_label.config(text="No folder selected")
            self.proceed_button.config(state="disabled")

        
    def open_advanced_settings(self):
        if self.adv_settings is None or not self.adv_settings.winfo_exists():
            self.adv_settings = AdvancedSettings(self)
        else:
            self.adv_settings.lift()  # bring existing window to front


    def check_for_calibration(self):
        # initialize variable to store calibrated values if then exist
        self.calibration = None
        self.perf_calibration = 0 

        current_config = [self.probe_var.get(), self.crucible_var.get()]

        # create calibration popup window
        if self.cal_menu is None or not self.cal_menu.winfo_exists():
            self.cal_menu = CalibrationMenu(self, current_config)
            self.wait_window(self.cal_menu)
        else:
            self.cal_menu.lift()  # bring existing window to front

        return self.cal_menu.complete
    

    def check_selections(self):
        # Get selected indices
        self.decision_vars_indx = self.decision_vars_box.curselection()  # returns a tuple of selected indices

        # check dropdowns for emptiness
        dropdown_var_vals = [self.crucible_var.get(), 
                             self.probe_var.get(), 
                             self.sample_var.get(), 
                             self.simulation_var.get(),
                             self.cross_section_var.get()]
        dropdown_var_dicts = [self.crucibles, 
                              self.probes, 
                              self.samples, 
                              self.simulation_options, 
                              self.cross_sections]
        
        check_dropdown_vars = zip(dropdown_var_vals, dropdown_var_dicts)

        for val, var_dict in check_dropdown_vars:
            if val not in list(var_dict.keys()):
                messagebox.showerror(
                    "Error",
                    "Value {val} is not a valid selection. Please select a valid option.".format(val=val)
                )
                return True

        # check folder selected
        if not self.test_folder_path:
            messagebox.showerror(
                "Error",
                "Please select a folder."
            )
            return True
        
        # check at least one decision variable selected
        if not self.decision_vars_indx: # empty tuple evaluates to False
            messagebox.showerror(
                "Error",
                "Please select at least one decision variable."
            )
            return True
        
        # check advanced settings for validity
        if not self.chi2_tol:
            messagebox.showerror(
                "Error",
                "Must select non-zero Chi-square value."
            )
            return True
        
        # don't allow thermal quadrapoles since code doesn't exist yet
        if self.simulation_var.get() == "Thermal Quadrupoles":
            messagebox.showerror(
                "Error",
                "Thermal quadrupoles feature not yet available."
            )
            return True

        # Check for calibrations
        if not self.check_for_calibration():
            return True

        return False
            
    def _parse_input(self, value, cast_type, field_name):
        # Convert to string and clean it up
        val_str = str(value).strip().lower()

        # Check for all variations of "nothing"
        if val_str in ("", "none", "null", "nan"):
            return None

        try:
            # Convert to the requested type (int or float)
            num_val = cast_type(value)
            
            # Precision check for floats
            if isinstance(num_val, float) and abs(num_val) < 1e-12:
                return None
                
            return num_val

        except (ValueError, TypeError):
            messagebox.showerror("Error", f"Invalid value for {field_name}.")
            return None
        

    def get_selections(self):
        selections_dict = {
            "probe": self.probe_var.get(),
            "crucible": self.crucible_var.get(),
            "sample": self.sample_var.get(),
            "simulation": self.simulation_var.get(),
            "simulation cross section": self.cross_section_var.get(),
            "decision variables indices": self.decision_vars_indx,
            "test duration override": self.override_dur,
            "plot frequency": self.plot_freq,
            "chi2 tolerance": self.chi2_tol,
            "perform new calibration": self.perf_calibration,
            "calibration data": self.calibration,
            "test data folder": self.test_folder_path
        }
        
        return selections_dict


    def proceed(self):
        if self.check_selections():
            return
        
        # Parse user input 
        self.override_dur = self._parse_input(self.override_dur, float, "test duration override")
        self.plot_freq = self._parse_input(self.plot_freq, int, "plot frequency")
        self.chi2_tol = self._parse_input(self.chi2_tol, float, "chi2 tolerance")

        if self.perf_calibration == 1:
            disp_perf_cal = "yes"
            disp_cal = "N/A"
        else:
            disp_perf_cal = "no"
            if self.calibration is None:
                disp_cal = "Use uncalibrated parameters"
            else:
                disp_cal = self.calibration.name
        
        msg = f"""
            --------------------------------------------------
            Proceeding with:
            ### Probe: {self.probe_var.get()}
            ### Crucible: {self.crucible_var.get()}
            ### Sample: {self.sample_var.get()}
            ### Cross-section: {self.cross_section_var.get()}
            ### Decision Variables: {[list(self.decision_vars.keys())[i] for i in self.decision_vars_indx]}
            ### Overridden Test Duration: {self.override_dur}
            ### Plot Frequency (Iterations): {self.plot_freq}
            ### Chi2 Tolerance: {self.chi2_tol}
            ### Perform New Calibration?: {disp_perf_cal}
            ### Calibration Parameters: {disp_cal}
            ### Data Folder: {self.test_folder_path}
            --------------------------------------------------
        """
        print(textwrap.dedent(msg).strip())

        self.user_cancelled = False
        self.destroy()  # close the GUI