import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from .bootstrap import setup_logging

logger = logging.getLogger(__name__)

@dataclass
class FileData:
    """Load and process experimental data from a single file."""
    filepath: Path
    V_min_cutoff: float  # Voltage threshold to detect when heating starts
    test_duration_overide: float # Optional override for test duration in seconds; if None, uses voltage cutoff to determine end of test
    generate_plots: bool # Whether to generate plots of the raw data and processed deltaT curve in preparation for saving
    plot_dir: Path # location to save plots if generated
    current_units: str  # Units for the current data (e.g., "mA", "A")

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

        Returns: (time, temp, voltage, current)
        """
        # Read CSV or txt file (assuming tab-separated)
        df = pd.read_csv(self.filepath, sep="\t", header=None)  # Adjust header if needed
        _, N_cols = df.shape
        logger.info("Importing %s with %s columns...", self.filepath.name, N_cols)

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
        """
        Determines the start and stop indices of the heating period based on voltage threshold.
        
        Returns: (V_start, V_end)
        """
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
        if self.current_units not in ["mA", "A"]:
            raise ValueError(f"Invalid current_units '{self.current_units}'. Must be 'mA' or 'A'.")
        elif self.current_units == "mA":
            current_raw = current_raw / 1000  # Convert mA to A
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
        if self.current_units == "mA":
            self.current = self.current
        self.power = self.voltage * self.current  # Power in Watts (V * A)

        # Average voltage during heating period, standard deviation, and standard error
        avgVoltage = np.mean(self.voltage)
        std_V = np.std(self.voltage, ddof=1)
        sem_V = std_V / np.sqrt(len(self.voltage))

        # Average current during heating period, standard deviation, and standard error
        avgCurrent = np.nanmean(self.current)
        std_I = np.nanstd(self.current, ddof=1)
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
        logger.info("File: %s", self.filepath.name)
        logger.info("  Ambient Temperature: %.2f C ± %.4f C", self.avgT_amb_K - 273.15, self.temp_amb_sem)
        logger.info(
            "  Temp range: %.4f to %.4f C (Diff = %.4f C)",
            self.deltaT.min() + self.avgT_amb_K - 273.15,
            self.deltaT.max() + self.avgT_amb_K - 273.15,
            self.deltaT.max() - self.deltaT.min(),
        )
        logger.info("  Average Power: %.4f W ± %.6f W", self.avgQ, self.semQ)
        logger.info("  Test length: %.4f seconds", self.time[-1])

    def _generate_plot(self, time_raw, temp_raw, voltage_raw, current_raw):
        # Create stacked subplots
        fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(9, 10))

        # Voltage vs time (full record)
        ax1.scatter(time_raw, voltage_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Average Measured Voltage: {np.mean(self.voltage):.2f} V")
        ax1.set_ylabel("Voltage (V)")
        ax1.set_xlabel("Time (s)")
        ax1.legend(markerscale=10, loc="lower center")
        ax1.set_title(f"{self.filepath.name} \n Ambient temp: {self.avgT_amb_K-273.15:.2f} +/- {self.temp_amb_sem:.4f} C, Test length: {self.time[-1]:.4f} s")

        # current vs time (full record)
        ax2.scatter(time_raw, current_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Average Measured Current: {np.nanmean(self.current):.2f} A")
        ax2.set_ylabel(f"Current (A)")
        ax2.set_xlabel("Time (s)")
        ax2.legend(markerscale=10, loc="lower center")

        # Power vs time (heating period only)
        ax3.scatter(self.time, self.power, s=0.6, c="r", alpha=0.6,
                    label=f"Power Applied (heating period only): {self.avgQ:.3f} W ± {self.semQ:.5f} W")
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Power (W)")
        ax3.legend(markerscale=10, loc="lower center")

        # Raw temperature vs time (full record)
        ax4.scatter(time_raw, temp_raw, s=0.6, c="r", alpha=0.6,
                    label=f"Temperature Difference: {self.deltaT.min() + self.avgT_amb_K -273.15:.4f} to {self.deltaT.max() + self.avgT_amb_K -273.15:.4f} C ({self.deltaT.max() - self.deltaT.min():.4f} C range)")
        ax4.set_ylabel("Temperature (C)")
        ax4.legend(markerscale=10, loc="lower center")
        
        # deltaT vs time (heating period only)
        ax5.scatter(self.time, self.deltaT, s=0.6, c="r", alpha=0.6,
                    label=f"Processed Data (heating period only)")
        ax5.set_xlabel(r"$\Delta t$ (s)")
        ax5.set_ylabel(r"$\Delta T$ (C)")
        # ax5.set_xscale("log")
        ax5.legend(markerscale=10, loc="lower center")

        fig.tight_layout()
        self.plot = fig
        self.plot.savefig(self.plot_dir / f"{self.filepath.stem}_raw_data.png", dpi=200, bbox_inches="tight")
        plt.close(fig)  # Close the figure to free memory, but keep the reference in self.plot for later display
    
    def show_plot(self):
        if not hasattr(self, "plot"):
            logger.warning(
                "No plot available to show. Please ensure 'generate_plots' is set to True and that the data was processed successfully. Check %s for saved plots.",
                self.plot_dir,
            )
            return
        
        self.plot.show()
        plt.show(block=True)
        plt.close(self.plot)
        
def get_folder_data(data_folder: Path, current_units, V_min_cutoff=0.5, test_duration_overide=None, generate_plots: bool = True):
    """Load and process all .txt files from a folder, returning FileData instances.
    
    
    Parameters
    ----------
    data_folder : Path
        The folder containing the .txt files to process.
    current_units : str
        The units for the current ("A" or "mA").
    V_min_cutoff : float, optional
        The minimum voltage cutoff for data processing (default is 0.5).
    test_duration_overide : float, optional
        The duration to override the test duration (default is None).
    generate_plots : bool, optional
        Whether to generate and save plots of raw data (default is True).

    Returns
    -------
    list of FileData
        A list of FileData instances for each processed file.
    """
    logger.info("Importing data from %s...", data_folder.name)
    folder_data = []

    if not data_folder.exists():
        logger.error("Folder does not exist: %s", data_folder.resolve(strict=False))
        # exit(1)

    if generate_plots:
        out_dir = data_fo2lder.resolve() / "raw_data_plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Plots will be saved to: %s", out_dir)
    else:
        out_dir = None

    files = list(data_folder.glob("*.txt")) + [f for f in data_folder.glob("*") if "." not in f.name]

    for file_path in files:
        # Ensure we are not trying to process sub-folders
        if file_path.is_file():   
            try:
                file_data = FileData(
                    file_path, 
                    current_units=current_units,
                    V_min_cutoff=V_min_cutoff,
                    test_duration_overide=test_duration_overide,
                    generate_plots=generate_plots,
                    plot_dir=out_dir
                    )
                file_data.print_summary()
                folder_data.append(file_data)
                
            except Exception:
                logger.exception("Could not process %s", file_path.name)

    if not folder_data:
        logger.warning("Unable to successfully read any .txt files from folder: %s.", data_folder.absolute())
        return None

    return folder_data

if __name__ == "__main__":
    setup_logging()
    folder_path = Path("C:\\Users\\samia\\Documents\\Financial & Administrative\\Employment\\Job Specific\\BYU TEMP Lab\\$Raw Data\\3A-IN718-01 Ar Calib 6-26-26")
    get_folder_data(folder_path, current_units="A", generate_plots=True)