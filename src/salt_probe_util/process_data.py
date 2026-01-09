import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
import warnings


def read_data(filename: Path):
    """
    Reads experimental data from a tab-separated file.
    Expected format: [Time, Temp, Voltage, Current]
    """
    # Read CSV or txt file (assuming tab-separated)
    df = pd.read_csv(filename, sep="\t", header=None)  # Adjust header if needed
    _, N_cols = df.shape
    print(f"Importing {filename.name} with {N_cols} columns...")

    if N_cols != 4:
        raise ValueError(
            f"Function 'read_data' received {N_cols} columns, but requires exactly 4 "
            "(Time, Temp, Voltage, Current)."
        )
    
    # Unpack columns
    time = df.iloc[:, 0].values
    temp = df.iloc[:, 1].values
    voltage = df.iloc[:, 2].values
    current = df.iloc[:, 3].values

    return time, temp, voltage, current


def get_start_stop(voltage, time, V_min_cutoff, test_duration):
    # Find first applied voltage > V_min_cutoff to establish t=0
    V_inx = np.where(voltage > V_min_cutoff)[0] # indices where voltage is above cutoff
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
            f"Overide sample length {test_duration} s passed to 'extract_data' "
            "is longer than the collected sample time. "
            "Falling back to end of heating period.",
            UserWarning
            )
            V_end = V_inx[-1]

    return V_start, V_end


def process_data(filepath: Path, test_duration: float=None, V_min_cutoff: float=0.8):
    """
    Given filename (and optionally the test length in seconds and 
    Voltage to detect the heating wire is active in Volts),
    reads 4-column experimental data (tab delimited) and returns filtered deltaT-time 
    array during the time the heating wire is active,
    average power applied, and ambient temperature in Kelvin.
    """

    time, temp, voltage, current = read_data(filepath)
    V_start, V_end = get_start_stop(voltage, time, V_min_cutoff, test_duration)

    # Ambient temperature
    avgT_amb_C = np.mean(temp[:V_start-1])
    avgT_amb_K = avgT_amb_C + 273.15  # Convert Celsius to Kelvin (used in heat transfer eq.)

    # Estimate noise
    temp_noise_std = np.std(temp[:V_start-1]) # standard deviation of temps in general
    temp_amb_sem = temp_noise_std / np.sqrt(V_start-1) # standard error of the mean for ambient temp

    # Align time, temp, Voltage, and Current with V_start and V_end
    time = time[V_start:V_end] - time[V_start]
    deltaT = temp[V_start:V_end] - avgT_amb_C # deltaT = temp - avgT_amb
    voltage = voltage[V_start:V_end]
    current = current[V_start:V_end]

    # Average voltage during heating period, standard deviation, and standard error
    avgVoltage = np.mean(voltage)
    std_V = np.std(voltage)
    sem_V = std_V / np.sqrt(len(voltage))

    # Average current during heating period, standard deviation, and standard error
    avgCurrent = np.nanmean(current) / 1000  # Convert mA to A
    std_I = np.nanstd(current) / 1000
    n_valid = np.count_nonzero(~np.isnan(current)) # handle NaN values
    sem_I = std_I / np.sqrt(n_valid) if n_valid > 0 else 0

    # Average power applied during heating period, error propagation for standard error
    avgQ = avgVoltage * avgCurrent
    semQ = avgQ * np.sqrt((sem_V / avgVoltage)**2 + (sem_I / avgCurrent)**2)

    # Construct experimental temp vs time array
    tempData = np.column_stack((time, deltaT))

    data_dict = {
        "filepath": filepath,
        "tempData": tempData,
        "tempData_std": temp_noise_std,
        "avgT_amb_K": {
            "initial_value": avgT_amb_K,
            "bounds": (avgT_amb_K - 5, avgT_amb_K + 5),
            "prior_sigma": temp_amb_sem
            },
        "avgQ": {
            "initial_value": avgQ,
            "bounds": (0.9 * avgQ, 1.1 * avgQ),
            "prior_sigma": semQ
        }
    }
    return data_dict

def get_files_data(data_folder: Path):
    print(f"Importing data from {data_folder.name}...")
    files_data = []

    for file_path in data_folder.glob("*.txt"):
        # Ensure we are not trying to process sub-folders
        if file_path.is_file():   
            try:
                result = process_data(file_path)
                files_data.append(result)
                
            except Exception as e:
                print(f"Could not process {file_path.name}: {e}")

    if not files_data:
        print(f"Unable to successfully read any .txt files from folder: {data_folder.absolute()}.")
        return None

    return files_data


## is this garbage? vvvvvv
# def process_file(filepath):
#     filename = os.path.basename(filepath)
#     print(f"Processing {filename}")
#     expTvt, avgT_amb = extract_data(filepath, timewindow)
#     par_vector, par_names = properties(crucible, sample, avgT_amb, MC)

#     # Map parameters to solve
#     idx_par_to_Solv = [(j, SolvNam.index(par)) for j, par in enumerate(par_names) if par in SolvNam]
#     idx_par_to_Solv = np.array(idx_par_to_Solv)

#     # Initial guess
#     for j, (idx_par, idx_solv) in enumerate(idx_par_to_Solv):
#         SolvVal[idx_solv] = par_vector[idx_par]

#     # Optimize
#     res = least_squares(
#         chi2_residuals,
#         SolvVal,
#         bounds=(SolvConstraintsLower, SolvConstraintsUpper),
#         args=(SolvNam, par_vector.copy(), par_names, idx_par_to_Solv, expTvt),
#         method='trf'
#     )
#     SolvedParam = res.x
#     Chi2_val = np.sum(res.fun**2)
#     print(f"Solved parameters: {SolvedParam}, Chi2: {Chi2_val}")
#     return avgT_amb, Chi2_val, SolvedParam

if __name__ == "__main__":
    # process_data("./MATLAB_ONLY/FLiNaK_730C_3V_1 (1).txt", test_duration=10.0)
    filepath = Path("./MATLAB_ONLY/FLiNaK_730C_3V_1 (1).txt")
    file_data = process_data(filepath)
    plt.scatter(file_data["tempData"][:, 0], file_data["tempData"][:, 1], label=rf"Temp: {file_data["avgT_amb_K"]:.2f} K", s=0.5, c="r", alpha=0.5)
    plt.xlabel("Time (s)")
    plt.xscale("log")
    plt.ylabel(r"$\Delta T$")
    plt.legend(markerscale=20)    
    plt.show()