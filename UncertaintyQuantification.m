clear

[file_sought,file_location] = uigetfile('.txt', 'Select the fmincon output file.');
cd(file_location)
SolvedPropTable = readtable(file_sought);
SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");

% calculate Chi^2 values for up to +/- 50% of the mean k for each temperature

%


[file_sought,file_location] = uigetfile('.txt', 'Select the MC output file.');
cd(file_location)
MC_runs = readtable(file_sought,VariableNamingRule="preserve");

targetTemps = [500, 550, 600, 700, 800];
numCols = width(MC_runs);

tempVals = MC_runs{:, 2};
roughTemps = round(tempVals / 50) * 50;

% MC_param_selection = table("Temperature","Parameter","Standard_Deviation","Uncertainty");
% 
% for i = (numCols-30):numCols
%     for j = 1:length(targetTemps)
%         t = targetTemps(j);
%         groupIndices = find(roughTemps == t);
%         if isempty(groupIndices)
%             continue;
%         end
%         rb = min(groupIndices);
%         re = max(groupIndices);
%         % figure;
%         % histogram(MC_runs{rb:re,i},'BinMethod','fd');
%         % title(string(MC_runs.Properties.VariableNames{i})+" "+string(j));
% 
%         % mean(MC_runs{rb:re,i})
%         stdev = std(MC_runs{rb:re,i});
% 
%         MC_param_selection(end+1,:)={targetTemps(j) MC_runs.Properties.VariableNames{i} stdev 1.96*stdev};
%     end
% end

MC_Uncertainty_Results = table("Temperature","Standard_Deviation","Uncertainty");

for k = 1:length(targetTemps)
    t = targetTemps(k);
    groupIndices = find(roughTemps == t);
    if isempty(groupIndices)
        continue;
    end
    rb = min(groupIndices);
    re = max(groupIndices);
    stdev = std(MC_runs{rb:re,"K_Sample(W/(m*K))"});

    figure;
    histogram(MC_runs{rb:re,"K_Sample(W/(m*K))"},'BinMethod','fd');
    title("MC Results, "+string(targetTemps(k))+"°C")
    xlabel("Sample Thermal Conductivity (W/m*K)")
    ylabel("Count")
    
    MC_Uncertainty_Results(end+1,:)={targetTemps(k) stdev 1.96*stdev};
end