
% Clear workspace, command window, and close all open figures
clear; clc; close all;

% --- Folder Selection ---
% Open a dialog box for the user to select the data folder
data_folder = uigetdir('', 'Select the folder containing your data files');

% Check if the user canceled the dialog box
if data_folder == 0
    disp('Folder selection canceled. Exiting script.');
    return;
end

% Find all text files in the selected directory 
file_pattern = fullfile(data_folder, '*.txt'); 
files = dir(file_pattern);

if isempty(files)
    disp('No text files found in the selected folder.');
    return;
end

% --- Step 1: Extract temperatures and voltages to find unique groups ---
file_temps = cell(length(files), 1);
file_volts = cell(length(files), 1);
group_keys = cell(length(files), 1);

for i = 1:length(files)
    filename = files(i).name;
    
    % Extract the temperature (digits before 'C')
    temp_match = regexp(filename, '(\d+)C', 'tokens', 'once');
    if ~isempty(temp_match)
        file_temps{i} = temp_match{1};
    else
        file_temps{i} = 'UnknownTemp'; 
    end
    
    % Extract the voltage (digits before 'V')
    volt_match = regexp(filename, '(\d+)V', 'tokens', 'once');
    if ~isempty(volt_match)
        file_volts{i} = volt_match{1};
    else
        file_volts{i} = 'UnknownVolt'; 
    end
    
    % Create a combined grouping key (e.g., '500_5')
    group_keys{i} = [file_temps{i}, '_', file_volts{i}];
end

% Find the unique combinations of Temperature and Voltage
unique_groups = unique(group_keys);

% --- Step 2: Loop through each unique combination ---
for t = 1:length(unique_groups)
    current_group = unique_groups{t};
    
    % Skip if the file didn't have both a temperature and a voltage
    if contains(current_group, 'Unknown')
        continue; 
    end
    
    % Split the key back into temp and volt for labeling
    split_key = strsplit(current_group, '_');
    current_temp = split_key{1};
    current_volt = split_key{2};
    
    group_label = [current_temp, ' °C, ', current_volt, ' V'];
    
    % Create a new figure for this specific Temperature/Voltage group
    fig = figure('Name', ['Results: ', group_label], 'Position', [100, 100, 800, 900]);
    
    % Create subplot axes for 4 rows and turn 'hold on' 
    ax_temp = subplot(4, 1, 1); hold(ax_temp, 'on');
    ax_volt = subplot(4, 1, 2); hold(ax_volt, 'on');
    ax_curr = subplot(4, 1, 3); hold(ax_curr, 'on');
    ax_pow  = subplot(4, 1, 4); hold(ax_pow, 'on');
    
    % Initialize separate legend arrays for each subplot to hold specific averages
    legend_temp = {};
    legend_volt = {};
    legend_curr = {};
    legend_pow = {};
    
    % --- Step 3: Loop through files and plot ones matching this group ---
    for i = 1:length(files)
        if strcmp(group_keys{i}, current_group)
            filename = files(i).name;
            full_filepath = fullfile(data_folder, filename);
            
            % Load the data using readmatrix (handles empty spaces as NaN safely)
            data = readmatrix(full_filepath);
            time = data(:, 1);
            temp = data(:, 2);
            volt = data(:, 3);
            curr = data(:, 4);
            
            % --- Convert mA to A if necessary ---
            % We check if the maximum absolute value is > 10 (ignoring NaNs)
            if max(abs(curr), [], 'omitnan') > 10
                curr = curr / 1000;
            end
            
            % Calculate Power (Do this after mA conversion so Watts are correct)
            power = volt .* curr;
            
            % Create logical masks for each variable pair
            % This ensures we only keep rows where BOTH time and the specific variable are numbers
            valid_temp = ~isnan(time) & ~isnan(temp);
            valid_volt = ~isnan(time) & ~isnan(volt);
            valid_curr = ~isnan(time) & ~isnan(curr);
            valid_pow  = ~isnan(time) & ~isnan(power);
            
            % Calculate Averages using only the clean, filtered data
            avg_temp = mean(temp(valid_temp));
            avg_volt = mean(volt(valid_volt));
            avg_curr = mean(curr(valid_curr));
            avg_pow  = mean(power(valid_pow));
            
            % Determine line color based on the last character of the filename
            [~, name_only, ~] = fileparts(filename); 
            last_char = name_only(end); 
            
            if last_char == '1'
                line_color = 'r'; % Red for files ending in 1
            elseif last_char == '2'
                line_color = 'b'; % Blue for files ending in 2
            else
                line_color = 'k'; % Black default for any other endings
            end
            
            % Plot the data using the logical masks to ignore NaNs
            plot(ax_temp, time(valid_temp), temp(valid_temp), 'Color', line_color, 'LineWidth', 1.5);
            plot(ax_volt, time(valid_volt), volt(valid_volt), 'Color', line_color, 'LineWidth', 1.5);
            plot(ax_curr, time(valid_curr), curr(valid_curr), 'Color', line_color, 'LineWidth', 1.5);
            plot(ax_pow, time(valid_pow), power(valid_pow), 'Color', line_color, 'LineWidth', 1.5);
            
            % Format the filename for the legend (escape underscores)
            clean_name = strrep(filename, '_', '\_');
            
            % Append the filename and its specific average to the respective legend arrays
            legend_temp{end+1} = sprintf('%s (Avg: %.4f °C)', clean_name, avg_temp);
            legend_volt{end+1} = sprintf('%s (Avg: %.4f V)', clean_name, avg_volt);
            legend_curr{end+1} = sprintf('%s (Avg: %.4f A)', clean_name, avg_curr);
            legend_pow{end+1}  = sprintf('%s (Avg: %.4f W)', clean_name, avg_pow);
        end
    end
    
    % --- Step 4: Apply Formatting for this Group's Figure ---
    % Format Temperature Subplot
    title(ax_temp, ['Temperature Delta vs. Time (', group_label, ')'], 'FontSize', 12);
    ylabel(ax_temp, 'Temperature Delta (°C)', 'FontSize', 11);
    grid(ax_temp, 'on'); box(ax_temp, 'on');
    legend(ax_temp, legend_temp, 'Location', 'best');
    
    % Format Voltage Subplot
    title(ax_volt, ['Voltage vs. Time (', group_label, ')'], 'FontSize', 12);
    ylabel(ax_volt, 'Voltage (V)', 'FontSize', 11);
    grid(ax_volt, 'on'); box(ax_volt, 'on');
    legend(ax_volt, legend_volt, 'Location', 'best');
    
    % Format Current Subplot
    title(ax_curr, ['Current vs. Time (', group_label, ')'], 'FontSize', 12);
    ylabel(ax_curr, 'Current (A)', 'FontSize', 11);
    grid(ax_curr, 'on'); box(ax_curr, 'on');
    legend(ax_curr, legend_curr, 'Location', 'best');
    
    % Format Power Subplot
    title(ax_pow, ['Power vs. Time (', group_label, ')'], 'FontSize', 12);
    xlabel(ax_pow, 'Time', 'FontSize', 11);
    ylabel(ax_pow, 'Power (W)', 'FontSize', 11);
    grid(ax_pow, 'on'); box(ax_pow, 'on');
    legend(ax_pow, legend_pow, 'Location', 'best');

    % --- Step 5: Save the Figure ---
    % Create a descriptive filename based on temp and voltage
    save_filename = sprintf('Plot_%sC_%sV.fig', current_temp, current_volt);
    full_save_path = fullfile(data_folder, save_filename);
    
    % Save the figure to the chosen directory
    savefig(fig, full_save_path);
    disp(['Saved figure: ', save_filename]);
end
disp('Plotting complete!');