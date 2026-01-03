import tkinter as tk
from tkinter import ttk, filedialog

class CalibrationMenu(tk.Toplevel):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.title("Advanced Settings")
        self.resizable(False, False)

        # Layout
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)

