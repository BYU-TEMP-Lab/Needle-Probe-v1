% Script to compare theoretical properties from Properties.m with calibration fits
clear; clc; close all;

% Prompt user for temperature range[cite: 1]
prompt = {'Enter minimum temperature (°C):', 'Enter maximum temperature (°C):', 'Enter temperature step (°C):'};
dlgtitle = 'Temperature Range Specification';
dims = [1 50];
definput = {'20', '800', '20'};
answer = inputdlg(prompt, dlgtitle, dims, definput);
if isempty(answer)
    disp('User canceled input.');
    return;
end
T_min = str2double(answer{1});
T_max = str2double(answer{2});
T_step = str2double(answer{3});
T_range = T_min:T_step:T_max;

% Use uigetfile to select the calibration text file[cite: 1]
disp('Please select calibration_fits_linear.txt');
[filename, filepath] = uigetfile('*.txt', 'Select the calibration fits file');
if isequal(filename, 0)
    disp('User canceled file selection.');
    return;
end
fullpath = fullfile(filepath, filename);

% Parse calibration_fits_linear.txt[cite: 2]
% Extracts slope and intercept from lines formatted as: "... Equation: y = m*(T-273.15) + b"
fid = fopen(fullpath, 'r');
calib_data = repmat(struct('name', '', 'm', [], 'b', []), 33, 1);

while ~feof(fid)
    line = fgetl(fid);
    tokens = regexp(line, '^(.*?)\s+Equation:\s+y\s*=\s*([+\-.\deE]+)\*\(T-273\.15\)\s*\+\s*([+\-.\deE]+)', 'tokens');
    
    if ~isempty(tokens)
        prop_str = tokens{1}{1};
        m = str2double(tokens{1}{2});
        b = str2double(tokens{1}{3});
        
        % Map the extracted calibration text prefix to the exact Properties.m output index[cite: 1, 2]
        idx = 0;
        if contains(prop_str, 'K__Eff__Wires'); idx = 1;
        elseif contains(prop_str, 'Alpha__Eff__Wires'); idx = 2;
        elseif contains(prop_str, 'K__Insulation'); idx = 3;
        elseif contains(prop_str, 'Alpha__Insulation'); idx = 4;
        elseif contains(prop_str, 'Rth__Insulation_Sheath'); idx = 5;
        elseif contains(prop_str, 'K__Sheath'); idx = 6;
        elseif contains(prop_str, 'Alpha__Sheath'); idx = 7;
        elseif contains(prop_str, 'K__Crucible'); idx = 10;
        elseif contains(prop_str, 'Alpha__Crucible'); idx = 11;
        elseif contains(prop_str, 'Emissivity__Probe'); idx = 12;
        elseif contains(prop_str, 'Emissivity__Crucible'); idx = 13;
        elseif contains(prop_str, 'Rth__Sheath_Sample'); idx = 32;
        elseif contains(prop_str, 'Rth__Sample_Crucible'); idx = 33;
        end
        
        if idx > 0
            calib_data(idx).name = prop_str;
            calib_data(idx).m = m;
            calib_data(idx).b = b;
        end
    end
end
fclose(fid);

% Define default parameters to execute Properties.m[cite: 1]
probe = '3A-IN718-01';
crucible = 'Nickel200';
sample = 'Ar';
Voltage = 1; VoltSTD = 0; Current = 1; CurrentSTD = 0; MC = 0;

% Initialize array for theoretical outputs
prop_vals = zeros(length(T_range), 33);

% Calculate properties for each temperature point[cite: 1]
for i = 1:length(T_range)
    Temp = T_range(i);
    [par_vector, par_names] = Properties(probe, crucible, sample, Temp, Voltage, VoltSTD, Current, CurrentSTD, MC);
    prop_vals(i, :) = par_vector;
end

% Set up the figure for plots[cite: 1]
figure('Name', 'Property Comparison: Properties.m vs. Calibration Fits', 'Position', [100, 100, 1400, 800]);

% Find valid indices mapped from the calibration file
valid_indices = find(~cellfun(@isempty, {calib_data.name}));
num_plots = length(valid_indices);
cols = ceil(sqrt(num_plots));
rows = ceil(num_plots / cols);

% Iterate and generate subplot for each overlapping property
for i = 1:num_plots
    p_idx = valid_indices(i);
    
    % Evaluate calibration linear fit (T-273.15 perfectly equates to Temp in Celsius)[cite: 1, 2]
    calib_y = calib_data(p_idx).m .* T_range + calib_data(p_idx).b;
    
    % Extract analytical property values
    prop_y = prop_vals(:, p_idx);
    
    % Format strings for cleaner plot titles and axis labels
    clean_title = strrep(par_names(p_idx, 1), '\_', '_');
    y_label = strrep(par_names(p_idx, 2), '\_', '_');
    
    subplot(rows, cols, i);
    plot(T_range, prop_y, 'b-', 'LineWidth', 2); hold on;
    plot(T_range, calib_y, 'r--', 'LineWidth', 2);
    
    title(clean_title, 'Interpreter', 'none');
    xlabel('Temperature (°C)');
    ylabel(y_label, 'Interpreter', 'none');
    grid on;
    
    if i == 1
        legend('Properties.m', 'Calibration Fit', 'Location', 'best');
    end
end