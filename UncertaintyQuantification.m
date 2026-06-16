clear

disp("Notice: Data is grouped to nearest 50°C. If tests were done at"+ newline +...
    "temperatures that are not multiples of 50, results will likely have errors.")
targetTemps = 50:50:1000;

[file_sought,file_location] = uigetfile('.txt', 'Select the fmincon output file.');
cd(file_location)
SolvedPropTable = readtable(file_sought);
SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");

testInfo = strsplit(file_sought);
sample = testInfo(1);
probe = testInfo(2);
crucible = testInfo(3);
date = extractBefore(testInfo(4),"_");

tempVals = SolvedPropTable{:,2};
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
    sum_temp = 0;
    sum_squares = 0;
    for j = rb:re
        sum_temp = sum_temp + SolvedPropTable{j,"K_Sample_W__m_K__"};
        test_unc = SolvedPropTable{j,"Chi2Error"};
        sum_squares = sum_squares + test_unc^2;
    end
    mean_temp_result = sum_temp/(re-(rb-1));
    uncF = sqrt(sum_squares);
    Fit_Uncertainty_Results(end+1,:)= {targetTemps(i) uncF};
    Average_Results(end+1, :) = {targetTemps(i) mean_temp_result};
end
Fit_Uncertainty_Results.Properties.VariableNames = {'Temperature', 'Uncertainty'};
Average_Results.Properties.VariableNames = {'Temperature', 'Average_K_Sample'};

Repeatability_Uncertainty_Results = table;

for n = 1:length(targetTemps)
    t = targetTemps(n);
    groupIndicesR = find(roughTemps == t);
    if isempty(groupIndicesR)
        continue;
    end
    rb = min(groupIndicesR);
    re = max(groupIndicesR);
    stdev = std(SolvedPropTable{rb:re,"K_Sample_W__m_K__"});
    N = re - (rb-1); % number of tests
    nu = N -1; % degrees of freedom
    t_table = dictionary([1,2,3,4,5,6,7,8,9,10],[12.706,4.303,3.182,2.770,2.571,2.447,2.365,2.306,2.262,2.228]);
    uncR = t_table(nu)*(stdev/sqrt(N));
    
    Repeatability_Uncertainty_Results(end+1,:)={targetTemps(n) uncR};
end
Repeatability_Uncertainty_Results.Properties.VariableNames = {'Temperature', 'Uncertainty'};

[file_sought,file_location] = uigetfile('.txt', 'Select the MC output file.');
cd(file_location)
MC_runs = readtable(file_sought,VariableNamingRule="preserve");

numCols = width(MC_runs);
tempValsMC = MC_runs{:, 2};
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
    stdev = std(MC_runs{rb:re,"K_Sample(W/(m*K))"});

    figure;
    histogram(MC_runs{rb:re,"K_Sample(W/(m*K))"},'BinMethod','fd');
    title("MC Results, "+string(targetTemps(k))+"°C")
    xlabel("Sample Thermal Conductivity (W/m*K)")
    ylabel("Count")
    
    MC_Uncertainty_Results(end+1,:)={targetTemps(k) stdev 1.96*stdev};
end
MC_Uncertainty_Results.Properties.VariableNames = {'Temperature','Standard_Deviation','Uncertainty'};

Total_Uncertainty_Results = table;
for m = 1:height(Fit_Uncertainty_Results)
    uncT = sqrt(Fit_Uncertainty_Results{m,"Uncertainty"}^2 + Repeatability_Uncertainty_Results{m,"Uncertainty"}^2 + MC_Uncertainty_Results{m,"Uncertainty"}^2);
    Total_Uncertainty_Results(end+1,:) = {targetTemps(m) uncT};
end
Total_Uncertainty_Results.Properties.VariableNames = {'Temperature','Uncertainty'};

figure;
errorbar(Average_Results{:,"Temperature"},Average_Results{:,"Average_K_Sample"},Total_Uncertainty_Results{:,"Uncertainty"})
xlim([Average_Results{1,"Temperature"}-50,Average_Results{end,"Temperature"}+50]);
xlabel("Temperature (°C)")
ylabel("Thermal Conductivity (W/m*K)")
saveas(gcf,string(sample) + "_" + string(date) +'_Final_Results.fig');
saveas(gcf,string(sample) + "_" + string(date) +'_Final_Results.png');