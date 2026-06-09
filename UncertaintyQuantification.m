MC_runs = readtable("MgNaCl 3A-IN718-01 Inconel625 06,08,26,14-24_fminsearch MC_runinfo_LABELLED.txt",VariableNamingRule="preserve");

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