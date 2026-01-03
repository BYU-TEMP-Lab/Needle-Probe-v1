import tkinter as tk
from tkinter import ttk, filedialog

class AdvancedSettings(tk.Toplevel):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.title("Advanced Settings")
        self.resizable(False, False)

        # Variables for settings
        self.test_duration_override = tk.StringVar(value=parent.defaults.get("test duration override"))
        self.plot_frequency = tk.StringVar(value=parent.defaults.get("plot frequency"))
        self.chi2_tolerance = tk.StringVar(value=parent.defaults.get("chi2 tolerance"))

        # Layout
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Override Test Duration (s):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.test_duration_override).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Plot Frequency (iterations):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.plot_frequency).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Chi² Tolerance:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.chi2_tolerance).grid(row=2, column=1, padx=5, pady=5)

        # --- Default Setting Selection ---
        ttk.Label(form, text="Default Settings File:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.default_file_label = ttk.Label(form, text=parent.default_filename, wraplength=250, justify="left")
        self.default_file_label.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(form, text="Load Defaults", command=self.get_defaults).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self.save_and_close_button = ttk.Button(form, text="Save and Close", command=self.save_and_close)
        self.save_and_close_button.grid(row=5, column=0, columnspan=2, pady=10)

    def get_defaults(self):
        selected_file = filedialog.askopenfilename(
            title="Select Default Settings JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir="."
        )
        if selected_file:
            self.parent.load_defaults_file(selected_file)
            self.default_file_label.config(text=selected_file)
            self.parent.update_defaults()
            self._update_defaults()
            self.save_and_close_button.config(state="normal")

    def _update_defaults(self):
        self.test_duration_override.set(self.parent.defaults.get("test duration override"))
        self.plot_frequency.set(self.parent.defaults.get("plot frequency"))
        self.chi2_tolerance.set(self.parent.defaults.get("chi2 tolerance"))

    def save_and_close(self):
        self.parent.override_dur = self.test_duration_override.get()
        self.parent.plot_freq = self.plot_frequency.get()
        self.parent.chi2_tol = self.chi2_tolerance.get()
        self.destroy()

    # def get_settings(self):
    #     """Return settings as a dict."""
    #     return {
    #         "override test duration": self.test_duration_override.get(),
    #         "plot frequency": self.plot_frequency.get(),
    #         "Chi2 tolerance": self.chi2_tolerance.get()
        # }