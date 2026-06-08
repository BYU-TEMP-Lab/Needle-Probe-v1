clc
clear
close all

today = char(datetime('now','Format','MM-dd-yy,HH-mm'));

probe = '3A-IN718-01';
crucible = 'Inconel625';
sample = 'MgNaCl';
tvec = [0.0001 70];
tempvec = [500 550 600 650 700 750 800];
parwanted = [1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31];

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
        Voltage = 4.1951;
        VoltageSTD = 0.00158840632635735;
        Current = 0.7816;
        CurrentSTD = 0.000478290768346059;
        [par_vector, par_names] = Properties(probe,crucible,sample,avgTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);

        par_vector_varied = par_vector;
        par_vector_varied(k) = par_vector_varied(k)*0.95;

        t = linspace(tbegin,tend,((tend-tbegin)/0.001));
        t = t';
        IV = 1;
        cp = 1;
        f_initial = NeedleProbeModel(t,par_vector,cp,IV);
        f_varied = NeedleProbeModel(t,par_vector_varied,cp,IV);

        dy = diff(f_initial(:))./diff(log(t(:)));
        dy_varied = diff(f_varied(:))./diff(log(t(:)));

        % % Add this inside your parameter loop, replacing the diff() calculations
        % delta_p = 0.05; % You are reducing by 5%
        % X_p = (f_initial - f_varied) / delta_p;

        sensitivity = 100*(dy_varied-dy)./dy;

        figure(i)
        set(gcf, 'Position', [0,0,800,800])
        hold on
        semilogx(t(2:end),sensitivity,'Color',c(j,:),'LineStyle',s{j},'LineWidth',1.5)
        % xlim([0.0001 60]);
        % Plot X_p
        % semilogx(t, X_p, 'Color', c(j,:), 'LineStyle', s{j}, 'LineWidth', 1.5)
        % ylabel('Scaled Sensitivity X_p (K)');
        hold on
        title(['SA for ', probe, ' with ', sample, ', in ', crucible, ' at ', int2str(avgTemp), '°C'])
        set(gca, 'XScale', 'log');
        xlabel('Time (s)');
        % ylabel('Relative Change of dT/dt (%)');
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
    close all
end