%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%                                                                         %
%  Title: NeedleProbeMain.m
%  Date: 7-17-2024
%  Purpose: Iteratively solve FlexPDE model of system solving for 1-3     
%           input parameters to fit to experimental data                                                                         
%  Inputs: 
%       Experimental data file folder (Temp, time, voltage, current)
%	    Parameters to solve for (i.e. k, cp, rhocp, contact resistance)
%	    Testing conditions (sample, crucible materials, etc.)                   
%  Outputs: 
%       Solved properties 
%       Plots of solution vs. temp, Error
%  Functions:
%       ExtractData.m
%       Properties.m
%       RunFlexPDE_Radial.m
%       RunFlexPDE_Axial.m
%       Chi2.m
%  Version: 1.0                                                           
%  Authors: Tyler Hamm, Jacob Numbers                                     
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
clc; clear all; close all;


%%%%%%%% Provide Input Information %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Select folder of experimental data files
testfolder = uigetdir;
files = dir(fullfile(testfolder, '*'));

% Select crucible material. Select from:
    % 'Steel316','Nickel200','Inconel625'
crucible = 'Nickel200'; 

% Select sample 
sample = 'Argon';

% Select properties for which to solve. Select from any of the par_vector options...
SolvNam = ["Thermal Contact Resistance Sheath-Insulation","cp Insulation"];
SolvVal = [0.0052,780];    % Initial guess
% Constraints: Use to prevent divide by zero and other errors
SolvConstraintsUpper = [2,1400];    % Upper bound constraints for properties
SolvConstraintsLower = [0.0001,300];    % Lower bound constraints for properties

% Select settings for program
cross_section = 'radial'; % or 'axial'
timewindow = [0 4]; % (s) Sets the time interv  al to be analyzed 
MC = 0;
plotfrequency = 5;  % Iteration frequency to plot comparison
Chi2_tolerance = 1e-4;  % Stops if the change in the objective function value is less than this tolerance

% Remove folders
files = files(~[files.isdir]);

% Initialize table to store optimization solution values
ParamTemp = table('Size', [length(files), 2+length(SolvNam)], ...
    'VariableTypes', repmat({'double'}, 1, 2+length(SolvNam)), ...
    'VariableNames', [{'T_amb_K'}, {'Chi_Squared'}, SolvNam]);

% Delete any existing parallel pools
delete(gcp('nocreate'))

%%%%%%%% Obtain Data From Data File %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for i = 1:length(files)
    %if files(i).isdir, continue; end
    
    filename = fullfile(testfolder, files(i).name);
    disp(['Processing file: ', files(i).name]);
    ExpDataFile = files(i).name;

    % Extract relevant info and temp profile from current data file
    [expTvt,avgQ,avgT_amb] = ExtractData(filename,timewindow);
    
    % Obtain temp- and test-specific properties 
    [par_vector, par_names] = Properties(crucible,sample,avgT_amb,avgQ,MC);
    
    % Map parameters to solve to properties vector 
    idx_par_to_Solv = zeros(length(SolvVal),2);
    k = 1;
    for j = 1:length(par_names)
        [isMatch, idx] = ismember(par_names(j, 1), SolvNam);
        if isMatch
            idx_par_to_Solv(k,1) = j; 
            idx_par_to_Solv(k,2) = idx;
            k = k + 1;
        end
    end

%%%%%%%% Run optimization %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
     % Assign initial properties from Properties.m
    for j = 1:length(SolvVal)
        SolvVal(idx_par_to_Solv(j,2)) = par_vector(idx_par_to_Solv(j,1));
    end
    
    % Get initial comparison
    PlotSolution_andlog(SolvVal,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt,testfolder,ExpDataFile,"Initial",cross_section)

    f = @(x)Chi2log10(x,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt,cross_section);
    %f = @(x)Chi2(x,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt);
    %f = @(x)GoF(x,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt);

    % Options for optimization
    A = [];
    b = [];
    Aeq = [];
    beq = [];
    lb = SolvConstraintsLower;
    ub = SolvConstraintsUpper;

    % Set options for patternsearch
    options = optimoptions(@patternsearch, ...
        'UseParallel', true, ...
        'Display', 'iter', ...
        'MaxIterations', 500 , ...
        'FunctionTolerance', Chi2_tolerance, ... % Tolerance on the objective function value
        'PlotFcn', @psplotbestf); % (PATTERNSEARCH)Plot the best objective function value

    % Set options for surrogate optimization
    sooptions = optimoptions(@surrogateopt, ...
        'UseParallel', true, ...
        'Display', 'iter', ...
        'MaxFunctionEvaluations', 1000, ...
        'MinSurrogatePoints', 4*length(SolvVal), ... % Increase the minimum number of surrogate points
        'PlotFcn', @surrogateoptplot); % (Surrogate Optimization)Plot the best objective function value
    
    % Set options for genetic algorithm, with hybrid patternsearch
    gaoptions = optimoptions(@ga, ...
        'UseParallel', true, ...
        'Display', 'iter', ...
        'MaxGenerations', 75, ...
        'PlotFcn', @gaplotbestf, ...
        'PopulationSize', 20, ...
        'HybridFcn', {@patternsearch, [], optimoptions('patternsearch', 'Display', 'iter')});
    
    % Set options for the particle swarm optimization
    swarmoptions = optimoptions('particleswarm', ...
        'UseParallel', true, ...
        'Display', 'iter', ...
        'MaxIterations', 50, ...
        'SwarmSize', 50, ...   % This is analogous to 'PopulationSize' in genetic algorithms
        'PlotFcn', @pswplotbestf);

    % Define the number of variables
    nvars = length(SolvVal);
    
    % Set up parallel computing
    parpool;
    if isempty(gcp('nocreate'))
        parpool('local');
    end
            
    % Run the optimization
    [SolvedParam, Chi2, exitflag, output] = patternsearch(f, SolvVal, [], [], [], [], lb, ub, options); % Patternsearch
    %[SolvedParam, Chi2, exitflag, output] = surrogateopt(f, lb, ub,sooptions); % Surrogate optimization
    %[SolvedParam, Chi2, exitflag, output] = ga(f, nvars, [], [], [], [], lb, ub, [], gaoptions); % genetic algorithm optimization
    %[SolvedParam, Chi2, exitflag, output] = particleswarm(f, nvars, lb, ub, swarmoptions); % particle swarm optimization
    
    
    % Display results
    disp('Solved parameters:');
    disp(SolvedParam);
    disp('Chi2:');
    disp(Chi2);
    disp('Exit flag:');
    disp(exitflag);

    % Store in text file
    OutputResults(filename, avgT_amb, Chi2, SolvedParam,testfolder)
    % Store values in the table
    ParamTemp.T_amb_K(i) = avgT_amb;
    ParamTemp.Chi_Squared(i) = Chi2;
    for k = 1:length(SolvNam)
        ParamTemp.(SolvNam{k})(i) = SolvedParam(k);
    end
    
    % Plot final comparison
    PlotSolution_andlog(SolvedParam,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt,testfolder,ExpDataFile,"Final",cross_section)
    
    delete(gcp('nocreate'))
    
end

% Display the table
disp(ParamTemp);

% Define the folder name to save the plots
[~, dirName, ~] = fileparts(testfolder);

% Construct the output table path
tablename = ['Parameters_Temp' dirName '_Patternsearch.csv'];

writetable(ParamTemp, tablename);

% Iterate through the columns of the table and create a new plot for each
columnNames = ParamTemp.Properties.VariableNames;

for i = 1:length(columnNames)
    if ~strcmp(columnNames{i}, 'T_amb_K') % Skip T_amb_K column
        figure;
        plot(ParamTemp.T_amb_K, ParamTemp.(columnNames{i}), '-o');
        xlabel('Ambient Temperature (K)');
        ylabel(columnNames{i});
        title(['Temperature vs ', columnNames{i}]);
        grid on;
    end
end


function PlotSolution_andlog(SolvVal, SolvNam, par_vector, par_names, idx_par_to_Solv, expTvt,testfolder,ExpDataFile,Title,cross_section)

    % Assign solving properties to par_vector
    for i = 1:length(SolvVal)
        par_vector(idx_par_to_Solv(i,1)) = SolvVal(idx_par_to_Solv(i,2));
    end
    
    % Add initial or final to experimental data file
    TitleExpDataFile = Title + '_' + ExpDataFile;
    
    
    endtime = expTvt(end,1);
    
    if strcmpi(cross_section,'axial')
        [uniqueID,filename] = RunFlexPDE_Axial(par_vector,par_names,SolvNam,endtime);
    elseif strcmpi(cross_section,'radial')
        [uniqueID, filename] = RunFlexPDE_Radial(par_vector, par_names, SolvNam,endtime);
    end
    
    % Construct the output folder path
    outputFolder = ['Flex_' uniqueID '_output'];

    % Path to the temp.txt file
    tempFilePath = fullfile(outputFolder, 'temp.txt');

    % Wait until the file exists
    while ~exist(tempFilePath, 'file')
        % Pause for a short duration to avoid excessive CPU usage
        pause(1); % Pause for 1 second before checking again
    end

    % Open the temp.txt file for reading
    fileID = fopen(tempFilePath, 'r');

    % Read the header lines (adjust the number according to the file structure)
    headerLines = 8; % Adjust this according to the number of header lines
    for i = 1:headerLines
        fgetl(fileID);
    end

    % Read the numerical data
    FlexTvt = fscanf(fileID, '%f, %f', [2, Inf])';

    % Close the file
    fclose(fileID);

    % Delete the FlexPDE file, the respective folder and its contents
    rmdir(outputFolder, 's');
    delete(filename);
    bakfile = [filename '.bak'];
    delete(bakfile);

    % Subtract ambient temp
    FlexTvt(:,2) = FlexTvt(:,2) - FlexTvt(1,2);

    % Interpolate the FlexPDE data to match the other array time steps
    interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), expTvt(:, 1), 'spline');

    % Make temp vs time array of Flex data
    interpFlexTvt = [expTvt(:,1), interpFlexTemp];
     
    % Create log10 time domain
    log10time = logspace(log10(1e-2),log10(expTvt(end,1)),length(expTvt));

    % Interpolate the FlexPDE and experimental data in the log-domain
    interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), log10time, 'spline');
    interpExpTemp = interp1(expTvt(:, 1), expTvt(:, 2), log10time, 'spline');

    % Define the folder name to save the plots
    [~, dirName, ~] = fileparts(testfolder);
    outputFolder = ['Output_',dirName];

    % Check if the folder exists, and if not, create it
    if ~exist(outputFolder, 'dir')
        mkdir(outputFolder);
    end
    
    %%%%%%%%% Plot the temperature profiles in linear x-domain %%%%%%%%%%%%
    figure;
    plot(expTvt(:, 1), expTvt(:, 2), '-r', 'DisplayName', 'Experimental'); % '-r' specifies a red line
    hold on; % Hold the plot to add more data
    plot(interpFlexTvt(:, 1), interpFlexTvt(:, 2), '-b', 'DisplayName', 'FlexPDE'); % '-b' specifies a blue line
    xlabel('Time (s)');
    ylabel('Temperature Rise (K)');
    title(['Linear Domain: Temperature vs. Time', Title]);
    legend('show');
    % Set the legend position to top left
    legend('Location', 'northwest'); 
    grid on;

    % Initialize the text string
    textString = '';

    % Create the text string dynamically
    for i = 1:length(SolvNam)
        textString = sprintf('%s%s: %.3e\n', textString, SolvNam{i}, SolvVal(i));
    end

    % Remove the trailing newline character
    textString = textString(1:end-1);

    % Get the current axis limits for the linear plot
    xLimits = xlim;
    yLimits = ylim;

    % Position for the text (bottom right corner)
    xPos = xLimits(2) - 0.1 * (xLimits(2) - xLimits(1));
    yPos = yLimits(1) + 0.1 * (yLimits(2) - yLimits(1)); 
    
    % Add the text to the linear plot
    text(xPos, yPos, textString, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom', 'BackgroundColor', 'white', 'EdgeColor', 'black','FontSize', 8);
    
    % Save the plot as a .fig file in the Output folder
    savefilename = fullfile(outputFolder, ('Linear_' + TitleExpDataFile + '.fig')); % E.g., 'Output/myPlot_example.png'
    savefig(gcf, savefilename);
    close(gcf);
    
    %%%%%%%%% Plot the temperature profiles in log10 x-domain %%%%%%%%%%%%
    figure;
    % Plot experimental data in log-domain
    semilogx(log10time,interpExpTemp, '-r', 'DisplayName', 'Experimental'); % '-r' specifies a red line
    hold on; % Hold the plot to add more data
    % Plot FlexPDE data in log-domain
    semilogx(log10time,interpFlexTemp, '-b', 'DisplayName', 'FlexPDE'); % '-b' specifies a blue line
    xlabel('Log10(Time)');
    ylabel('Temperature Rise (K)');
    title(['Log10 Domain: Temperature vs. Time', Title]);
    legend('show');
    % Set the legend position to top left
    legend('Location', 'northwest'); 
    grid on;
    
    % Initialize the text string
    textString = '';

    % Create the text string dynamically
    for i = 1:length(SolvNam)
        textString = sprintf('%s%s: %.3e\n', textString, SolvNam{i}, SolvVal(i));
    end

    % Remove the trailing newline character
    textString = textString(1:end-1);

    % Get the current axis limits for the linear plot
    xLimits = xlim;
    yLimits = ylim;
    
    % Position for the text (bottom right corner)
    xPos = xLimits(2) - 0.1 * (xLimits(2) - xLimits(1));
    yPos = yLimits(1) + 0.05 * (yLimits(2) - yLimits(1)); 
    
    % Add the text to the linear plot
    text(xPos, yPos, textString, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom', 'BackgroundColor', 'white', 'EdgeColor', 'black','FontSize', 8);
    
    % Save the plot as a .fig file in the Output folder
    savefilename = fullfile(outputFolder, ('Log_' + TitleExpDataFile + '.fig')); % E.g., 'Output/myPlot_example.png'
    savefig(gcf, savefilename);
    close(gcf);
    
end


function PlotSolution(SolvVal,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt,Title)

    % Assign solving properties to par_vector
    for i = 1:length(SolvVal)
        par_vector(idx_par_to_Solv(i,1)) = SolvVal(idx_par_to_Solv(i,2));
    end

    endtime = expTvt(end,1);
    
    [uniqueID,filename] = RunFlexPDE_Radial(par_vector,par_names,SolvNam,endtime);

    % Construct the output folder path
    outputFolder = ['Flex_' uniqueID '_output'];

    % Path to the temp.txt file
    tempFilePath = fullfile(outputFolder, 'temp.txt');

    % Wait until the file exists
    while ~exist(tempFilePath, 'file')
        % Pause for a short duration to avoid excessive CPU usage
        pause(1); % Pause for 1 second before checking again
    end

    % Open the temp.txt file for reading
    fileID = fopen(tempFilePath, 'r');

    % Read the header lines (adjust the number according to the file structure)
    headerLines = 8; % Adjust this according to the number of header lines
    for i = 1:headerLines
        fgetl(fileID);
    end

    % Read the numerical data
    FlexTvt = fscanf(fileID, '%f, %f', [2, Inf])';

    % Close the file
    fclose(fileID);

    % Delete the FlexPDE file, the respective folder and its contents
    rmdir(outputFolder, 's');
    delete(filename)
    bakfile = [filename '.bak'];
    delete(bakfile);

    % Subtract ambient temp
    FlexTvt(:,2) = FlexTvt(:,2) - FlexTvt(1,2);

    % Interpolate the FlexPDE data to match the other array time steps
    interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), expTvt(:, 1), 'spline');

    % Make temp vs time array of Flex data
    interpFlexTvt = [expTvt(:,1),interpFlexTemp];

    %%%%%%%%% Plot the two temperature profiles %%%%%%%%%%%%
    figure;

    % Plot the experimental dataset
    plot(expTvt(:,1),expTvt(:,2), '-r', 'DisplayName', 'Experimental'); % '-r' specifies a red line
    hold on; % Hold the plot to add more data

    % Plot the FlexPDE dataset
    plot(interpFlexTvt(:,1),interpFlexTvt(:,2), '-b', 'DisplayName', 'FlexPDE'); % '-b' specifies a blue line

    % Add labels and title
    xlabel('Time (s)');
    ylabel('Temperature Rise (K)');
    title('Temperature vs. Time',Title);

    % Add a legend
    legend('show');

    % Display the grid
    grid on;
    
    % Initialize the text string
    textString = '';

    % Create the text string dynamically
    for i = 1:length(SolvNam)
        textString = sprintf('%s%s: %.3e\n', textString, SolvNam{i}, SolvVal(i));
    end
    
    % Remove the trailing newline character
    textString = textString(1:end-1);
    
    % Get the current axis limits
    xLimits = xlim;
    yLimits = ylim;

   % Position for the text (bottom right corner)
    xPos = xLimits(2) - 0.1 * (xLimits(2) - xLimits(1));
    yPos = yLimits(1) + 0.1 * (yLimits(2) - yLimits(1)); 
    
    % Add the text to the plot
    text(xPos, yPos, textString, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom', 'BackgroundColor', 'white', 'EdgeColor', 'black');
    
end


function OutputResults(testFileName, testTemperature, Chi2Value, SolvedParam,testfolder)
    % Create the output folder if it does not exist
    [~, dirName, ~] = fileparts(testfolder);
    outputFolder = ['Output_',dirName];
    if ~exist(outputFolder, 'dir')
        mkdir(outputFolder);
    end

    % Get the current date
    currentDate = datestr(now, 'yyyymmdd');

    % Create the output file name
    [~, name, ~] = fileparts(testFileName); % Extract the base name of the test file
    outputFileName = fullfile(outputFolder, sprintf('%s_%s_results.txt', name, currentDate));

    % Open the file for writing
    fileID = fopen(outputFileName, 'w');

    % Write the header
    fprintf(fileID, 'TestTemperature\tChi2Value\tSolvedParam\n');

    % Write the data
    fprintf(fileID, '%f\t%f\t', testTemperature, Chi2Value);
    fprintf(fileID, '%f\t', SolvedParam);
    fprintf(fileID, '\n');

    % Close the file
    fclose(fileID);
end


