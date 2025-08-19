function chi2 = Chi2(SolvVal,SolvNam,par_vector,par_names,idx_par_to_Solv,expTvt)

% Assign solving properties to par_vector
for i = 1:length(SolvVal)
    par_vector(idx_par_to_Solv(i,1)) = SolvVal(idx_par_to_Solv(i,2));
end

endtime = expTvt(end,1);

[uniqueID,filename] = RunFlexPDE(par_vector,par_names,SolvNam,endtime);

% Construct the output folder path
outputFolder = ['Flex_' uniqueID '_output'];

% Path to the temp.txt file
tempFilePath = fullfile(outputFolder, 'temp.txt');

% Wait until the file exists
while ~exist(tempFilePath, 'file')
    % Pause for a short duration to avoid excessive CPU usage
    pause(0.1); % Pause for 0.1 second before checking again
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

% Define the experimental temperature arrays
expTemp = expTvt(:, 2);


%%%%%%%% Objective function %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%chi2 = sum(abs(interpFlexTemp-expTemp).^2)/length(expTemp) %chi2 to be minimized
chi2 = sum(abs((interpFlexTemp-expTemp).^2)./expTemp);


