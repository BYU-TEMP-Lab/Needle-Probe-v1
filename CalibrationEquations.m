[file_sought,file_location] = uigetfile('.txt', 'Select the output fminsearch file.');
cd(file_location)
SolvedPropTable = readtable(file_sought);
SolvedPropTable = sortrows(SolvedPropTable,"Temp__C_","ascend");

show_figs = 'on';

vars = SolvedPropTable.Properties.VariableNames;
T_range = linspace(0, 800, 100);
fit_choice = menu("Choose fit order:", 'average', 'linear', 'quadratic', 'cubic', 'fourth-order', 'power', 'logarithmic', 'exponential');

if fit_choice == 1
    fit_type = "average";
elseif fit_choice == 2
    fit_type = "linear";
elseif fit_choice == 3
    fit_type = "quadratic";
elseif fit_choice == 4
    fit_type = "cubic";
elseif fit_choice == 5
    fit_type = "fourth-order";
elseif fit_choice == 6
    fit_type = "power";
elseif fit_choice == 7
    fit_type = "logarithmic";
elseif fit_choice == 8
    fit_type = "exponential";
end

fileID = fopen("calibration_fits_" + fit_type + ".txt", 'w');

for i = 3:width(SolvedPropTable)
    colName = vars{i};
    figure('Visible', show_figs);
    hold on
    scatter(SolvedPropTable, "Temp__C_", colName)
     
    % Extract x and y data for cleaner function calls
    x_data = SolvedPropTable.Temp__C_;
    y_data = SolvedPropTable{:,i};

    if fit_choice == 1
        value = mean(y_data);
        fprintf(fileID, '%s Average Value: %.6e\n', colName, value);
        
    elseif fit_choice == 2
        line_coeffs = polyfit(x_data, y_data, 1);
        fprintf(fileID, '%s Equation: y = %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2));
        
    elseif fit_choice == 3
        line_coeffs = polyfit(x_data, y_data, 2);
        fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3));
        
    elseif fit_choice == 4
        line_coeffs = polyfit(x_data, y_data, 3);
        fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^3 + %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3), line_coeffs(4));
        
    elseif fit_choice == 5
        line_coeffs = polyfit(x_data, y_data, 4);
        fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^4 + %.6e*(T-273.15)^3 + %.6e*(T-273.15)^2 + %.6e*(T-273.15) + %.6e\n', colName, line_coeffs(1), line_coeffs(2), line_coeffs(3), line_coeffs(4), line_coeffs(5));
        
    elseif fit_choice == 6
        % Power fit: y = a * x^b
        f = fit(x_data, y_data, 'power1');
        coeffs = coeffvalues(f);
        fprintf(fileID, '%s Equation: y = %.6e*(T-273.15)^%.6e\n', colName, coeffs(1), coeffs(2));
        
    elseif fit_choice == 7
        % Logarithmic fit: y = a * ln(x) + b (Requires custom fittype)
        ft = fittype('a*log(x) + b'); 
        f = fit(x_data, y_data, ft);
        coeffs = coeffvalues(f);
        fprintf(fileID, '%s Equation: y = %.6e*ln(T-273.15) + %.6e\n', colName, coeffs(1), coeffs(2));
        
    elseif fit_choice == 8
        % Exponential fit: y = a * e^(b*x)
        f = fit(x_data, y_data, 'exp1');
        coeffs = coeffvalues(f);
        fprintf(fileID, '%s Equation: y = %.6e*exp(%.6e*(T-273.15))\n', colName, coeffs(1), coeffs(2));
    end

    % Plotting logic
    if fit_choice == 1
        yline(value)
    elseif fit_choice > 1 && fit_choice <= 5
        fit_curve = polyval(line_coeffs, T_range);
        plot(T_range, fit_curve)
    elseif fit_choice > 5
        % Evaluate the curve fit object over T_range
        fit_curve = f(T_range);
        plot(T_range, fit_curve)
    end
end
fclose(fileID);