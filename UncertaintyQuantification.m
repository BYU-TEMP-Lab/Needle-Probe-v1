clear
[file_sought,file_location] = uigetfile('.txt', 'Select the output fminsearch file.');
cd(file_location)
MC_runs = readtable(file_sought,VariableNamingRule="preserve");

targetTemps = [500, 550, 600, 700, 800];
numCols = width(MC_runs);

tempStrings = string(MC_runs{:, 2});
tempVals = str2double(extractBefore(tempStrings, "°"));
roughTemps = round(tempVals / 50) * 50;

MC_results = table("Temperature","Parameter","Standard_Deviation","Uncertainty");

for i = (numCols-30):numCols
    for j = 1:length(targetTemps)
        t = targetTemps(j);
        groupIndices = find(roughTemps == t);
        if isempty(groupIndices)
            continue;
        end
        rb = min(groupIndices);
        re = max(groupIndices);
        % figure;
        % histogram(MC_runs{rb:re,i},'BinMethod','fd');
        % title(string(MC_runs.Properties.VariableNames{i})+" "+string(j));

        % mean(MC_runs{rb:re,i})
        stdev = std(MC_runs{rb:re,i});
        
        MC_results(end+1,:)={targetTemps(j) MC_runs.Properties.VariableNames{i} stdev 1.96*stdev};
    end
end