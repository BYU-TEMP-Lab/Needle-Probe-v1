import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
import warnings
from dataclasses import dataclass, field
from typing import Tuple

@dataclass
class FileData:
    """Load and process experimental data from a single file."""
    filepath: Path
    V_min_cutoff: float  # Voltage threshold to detect when heating starts
    test_duration_overide: float # Optional override for test duration in seconds; if None, uses voltage cutoff to determine end of test
    generate_plots: bool # Whether to generate plots of the raw data and processed deltaT curve in preparation for saving
    plot_dir: Path # location to save plots if generated

    # # Processed data fields (populated in __post_init__)
    # tempData: np.ndarray = field(default=None, init=False)
    # tempData_std: float = field(default=None, init=False)
    # avgT_amb_K: ParameterEstimate = field(default=None, init=False)
    # avgQ: ParameterEstimate = field(default=None, init=False)
    
    def __post_init__(self):
        """Process the file on initialization."""
        self._process_data()

    def _read_data(self):
        """
        Reads experimental data from a tab-separated file.
        Expected format: [Time, Temp, Voltage, Current]
        """
        # Read CSV or txt file (assuming tab-separated)
        df = pd.read_csv(self.filepath, sep="\t", header=None)  # Adjust header if needed
        _, N_cols = df.shape
        print(f"Importing {self.filepath.name} with {N_cols} columns...")

        if N_cols != 4:
            raise ValueError(
                f"Function 'read_data' received {N_cols} columns, but requires exactly 4 "
                "(Time, Temp, Voltage, Current)."
            )
        
        # Unpack columns
        time = df.iloc[:, 0].values # s
        temp = df.iloc[:, 1].values # C
        voltage = df.iloc[:, 2].values # V
        current = df.iloc[:, 3].values # mA

        return time, temp, voltage, current

    def _get_start_stop(self, voltage, time):
        # Find first applied voltage > V_min_cutoff to establish t=0
        V_inx = np.where(voltage > self.V_min_cutoff)[0] # indices where voltage is above cutoff
        if len(V_inx) == 0:
            raise ValueError(f"No voltage above {self.V_min_cutoff} V found in data.")
        V_start = V_inx[0]-1 # index of start time (subtract one for t=0 instead of t=1)

        # And then t_final the last index where voltage > V_min_cutoff
        if self.test_duration_overide is None:
            V_end = V_inx[-1] # returns index of last True, or 0 if none
        else:
            try:
                V_end = np.where(time >= time[V_start] + self.test_duration_overide)[0][0]  # end time based on sample length
            except IndexError:
                warnings.warn(
                f"Overide sample length {self.test_duration_overide} s passed to 'extract_data' "
                "is longer than the collected sample time. "
                "Falling back to end of heating period.",
                UserWarning
                )
                V_end = V_inx[-1]

        return V_start, V_end

    def _process_data(self):
        """
        Given filename (and optionally the test length in seconds and 
        Voltage to detect the heating wire is active in Volts),
        reads 4-column experimental data (tab delimited) and returns filtered deltaT-time 
        array during the time the heating wire is active,
        average power applied, and ambient temperature in Kelvin.
        """

        time_raw, temp_raw, voltage_raw, current_raw = self._read_data()
        V_start, V_end = self._get_start_stop(voltage_raw, time_raw)

        # Ambient temperature
        avgT_amb_C = np.mean(temp_raw[:V_start-1])
        self.avgT_amb_K = avgT_amb_C + 273.15  # Convert Celsius to Kelvin (used in heat transfer eq.)

        # Estimate noise
        temp_noise_std = np.std(temp_raw[:V_start-1], ddof=1) # standard deviation of temperature noise
        self.temp_amb_sem = temp_noise_std / np.sqrt(V_start-1) # standard error of the mean for ambient temp

        # Align time, temp, Voltage, and Current with V_start and V_end
        self.time = time_raw[V_start:V_end] - time_raw[V_start]
        self.deltaT = temp_raw[V_start:V_end] - avgT_amb_C # deltaT = temp - avgT_amb
        self.voltage = voltage_raw[V_start:V_end]
        self.current = current_raw[V_start:V_end]

        # Average voltage during heating period, standard deviation, and standard error
        avgVoltage = np.mean(self.voltage)
        std_V = np.std(self.voltage, ddof=1)
        sem_V = std_V / np.sqrt(len(self.voltage))

        # Average current during heating period, standard deviation, and standard error
        avgCurrent = np.nanmean(self.current) / 1000  # Convert mA to A
        std_I = np.nanstd(self.current, ddof=1) / 1000
        n_valid = np.count_nonzero(~np.isnan(self.current)) # handle NaN values
        sem_I = std_I / np.sqrt(n_valid) if n_valid > 0 else 0

        # Average power applied during heating period, error propagation for standard error
        self.avgQ = avgVoltage * avgCurrent
        # semQ = avgQ * np.sqrt((sem_V / avgVoltage)**2 + (sem_I / avgCurrent)**2)
        self.semQ = np.sqrt((avgCurrent * sem_V)**2 + (avgVoltage * sem_I)**2) # taylor series error propogation

        # generate plots for optional saving
        if self.generate_plots:
            self._generate_plot(time_raw, temp_raw, voltage_raw, current_raw)

    def print_summary(self):
        print(f"File: {self.filepath.name}")
        print(f"  Ambient Temperature: {self.avgT_amb_K-273.15:.2f} C ± {self.temp_amb_sem:.4f} C")
        print(f"  Average Power: {self.avgQ:.4f} W ± {self.semQ:.4f} W")
        print(f"  Test length: {self.time[-1]:.4f} seconds")
        print(f"  Temp range: {self.deltaT.min() + self.avgT_amb_K -273.15:.4f} to {self.deltaT.max() + self.avgT_amb_K -273.15:.4f} C (Diff = {self.deltaT.max() - self.deltaT.min():.4f} C)")

    def _generate_plot(self, time_raw, temp_raw, voltage_raw, current_raw):
        # Create two stacked subplots sharing the x-axis (time)
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(9, 8))

        # Raw temperature vs time (full record)
        ax1.scatter(time_raw, temp_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Ambient temp: {self.avgT_amb_K-273.15:.2f} C")
        ax1.set_ylabel("Temperature (C)")
        ax1.legend(markerscale=10, loc="lower center")
        ax1.set_title(f"{self.filepath.name}")

        # Voltage vs time (full record)
        ax2.scatter(time_raw, voltage_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Average Measured Voltage: {np.mean(self.voltage):.2f} V")
        ax2.set_ylabel("Voltage (V)")
        ax2.set_xlabel("Time (s)")
        ax2.legend(markerscale=10, loc="lower center")

        # current vs time (full record)
        ax3.scatter(time_raw, current_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Average Measured Current: {np.nanmean(self.current):.2f} mA")
        ax3.set_ylabel("Current (mA)")
        ax3.set_xlabel("Time (s)")
        ax3.legend(markerscale=10, loc="lower center")
        
        ax4.scatter(self.time, self.deltaT, s=0.6, c="r", alpha=0.6,
                    label=f"Temperature Difference: {self.deltaT.min() + self.avgT_amb_K -273.15:.4f} to {self.deltaT.max() + self.avgT_amb_K -273.15:.4f} C ({self.deltaT.max() - self.deltaT.min():.4f} C range)")
        ax4.set_xlabel(r"$\Delta t$ (s)")
        ax4.set_ylabel(r"$\Delta T$ (C)")
        # ax4.set_xscale("log")
        ax4.legend(markerscale=10, loc="lower center")

        fig.tight_layout()
        self.plot = fig
        self.plot.savefig(self.plot_dir / f"{self.filepath.stem}_raw_data.png", dpi=200, bbox_inches="tight")
    
    def show_plot(self):
        if not hasattr(self, "plot"):
            print("No plot available to show. Please ensure 'generate_plots' is set to True and that the data was processed successfully. Check {self.plot_dir} for saved plots.")
            return
        
        self.plot.show()
        plt.show(block=True)
        plt.close(self.plot)
        
def get_folder_data(data_folder: Path, V_min_cutoff=0.5, test_duration_overide=None, generate_plots: bool = True):
    """Load and process all .txt files from a folder, returning FileData instances."""
    print(f"Importing data from {data_folder.name}...")
    folder_data = []

    if generate_plots:
        out_dir = data_folder.resolve() / "raw_data_plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Plots will be saved to: {out_dir}")


    for file_path in data_folder.glob("*.txt"):
        # Ensure we are not trying to process sub-folders
        if file_path.is_file():   
            try:
                file_data = FileData(
                    file_path, 
                    V_min_cutoff=V_min_cutoff,
                    test_duration_overide=test_duration_overide,
                    generate_plots=generate_plots,
                    plot_dir=out_dir
                    )
                file_data.print_summary()
                folder_data.append(file_data)
                
            except Exception as e:
                print(f"Could not process {file_path.name}: {e}")

    if not folder_data:
        print(f"Unable to successfully read any .txt files from folder: {data_folder.absolute()}.")
        return None

    return folder_data

if __name__ == "__main__":
    # process_data("./MATLAB_ONLY/FLiNaK_730C_3V_1 (1).txt", test_duration=10.0)
    filepath = Path("./MATLAB_ONLY/FLiNaK_730C_3V_1 (1).txt")
    file_data = FileData(filepath, V_min_cutoff=0.5, generate_plots=True)
    file_data.print_summary()
    file_data.show_plot()