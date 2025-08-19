function chi2=Chi2(fitparam,fixparam,Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,cp,IV)

persistent counter chi2vec

todaysdate = datetime("today");
today = char(todaysdate);

Time=signal(:,1);
dTemp=signal(:,2);

% par1con = [10 40];
% par2con = [0 2.5e6];

if isempty(counter)
    counter = 0;
end

counter=counter+1; %counts number of iterations
param(Ifitpar)=abs(fitparam); %variable fitting parameters
param(Ifixpar)=abs(fixparam); %fixed parameters
Sfit=NeedleProbeModel(Time,param,cp,IV);

% minTime = min(Time);
% maxTime = max(Time);
% scaleTime = abs(Time./2 - (maxTime-minTime)/2);

%%%%% Scale from sensitivity analysis %%%%%
% % Load the two-column array
% data = load('NaNO3_KNO3_k_sample.mat');
% two_column_array = data.array_to_save;
% 
% % Separate the columns
% SA_time_original = two_column_array(:, 1); % First column (time)
% SA_values_original = two_column_array(:, 2); % Second column (values)
% 
% % Interpolate to match time
% interpolated_values = interp1(SA_time_original, SA_values_original, Time, 'linear', 'extrap');
% SA_scale_curve = [Time, interpolated_values];

%k_SA_scale = abs(Time./2 - (maxTime-minTime)/2);

chi2=sum(abs(abs(Sfit-dTemp).^2)./length(dTemp)); %chi2 to be minimized
%chi2=sum(abs(abs((Sfit-dTemp).*SA_scale_curve(:,2)).^2)./length(dTemp)); %chi2 to be minimized

% if any(isnan(chi2(:))) % Check if any value is NaN
%     disp('NaN detected!');
%     keyboard; % Pauses execution and opens the debug mode
% end

% if param(Ifitpar(1)) <= par1con(1) || param(Ifitpar(1)) >= par1con(2) || param(Ifitpar(2)) <= par2con(1) || param(Ifitpar(2)) >= par2con(2)
%     chi2 = NaN;
% end

chi2vec=[chi2vec;chi2];

% if cp == 1
%     para2 = 'Cp';
% elseif cp == 2
%     para2 = 'rhoCp';
% else
%     para2 = 'alpha';
% end

i = size(Ifitpar,2);


if manual_delay == 1
    pause(0.1);
end

end
