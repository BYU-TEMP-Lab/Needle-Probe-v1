clc
clear
close all

%Options for Speed and other utilities%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
on = 1;
off = 0;

global_fitting = off; % Uses fminsearch when off

Full_Analysis = off; %Makes the code do an entire analysis with Monte Carlo and chi2 error analyses and plots the results.

MC = off; %Turns on Monte Carlo error analysis.

cp = off; %Makes the program fit for specific heat instead of thermal diffusivity. Requires accurate density data.
rhocp = off; %Fits for rho*Cp, use if no known density data exists. Will overwrite cp;

raw_plot = off; %Create plots of the raw data. Keep off to increase speed.
iplotfit = off; %Shows the plot during the fitting process. Keep off to increase speed.
manual_delay = off; %Adds in a manual delay that helps to see the fitting process. Significantly increases runtime.
chi2plots = off; %show plots from the chi2 error analysis

MC_iterations = 250; %The numbers of iterations to run as part of the Monte Carlo Analysis
timewindow = [0.5 60]; % [1 50]; % (15 s) Sets the time interval to be analyzed, in seconds. Set beginning to 0 to start from the beginning
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

iterations = 0;

if MC == 1 || Full_Analysis == 1
    MC_iteration_limit = MC_iterations;
else
    MC_iteration_limit = 1;
end

if rhocp == 1
    cp = 2;
end

if cp == 1
    Para2 = 'Cp';
    Para2full = 'Specific Heat [J/(K*Kg)]';
elseif cp == 2
    Para2 = 'rho*Cp';
    Para2full = 'Density*Specific Heat [J/(K*m^3)]';
else
    Para2 ='alpha';
    Para2full = 'Thermal Diffusivity [m^2/s]';
end

currentFOLDER = pwd;
%todaysdate = datetime("today");
today = sprintf('%02d%02d%02d', month(datetime), day(datetime), mod(year(datetime), 100));
% today = char(todaysdate);

%crucible = 'Nickel200';

m=menu('Crucible Material:',...
    'Steel316',...
    'Nickel 200',...
    'Inconel 625',...
    'end');

if m == 1
    crucible = 'Steel316';
elseif m == 2
    crucible = 'Nickel200';
elseif m == 3
    crucible = 'Inconel625';
else
    disp('No crucible selected, program terminated')
    return
end

% sample = 'Ar';

m=menu('Sample Material:',...
    'H2O',...
    'NaNO3',...
    'Toluene',...
    'KNO3',...
    'Propylene Glycol',...
    'FLiNaK',...
    'FLiBe',...
    'FMgNaK',...
    'LiCl-KCl',...
    'NaCl-KCl',...
    'LiF-NaF',...
    'LiCl-NaCl',...
    'ZnCl-KCl',...
    'NaNO3-KNO3',...
    '1npNaNO3-KNO3',...
    'Ar',...
    'end');

if m == 1
    sample = 'H2O';
elseif m == 2
    sample = 'NaNO3';
elseif m == 3
    sample = 'Toluene';
elseif m == 4
    sample = 'KNO3';
elseif m == 5
    sample = 'PropyleneGlycol';
elseif m == 6
    sample = 'FLiNaK';
elseif m == 7
    sample = 'FLiBe';
elseif m == 8
    sample = 'FMgNaK';
elseif m == 9
    sample = 'LiCl-KCl';
elseif m == 10
    sample = 'NaCl-KCl';
elseif m == 11
    sample = 'LiF-NaF';
elseif m == 12
    sample = 'LiCl-NaCl';
elseif m == 13
    sample = 'KCl-ZnCl';
elseif m == 14
    sample = 'NaNO3-KNO3';
elseif m == 15
    sample = '1npNaNO3-KNO3';
elseif m == 16
    sample = 'Ar';
else
    disp('Cannot run data without a sample. Program terminated.')
    return
end

choices = {
    "1 - K Eff. Wires",           
    "2 - Alpha Eff. Wires",           
    "3 - K Insulation",           
    "4 - Alpha Insulation",  
    "5 - Rth Insulation-Sheath",  
    "6 - K Sheath",           
    "7 - Alpha Sheath", 
    "8 - K Sample",
    "9 - Alpha Sample",
    "10 - K Crucible",
    "11 - Alpha Crucible",
    "12 - Emissivity Probe",
    "13 - Emissivity Crucible",
    "19 - Rwires",
    "20 - Rsheath Inner",
    "21 - Rsheath",
    "22 - Rsample",
    "23 - Rcrucible",
    "26 - Rho Sample",
    "27 - Cp Sample",
    "28 - Rhosample * Cp Sample",
    "29 - Current",
    "30 - Flux Decay Factor"
};

% Display the dialog to select multiple values
[m, ok] = listdlg('PromptString', 'Select Properties to Solve For:', ...
    'SelectionMode', 'multiple', ...
    'ListString', choices);

% Initialize the lists to store selected values
SolveListNames = {};
SolveList = [];

% Check if the user made a selection
if ok
    for i = 1:length(m)
        switch m(i)
            case 1
                SolveListNames = [SolveListNames, "1"];
                SolveList = [SolveList, 1];
            case 2
                SolveListNames = [SolveListNames, "2"];
                SolveList = [SolveList, 2];
            case 3
                SolveListNames = [SolveListNames, "3"];
                SolveList = [SolveList, 3];
            case 4
                SolveListNames = [SolveListNames, "4"];
                SolveList = [SolveList, 4];
            case 5
                SolveListNames = [SolveListNames, "5"];
                SolveList = [SolveList, 5];
            case 6
                SolveListNames = [SolveListNames, "6"];
                SolveList = [SolveList, 6];
            case 7
                SolveListNames = [SolveListNames, "7"];
                SolveList = [SolveList, 7];
            case 8
                SolveListNames = [SolveListNames, "8"];
                SolveList = [SolveList, 8];
            case 9
                SolveListNames = [SolveListNames, "9"];
                SolveList = [SolveList, 9];
            case 10
                SolveListNames = [SolveListNames, "10"];
                SolveList = [SolveList, 10];
            case 11
                SolveListNames = [SolveListNames, "11"];
                SolveList = [SolveList, 11];
            case 12
                SolveListNames = [SolveListNames, "12"];
                SolveList = [SolveList, 12];
            case 13
                SolveListNames = [SolveListNames, "13"];
                SolveList = [SolveList, 13];
            case 14
                SolveListNames = [SolveListNames, "19"];
                SolveList = [SolveList, 19];
            case 15
                SolveListNames = [SolveListNames, "20"];
                SolveList = [SolveList, 20];
            case 16
                SolveListNames = [SolveListNames, "21"];
                SolveList = [SolveList, 21];
            case 17
                SolveListNames = [SolveListNames, "22"];
                SolveList = [SolveList, 22];
            case 18
                SolveListNames = [SolveListNames, "23"];
                SolveList = [SolveList, 23];
            case 19
                SolveListNames = [SolveListNames, "26"];
                SolveList = [SolveList, 26];
            case 20
                SolveListNames = [SolveListNames, "27"];
                SolveList = [SolveList, 27];
            case 21
                SolveListNames = [SolveListNames, "28"];
                SolveList = [SolveList, 28];
            case 22
                SolveListNames = [SolveListNames, "29"];
                SolveList = [SolveList, 29];
            case 23
                SolveListNames = [SolveListNames, "30"];
                SolveList = [SolveList, 30];
        end
    end
end

joinedString = char(strjoin(SolveListNames, '_'));

if global_fitting == 0
    run_name = [sample ' ' joinedString ' ' today '_fminsearch'];
else
    run_name = [sample ' ' joinedString ' ' today '_global'];
end

runfolder = [currentFOLDER '\Analysis_Results\' run_name];
if ~exist(runfolder, 'dir')
    mkdir(runfolder);
end 

[plotfolder, datafolderUSE, aveTemp_vector] = ExtractData(run_name,raw_plot,runfolder,timewindow);

tic

datafolder = datafolderUSE;
cd(datafolder);
names = dir();
cd(currentFOLDER);

ExcelFile = [run_name '.xlsx'];

Results = zeros(numel(names)-2, 9);

for n = 3:numel(names)
    [~, fn] = fileparts(names(n).name);
    %loading data
    cd(datafolder);
    signal= load([fn '.txt']);
    % Remove possible first time step (11-25-24, getting desperate)
    %signal = signal(n+9*1:end, :);

    cd(currentFOLDER);

    M = size(signal);

    Time=signal(:,1);
    dTemp=signal(:,2);

    % checks if there's a voltage signal present and takes its average, if
    % not present will assume voltage to wire is 85% of voltage from power
    % supply
    if M(2) >= 3
        Voltage=median(signal(:,3));    %Changed to median from mean to avoid influence of outliers
        VoltageSTD=std(signal(:,3));
    else
        Voltage = .85*str2double(fn(end));%.921*str2double(fn(end));
        VoltageSTD = Voltage*.05/2;
    end

    % Cleaning up current signal because the current is at a different
    % sampling freq. then also takes average
    if M(2) >= 4
        for b = 1:1:length(Time)
            if signal(b,4) < 10
                signal(b,4) = NaN;
            end
        end
        % corrects mA to A
        Current = median(signal(:,4),'omitnan')/1000;   %Changed to median from mean to avoid influence of outliers
        CurrentSTD = std(signal(:,4),'omitnan')/1000;
        IV = on;
        if isnan(Current)
            IV = off;
        end
    else
        Current = 0;
        CurrentSTD = 0;
        IV = off;
    end

    ndata=length(Time);
    fprintf('filename: %s \n',fn);
    fprintf('number of data points: %i \n',ndata);
    aveTemp = aveTemp_vector(n-2);

    for run = 1:MC_iteration_limit
        if Full_Analysis == on
            if run == 1
                MC = 0;
            else
                MC = 1;
            end
        end
        [par_vector, par_names] = Properties(crucible,sample,aveTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);

        if ~exist('iexecuted','var')
            n0=length(par_vector);			%total number of parameters
            iexecuted=1;
            ipar=1;			%fit parameter index for error test
            ntest=20;		%number of error analysis values
        end

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % if cp == 1
        %     %Ifitpar = [3 23];
        %     Ifitpar = [3 23];   % Fits for k, cp of sample       
        % elseif cp == 2
        %     Ifitpar = [3 24];   % Fits for k, rho, cp of sample       
        % else
        %     Ifitpar = [3 4];    % Fits for k, alpha of sample
        % end

        Ifitpar = SolveList;

        npar = size(Ifitpar,2);
        parstart = zeros(npar,1);

        for b = 1:npar
            parstart(b) = par_vector(Ifitpar(b));
            parlabel(b) = par_names(Ifitpar(b),1) + ' [' + par_names(Ifitpar(b),2) + ']';
        end

          fitresult_run = zeros(MC_iteration_limit,npar);

%         Para1start = par_vector(Ifitpar(1));
%         Para2start = par_vector(Ifitpar(2));
%         Par1_label = par_names(Ifitpar(1),1) + ' [' + par_names(Ifitpar(1),2) + ']';
%         Par2_label = par_names(Ifitpar(2),1) + ' [' + par_names(Ifitpar(2),2) + ']';

        a=ones(1,n0);
        a(Ifitpar)=0;
        Ifixpar=find(a);	%fix parameter index array
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if global_fitting == 0
            %%%%%%%%%% fminsearch fitting
            Sstart=NeedleProbeModel(Time,par_vector,cp,IV);
            close all;

            foptions=optimset('TolFun', 1e-6, 'TolX', 1e-6, 'MaxIter', 1e4,'MaxFunEvals',1e4 ...
                );

            [fitresult, Chi2_value]=fminsearch('Chi2',par_vector(Ifitpar),foptions,par_vector(Ifixpar),Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,cp,IV);

            %[optimized_params, resnorm] = lsqcurvefit(objective_func, initial_params, x_data, y_data, [], [], options);

            fitresult = abs(fitresult);

            clear Chi2

            %%%%%%%%%%% lsqnonlin:
            % % Generate the initial starting model
            % Sstart = NeedleProbeModel(Time, par_vector, cp, IV);
            % close all;
            % 
            % % Optimization options for lsqnonlin
            % options = optimoptions('lsqnonlin', ...
            %     'Algorithm', 'trust-region-reflective', ... % Default algorithm, suitable for most problems
            %     'TolFun', 1e-9, ...
            %     'TolX', 1e-9, ...
            %     'MaxIter', 1e5, ...
            %     'MaxFunctionEvaluations', 6e6, ...
            %     'Display', 'iter'); % Display iteration details (optional)
            % 
            % % Define the residual function handle
            % residual_func = @(fit_params) Residuals(fit_params, par_vector(Ifixpar), Ifitpar, Ifixpar, Sstart, signal, manual_delay, iplotfit, cp, IV);
            % 
            % % Run lsqnonlin
            % [fitresult, resnorm, residuals, exitflag, output] = lsqnonlin(residual_func, par_vector(Ifitpar), [], [], options);
            % 
            % % Ensure parameters are positive (optional)
            % fitresult = abs(fitresult);
            % 
            % chi2 = Chi2(fitparam,par_vector(Ifixpar),Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,cp,IV)
            % 
            % [chi2_fitresult, Chi2_value]=fminsearch('Chi2',par_vector(Ifitpar),foptions,par_vector(Ifixpar),Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,cp,IV);
            % 
            % % Clear unnecessary variables
            % clear Chi2

        else

            % Initialize starting parameters and options
            Sstart = NeedleProbeModel(Time, par_vector, cp, IV); % Model initialization
            close all;
            
            foptions = optimset('MaxIter', 1e9, 'MaxFunEvals', 3e16, 'Display', 'iter'); % Optimization options
            
            % Define the Chi2 function as an anonymous function for optimization
            chi2_func = @(fit_params) Chi2(fit_params, par_vector(Ifixpar), Ifitpar, Ifixpar, Sstart, signal, manual_delay, iplotfit, cp, IV);
            
            % Bounds for the parameters (optional, set to large ranges if unknown)
            lb = par_vector(Ifitpar) * 0; % Example: 0% of initial guess
            ub = par_vector(Ifitpar) * 5000; % Example: 5000% of initial guess
            
            % Define the optimization problem for fmincon
            problem = createOptimProblem('fmincon', ...
                'objective', chi2_func, ...
                'x0', par_vector(Ifitpar), ...
                'lb', lb, ...
                'ub', ub, ...
                'options', foptions);
            
            % Use MultiStart to explore multiple initial guesses
            ms = MultiStart('UseParallel', true); % Enable parallel computing for efficiency
            num_starts = 100; % Number of starting points
            [fitresult, fval] = run(ms, problem, num_starts);
            
            % Ensure the results are valid
            fitresult = abs(fitresult); % Ensure positive values
            clear Chi2
        end


        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %show actual result
        close all;
        param=par_vector;
        param(Ifitpar)=fitresult;
        Sfit=NeedleProbeModel(Time,param,cp,IV);

        if MC == 0
            figure;
            semilogx(Time,dTemp-Sfit,'o',Time,Sstart-Sfit,'o');
            zoom on;
            xlabel('Time(sec)');
            ylabel('▲T (Kelvin)');
            legend('Data - Solved Model','Initial Model - Solved Model', 'Location', 'northwest')
            title(['Residuals: ', num2str(Voltage),'V ', num2str(aveTemp), '°C ' ,today]);

            f = gcf;
            cd(plotfolder);
            name1 = [sample '_' crucible '_' num2str(aveTemp) '_Voltage' num2str(Voltage) '_residues' '.png'];
            saveas(f,name1);
            close
            cd(currentFOLDER);

            figure;
            semilogx(Time,dTemp,'o', Time,Sstart, Time,Sfit);
            zoom on;
            xlabel('Time(sec)');
            ylabel('▲T (Kelvin)');
            legend('Exp. Data', 'Initial Model', 'Solved Model', 'Location', 'northwest')
            run_name_string = strrep(run_name, '_', ' ');
            title(['Solution: ', run_name_string, ' ', num2str(fix(aveTemp)), '°C ', num2str(Voltage), 'V']);

            f = gcf;
            cd(plotfolder);
            name1 = [sample '_' crucible '_' num2str(aveTemp) '_Voltage' num2str(Voltage) ' result fit' '.png'];
            saveas(f,name1);
            %close
            cd(currentFOLDER);

        end

        %         fprintf('fit parameters: %s %s\n',par_names(Ifitpar(1),1), par_names(Ifitpar(2),1));
        %         fprintf('start parameters: %f   %f\n',Para1start, Para2start);
        %         fprintf('fit results: %f   %f\n',fitresult(1), fitresult(2));
        fprintf('Fit parameters: ')
        for c=1:npar
            fprintf('[%s] ',par_names(Ifitpar(1,c)))
        end

        fprintf('\nStarting parameter values:')
        for c=1:npar
            if any([2 4 6 14 20 21]==Ifitpar(c))
                fprintf(' [%e]',parstart(c));
            else
                fprintf(' [%f]',parstart(c));
            end
        end

        fprintf('\nFit results:')
        for c=1:npar
            if any([2 4 6 14 20 21]==Ifitpar(c))
                fprintf(' %e',fitresult(c));
            else
                fprintf(' %f',fitresult(c));
            end
        end
        fprintf('\n');

        fitresult_run(run,:) = fitresult;

        cd(runfolder)

        MCruninfo = fopen([run_name, ' MC_runinfo.txt'],'at');
        fprintf(MCruninfo, '%s', num2str(run));
        fprintf(MCruninfo,'\t');
        fprintf(MCruninfo, '%s', [num2str(aveTemp), '°C ', num2str(Voltage),'V ']);
        fprintf(MCruninfo,'\t');

        for d=1:npar
            if any([2 4 6 14 20 21]==Ifitpar(d))
                fprintf(MCruninfo,' %e',fitresult(d));
                fprintf(MCruninfo,'\t');
            else
                fprintf(MCruninfo,' %f',fitresult(d));
                fprintf(MCruninfo,'\t');
            end
        end

        fprintf(MCruninfo, '%s', num2str(par_vector));

        fprintf(MCruninfo, '\n');
        fclose(MCruninfo);

        cd(currentFOLDER)

        %         cd(runfolder)
        %
        %         Header = {'Iteration','Temp','Volt','Sstart0','Sfit0','K','a'};
        %
        %         if ~exist(ExcelFile,'dir')
        %             writecell(Header,ExcelFile,'Sheet',1);
        %         end
        %
        %         nextLINE = {brian,aveTemp,Voltage,Sstart(1),Sfit(1),fitresult(1),fitresult(2)};
        %         writecell(nextLINE,ExcelFile,'Sheet',1,'WriteMode','append');
        %
        %         cd(currentFOLDER)

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if MC == 0
            %error analysis
            ipar=min(length(Ifitpar),ipar);
            parmin=0.5*fitresult(ipar);
            parmax=1.5*fitresult(ipar);

            parvec=linspace(parmin,parmax,ntest)';
            chitestvec=zeros(ntest,1);
            familyvec=zeros(ndata,ntest);
            for ii=1:ntest
                partest=parvec(ii);
                fitresulttest=fitresult;
                fitresulttest(ipar)=partest;
                chitestvec(ii)=[Chi2(fitresulttest,par_vector(Ifixpar),Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,cp,IV)];
            end
            clear Chi2

            Tvec=Time*ones(1,ntest);

            for ii=1:ntest
                partest=parvec(ii);
                param(Ifitpar(ipar))=partest; %variable fitting parameters
                familyresult = NeedleProbeModel(Time,param,cp,IV);
                familyvec(:,ii)=familyresult;
            end

            P=polyfit(parvec,chitestvec,2); % 2);
            parabool=polyval(P,parvec);
            sigpar=sqrt(abs(-P(2)^2+4*P(1)*P(3)))/(2*P(1));
            Chi2_error = sigpar/sqrt(ndata);

            if chi2plots == 1
                figure;
                comstr=['par. ',int2str(ipar),' varies between ',num2str(parmin),' and ',num2str(parmax)];

                semilogx(Time,familyvec);
                zoom on;
                xlabel('Time(sec)');
                ylabel('▲T (Kelvin)');
                title(['familyvec over Tvec',today,' ',comstr]);

                figure;
                plot(parvec,chitestvec,'o',parvec,parabool);
                chisave=[parvec,chitestvec,parabool];
                title([run_name,' par(',int2str(ipar),'): ',num2str(fitresult(ipar)),'+/-',num2str(sigpar),'/sqrt(',int2str(ndata),') file: ',fn]);
                zoom on;

                figure;
                semilogx(Time,dTemp,'o',Time,Sstart,Time,Sfit,Tvec,familyvec)
                zoom on;
                xlabel('Time(sec)');
                ylabel('exp,startfit,resultfit,trial curves');
                title(['family vec 2',today,' ',comstr]);
            end

        end
        iterations = iterations + 1;

        allresults(iterations,1) = aveTemp;
        for g=1:npar
            allresults(iterations,(g+1)) = fitresult(g);
        end
        allresults(iterations,g+2) = Chi2_value;
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    end

    if MC == 0
        cd(runfolder)

        textfile = fopen([run_name, '.txt'],'at');
        fprintf(textfile, '%s', [num2str(Voltage), 'V ', num2str(aveTemp), '°C']);
        fprintf(textfile,'\t');

        for e=1:npar
            if any([2 4 6 14 20 21]==Ifitpar(e))
                fprintf(textfile,' %e',fitresult(e));
                fprintf(textfile,'\t');
            else
                fprintf(textfile,' %f',fitresult(e));
                fprintf(textfile,'\t');
            end
        end

        fprintf(textfile, '%f', Chi2_error);

        fprintf(textfile, '\n');
        fclose(textfile);

        %         Header = {'Sample', 'Crucible', 'Temperature', 'Voltage', 'k_start', 'k_end', [Para2, ' start'],[Para2, ' end'],'Chi2 Error'};


        %         if ~exist(ExcelFile,'dir')
        %             writecell(Header,ExcelFile,'Sheet',1);
        %         end

        %         nextLINE = {sample, crucible, aveTemp, Voltage, par_vector(3), fitresult(1), Para2start, fitresult(2), Chi2_error};
        %         writecell(nextLINE,ExcelFile,'Sheet',1,'WriteMode','append');
        disp(['Temperature: ' num2str(fix(aveTemp)) ' ' 'Voltage: ' num2str(Voltage)]);
        cd(currentFOLDER)
    end

    if MC == 1
        % Creates the histogram of values found using MC analysis.

        mcplots = ['MC Plots ', run_name];
        mcplotsfolder = [runfolder '\' mcplots];
        if ~exist(mcplotsfolder, 'dir')
            mkdir(mcplotsfolder);
        end

        for h=1:npar
            one_std(h) = std(fitresult_run(:,h));
            two_std(h) = 2*one_std(h);
            meanfit(h) = mean(fitresult_run(:,h));

            cd(mcplotsfolder)

            figure
            histogram(fitresult_run(:,1),'FaceColor',[0, 0.5, 0]);
            xlabel(parlabel(h));
            ylabel('Quantity');
            title("Monte Carlo Simulation" + " (" + num2str(run) + " Iterations) " + par_names(Ifitpar(h),1)+ " " + sample + " " + num2str(aveTemp) + "°C");

            xline(meanfit(h)+one_std(h),'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation above
            text(meanfit(h)+one_std(h)+.001,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
            xline(meanfit(h)+two_std(h),'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations above
            text(meanfit(h)+two_std(h)+.001,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
            xline(meanfit(h)-one_std(h),'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation below
            text(meanfit(h)-one_std(h)+.001,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
            xline(meanfit(h)-two_std(h),'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations below
            text(meanfit(h)-two_std(h)+.001,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);

            saveas(gcf,['histogram', ' ', convertStringsToChars(par_names(Ifitpar(h),1)), ' ', sample, ' ', num2str(aveTemp), 'C.fig']);
            saveas(gcf,['histogram', ' ', convertStringsToChars(par_names(Ifitpar(h),1)), ' ', sample, ' ', num2str(aveTemp), 'C.png']);

            hold off

            Points = 1:1:MC_iteration_limit;
            standard_deviationk = zeros(MC_iteration_limit,1);
            for N = 1:1:length(fitresult_run(:,1)) %number of points used in standard deviation
                standard_deviation(N,h) = 2*std(fitresult_run(1:N,1));
            end

            figure
            plot(Points,standard_deviation(:,h),'.');
            xlabel('Number of Points');
            ylabel('2 Standard Deviations');
            title(['Convergence for MCM Standard Deviation of ', num2str(sample), ' ', num2str(aveTemp), '°C']);

            saveas(gcf,['stdev convergence', ' ', convertStringsToChars(par_names(Ifitpar(h),1)), ' ', sample, ' ', num2str(aveTemp), 'C.fig']);
            saveas(gcf,['stdev convergence', ' ', convertStringsToChars(par_names(Ifitpar(h),1)), ' ', sample, ' ', num2str(aveTemp), 'C.png']);


        end

        % one_std1 = std(fitresult_brian(:,1));
        % two_std1 = 2*one_std1;
        % mean1 = mean(fitresult_brian(:,1));
        % 
        % one_std2 = std(fitresult_brian(:,2));
        % two_std2 = 2*one_std2;
        % mean2 = mean(fitresult_brian(:,2));
        % 
        % 
        % cd(mcplotsfolder)
        % 
        % figure
        % histogram(fitresult_brian(:,1),'FaceColor',[0, 0.5, 0]);
        % xlabel(Par1_label);
        % ylabel('Quantity');
        % title("Monte Carlo Simulation" + " (" + num2str(brian) + " Iterations) " + par_names(Ifitpar(1),1)+ " " + sample + " " + num2str(aveTemp) + "°C");
        % 
        % xline(mean1+one_std1,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation above
        % text(mean1+one_std1+.001,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean1+two_std1,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations above
        % text(mean1+two_std1+.001,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean1-one_std1,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation below
        % text(mean1-one_std1+.001,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean1-two_std1,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations below
        % text(mean1-two_std1+.001,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % 
        % saveas(gcf,['histogram', sample, ' ', num2str(aveTemp), 'C.fig']);
        % saveas(gcf,['histogram', ' ', par_names(Ifitpar(h)), ' ', sample, ' ', num2str(aveTemp), 'C.png']);
        % 
        % hold off
        % 
        % figure
        % histogram(fitresult_brian(:,2),'FaceColor',[0, 0.5, 0]);
        % xlabel(Par2_label);
        % ylabel('Quantity');
        % title("Monte Carlo Simulation" + " (" + num2str(brian) + " Iterations) " + par_names(Ifitpar(2),1)+ " " + sample + " " + num2str(aveTemp) + "°C");
        % 
        % xline(mean2+one_std2,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation above
        % text(mean2+one_std2,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean2+two_std2,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations above
        % text(mean2+two_std2,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean2-one_std2,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%one standard deviation below
        % text(mean2-one_std2,145,'1\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % xline(mean2-two_std2,'--','color',[0.6350, 0.0780, 0.1840],'LineWidth',2);%two standard deviations below
        % text(mean2-two_std2,145,'2\sigma','FontSize',12,'FontWeight','bold','color',[0.6350, 0.0780, 0.1840]);
        % 
        % saveas(gcf,['histogram_', Para2, '_', sample, ' ', num2str(aveTemp), 'C.fig']);
        % saveas(gcf,['histogram_2_', Para2, ' ', sample, ' ', num2str(aveTemp), 'C.png']);
        % 
        % hold off
        % 
        % 
        % standard_deviationk = zeros(MC_iteration_limit,1);
        % standard_deviation2 = zeros(MC_iteration_limit,1);
        % for N = 1:1:length(fitresult_brian(:,1)) %number of points used in standard deviation
        % 
        %     standard_deviationk(N,1) = 2*std(fitresult_brian(1:N,1));
        %     standard_deviation2(N,1) = 2*std(fitresult_brian(1:N,2));
        % end
        % 
        % figure
        % plot(Points,standard_deviationk,'.');
        % xlabel('Number of Points');
        % ylabel('2 Standard Deviations [W/m-K]');
        % title(['Convergence for MCM Standard Deviation of ', num2str(sample), ' ', num2str(aveTemp), '°C']);
        % 
        % saveas(gcf,['stdev convergence k', sample, ' ', num2str(aveTemp), 'C.fig']);
        % saveas(gcf,['stdev convergence k', sample, ' ', num2str(aveTemp), 'C.png']);
        % 
        % figure
        % plot(Points,standard_deviation2,'.');
        % xlabel('Number of Points');
        % ylabel('2 Standard Deviations [W/m-K]');
        % title(['Convergence for MCM Standard Deviation of ', num2str(sample), ' ', num2str(aveTemp), '°C']);
        % 
        % saveas(gcf,['stdev convergence ', Para2, ' ', sample, ' ', num2str(aveTemp), 'C.fig']);
        % saveas(gcf,['stdev convergence ', Para2, ' ', sample, ' ', num2str(aveTemp), 'C.png']);

        if Full_Analysis == 0

            cd(runfolder)

            textfile = fopen([run_name, ' MC', '.txt'],'at');
            fprintf(textfile, '%s', [num2str(Voltage), 'V ', num2str(aveTemp), '°C']);
            fprintf(textfile,'\t');
            fprintf(textfile, '%f', mean1);
            fprintf(textfile,'\t');
            fprintf(textfile, '%f', two_std1);

            fprintf(textfile,'\t');
            fprintf(textfile, '%s', num2str(mean2));
            fprintf(textfile,'\t');
            fprintf(textfile, '%s', num2str(two_std2));

            fprintf(textfile, '\n');
            fclose(textfile);
        end
        cd(currentFOLDER)
    end

    if Full_Analysis == 1
        totalerror = sqrt(Chi2_error^2 + two_std(1).^2);
        Results(n-2,:) = [aveTemp Voltage fitresult(1) mean(1) Chi2_error two_std(1) totalerror fitresult(2) two_std(2)];
    end
end

if Full_Analysis == 1

    j = 1;
    m = 1;
    ii = 1;
    Temp0 = Results(1,1);
    an = zeros(length(Results(:,1))+1,1);

    while ii < length(Results(:,1)) + 1
        j = 1;
        Tempmin = Temp0-5;
        Tempmax = Temp0+5;
        for n = 1:length(Results(:,1))
            if (Results(n,1) >= Tempmin) && (Results(n,1) <= Tempmax)
                an(n) = 1;
                Temp(j) = Results(n,1);
                k(j) = Results(n,3);
                kMC(j) = Results(n,4);
                u_k(j) = Results(n,7);
                par2(j) = Results(n,8);
                u_par2(j) = Results(n,9);
                j = j+1;
            end
        end
        ave_temp(m) = mean(Temp);
        ave_k(m) = mean(k);
        ave_kMC(m) = mean(kMC);
        ave_par2(m) = mean(par2);
        Uncertaintyk(m) = sqrt(sum(u_k.^2)/length(u_k));
        Uncertainty2(m) = sqrt(sum(u_par2.^2)/length(u_par2));
        m = m+1;
        Temp = [];
        k = [];
        par2 = [];
        kMC = [];
        u_k = [];
        u_par2 = [];
        x = 0;
        while x == 0
            if an(ii) ~= 0
                ii = ii +1;
            elseif ii < length(Results(:,1)) + 1
                Temp0 = Results(ii,1);
                x = 1;
            elseif ii == length(Results(:,1)) + 1
                x = 1;
            end
        end
    end

    T = ave_temp + 273.15;

    cp_FLiNaK = (40.3 + .0439.*T)./.04129;
    cp_KNO3 = 1518*ones(length(ave_temp),1);
    cp_Water = 12010.1471-80.4072879.*T.^1+0.309866854.*T.^2-5.38186884E-4.*T.^3+3.62536437E-7.*T.^4;
    cp_Argon = 525;
    k_Water = -0.869083936+0.00894880345.*T.^1-0.0000158366345.*T.^2+0.00000000797543259.*T.^3;
    k_Argon = 0.0226;
    k_KNO3 = .4303-.000422.*(T-610.15);
    k_FLiNaK = 1.24 - .000538*T;

    cd(runfolder)

    % for i = 1:length(SolveListNames)
    %     len = length(SolveListNames);
    % 
    %     yyaxis left
    %     plot(allresults(:,1),allresults(:,i+1),'o')
    %     ylabel(par_names(Ifitpar(i)));
    % 
    %     % yyaxis right
    %     % plot(allresults(:,1),allresults(:,end),'x')
    %     % ylabel('Chi^2 Value');
    % 
    %     xlabel('Temperature °C');
    %     param = char(SolveListNames(i));
    %     saveas(gcf,[sample, param, 'Solution.fig'])
    %     saveas(gcf,[sample, param, 'Solution.png'])
    % 
    % 
    %     figure
    %     hold on
    %     errorbar(ave_temp,ave_k,Uncertaintyk,'s')
    %     title('Thermal Conductivity')
    %     xlabel('Temperature °C')
    %     ylabel('Conductivity W/m*K')
    %     saveas(gcf,[sample, ' K Results.fig'])
    %     saveas(gcf,[sample, ' K Results.png'])
    %     hold off
    % end


    figure
    hold on
    errorbar(ave_temp,ave_k,Uncertaintyk,'s')
    if strcmp(sample,'Water') && strcmp(Par1_label,'K Sample [W/(m*K)]')
        plot(ave_temp, k_Water)
    elseif strcmp(sample,'FliNaK') && strcmp(Par1_label,'K Sample [W/(m*K)]')
        plot(ave_temp, k_FLiNaK)
    elseif strcmp(sample,'KNO3') && strcmp(Par1_label,'K Sample [W/(m*K)]')
        plot(ave_temp, k_KNO3)
    end
    title('Thermal Conductivity')
    xlabel('Temperature [°C]')
    ylabel('Thermal Conductivity [W/m*K]')
    saveas(gcf,[sample, ' K Results.fig'])
    saveas(gcf,[sample, ' K Results.png'])
    hold off

    %    figure
    %    hold on
    %    errorbar(ave_temp,ave_kMC,Uncertaintyk,'s')
    %    title('Thermal Conductivity by MC')
    %    xlabel('Temperature °C')
    %    ylabel('Conductivity W/m*K')
    %    saveas(gcf,[sample, ' KMC Results.png'])
    %    hold off

    figure
    hold on
    errorbar(ave_temp,ave_par2,Uncertainty2,'s')
    title('Specific Heat')
    if strcmp(sample,'Water') && strcmp(Par2_label,'Cp sample [J/(Kg*K)]')
        plot(ave_temp, cp_Water)
    elseif strcmp(sample,'FliNaK') && strcmp(Par2_label,'Cp sample [J/(Kg*K)]')
        plot(ave_temp, cp_Water)
    elseif strcmp(sample,'KNO3') && strcmp(Par2_label,'Cp sample [J/(Kg*K)]')
        plot(ave_temp, cp_Water)
    end
    xlabel('Temperature [°C]')
    ylabel('Specific Heat [J/(Kg*K)]')
    saveas(gcf,[sample, 'Cp Results.fig'])
    saveas(gcf,[sample, 'Cp Results.png']) %saveas(gcf,[sample, Para2 , 'Results.png'])
    hold off

    ResultsText = fopen([run_name, ' Final Results.txt'],'at');
    for q = 1:length(ave_temp)
        fprintf(ResultsText, '%f', ave_temp(q));
        fprintf(ResultsText,'\t');
        fprintf(ResultsText, '%f', ave_k(q));
        fprintf(ResultsText,'\t');
        fprintf(ResultsText, '%f', Uncertaintyk(q));
        fprintf(ResultsText,'\t');
        fprintf(ResultsText, '%f%%', 100*Uncertaintyk(q)/ave_k(q));
        fprintf(ResultsText,'\t');
        if cp == 0
            fprintf(ResultsText, '%e', ave_par2(q));
            fprintf(ResultsText,'\t');
            fprintf(ResultsText, '%e', Uncertainty2(q));
        else
            fprintf(ResultsText, '%f', ave_par2(q));
            fprintf(ResultsText,'\t');
            fprintf(ResultsText, '%f', Uncertainty2(q));
        end
        fprintf(ResultsText,'\t');
        fprintf(ResultsText, '%f%% \n', 100*Uncertainty2(q)/ave_par2(q));
    end
    fclose(ResultsText);
    cd(currentFOLDER)
end

cd(runfolder)
figure
yyaxis right
plot(allresults(:,1),allresults(:,end),'x')
ylabel('Chi^2 Value');

for i = 1:length(SolveListNames)
    len =length(SolveListNames);

    yyaxis left
    plot(allresults(:,1),allresults(:,i+1),'o')
    ylabel(par_names(Ifitpar(i)));

    % yyaxis right
    % plot(allresults(:,1),allresults(:,end),'x')
    % ylabel('Chi^2 Value');

    xlabel('Temperature °C');
    param = char(SolveListNames(i));
    saveas(gcf,[sample, param, 'Solution.fig'])
    saveas(gcf,[sample, param, 'Solution.png'])
end
    % figure
    % plot(allresults(:,1),allresults(:,3),'o')

toc