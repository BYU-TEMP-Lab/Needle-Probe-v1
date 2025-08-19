clc
clear
close all

% Inputs to run in parallel
config(1).crucible = 'Nickel200';
config(1).sample = 'Argon';
config(1).tvec = [0.001 50];
config(1).Tempvec = [22 200 650];
config(1).parwanted = [9 10 11 12 22 29]; %[7 8 9 10 11 12 13 14 15 16 17 19 20 22 23 24 25 26 29];

config(2).crucible = 'Steel316';
config(2).sample = 'Water';
config(2).tvec = [0.001, 50];
config(2).Tempvec = [22 50 80];
config(2).parwanted = [9 10 11 12 22 29];

config(3).crucible = 'Nickel200';
config(3).sample = 'FLiNaK';
config(3).tvec = [0.001, 50];
config(3).Tempvec = [480 610 750];
config(3).parwanted = [9 10 11 12 22 29];

% Delete any existing parallel pools
delete(gcp('nocreate'))
% Set up parallel computing
parpool;
if isempty(gcp('nocreate'))
    parpool('local');
end
    
% Run myFunction in parallel for each input
parfor i = 1:length(config)
    iC = config(i);
    SA(iC.crucible, iC.sample, iC.tvec, iC.Tempvec, iC.parwanted);
end

delete(gcp('nocreate'))

function SA(crucible, sample, tvec, tempvec, parwanted)

    c(1,:) = 'b- ';
    c(2,:) = 'g- ';
    c(3,:) = 'r- ';
    c(4,:) = 'c- ';
    c(5,:) = 'm- ';
    c(6,:) = 'y- ';
    c(7,:) = 'k- ';
    c(8,:) = 'b-.';
    c(9,:) = 'g-.';
    c(10,:) = 'r-.';
    c(11,:) = 'c-.';
    c(12,:) = 'm-.';
    c(13,:) = 'y-.';
    c(14,:) = 'k-.';
    c(15,:) = 'b--';
    c(16,:) = 'g--';
    c(17,:) = 'r--';
    c(18,:) = 'c--';
    c(19,:) = 'm--';
    c(20,:) = 'y--';
    c(21,:) = 'k--';
    c(22,:) = 'b: ';
    c(23,:) = 'g: ';
    c(24,:) = 'r: ';
    c(25,:) = 'c: ';
    c(26,:) = 'm: ';
    c(27,:) = 'y: ';
    c(28,:) = 'y: ';
    c(29,:) = 'k: ';
    
    tbegin = tvec(1);
    tend = tvec(2);

    for i = 1:3
        for j = 1:length(parwanted)
            k = parwanted(j);
            avgTemp = tempvec(i);

            MC = 0;
            Voltage = 4.345488;
            Current = 0.94392;
            avgQ = Voltage*Current;
            avgT_amb = avgTemp + 273.15;
            [par_vector, par_names] = Properties(crucible,sample,avgT_amb,avgQ,MC);

            SolvNam = par_names(j);

            par_vector_varied = par_vector;
            par_vector_varied(k) = par_vector_varied(k)*0.95;

            t = tbegin:.001:tend;
            t = t';
            FlexTvt = RunFlexPDE_Full(par_vector,par_names,SolvNam,tend);
            FlexTvt_varied = RunFlexPDE_Full(par_vector_varied,par_names,SolvNam,tend);

            % Subtract ambient temp
            FlexTvt(:,2) = FlexTvt(:,2) - FlexTvt(1,2);
            FlexTvt_varied(:,2) = FlexTvt_varied(:,2) - FlexTvt_varied(1,2);
            % Interpolate the FlexPDE data to match time steps
            interpFlexTemp = interp1(FlexTvt(:, 1), FlexTvt(:, 2), t, 'spline');
            interpFlexTemp_varied = interp1(FlexTvt_varied(:, 1), FlexTvt_varied(:, 2), t, 'spline');
            % Make temp vs time array of Flex data
%             interpFlexTvt = [t, interpFlexTemp];
%             interpFlexTvt_varied = [t, interpFlexTemp_varied]; 

            dy = diff(interpFlexTemp(:))./diff(log(t(:)));
            dy_varied = diff(interpFlexTemp_varied(:))./diff(log(t(:)));

            sensitivity = 100*(dy_varied-dy)./dy;

            figure(i)
            hold on
            semilogx(t(2:end),sensitivity,c(k,:),'LineWidth',2)
            hold on
            title(['SA for ',sample, ' in ', crucible, ' at ', int2str(avgTemp), '°C'])
            xlabel('Time (s)');
            ylabel('Relative Change of dT/dt (%)');
            legend(par_names(parwanted(1:j)))
    %         xline(15,'--','LineWidth',2,'color',[17, 17, 17]/255);
    %         text(.4,-65,'Approximate \rightarrow ','FontSize',12,'FontWeight','bold','color',[17, 17, 17]/255);
    %         text(.45,-68,'Test Duration','FontSize',12,'FontWeight','bold','color',[17, 17, 17]/255);
    %         text(.11,-50,'Water','FontSize',24,'FontWeight','bold','color',[17, 17, 17]/255); 
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
    end
end