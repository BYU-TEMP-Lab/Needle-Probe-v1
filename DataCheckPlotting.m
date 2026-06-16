% 1. Define the folder and what files to look for
% Use '.' for the current folder, or put a full path like 'C:\Data\'
folderPath = uigetdir('', 'Select the folder containing the data');
filePattern = fullfile(folderPath, '*.txt'); % Looks for all text files
files = dir(filePattern);

% Check if any files were found
if isempty(files)
    disp('No text files found in the specified directory.');
    return;
end

% 2. Loop through each file
for k = 1:length(files)
    
    % Get the exact name and path of the current file
    baseFileName = files(k).name;
    fullFileName = fullfile(files(k).folder, baseFileName);
    
    % Read the data
    data = readtable(fullFileName);
    varNames = {'Time', 'TemperatureDelta', 'Voltage', 'Current'};
    data.Properties.VariableNames = varNames(1:width(data));
    
    % Create a new figure, naming the window after the file
    fig = figure('Name', baseFileName, 'NumberTitle', 'off');
    
    % Set up Main Axes (ax1) and make room on the right
    ax1 = axes(fig);
    ax1.Position(3) = 0.65; 
    
    % Add a title using the filename (Interpreter 'none' stops underscores from making subscripts)
    title(ax1, baseFileName, 'Interpreter', 'none');
    
    % Plot Temperature (Left)
    yyaxis(ax1, 'left'); 
    plot(ax1, data.Time, data.TemperatureDelta);
    ylabel(ax1, 'Temperature Delta');
    
    % Plot Voltage (Right)
    yyaxis(ax1, 'right'); 
    plot(ax1, data.Time, data.Voltage);
    
    % --- DYNAMIC VOLTAGE LIMITS ---
    minVolt = min(data.Voltage);
    maxVolt = max(data.Voltage);
    % ylim(ax1, [minVolt - 0.1, maxVolt + 0.1]); 
    ylabel(ax1, 'Voltage');
    
    % Set up the Data Overlay Axes (ax2)
    ax2 = axes('Position', ax1.Position);
    hold(ax2, 'on'); 
    scatter(ax2, data.Time, data.Current, 5, '.r');
    
    % --- DYNAMIC CURRENT LIMITS ---
    minCurr = min(data.Current);
    maxCurr = max(data.Current);
    % ylim(ax2, [minCurr - 5, maxCurr + 5]);
    
    % Force transparency so ax1 shows through
    ax2.Color = 'none'; 
    
    % Hide ax2 labels and lines
    ax2.XAxis.Visible = 'off';
    ax2.YAxis.Visible = 'off'; 
    
    % Link X-axes
    linkaxes([ax1, ax2], 'x');
    
    % Set up the Dummy Axis (ax3) just for the Current labels
    offset = 0.12; 
    ax3 = axes('Position', [ax1.Position(1) + ax1.Position(3) + offset, ax1.Position(2), 0.01, ax1.Position(4)]);
    
    % Match ax2's Y-limits and color it red
    ax3.YAxisLocation = 'right';
    ax3.YColor = 'r';
    ax3.YLim = ax2.YLim;
    ylabel(ax3, 'Current');
    
    % Hide the background, X-axis, and box on the dummy axis
    ax3.Color = 'none';
    ax3.XAxis.Visible = 'off';
    box(ax3, 'off');
    
    % Keep limits linked
    linkprop([ax2, ax3], 'YLim');
    
    % Optional: Force MATLAB to draw the figure immediately before moving to the next
    drawnow; 
    
end