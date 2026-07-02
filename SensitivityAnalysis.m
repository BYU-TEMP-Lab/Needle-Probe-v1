clc
clear
close all

y_flag = 2;

today = char(datetime('now','Format','MM-dd-yy,HH-mm'));

probe = '3A-IN718-01';
crucible = 'Inconel625';
sample = 'MgNaCl';
tvec = [0.00001 120];
tempvec = [500 550 600 600 800];
parwanted = [8 9 26 27]; % 1 to 31

baseColors = lines(8); 
baseStyles = {'-', '--', ':', '-.'};
c = zeros(length(parwanted), 3);
s = cell(length(parwanted), 1);
for i = 1:length(parwanted)
    c_idx = mod(i-1, 8) + 1;        % Cycles 1 through 8
    s_idx = floor((i-1)/8) + 1;     % Steps 1 through 4
    
    c(i, :) = baseColors(c_idx, :);
    s{i} = baseStyles{s_idx};
end
rng(1); % Set seed for reproducibility
shuffle_idx = randperm(length(parwanted));
c = c(shuffle_idx, :);
s = s(shuffle_idx);

tbegin = tvec(1);
tend = tvec(2);

sum_other_integrals = 0;
for i = 1:length(tempvec)
    for j = 1:length(parwanted)
        k = parwanted(j);
        avgTemp = tempvec(i);

        MC = 0;
        Voltage = 2.77;
        VoltageSTD = 0.00158840632635735;
        Current = 367;
        CurrentSTD = 0.000478290768346059;
        [par_vector, par_names] = Properties(probe,crucible,sample,avgTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);

        par_vector_varied = par_vector;
        par_vector_varied(k) = par_vector_varied(k)*0.95;

        t = linspace(tbegin,tend,floor((tend - tbegin) / 0.001) + 1);
        t = t';
        IV = 1;
        cp = 1;
        f_initial = NeedleProbeModel(t,par_vector,IV);
        f_varied = NeedleProbeModel(t,par_vector_varied,IV);

        if y_flag == 1 % Sloped Based Percent
            dy = diff(f_initial(:))./diff(log(t(:)));
            dy_varied = diff(f_varied(:))./diff(log(t(:)));
            sensitivity = 100*(dy_varied-dy)./dy;
        elseif y_flag == 2 % Slope Based Diff
            dy = diff(f_initial(:))./diff(log(t(:)));
            dy_varied = diff(f_varied(:))./diff(log(t(:)));
            sensitivity = dy_varied - dy; %100*(dy_varied-dy)./dy;
        elseif y_flag == 3 % Magnitude Based
            delta_p = 0.05; % You are reducing by 5%
            X_p = (f_initial - f_varied) / delta_p;
        end

        figure(i)
        set(gcf, 'Position', [0,0,800,800])
        hold on
        if y_flag == 1 | y_flag == 2 % Slope Based
            semilogx(t(2:end),sensitivity,'Color',c(j,:),'LineStyle',s{j},'LineWidth',1.5)
            if y_flag == 1
                ylabel('Relative Change of dT/dt (%)');
            elseif y_flag == 2
                ylabel('Change of dT/dt')
            end
        elseif y_flag == 3 % Magnitude Based
            semilogx(t, X_p, 'Color', c(j,:), 'LineStyle', s{j}, 'LineWidth', 1.5)
            ylabel('Scaled Sensitivity X_p (K)');
        end

        hold on
        title(['SA for ', probe, ' with ', sample, ', in ', crucible, ' at ', int2str(avgTemp), '°C'])
        set(gca, 'XScale', 'log');
        xlabel('Time (s)');
        legend(par_names(parwanted(1:j)),'Location','eastoutside')
        % pause
    end

    % Define the custom folder and file name
    customFolder = ['SA_Plots/',today];
    fileNamefig = ['SA_',probe,'_',sample,'_',crucible,'_',int2str(avgTemp),'C.fig'];
    fileNamepng = ['SA_',probe,'_',sample,'_',crucible,'_',int2str(avgTemp),'C.png'];

    % Create the folder if it does not exist
    if ~exist(customFolder, 'dir')
        mkdir(customFolder);
    end

    % Construct the full path
    fullFileNamefig = fullfile(customFolder, fileNamefig);
    fullFileNamepng = fullfile(customFolder, fileNamepng);
    
    % Save the plot
    savefig(fullFileNamefig);
    saveas(gcf,fullFileNamepng,'png')
    
    hold off
end