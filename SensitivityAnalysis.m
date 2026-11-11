clc
clear
close all

y_flag = 2;

today = char(datetime('now','Format','MM-dd-yy,HH-mm'));

probe = '3A-IN718-01';
crucible = 'Inconel625';
sample = 'Ar';
tvec = [1 1080];
tempvec = [400 500 600 700 800];
parwanted = [13 25 34]; %1:34;
numParams = length(parwanted);

% 9 high-contrast, visually distinct colors
baseColors = [
    0.0000, 0.4470, 0.7410; % Blue
    0.8500, 0.3250, 0.0980; % Red-Orange
    0.9290, 0.6940, 0.1250; % Gold
    0.4940, 0.1840, 0.5560; % Purple
    0.4660, 0.6740, 0.1880; % Green
    0.3010, 0.7450, 0.9330; % Cyan
    0.6350, 0.0780, 0.1840; % Dark Red
    0.1500, 0.1500, 0.1500; % Charcoal Black
    0.8500, 0.3700, 0.7500  % Magenta
];
baseStyles  = {'-', '--', ':', '-.'};
baseMarkers = {'none', 'o', 's', '^', 'd', 'v', 'p', 'h'};

c = zeros(numParams, 3);
s = cell(numParams, 1);
m = cell(numParams, 1);

for i = 1:numParams
    c_idx = mod(i-1, 9) + 1;                  % Cycles 1 through 9
    s_idx = floor((i-1)/9) + 1;               % Steps 1 through 4 (supports up to 36 lines)
    m_idx = mod(i-1, length(baseMarkers)) + 1;% Coprime with 9: unique marker per repeated color
    
    c(i, :) = baseColors(c_idx, :);
    s{i}    = baseStyles{s_idx};
    m{i}    = baseMarkers{m_idx};
end

rng(1); % Set seed for reproducibility
shuffle_idx = randperm(numParams);
c = c(shuffle_idx, :);
s = s(shuffle_idx);
m = m(shuffle_idx);

% Precompute t and log-spaced MarkerIndices (staggered so overlapping lines don't hide markers)
tbegin = tvec(1);
tend   = tvec(2);
t = linspace(tbegin, tend, floor((tend - tbegin) / 0.001) + 1)';

numMarkers = 10; % Number of markers shown per line across the log axis
m_indices = cell(numParams, 1);
for j = 1:numParams
    % Slight log-space offset per parameter so markers on y=0 lines don't stack on top of each other
    offset = (j - 1) / numParams * 0.08;
    t_targets = logspace(log10(tbegin) + offset, log10(tend) - 0.08 + offset, numMarkers);
    
    % Convert target times into array indices (clamped to length(t)-1 for t(2:end) compatibility)
    idx = round((t_targets - tbegin) / 0.001) + 1;
    idx = max(1, min(length(t) - 1, idx));
    m_indices{j} = unique(idx);
end

sum_other_integrals = 0;
for i = 1:length(tempvec)
    avgTemp = tempvec(i);
    MC = 0;
    Voltage = 2.77;
    VoltageSTD = 0.00158840632635735;
    Current = 367;
    CurrentSTD = 0.000478290768346059;
    
    [par_vector, par_names] = Properties(probe,crucible,sample,avgTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);
    
    IV = 1;
    cp = 1;
    f_initial = MatrixNeedleProbeModel(t, par_vector, IV); % Computed once per temperature
    
    figure(i)
    set(gcf, 'Position', [0, 0, 1000, 800]) % Slightly wider to fit 34-item legend
    hold on
    
    for j = 1:length(parwanted)
        k = parwanted(j);
        par_vector_varied = par_vector;
        par_vector_varied(k) = par_vector_varied(k) * 0.95;
        
        f_varied = MatrixNeedleProbeModel(t, par_vector_varied, IV);
        
        if y_flag == 1 % Slope Based Percent
            dy = diff(f_initial(:)) ./ diff(log(t(:)));
            dy_varied = diff(f_varied(:)) ./ diff(log(t(:)));
            sensitivity = 100 * (dy_varied - dy) ./ dy;
        elseif y_flag == 2 % Slope Based Diff
            dy = diff(f_initial(:)) ./ diff(log(t(:)));
            dy_varied = diff(f_varied(:)) ./ diff(log(t(:)));
            sensitivity = dy_varied - dy;
        elseif y_flag == 3 % Magnitude Based
            delta_p = 0.05;
            X_p = (f_initial - f_varied) / delta_p;
        end
        
        if y_flag == 1 || y_flag == 2
            semilogx(t(2:end), sensitivity, ...
                'Color', c(j,:), ...
                'LineStyle', s{j}, ...
                'Marker', m{j}, ...
                'MarkerIndices', m_indices{j}, ...
                'MarkerSize', 5, ...
                'LineWidth', 1.5);
        elseif y_flag == 3
            semilogx(t, X_p, ...
                'Color', c(j,:), ...
                'LineStyle', s{j}, ...
                'Marker', m{j}, ...
                'MarkerIndices', m_indices{j}, ...
                'MarkerSize', 5, ...
                'LineWidth', 1.5);
        end
    end
    
    % Apply labels and legend once after all 34 lines are plotted
    if y_flag == 1
        ylabel('Relative Change of dT/dt (%)');
    elseif y_flag == 2
        ylabel('Change of dT/dt');
    elseif y_flag == 3
        ylabel('Scaled Sensitivity X_p (K)');
    end
    
    set(gca, 'XScale', 'log');
    xlabel('Time (s)');
    title(['SA for ', probe, ' with ', sample, ', in ', crucible, ' at ', int2str(avgTemp), '°C']);
    legend(par_names(parwanted), 'Location', 'eastoutside', 'NumColumns', 2);
    
    % Save the plot
    customFolder = ['SA_Plots/', today];
    if ~exist(customFolder, 'dir')
        mkdir(customFolder);
    end
    
    % Note: tempvec has two 600s; include index 'i' if you don't want the second 600C to overwrite the first
    fileNamefig = ['SA_', probe, '_', sample, '_', crucible, '_', int2str(avgTemp), 'C.fig'];
    fileNamepng = ['SA_', probe, '_', sample, '_', crucible, '_', int2str(avgTemp), 'C.png'];
    
    savefig(fullfile(customFolder, fileNamefig));
    saveas(gcf, fullfile(customFolder, fileNamepng), 'png');
    
    hold off
end