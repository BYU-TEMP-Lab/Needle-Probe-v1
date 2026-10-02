# testing_gui.py
import tkinter as tk
from tkinter import ttk
import threading
import time
import os
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Hardware Drivers (Ensure these are in your /drivers folder)
# from labjack import ljm
from drivers.agilent_e3633a import AGILENT_E3633A
from drivers.labjack_t7 import LABJACK_T7

# --- EXPERIMENT PARAMETERS ---
TEST_VOLTAGES = [3.0, 4.0, 5.0, 3.0, 4.0, 5.0] 
AMBIENT_RECORD_TIME = 5.0  
HEATING_TIME = 30.0        
COOLING_RECORD_TIME = 2.0  
EQUILIBRIUM_WINDOW = 30.0     
EQUILIBRIUM_CHUNKS = 6        
EQUILIBRIUM_TOLERANCE = 0.2   

class NeedleProbeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Needle Probe DAQ Control")
        
        # Data storage for live plots (keeps the last 500 points for performance)
        self.plot_time = deque(maxlen=500)
        self.plot_temp = deque(maxlen=500)
        self.plot_volt = deque(maxlen=500)
        self.plot_curr = deque(maxlen=500)
        
        # Thread control flags
        self.running = False
        self.wait_for_temp_flag = False
        self.daq_thread = None
        
        self.setup_ui()
        self.init_hardware()
        
        # Start GUI update loop
        self.update_plots()

    def init_hardware(self):
        """Initializes the LabJack and Agilent hardware."""
        self.log_message("Initializing Hardware...")
        try:
            self.psu = AGILENT_E3633A()
            self.psu.disableOutput()
            self.daq = LABJACK_T7()
            
            self.daq.addSingleEndedTC('AIN0') 
            ljm.eWriteName(self.daq.handle, "AIN2_NEGATIVE_CH", 3)
            ljm.eWriteName(self.daq.handle, "AIN2_RANGE", 10.0)
            ljm.eWriteName(self.daq.handle, "AIN4_NEGATIVE_CH", 199)
            ljm.eWriteName(self.daq.handle, "AIN4_RANGE", 10.0)
            self.log_message("Hardware Ready.")
        except Exception as e:
            self.log_message(f"Hardware Error: {e}")

    def setup_ui(self):
        """Builds the Tkinter layout."""
        # --- Control Panel (Left Side) ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="nswe")
        
        ttk.Label(control_frame, text="Sample Name:").grid(row=0, column=0, sticky="w")
        self.entry_sample = ttk.Entry(control_frame)
        self.entry_sample.insert(0, "MoltenSalt_Batch1")
        self.entry_sample.grid(row=1, column=0, pady=5, sticky="we")
        
        ttk.Label(control_frame, text="Furnace Target Temp (°C):").grid(row=2, column=0, sticky="w")
        self.entry_temp = ttk.Entry(control_frame)
        self.entry_temp.insert(0, "500")
        self.entry_temp.grid(row=3, column=0, pady=5, sticky="we")
        
        self.btn_wait = ttk.Button(control_frame, text="Wait for Equilibrium", command=self.trigger_wait)
        self.btn_wait.grid(row=4, column=0, pady=10, sticky="we")
        
        self.btn_start = ttk.Button(control_frame, text="Start Sequence", command=self.start_sequence)
        self.btn_start.grid(row=5, column=0, pady=10, sticky="we")
        
        self.btn_stop = ttk.Button(control_frame, text="Emergency Stop", command=self.stop_sequence)
        self.btn_stop.grid(row=6, column=0, pady=10, sticky="we")
        
        # Console output
        self.console = tk.Text(control_frame, height=15, width=40)
        self.console.grid(row=7, column=0, pady=10)
        
        # --- Plots (Right Side) ---
        plot_frame = ttk.Frame(self.root)
        plot_frame.grid(row=0, column=1, sticky="nswe")
        
        self.fig, (self.ax_temp, self.ax_volt, self.ax_curr) = plt.subplots(3, 1, figsize=(8, 8))
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def log_message(self, msg):
        """Prints to the GUI text box."""
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        print(msg)

    def trigger_wait(self):
        """Operator button to manually start the equilibrium wait phase."""
        self.wait_for_temp_flag = True
        self.log_message("Flag set: Will wait for equilibrium before next test.")

    def start_sequence(self):
        if self.running:
            return
        self.running = True
        sample_name = self.entry_sample.get()
        target_temp = self.entry_temp.get()
        
        # Start the hardware DAQ loop in a background thread
        self.daq_thread = threading.Thread(target=self.hardware_loop, args=(sample_name, target_temp), daemon=True)
        self.daq_thread.start()

    def stop_sequence(self):
        self.running = False
        try:
            self.psu.disableOutput()
        except:
            pass
        self.log_message("Sequence Stopped by Operator.")

    def update_plots(self):
        """Periodically refreshes the matplotlib canvases with new data."""
        if self.running and len(self.plot_time) > 0:
            self.ax_temp.clear()
            self.ax_volt.clear()
            self.ax_curr.clear()
            
            self.ax_temp.plot(self.plot_time, self.plot_temp, color='red')
            self.ax_temp.set_title("Temperature (°C)")
            
            self.ax_volt.plot(self.plot_time, self.plot_volt, color='blue')
            self.ax_volt.set_title("Voltage (V)")
            
            self.ax_curr.plot(self.plot_time, self.plot_curr, color='green')
            self.ax_curr.set_title("Current (A)")
            
            self.canvas.draw()
            
        # Call this function again every 500ms
        self.root.after(500, self.update_plots)

    def hardware_loop(self, sample_name, target_temp):
        """The background thread that communicates with hardware and runs logic."""
        data_dir = os.path.join("data", sample_name)
        os.makedirs(data_dir, exist_ok=True)
        
        read_names = ["AIN0_EF_READ_A", "AIN2", "AIN4"]
        num_frames = len(read_names)
        
        start_time_global = time.perf_counter()
        
        for test_idx, target_v in enumerate(TEST_VOLTAGES):
            if not self.running: break
            
            test_num = test_idx + 1
            filename = os.path.join(data_dir, f"Test_{test_num}_{target_temp}C_{int(target_v)}V.txt")
            
            # --- Wait for Equilibrium Phase ---
            # If it's the first test, or if the operator pressed the button
            if test_idx == 0 or self.wait_for_temp_flag:
                self.log_message(f"Waiting for thermal equilibrium...")
                self.wait_for_temp_flag = False # Reset flag
                
                history = deque(maxlen=60) # Fast, rough equilibrium check
                while self.running:
                    current_temp = ljm.eReadName(self.daq.handle, 'AIN0_EF_READ_A')
                    history.append(current_temp)
                    
                    # Update live plots even during the wait phase
                    t_now = time.perf_counter() - start_time_global
                    self.plot_time.append(t_now)
                    self.plot_temp.append(current_temp)
                    self.plot_volt.append(0.0)
                    self.plot_curr.append(0.0)
                    
                    if len(history) == 60:
                        if (max(history) - min(history)) < EQUILIBRIUM_TOLERANCE:
                            self.log_message(f"Equilibrium Reached at {current_temp:.2f}°C")
                            break
                    time.sleep(0.5)

            if not self.running: break

            # --- Active Test Phase ---
            self.log_message(f"Starting Test {test_num}/6 at {target_v}V")
            self.psu.setVoltage(target_v)
            
            data_log = []
            t_start = time.perf_counter()
            t_heat_start = t_start + AMBIENT_RECORD_TIME
            t_heat_end = t_heat_start + HEATING_TIME
            t_total_end = t_heat_end + COOLING_RECORD_TIME
            heater_on = False
            
            while self.running:
                current_t = time.perf_counter()
                elapsed_t = current_t - t_start
                
                if elapsed_t >= t_total_end:
                    break
                    
                if elapsed_t >= AMBIENT_RECORD_TIME and elapsed_t < t_heat_end and not heater_on:
                    self.psu.enableOutput()
                    heater_on = True
                    self.log_message(f"[{elapsed_t:.1f}s] Heater ON")
                    
                if elapsed_t >= t_heat_end and heater_on:
                    self.psu.disableOutput()
                    heater_on = False
                    self.log_message(f"[{elapsed_t:.1f}s] Heater OFF")

                results = ljm.eReadNames(self.daq.handle, num_frames, read_names)
                data_log.append(f"{elapsed_t:.4f},{results[0]:.4f},{results[1]:.4f},{results[2]:.4f}")
                
                # Update GUI plotting queues
                self.plot_time.append(current_t - start_time_global)
                self.plot_temp.append(results[0])
                self.plot_volt.append(results[1])
                self.plot_curr.append(results[2])

            self.psu.disableOutput()
            
            self.log_message(f"Saving {filename}")
            with open(filename, 'w') as f:
                f.write("Time(s),Temperature(C),Voltage(V),Current(A)\n")
                f.write("\n".join(data_log))

        self.log_message("Sequence Complete.")
        self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = NeedleProbeGUI(root)
    
    # Graceful shutdown of hardware when user clicks the 'X'
    def on_closing():
        app.running = False
        try:
            app.psu.disableOutput()
            app.psu.shutdown()
            app.daq.shutdown()
        except:
            pass
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()