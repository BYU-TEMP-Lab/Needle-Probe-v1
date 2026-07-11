import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from ..build_model import model_param_map as decision_vars

class AdvancedSettings(tk.Toplevel):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.title("Advanced Settings")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Variables for settings
        # self.test_duration_override = tk.StringVar(value=parent.defaults.get("test duration override"))
        # self.plot_frequency = tk.StringVar(value=parent.defaults.get("plot frequency"))
        # self.chi2_tolerance = tk.StringVar(value=parent.defaults.get("chi2 tolerance"))
        # self.convection_coefficient = tk.StringVar(value=parent.defaults.get("convection coefficient"))
        self.test_duration_override = tk.StringVar(value=parent.override_dur)
        self.plot_frequency = tk.StringVar(value=parent.plot_freq)
        self.chi2_tolerance = tk.StringVar(value=parent.chi2_tol)
        self.convection_coefficient = tk.StringVar(value=parent.convection_coeff)

        self.parameter_names = list(getattr(parent, "decision_vars", decision_vars).keys())
        self._sensitivity_mode = self._is_sensitivity_mode()

        # Layout
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Override Test Duration (s):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.test_duration_entry = ttk.Entry(form, textvariable=self.test_duration_override)
        self.test_duration_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Plot Frequency (iterations):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.plot_frequency_entry = ttk.Entry(form, textvariable=self.plot_frequency)
        self.plot_frequency_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Chi² Tolerance:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.chi2_tolerance_entry = ttk.Entry(form, textvariable=self.chi2_tolerance)
        self.chi2_tolerance_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Convection Coefficient:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.convection_coefficient_entry = ttk.Entry(form, textvariable=self.convection_coefficient)
        self.convection_coefficient_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # --- Default Setting Selection ---
        ttk.Label(form, text="Default Settings File:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.default_file_label = ttk.Label(
            form,
            text="/".join(parent.default_file_path.parts[-2:]),
            wraplength=250,
            justify="left",
        )
        self.default_file_label.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form, text="Load Defaults", command=self.get_defaults).grid(row=4, column=2, padx=5, pady=5, sticky="w")

        ttk.Separator(form, orient="horizontal").grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 8))

        ttk.Label(form, text="Decision Variables:").grid(row=6, column=0, padx=5, pady=5, sticky="ne")
        selection_frame = ttk.Frame(form)
        selection_frame.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        selection_frame.columnconfigure(0, weight=1)

        self.parameter_listbox = tk.Listbox(
            selection_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=12,
            width=45,
        )
        self.parameter_listbox.grid(row=0, column=0, sticky="ew")

        parameter_scrollbar = ttk.Scrollbar(selection_frame, orient="vertical", command=self.parameter_listbox.yview)
        parameter_scrollbar.grid(row=0, column=1, sticky="ns")
        self.parameter_listbox.configure(yscrollcommand=parameter_scrollbar.set)

        for name in self.parameter_names:
            self.parameter_listbox.insert(tk.END, name)

        self.parameter_hint = ttk.Label(
            form,
            text="Calibration defaults to all parameters. Thermal conductivity measurement defaults to Sample k only.",
            wraplength=380,
            justify="left",
        )
        self.parameter_hint.grid(row=7, column=1, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        self.save_and_close_button = ttk.Button(form, text="Save and Close", command=self.save_and_close)
        self.save_and_close_button.grid(row=8, column=0, columnspan=3, pady=10)

        if self._sensitivity_mode:
            self._disable_non_default_fields()

        self._apply_parameter_defaults()

    def get_defaults(self):
        selected_file = filedialog.askopenfilename(
            title="Select Default Settings JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir="."
        )
        if selected_file:
            selected_path = Path(selected_file)
            self.parent.load_defaults_file(selected_path)
            self.default_file_label.config(text="/".join(selected_path.parts[-2:]))
            self.parent.update_defaults()
            self._update_defaults()
            self.save_and_close_button.config(state="normal")

    def _update_defaults(self):
        self.test_duration_override.set(self.parent.defaults.get("test duration override"))
        self.plot_frequency.set(self.parent.defaults.get("plot frequency"))
        self.chi2_tolerance.set(self.parent.defaults.get("chi2 tolerance"))
        self.convection_coefficient.set(self.parent.defaults.get("convection coefficient"))

    def _is_sensitivity_mode(self):
        task = getattr(self.parent, "task_mode", None)
        if task is None and hasattr(self.parent, "task_mode_var"):
            task = self.parent.task_mode_var.get()
        return task == "Sensitivity analysis"

    def _disable_non_default_fields(self):
        for widget in (
            self.test_duration_entry,
            self.plot_frequency_entry,
            self.chi2_tolerance_entry,
            self.convection_coefficient_entry,
        ):
            widget.configure(state="disabled")
        self.parameter_hint.configure(text="Sensitivity analysis uses the defaults loader plus parameter selection.")

    def _default_parameter_names(self):
        task = getattr(self.parent, "task_mode", None)
        if task is None and hasattr(self.parent, "task_mode_var"):
            task = self.parent.task_mode_var.get()

        if task == "Thermal conductivity measurement":
            return ["Sample k"]

        return list(self.parameter_names)

    def _apply_parameter_defaults(self):
        default_names = getattr(self.parent, "selected_parameters", None) or self._default_parameter_names()
        self.parameter_listbox.selection_clear(0, tk.END)
        for index, name in enumerate(self.parameter_names):
            if name in default_names:
                self.parameter_listbox.selection_set(index)

    def get_selected_parameters(self):
        selected_indices = self.parameter_listbox.curselection()
        return [self.parameter_names[index] for index in selected_indices]

    def save_and_close(self):
        self.parent.override_dur = self.test_duration_override.get()
        self.parent.plot_freq = self.plot_frequency.get()
        self.parent.chi2_tol = self.chi2_tolerance.get()
        self.parent.convection_coeff = self.convection_coefficient.get()
        self.parent.selected_parameters = self.get_selected_parameters()
        self.parent.decision_vars_indx = list(self.parameter_listbox.curselection())
        self.destroy()

    # def get_settings(self):
    #     """Return settings as a dict."""
    #     return {
    #         "override test duration": self.test_duration_override.get(),
    #         "plot frequency": self.plot_frequency.get(),
    #         "Chi2 tolerance": self.chi2_tolerance.get()
        # }