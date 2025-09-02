import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import warnings

def read_data(filename):
    # Read CSV or txt file (assuming comma-separated)
    df = pd.read_csv(filename, sep="\t", header=None)  # Adjust header if needed
    data = df.values
    _, N_cols = data.shape
    print(f"Importing {filename} with {N_cols} columns.")

    if N_cols != 4:
        raise ValueError(f"Function 'extract_data' received a file with {N_cols} columns of data, but requires 4")

    time = data[:, 0]
    temp = data[:, 1]
    voltage = data[:, 2]
    current = data[:, 3]

    return time, temp, voltage, current


def get_start_stop(voltage, time, V_min_cutoff, test_duration):
    # Find first applied voltage > V_min_cutoff to establish t=0
    V_inx = np.where(voltage > V_min_cutoff)[0] # indices where condition is met
    if len(V_inx) == 0:
        raise ValueError(f"No voltage above {V_min_cutoff} V found in data.")
    V_start = V_inx[0]-1 # index of start time (subtract one for t=0 instead of t=1)

    # And then t_final the last index where voltage > V_min_cutoff
    if test_duration is None:
        V_end = V_inx[-1] # returns index of last True, or 0 if none
    else:
        try:
            V_end = np.where(time >= time[V_start] + test_duration)[0][0]  # end time based on sample length
        except IndexError:
            warnings.warn(
            f"Sample length {test_duration} s passed to 'extract_data' "
            "is longer than the collected sample time. "
            "Falling back to end of heating period.",
            UserWarning
            )
            V_end = V_inx[-1]

    return V_start, V_end


def process_data(filename, test_duration: float=None, V_min_cutoff: float=0.8):
    """
    Given filename (and optionally the test length in seconds and 
    Voltage to detect the heating wire is active in Volts),
    reads 4-column experimental data (tab delimited) and returns filtered deltaT-time 
    array during the time the heating wire is active,
    average power applied, and ambient temperature in Kelvin.
    """

    time, temp, voltage, current = read_data(filename)
    V_start, V_end = get_start_stop(voltage, time, V_min_cutoff, test_duration)

    # Ambient temperature
    avgT_amb = np.mean(temp[:V_start-1])
    avgT_amb = avgT_amb + 273.15  # Convert Celsius to Kelvin (used in heat transfer eq.)

    # Align time, temp, Voltage, and Current with V_start and V_end
    time = time[V_start:V_end] - time[V_start]
    deltaT = temp[V_start:V_end] - avgT_amb # deltaT = temp - avgT_amb
    voltage = voltage[V_start:V_end]
    current = current[V_start:V_end]

    # Average power
    avgVoltage = np.mean(voltage)
    avgCurrent = np.nanmean(current) / 1000  # Convert mA to A
    avgQ = avgVoltage * avgCurrent

    # Construct experimental temp vs time array
    tempData = np.column_stack((time, deltaT))

    return tempData, avgQ, avgT_amb

if __name__ == "__main__":
    process_data("./MATLAB_ONLY/FLiNaK_730C_3V_1 (1).txt", test_duration=10.0)