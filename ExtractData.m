function [expTvt,avgQ,avgT_amb] = ExtractData(filename,timewindow)
%[plotfolder, datafolderUSE, avgT_amb_vector] = ExtractData(run_name,raw_plot,runfolder,timewindow)

start_time = timewindow(1);  % Make sure values are a multiple of the sampling period. 
end_time = timewindow(2);


M = readmatrix(filename);
N = size(M);

time = M(:,1);
temp = M(:,2);
if N(2) >= 3
    Voltage = M(:,3);
end
if N(2) >= 4
    Current = M(:,4);
end

% Determines if voltage has been applied to the wire and uses this to
% establish time=0 and T=0
a = 1;
Vcheck = 1;
while a == 1
    if Voltage(Vcheck) <= .8
        Vcheck = Vcheck + 1;
    elseif Voltage(Vcheck) > .8
        a = 0;
    end
end

dt = time(2) - time(1);

avgT_amb = mean(temp(1:(Vcheck-2)));
temp = temp(Vcheck:end);
temp = temp - avgT_amb;
avgT_amb = avgT_amb + 273.15; % Convert to degrees Kelvin

time = time(Vcheck:end);
time = time - time(1);

Voltage = Voltage((Vcheck-1):(end-1)); % Voltage data is 1 ms behind temp data
if N(2) >= 4
    Current = Current((Vcheck+20):end);
    avgCurrent = mean(Current,'omitnan')/1000;
end

% Determine average power applied
avgVoltage = mean(Voltage);
avgQ = avgVoltage*avgCurrent;

% Create experimental temp profile list
expTvt = [time, temp];

% Cut off after time window; Find the indices where time is within the specified range
indices = (expTvt(:, 1) >= start_time) & (expTvt(:, 1) <= end_time);

% Create a new array with the filtered data
expTvt = expTvt(indices, :);

end