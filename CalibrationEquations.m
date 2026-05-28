[file_sought,file_location] = uigetfile('.txt', 'Select the output fminsearch file.');
cd(file_location)
SolvedPropTable = readtable(file_sought);
SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");

show_figs = 'on';

vars = SolvedPropTable.Properties.VariableNames;
T_range = linspace(0, 800, 100);
fittype = menu("Choose fit order:",'average','linear','quadratic','cubic','fourth-order');
if fittype == 1
    fit_type = "average";
elseif fittype == 2
    fit_type = "linear";
elseif fittype == 3
    fit_type = "quadratic";
elseif fittype == 4
    fit_type = "cubic";
elseif fittype == 5
    fit_type = "fourth-order";
end

fileID = fopen("calibration_fits_"+fit_type+".txt",'w');

for i = 3:width(SolvedPropTable)
     colName = vars{i};
     figure('Visible',show_figs);
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
