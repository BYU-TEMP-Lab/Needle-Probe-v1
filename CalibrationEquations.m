% 1. Pick the folder (You won't see files here, just folders)
targetDir = uigetdir('', 'Select the folder containing the data');

if targetDir == 0
    error('User cancelled folder selection.');
end

% 2. Define the pattern (using wildcards to be safe)
% If files are in a subfolder, you'd need: fullfile(targetDir, 'SubfolderName', 'pattern')
file_pattern = fullfile(targetDir, '*fminsearch*');
%file_sought = "*fminsearch.txt";
file_sought = "*Ar 3A-IN718-01 Inconel625 05,11,26,11-22_fminsearch*";
file_info = dir(file_sought);
if isempty(file_info)
    error('File not found! Check the filename and your current folder: %s', pwd);
end
fullfile = dir(file_sought);
SolvedPropTable = readtable(fullfile.name);
SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");


vars = SolvedPropTable.Properties.VariableNames;
T_range = linspace(0, 800, 100);
fileID = fopen('calibration_fits.txt','w');
fittype = menu("Choose fit order:",'average','linear','quadratic','cubic','fourth-order');


for i = 3:width(SolvedPropTable)
     colName = vars{i};
     figure('Visible','on');
     hold on
     scatter(SolvedPropTable,"Temp__C_",colName)
    if fittype == 1
         value = mean(SolvedPropTable{:,i});
         fprintf(fileID, '%s Average Value: %.6e\n', colName, value);
    elseif fittype == 2
         line_coeffs = polyfit(SolvedPropTable.Temp__C_,SolvedPropTable{:,i},1);
         fprintf(fileID, '%s Equation: y = %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2));
     elseif fittype == 3
         line_coeffs = polyfit(SolvedPropTable.Temp__C_,SolvedPropTable{:,i},2);
         fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3));
     elseif fittype == 4
         line_coeffs = polyfit(SolvedPropTable.Temp__C_,SolvedPropTable{:,i},3);
         fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^3 + %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3), line_coeffs(4));
     elseif fittype == 5
         line_coeffs = polyfit(SolvedPropTable.Temp__C_,SolvedPropTable{:,i},4);
         fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^4 + %.6e*(T-273.15)^3 + %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3), line_coeffs(4), line_coeffs(5));
     end
    if fittype == 1
        yline(value)
    end
    if fittype > 1
     fit = polyval(line_coeffs,T_range);
     plot(T_range,fit)
    end
end

fclose(fileID);
