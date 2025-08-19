function kSens = SA(parOpt, crucible, sample, tvec, tempvec, parwanted)

    % Define colors and line styles
    colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k','gray']; % Blue, Red, Green, Cyan, Magenta, Yellow, Black
    lineStyles = {'-', '--', ':', '-.','-o'}; % Solid, Dashed, Dotted, Dash-dotted

    % Generate 31 unique line styles
    lineStylesSet = {};
    index = 1;
    as = 0;
    for c = 1:length(colors)
        for ls = 1:length(lineStyles)
            lineStylesSet{end+1} = [colors(c), lineStyles{ls}];
            index = index + 1;
            if index > length(parwanted)
                break;
            end
        end
    end
    
    c = cell(length(parwanted),1);
    for i = 1:length(parwanted)
        c(i,:) = lineStylesSet(i);
    end
   
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
            avgQ = Voltage*Current;
            [par_vector, par_names] = Properties(parOpt, crucible,sample,avgTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);

            % SolvNam = par_names(j);

            par_vector_varied = par_vector;
            par_vector_varied(k) = par_vector_varied(k)*0.95;

            t = linspace(tbegin,tend,((tend-tbegin)/0.01));
            t = t';
            IV = 1;
            cp = 1; 
            f_initial = NeedleProbeModel(t,par_vector,cp,IV);
            f_varied = NeedleProbeModel(t,par_vector_varied,cp,IV);

            % FlexTvt = RunFlexPDE_Full(par_vector,par_names,SolvNam,tend);
            % FlexTvt_varied = RunFlexPDE_Full(par_vector_varied,par_names,SolvNam,tend);

            % Interpolate the FlexPDE data to match time steps
            % interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), t, 'spline');
            % interpFlexTemp_varied = interp1(FlexTvt_varied(:, 1), FlexTvt_varied(:, 2), t, 'spline');
            % Make temp vs time array of Flex data
%             interpFlexTvt = [t, interpFlexTemp];
%             interpFlexTvt_varied = [t, interpFlexTemp_varied]; 

            dy = diff(f_initial(:))./diff(log(t(:)));
            dy_varied = diff(f_varied(:))./diff(log(t(:)));

            sensitivity = 100*(dy_varied-dy)./dy;

            if strcmp(par_names{parwanted(j)}, 'K Sample')
                % Define your array to save
                sens_column = sensitivity; % Replace your_array with the actual array variable
                time_column = t(2:end);
                % Combine into a two-column array
                array_to_save = [time_column(:), sens_column(:)]; % Ensure both are column vectors
                
                file_name = [sample, int2str(avgTemp), '_k_sample.mat']; % Concatenate strings to form file name
            
                % Save the array to a .mat file with the dynamic name
                save(file_name, 'array_to_save');
                
                k_integral = trapz(time_column(:), sens_column(:));
                
            end 

            figure(i)
            hold on
            semilogx(t(2:end),sensitivity,c{j},'LineWidth',2)
            xlim([0.01 100])
            % ylim([2 8]
            set(gca, 'XScale', 'log');
            hold on
            title(['SA for ',sample, ' in ', crucible, ' at ', int2str(avgTemp), '°C'])
            xlabel('Time (s)');
            ylabel('Relative Change of dT/dt (%)');
            legend(par_names(parwanted(1:j)), 'Location', 'northwest') %(parwanted(1:j)))
    %         xline(15,'--','LineWidth',2,'color',[17, 17, 17]/255);
    %         text(.4,-65,'Approximate \rightarrow ','FontSize',12,'FontWeight','bold','color',[17, 17, 17]/255);
    %         text(.45,-68,'Test Duration','FontSize',12,'FontWeight','bold','color',[17, 17, 17]/255);
    %         text(.11,-50,'Water','FontSize',24,'FontWeight','bold','color',[17, 17, 17]/255); 
    
            sum_other_integrals = sum_other_integrals + trapz(time_column(:), sens_column(:));
        end
        % Define the custom folder and file name
        customFolder = 'SA_Plots';
        fileName = ['SA_',sample,'_',crucible,'_',int2str(avgTemp),'C.fig'];

        % Create the folder if it does not exist
        if ~exist(customFolder, 'dir')
            mkdir(customFolder);
        end

        % Construct the full path
        fullFileName = fullfile(customFolder, fileName);

        % Save the plot
        savefig(fullFileName); 
        
        hold off     

        close all;  
    end
    kSens = sum_other_integrals/k_integral;
end