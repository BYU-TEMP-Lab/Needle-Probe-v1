import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..libraries.calibrations import options as cal_dict

class CalibrationMenu(tk.Toplevel):
    def __init__(self, parent, current_config):
        super().__init__(parent)
        self.parent = parent
        self.title("Calibration Menu")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Initialize the validation flag
        self.validated_selections = False
        self.complete = False

        # check for calibration files
        matches = [name for name, obj in cal_dict.items() if [obj.probe, obj.crucible] == current_config]
        self.cal_options = matches + ["Use uncalibrated parameters"]

        # Layout
        self.form = ttk.Frame(self, padding=10)
        self.form.pack(fill="both", expand=True)

        # select previous calibration combobox
        self.cal_select_label = ttk.Label(self.form, text="Select Calibration:")
        self.cal_select_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.selected_calibration = tk.StringVar(self)
        self.cal_combobox = ttk.Combobox(self.form, textvariable=self.selected_calibration, values=list(self.cal_options), state="readonly", width=50)
        self.cal_combobox.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # perform new calibration checkbox
        self.perf_new_cal_label = ttk.Label(self.form, text="Perform New Calibration")
        self.perf_new_cal_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.perf_cal_var = tk.IntVar()
        self.perf_cal_checkbox = tk.Checkbutton(
            self.form,
            variable=self.perf_cal_var, # Link the variable to the checkbox
            command=self.update_gui,
        )
        self.perf_cal_checkbox.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.proceed_button = ttk.Button(self.form, text="Proceed", command=self.save_and_close)
        self.proceed_button.grid(row=5, column=0, columnspan=2, pady=10)

        self.update_idletasks()

    def update_gui(self):
        if self.perf_cal_var.get():
            self.cal_combobox.grid_remove()
            self.cal_select_label.grid_remove()
            self.perf_cal_checkbox.grid(row=0, column = 1)
            self.perf_new_cal_label.grid(row = 0, column = 0)
        else:
            self.cal_combobox.grid()
            self.cal_select_label.grid()
            self.perf_cal_checkbox.grid(row=1, column = 1)
            self.perf_new_cal_label.grid(row = 1, column = 0)

    def check_selections(self):
        if self.perf_cal_var.get():
            if self.parent.sample_var.get() not in ["Argon"]:
                messagebox.showerror(
                "Error",
                f"{self.parent.sample_var.get()} is not a valid calibration medium."
                )
                self.validated_selections = False
            else:
                self.validated_selections = True
        else:
            if not self.selected_calibration.get() in self.cal_options:
                messagebox.showerror(
                "Error",
                f"{self.selected_calibration.get()} is not a valid calibration selection."
                )
                self.validated_selections = False
            else:
                self.validated_selections = True

    def return_selections(self):
        self.parent.perf_calibration = self.perf_cal_var.get()

        if self.perf_cal_var.get() == 1 or self.selected_calibration.get() == "Use uncalibrated parameters":
            self.parent.calibration = None
        else:
            self.parent.calibration = cal_dict[self.selected_calibration.get()]

    def save_and_close(self):
        self.check_selections()
        if self.validated_selections:
            self.return_selections()
            self.complete = True
            self.destroy()
