clear

disp("Notice: Data is grouped to nearest 50°C. If tests were done at"+ newline +...
    "temperatures that are not multiples of 50, results will likely have errors.")
targetTemps = 50:50:1000;

% Initialize cell arrays to hold the final results of each dataset for plotting
all_datasets = {};
dataset_names = {};

add_more_datasets = 'Yes';
dataset_idx = 1;

% 1. Loop to allow the user to select multiple sets of input files
while strcmp(add_more_datasets, 'Yes')
    disp("======================================================")
    disp("Select files for Dataset #" + string(dataset_idx))
    
    [file_sought, file_location] = uigetfile('.txt', "Select the fmincon output file for Dataset " + string(dataset_idx));
    if file_sought == 0
        disp("Selection cancelled. Moving to plotting phase...")
        break;
    end
    cd(file_location)
    SolvedPropTable = readtable(file_sought);
    SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");
    
    testInfo = strsplit(file_sought);
    sample = testInfo(1);
    % probe = testInfo(2);
    % crucible = testInfo(3);
    date = extractBefore(testInfo(4), "_");
    dataset_name = string(sample) + "_" + string(date);
    
    tempVals = SolvedPropTable{:,"Temp__C_"};
    roughTemps = round(tempVals/50)*50;
    
    Fit_Uncertainty_Results = table;
    Average_Results = table;
    
    for i = 1:length(targetTemps)
        t = targetTemps(i);
        groupIndicesF = find(roughTemps == t);
        if isempty(groupIndicesF)
            continue;
        end
        rb = min(groupIndicesF);
        re = max(groupIndicesF);
        
        % 2. Process using rough temps for indices, but calculate actual average temperature
        bin_actual_temps = tempVals(rb:re);
        avg_actual_temp = mean(bin_actual_temps);
        
        sum_temp = 0;
        sum_squares = 0;
        for j = rb:re
            sum_temp = sum_temp + SolvedPropTable{j,"K__Sample_W__m_K__"};
            test_unc = SolvedPropTable{j,"Chi2Error"};
            sum_squares = sum_squares + test_unc^2;
        end
        mean_temp_result = sum_temp/(re-(rb-1));
        uncF = sqrt(sum_squares);
        
        Fit_Uncertainty_Results(end+1,:) = {targetTemps(i) uncF};
        % Save both the grouping temp (Temperature) and the Actual_Temp
        Average_Results(end+1, :) = {targetTemps(i) avg_actual_temp mean_temp_result};
    end
    Fit_Uncertainty_Results.Properties.VariableNames = {'Temperature', 'Uncertainty'};
    Average_Results.Properties.VariableNames = {'Temperature', 'Actual_Temp', 'Average_K_Sample'};
    
    Repeatability_Uncertainty_Results = table;
    
    for n = 1:length(targetTemps)
        t = targetTemps(n);
        groupIndicesR = find(roughTemps == t);
        if isempty(groupIndicesR)
            continue;
        end
        rb = min(groupIndicesR);
        re = max(groupIndicesR);
        stdev = std(SolvedPropTable{rb:re,"K__Sample_W__m_K__"});
        N = re - (rb-1); % number of tests
        
        if N > 1
            nu = N - 1; % degrees of freedom
            p = 0.975;
            uncR = tinv(p,nu)*(stdev/sqrt(N));
        else
            uncR = 0; % Prevent NaN uncertainty if a temperature bin only has 1 test
        end
        
        Repeatability_Uncertainty_Results(end+1,:)={targetTemps(n) uncR};
    end
    Repeatability_Uncertainty_Results.Properties.VariableNames = {'Temperature', 'Uncertainty'};
    
    [file_sought_MC, file_location_MC] = uigetfile('.txt', "Select the MC output file for Dataset " + string(dataset_idx));
    cd(file_location_MC)
    MC_runs = readtable(file_sought_MC, VariableNamingRule="preserve");
    
    % numCols = width(MC_runs);
    tempValsMC = MC_runs{:, "Temp(°C)"};
    roughTempsMC = round(tempValsMC / 50) * 50;
    
    MC_Uncertainty_Results = table;
    
    for k = 1:length(targetTemps)
        t = targetTemps(k);
        groupIndicesMC = find(roughTempsMC == t);
        if isempty(groupIndicesMC)
            continue;
        end
        rb = min(groupIndicesMC);
        re = max(groupIndicesMC);
        stdev = std(MC_runs{rb:re,"K\_Sample(W/(m*K))"});
    
        figure;
        histogram(MC_runs{rb:re,"K\_Sample(W/(m*K))"},'BinMethod','fd');
        title(dataset_name + " - MC Results, " + string(targetTemps(k)) + "°C")
        xlabel("Sample Thermal Conductivity (W/m*K)")
        ylabel("Count")
        
        MC_Uncertainty_Results(end+1,:)={targetTemps(k) stdev 1.96*stdev};
    end
    MC_Uncertainty_Results.Properties.VariableNames = {'Temperature','Standard_Deviation','Uncertainty'};
    
    Total_Uncertainty_Results = table;
    temps = intersect(intersect(Fit_Uncertainty_Results.Temperature, Repeatability_Uncertainty_Results.Temperature), MC_Uncertainty_Results.Temperature);
    for m = 1:numel(temps)
        t = temps(m);
        uncF = Fit_Uncertainty_Results.Uncertainty(Fit_Uncertainty_Results.Temperature==t);
        uncR = Repeatability_Uncertainty_Results.Uncertainty(Repeatability_Uncertainty_Results.Temperature==t);
        uncMC = MC_Uncertainty_Results.Uncertainty(MC_Uncertainty_Results.Temperature==t);
        Total_Uncertainty_Results(end+1,:) = {t sqrt(uncF.^2 + uncR.^2 + uncMC.^2)};
    end
    Total_Uncertainty_Results.Properties.VariableNames = {'Temperature','Uncertainty'};
    
    % Match the Average_Results strictly to the intersection of temperatures to avoid dimension mismatch
    idx_match = ismember(Average_Results.Temperature, temps);
    final_Average = Average_Results(idx_match, :);
    
    final_results = [final_Average Total_Uncertainty_Results(:, 'Uncertainty')];
    writetable(final_results, dataset_name + '_Final_Results.txt', 'Delimiter', '\t')
    
    % Store the processed dataset for the final combined plot
    all_datasets{end+1} = final_results;
    dataset_names{end+1} = dataset_name;
    
    % Ask if the user wants to add another pair of files
    add_more_datasets = questdlg('Do you want to add another dataset pair?', 'Add Dataset', 'Yes', 'No', 'No');
    dataset_idx = dataset_idx + 1;
end

% 3. Plot all of those together on a single figure
if ~isempty(all_datasets)
    figure('Name', 'Combined Thermal Conductivity', 'Color', 'w');
    hold on;
    
    min_x = inf;
    max_x = -inf;
    
    for d = 1:length(all_datasets)
        data = all_datasets{d};
        % Plots using Actual_Temp on the X axis, instead of the rounded TargetTemp
        errorbar(data{:,"Actual_Temp"}, data{:,"Average_K_Sample"}, data{:,"Uncertainty"}, ...
            '-o', 'DisplayName', dataset_names{d}, 'LineWidth', 1.5, 'MarkerSize', 6);
        
        % Update limits
        if min(data{:,"Actual_Temp"}) < min_x
            min_x = min(data{:,"Actual_Temp"});
        end
        if max(data{:,"Actual_Temp"}) > max_x
            max_x = max(data{:,"Actual_Temp"});
        end
    end
    
    xlim([min_x - 50, max_x + 50]);
    xlabel("Temperature (°C)")
    ylabel("Thermal Conductivity (W/m*K)")
    legend('Location', 'best')
    grid on;
    hold off;
    
    saveas(gcf, 'Combined_Final_Results.fig');
    saveas(gcf, 'Combined_Final_Results.png');
    disp("Combined plotting complete.")
end