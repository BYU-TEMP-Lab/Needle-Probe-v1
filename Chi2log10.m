function chi2 = Chi2log10(SolvVal, SolvNam, par_vector, par_names, idx_par_to_Solv, expTvt, cross_section)

% Assign solving properties to par_vector
for i = 1:length(SolvVal)
    par_vector(idx_par_to_Solv(i,1)) = SolvVal(idx_par_to_Solv(i,2));
end

endtime = expTvt(end,1);

if strcmpi(cross_section,'axial')
    [uniqueID,filename] = RunFlexPDE_Axial(par_vector,par_names,SolvNam,endtime);
elseif strcmpi(cross_section,'radial')
    [uniqueID,filename] = RunFlexPDE_Radial(par_vector,par_names,SolvNam,endtime);
end

%RunFlexPDE_Axial
% Construct the output folder path
outputFolder = ['Flex_' uniqueID '_output']; 

% Path to the temp.txt file
tempFilePath = fullfile(outputFolder, 'temp.txt');

% Wait until the file exists
while ~exist(tempFilePath, 'file')
    pause(0.01); % Pause for 1 second before checking again
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

% Create log10 time domain
log10time = logspace(log10(1e-2),log10(endtime),length(expTvt));

% Interpolate the FlexPDE and experimental data in the log-domain
interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), log10time, 'spline');
interpExpTemp = interp1(expTvt(:, 1), expTvt(:, 2), log10time, 'spline');

% Make temp vs time array of Flex data
%interpFlexTvt = [expTvt(:, 1), interpFlexTemp];

% Chi-squared calculation
chi2 = sum(abs(((interpFlexTemp - interpExpTemp).^2) ./ interpExpTemp));
%chi2 = sum(abs(interpFlexTemp-interpExpTemp).^2)/length(interpExpTemp); % Mean Squared Error

end
