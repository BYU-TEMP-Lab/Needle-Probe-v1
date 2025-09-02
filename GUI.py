import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class AdvancedSettings(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Advanced Settings")
        self.resizable(False, False)

        # Variables for settings
        self.test_duration_override = tk.DoubleVar(value=settings["override test duration"])
        self.plot_frequency = tk.IntVar(value=settings["plot frequency"])
        self.chi2_tolerance = tk.DoubleVar(value=settings["Chi2 tolerance"])

        # Layout
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Override Test Duration (s):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.test_duration_override).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Plot Frequency (iterations):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.plot_frequency).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Chi² Tolerance:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.chi2_tolerance).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form, text="Save and Close", command=self.save_and_close).grid(row=3, column=0, columnspan=2, pady=10)

    def save_and_close(self):
        self.master.advanced_settings_values = self.get_settings()
        self.destroy()

    def get_settings(self):
        """Return settings as a dict."""
        return {
            "override test duration": self.test_duration_override.get(),
            "plot frequency": self.plot_frequency.get(),
            "Chi2 tolerance": self.chi2_tolerance.get()
        }
    

class SimulationOptions(tk.Tk):
    def __init__(self, crucibles, probes, samples, decision_vars, cross_sections, test_duration_override=None, plotfrequency=5, Chi2_tolerance=1e-4):
        super().__init__()
        self.title("Simulation Options")
        self.resizable(False, False)

        # Store option dictionaries
        self.crucibles = crucibles
        self.probes = probes
        self.samples = samples
        self.cross_sections = cross_sections
        self.decision_vars = decision_vars
        self.advanced_settings_values = {
            "override test duration": test_duration_override,
            "plot frequency": plotfrequency,
            "Chi2 tolerance": Chi2_tolerance
        }

        # --- Container for centering ---
        form_frame = ttk.Frame(self)
        form_frame.pack(expand=True)

        # --- Title ---
        ttk.Label(form_frame, text="Simulation Options", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        # --- Dropdowns for Probe, Crucible, Sample, Simulation Cross Section ---
        self.empty_var = "Select..."

        ttk.Label(form_frame, text="Probe:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.probe_var = tk.StringVar(self)
        self.probe_var.set(self.empty_var)
        self.probe_combobox = ttk.Combobox(form_frame, textvariable=self.probe_var, values=list(probes.keys()), state="readonly")
        self.probe_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(form_frame, text="Crucible:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.crucible_var = tk.StringVar(self)
        self.crucible_var.set(self.empty_var)
        self.crucible_combobox = ttk.Combobox(form_frame, textvariable=self.crucible_var, values=list(crucibles.keys()), state="readonly")
        self.crucible_combobox.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(form_frame, text="Sample:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.sample_var = tk.StringVar(self)
        self.sample_var.set(self.empty_var)
        self.sample_combobox = ttk.Combobox(form_frame, textvariable=self.sample_var, values=list(samples.keys()), state="readonly")
        self.sample_combobox.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(form_frame, text="Simulation Cross-section:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.cross_section_var = tk.StringVar(self)
        self.cross_section_var.set(self.cross_sections[0]) # default to radial
        self.cross_section_combobox = ttk.Combobox(form_frame, textvariable=self.cross_section_var, values=cross_sections, state="readonly")
        self.cross_section_combobox.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # --- Decision Variables ---
        ttk.Label(form_frame, text="Decision Variables:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.decision_vars_box = tk.Listbox(form_frame, selectmode=tk.MULTIPLE, exportselection=False) # selectmode can be SINGLE, BROWSE, MULTIPLE, or EXTENDED
        self.decision_vars_box.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        for x in decision_vars.keys():
            self.decision_vars_box.insert(tk.END, x)

        # Select the default items
        self.decision_vars_box.selection_set(0) 
        self.decision_vars_box.selection_set(3)

        # --- Data Folder Selection ---
        ttk.Label(form_frame, text="Experimental Data Folder:").grid(row=6, column=0, padx=10, pady=5, sticky="e")
        self.folder_label = ttk.Label(form_frame, text="No folder selected", wraplength=250, justify="left")
        self.folder_label.grid(row=7, column=1, padx=10, pady=5, sticky="w")
        ttk.Button(form_frame, text="Select Folder", command=self.select_folder).grid(row=6, column=1, padx=10, pady=5, sticky="w")

        # --- Advanced Settings Button ---
        self.adv_settings = None
        ttk.Button(form_frame, text="Advanced Settings", command=self.open_advanced_settings).grid(row=8, column=0, columnspan=2, pady=10)

        # --- Proceed Button ---
        self.proceed_button = ttk.Button(form_frame, text="Proceed", state="disabled", command=self.proceed)
        self.proceed_button.grid(row=9, column=0, columnspan=2, pady=15)
        self.test_folder_path = None

    def select_folder(self):
        self.test_folder_path = filedialog.askdirectory(title="Select an experimental data folder", initialdir=".")
        if self.test_folder_path:
            self.folder_label.config(text=self.test_folder_path)
            self.proceed_button.config(state="normal")
        else:
            self.folder_label.config(text="No folder selected")
            self.proceed_button.config(state="disabled")
        

    def open_advanced_settings(self):
        if self.adv_settings is None or not self.adv_settings.winfo_exists():
            self.adv_settings = AdvancedSettings(self, self.advanced_settings_values)
        else:
            self.adv_settings.lift()  # bring existing window to front


    def check_selections(self):
        # Get selected indices
        self.decision_vars_indx = self.decision_vars_box.curselection()  # returns a tuple of selected indices

        # check for emptiness
        if (
            not self.test_folder_path
            or self.crucible_var.get() == self.empty_var
            or self.probe_var.get() == self.empty_var
            or self.sample_var.get() == self.empty_var
            or not self.decision_vars_indx   # empty tuple evaluates to False
            or self.cross_section_var.get() == self.empty_var
        ):
            messagebox.showerror(
                "Error",
                "Please select a folder, crucible, probe, sample, cross-section, and at least one decision variable."
            )

            return True
        
        # Set overide test duration to None if no input is given.        
        val = self.advanced_settings_values["override test duration"]
        if isinstance(val, (int, float)) and abs(val) < 1e-12:
            self.advanced_settings_values["override test duration"] = None

        return False
    

    def proceed(self):
        if self.check_selections():
            return
        
        print("Proceeding with:")
        print(f"### Probe: {self.probe_var.get()}")
        print(f"### Crucible: {self.crucible_var.get()}")
        print(f"### Sample: {self.sample_var.get()}")
        print(f"### Cross-section: {self.cross_section_var.get()}")
        print(f"### Decision Variables: {[list(self.decision_vars.keys())[i] for i in self.decision_vars_indx]}")
        print(f"### Folder: {self.test_folder_path}")
        print("### Advanced Settings:", self.advanced_settings_values)

        self.user_cancelled = False
        self.destroy()  # close the GUI

    def get_selections(self):
        return {
            "probe": self.probe_var.get(),
            "crucible": self.crucible_var.get(),
            "sample": self.sample_var.get(),
            "decision variables indices": self.decision_vars_indx,
            "folder": self.test_folder_path
        }

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    crucibles = {"Steel316": {}, "Nickel200": {}, "Inconel625": {}}
    probes = {"ProbeA": {}, "ProbeB": {}}
    samples ={
    "Sample A": {"property1": 1.0, "property2": 2.0},
    "Sample B": {"property1": 1.1, "property2": 2.1},
    "Sample C": {"property1": 1.2, "property2": 2.2},
    "Sample D": {"property1": 1.3, "property2": 2.3},
    "Sample E": {"property1": 1.4, "property2": 2.4},
    "Sample F": {"property1": 1.5, "property2": 2.5},
    "Sample G": {"property1": 1.6, "property2": 2.6},
    "Sample H": {"property1": 1.7, "property2": 2.7},
    "Sample I": {"property1": 1.8, "property2": 2.8},
    "Sample J": {"property1": 1.9, "property2": 2.9},
    "Sample K": {"property1": 2.0, "property2": 3.0},
    "Sample L": {"property1": 2.1, "property2": 3.1},
    "Sample M": {"property1": 2.2, "property2": 3.2},
    "Sample N": {"property1": 2.3, "property2": 3.3},
    "Sample O": {"property1": 2.4, "property2": 3.4},
    "Sample P": {"property1": 2.5, "property2": 3.5},
    "Sample Q": {"property1": 2.6, "property2": 3.6},
    "Sample R": {"property1": 2.7, "property2": 3.7},
    "Sample S": {"property1": 2.8, "property2": 3.8},
    "Sample T": {"property1": 2.9, "property2": 3.9},
    }
    decision_variables = [
    "Thermal Conductivity",
    "Specific Heat",
    "Density",
    "Emissivity",
    "Porosity",
    "Heat Capacity",
    "Thermal Diffusivity",
    "Wire Radius",
    "Probe Length",
    "Crucible Radius",
    "Sample Thickness",
    "Contact Resistance",
    "Ni Sheath Thickness",
    "Alumina Layer Thickness",
    "Wire Spacing",
    "Probe Tip Offset",
    "Heating Power",
    "Measurement Interval",
    "Data Smoothing Factor",
    "Calibration Coefficient",
    "Ambient Temperature",
    "Sample Composition",
    "Nickel Oxide Fraction",
    "Alumina Purity",
    "Probe Material Factor"
    ]

    cross_sections = ["radial", "axial"]

    options = SimulationOptions(crucibles, probes, samples, probes, cross_sections)
    options.mainloop()   # waits here until window closes

    if getattr(options, "user_cancelled", True):
        print("User closed the window without proceeding. Exiting program.")
    else:
        selections = options.get_selections()
        print(selections)  # or use selections in your simulation