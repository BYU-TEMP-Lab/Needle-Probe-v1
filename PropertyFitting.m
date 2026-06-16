clc
clear
close all

%Options for Speed and other utilities%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
on = 1;
off = 0;

global_fitting = off; % Uses fminsearch when off

MC = on; %Turns on Monte Carlo error analysis.

raw_plot = off; %Create plots of the raw data. Keep off to increase speed.
iplotfit = off; %Shows the plot during the fitting process. Keep off to increase speed.
manual_delay = off; %Adds in a manual delay that helps to see the fitting process. Significantly increases runtime.
chi2plots = on; %show plots from the chi2 error analysis

MC_iterations = 250; %The numbers of iterations to run as part of the Monte Carlo Analysis
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

iterations = 0;

if MC == 1
    MC_iteration_limit = MC_iterations;
else
    MC_iteration_limit = 0;
end

currentFOLDER = pwd;
today = char(datetime('now','Format','MM,dd,yy,HH-mm'));

m=menu('Probe Calibration or Sample Test?',...
    'Probe Calibration', ...
    'Sample Test', ...
    'end');

%Sets the time interval to be analyzed, in seconds. Set beginning to 0 to start from the beginning
if m == 1
    timewindow = [0 5]; % early and short to capture probe properties
elseif m == 2
    timewindow = [0.5 15]; % late and long to capture sample properties, ***could be adjusted based on sensitivity analysis***
else
    disp('No selection, program terminated')
    return
end

m=menu('Probe:',...
    '2A-SS-03', ...
    '2A-SS-04', ...
    '3A-IN718-01', ...
    'INL',...
    'end');

if m == 1
    probe = '2A-SS-03';
elseif m == 2
    probe = '2A-SS-04';
elseif m == 3
    probe = '3A-IN718-01';
elseif m == 4
    probe = 'INL';
else
    disp('No probe selected, program terminated')
    return
end

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
    'MgNaCl',...
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
elseif m == 17
    sample = 'MgNaCl';
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
    run_name = [sample ' ' probe ' ' crucible ' ' today '_fmincon'];
else
    run_name = [sample ' ' probe ' ' crucible ' ' today '_global'];
end

runfolder = [currentFOLDER '\Analysis_Results\' run_name];
if ~exist(runfolder, 'dir')
    mkdir(runfolder);
end 

[plotfolder, datafolderUSE, aveTemp_vector, chiplotfolder] = ExtractData(raw_plot,runfolder,timewindow);

tic

datafolder = datafolderUSE;
cd(datafolder);
names = dir();
cd(currentFOLDER);

Results = zeros(numel(names)-2, 9);

% this is running just to create the par_names to put a header on the output text file
[~, par_names] = Properties(probe,crucible,sample,25,5,0.00225,0.1,0.00225,MC);

cd(runfolder)
textfile = fopen([run_name, '.txt'],'at');
fprintf(textfile, '%s\t', 'Voltage (V)');
fprintf(textfile, '%s\t', 'Temp (°C)');
for p=1:length(SolveList)
    fprintf(textfile, '%s', [par_names(str2double(SolveListNames(p)),1),' (',par_names(str2double(SolveListNames(p)),2),')']);
    fprintf(textfile, '\t');
end
fprintf(textfile, '%s', 'Chi2 Error');
fprintf(textfile, '\n');

MCruninfo = fopen([run_name, ' MC_runinfo.txt'],'at');
fprintf(MCruninfo, '%s\t', 'Run');
fprintf(MCruninfo, '%s\t', 'Voltage(V)');
fprintf(MCruninfo, '%s\t', 'Temp(°C)');
for p=1:length(SolveList)
    fprintf(MCruninfo, '%s', [par_names(str2double(SolveListNames(p)),1),'(',par_names(str2double(SolveListNames(p)),2),')']);
    fprintf(MCruninfo, '\t');
end
for p=1:length(par_names)
    fprintf(MCruninfo, '%s', [par_names(p,1),'(',par_names(p,2),')']);
    fprintf(MCruninfo, '\t');
end
fprintf(MCruninfo, '\n');

cd(currentFOLDER)

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

    for run = 1:MC_iteration_limit+1
        
        if run == 1
            MC = 0;
        else
            MC = 1;
        end

        [par_vector, par_names] = Properties(probe,crucible,sample,aveTemp,Voltage,VoltageSTD,Current,CurrentSTD,MC);

        n0=length(par_vector);			%total number of parameters
        ipar=1;			%fit parameter index for error test
        ntest=20;		%number of error analysis values

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        Ifitpar = SolveList;

        npar = size(Ifitpar,2);
        parstart = zeros(npar,1);

        for b = 1:npar
            parstart(b) = par_vector(Ifitpar(b));
            parlabel(b) = par_names(Ifitpar(b),1) + ' [' + par_names(Ifitpar(b),2) + ']';
        end

        fitresult_run = zeros(MC_iteration_limit,npar);

        a=ones(1,n0);
        a(Ifitpar)=0;
        Ifixpar=find(a);	%fix parameter index array
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if global_fitting == 0
            %%%%%%% fmincon fitting
            Sstart=NeedleProbeModel(Time,par_vector,IV);
            close all;

            foptions=optimset('TolFun', 1e-6, 'TolX', 1e-6, 'MaxIter', 1e4,'MaxFunEvals',1e4);

            % 1. Initial guess
            x0 = par_vector(Ifitpar);

            % 2. Create an anonymous function to pass all your extra variables to 'Chi2'.
            %    MATLAB will optimize the variable 'x', while treating everything else as a constant.
            objFun = @(x) Chi2(x, par_vector(Ifixpar), Ifitpar, Ifixpar, Sstart, signal, manual_delay, iplotfit, IV);

            % 3. Define bounds
            lb =  x0.*0;
            ub =  Inf(size(lb));

            % 3.5 Define specific bounds for certain properties
            for i = 1:length(SolveList)
                if SolveList(i) == 1 || SolveList(i) == 2 % k eff wires and alpha eff wires
                    % larger bounds for uncertainty in lumped properties,
                    % +_50% of initial guess
                    lb(i) = x0(i)*0.5;
                    ub(i) = x0(i)*1.5;
                end
                if SolveList(i) == 5 % thermal contact resistance
                    % set on range of 0 - 1, since initial guess is 0
                    lb(i) = 0;
                    ub(i) = 1;
                end
                if SolveList(i) == 3 || SolveList(i) == 4 ||...
                SolveList(i) == 6 || SolveList(i) == 7 ||...
                SolveList(i) == 10 || SolveList(i) == 11
                % k sheath, alpha sheath, k crucible, alpha crucible, k insulation, alpha insulation
                    % smaller bounds for uncertainty in material properties
                    % (for 2A probes, insulation is actually lumped Alumina
                    % and Ceramabond and should use larger bounds)
                    lb(i) = x0(i)*0.9;
                    ub(i) = x0(i)*1.1;
                end
                if SolveList(i) == 12 || SolveList(i) == 13 % probe and crucible emissivity
                    % larger bounds on emissivity because of uncertainty
                    % regarding impact of molten salt on exposed surfaces
                    lb(i) = x0(i)*0.5;
                    ub(i) = x0(i)*1.5;
                end
                if SolveList(i) == 19 || SolveList(i) == 20 || SolveList(i) == 21 || SolveList(i) == 22 || SolveList(i) == 23 % radii
                    % smaller bounds on geometry due to measurement
                    % uncertainty from X-Rays and CT scans
                    lb(i) = x0(i)*0.9;
                    ub(i) = x0(i)*1.1;
                end
                if SolveList(i) == 30 % flux decay factor
                    % range of 0 - 0.001 because initial guess is 0
                    lb(i) = 0;
                    ub(i) = 0.001;
                end
            end

            % 4. Call fmincon using strict positional arguments:
            %    fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon, options)
            [fitresult, Chi2_value] = fmincon(objFun, x0, [], [], [], [], lb, ub, [], foptions);

            clear Chi2

        elseif global_fitting == 1
            % Initialize starting parameters and options
            Sstart = NeedleProbeModel(Time, par_vector, IV); % Model initialization
            close all;
            
            foptions = optimset('MaxIter', 1e9, 'MaxFunEvals', 3e16, 'Display', 'iter'); % Optimization options
            
            % Define the Chi2 function as an anonymous function for optimization
            chi2_func = @(fit_params) Chi2(fit_params, par_vector(Ifixpar), Ifitpar, Ifixpar, Sstart, signal, manual_delay, iplotfit, IV);
            
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
        Sfit=NeedleProbeModel(Time,param,IV);

        if run == 1
            figure(Visible='off');
            semilogx(Time,dTemp-Sfit,'o',Time,Sstart-Sfit,'o');
            zoom on;
            xlabel('Time(sec)');
            ylabel('▲T (Kelvin)');
            legend('Data - Solved Model','Initial Model - Solved Model', 'Location', 'northwest')
            title(['Residuals: ', num2str(Voltage),'V ', num2str(aveTemp), '°C ' ,today]);

            f = gcf;
            drawnow;
            name1 = [sample '_' crucible '_' num2str(aveTemp) '°C_' num2str(Voltage) 'V_residues' '.png'];
            fullPath = fullfile(plotfolder, name1);
            exportgraphics(f, fullPath);
            close(f)

            figure(Visible='off');
            semilogx(Time,dTemp,'o', Time,Sstart, Time,Sfit);
            zoom on;
            xlabel('Time(sec)');
            ylabel('▲T (Kelvin)');
            legend('Exp. Data', 'Initial Model', 'Solved Model', 'Location', 'northwest')
            run_name_string = strrep(run_name, '_', ' ');
            title(['Solution: ', run_name_string, ' ', num2str(fix(aveTemp)), '°C ', num2str(Voltage), 'V']);

            f = gcf;
            drawnow;
            name1 = [sample '_' crucible '_' num2str(aveTemp) '°C_' num2str(Voltage) 'V_result_fit' '.png'];
            fullPath = fullfile(plotfolder, name1);
            exportgraphics(f, fullPath);
            close(f)

        end

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

        if run ~= 1
            cd(runfolder)
    
            MCruninfo = fopen([run_name, ' MC_runinfo.txt'],'at');
            fprintf(MCruninfo, '%s\t', num2str(run-1));
            fprintf(MCruninfo, '%s\t', num2str(aveTemp));
            fprintf(MCruninfo, '%s\t', num2str(Voltage));
            for d=1:npar
                if any([2 4 6 14 20 21]==Ifitpar(d))
                    fprintf(MCruninfo,' %e',fitresult(d));
                    fprintf(MCruninfo,'\t');
                else
                    fprintf(MCruninfo,' %f',fitresult(d));
                    fprintf(MCruninfo,'\t');
                end
            end
            fprintf(MCruninfo, '%g\t', par_vector);
            fprintf(MCruninfo, '\n');
            fclose(MCruninfo);
    
            cd(currentFOLDER)
        end
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if run == 1
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
                chitestvec(ii)=[Chi2(fitresulttest,par_vector(Ifixpar),Ifitpar,Ifixpar,Sstart,signal,manual_delay,iplotfit,IV)];
            end
            clear Chi2

            Tvec=Time*ones(1,ntest);

            for ii=1:ntest
                partest=parvec(ii);
                param(Ifitpar(ipar))=partest; %variable fitting parameters
                familyresult = NeedleProbeModel(Time,param,IV);
                familyvec(:,ii)=familyresult;
            end

            % 1. Define the shifted LINEX equation
            linexEquation = 'a*(exp(b*(x-x0)) - b*(x-x0) - 1) + c';
            myFitType = fittype(linexEquation, 'independent', 'x', 'dependent', 'y');
            
            % 2. Generate smart starting points to ensure the fit converges
            [minChi2, minIdx] = min(chitestvec);
            x0_guess = parvec(minIdx);
            c_guess = max(minChi2, 1e-6); % Force guess to be positive
            
            % Use your existing polyfit to guess the initial LINEX shape parameters
            P = polyfit(parvec, chitestvec, 2);
            quad_a = max(P(1), 1e-6); % Force quadratic curvature guess to be positive
            b_guess = -1; % Start with a moderate asymmetry assumption
            a_guess = (2 * quad_a) / (b_guess^2); % Map quadratic curvature to LINEX 'a'
            
            % CRITICAL FIX: Add 'Lower' bounds so 'a' and 'c' cannot mathematically go negative
            options = fitoptions('Method', 'NonlinearLeastSquares', ...
                                 'StartPoint', [a_guess, b_guess, c_guess, x0_guess], ...
                                 'Lower', [1e-8, -Inf, 0, -Inf]); % a > 0, c >= 0
            
            % 3. Fit the LINEX curve
            [curve, goodness] = fit(parvec, chitestvec, myFitType, options);
            
            % 4. Extract fitted parameters
            a_fit = curve.a;
            b_fit = curve.b;
            x0_fit = curve.x0;
            c_fit = curve.c;
            
            % 5. Define the target Delta Chi^2 
            delta_chi2 = c_fit / ndata;
            
            % 6. Create an anonymous function to find where LINEX equals the target delta
            rootFunc = @(dx) a_fit*(exp(b_fit*dx) - b_fit*dx - 1) - delta_chi2;
            
            % 7. Use fzero to find the asymmetric bounds
            % CRITICAL FIX: Added abs() to guarantee a real number for fzero
            dx_guess = sqrt(abs(2 * delta_chi2 / (a_fit * b_fit^2)));
            
            % Find left and right bounds (shifts from the minimum)
            % By starting exactly at +/- dx_guess, fzero will find the roots cleanly
            dx_left = fzero(rootFunc, -dx_guess);
            dx_right = fzero(rootFunc, dx_guess);
            
            % 8. Final Asymmetric Errors
            Chi2_error_minus = abs(dx_left);
            Chi2_error_plus = abs(dx_right);

            % 9. GUM-Compliant Expanded Uncertainty Calculation
            % Map the LINEX asymmetric errors to the GUM bounds
            b_plus = Chi2_error_plus;
            b_minus = Chi2_error_minus;
            
            % Set n_chi2 (using the number of data points fitted)
            n_chi2 = ndata; 
            
            % Calculate the combined standard uncertainty of the mean (Type B rectangular)
            % GUM 4.3.7, 4.3.8, and 4.2.3
            u_c = (b_plus + b_minus) / sqrt(12 * n_chi2);
            
            % Calculate Expanded Uncertainty (95% confidence level, k = 1.96)
            % GUM 6.2.2 and Annex G.1.3
            U_expanded = 1.96 * u_c;
            Chi2_error = U_expanded;
            
            % 10. Final Reporting Statement (GUM 7.2.2)
            % Extract the optimal parameter value from the fit (the minimum of the curve)
            nominal_value = x0_fit;
                        
            % Optional: You can evaluate the curve for plotting just like before
            parabool = curve(parvec); % Though it's now a 'linexbool' rather than a parabola!

            if chi2plots == 1
                figure(Visible="off");
                comstr=['par. ',int2str(ipar),' varies between ',num2str(parmin),' and ',num2str(parmax)];

                semilogx(Time,familyvec);
                zoom on;
                xlabel('Time(sec)');
                ylabel('▲T (Kelvin)');
                title(['familyvec over Tvec',today,' ',comstr]);

                f = gcf;
                drawnow;
                name1 = [num2str(aveTemp),'°C_',num2str(Voltage),'V_Chi2_plot_1.png'];
                fullPath = fullfile(chiplotfolder, name1);
                exportgraphics(f, fullPath);
                close(f)

                figure(Visible="off");
                plot(parvec,chitestvec,'o',parvec,parabool);
                chisave=[parvec,chitestvec,parabool];
                title([run_name,' par(',int2str(ipar),'): ',num2str(fitresult(ipar)),') file: ',fn]);
                zoom on;

                f = gcf;
                drawnow;
                name1 = [num2str(aveTemp),'°C_',num2str(Voltage),'V_Chi2_plot_2.png'];
                fullPath = fullfile(chiplotfolder, name1);
                exportgraphics(f, fullPath);
                close(f)

                figure(Visible="off");
                semilogx(Time,dTemp,'o',Time,Sstart,Time,Sfit,Tvec,familyvec)
                zoom on;
                xlabel('Time(sec)');
                ylabel('exp,startfit,resultfit,trial curves');
                title(['family vec 2 ',today,' ',comstr]);

                f = gcf;
                drawnow;
                name1 = [num2str(aveTemp),'°C_',num2str(Voltage),'V_Chi2_plot_3.png'];
                fullPath = fullfile(chiplotfolder, name1);
                exportgraphics(f, fullPath);
                close(f)
            end

        end
        if run == 1
            iterations = iterations + 1;
    
            allresults(iterations,1) = aveTemp;
            for g=1:npar
                allresults(iterations,(g+1)) = fitresult(g);
            end
            allresults(iterations,g+2) = Chi2_value;
        end 
       %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

        if run == 1
            cd(runfolder)
            textfile = fopen([run_name, '.txt'],'at');
            fprintf(textfile, '%f\t%f\t',Voltage, aveTemp);
    
            for e=1:npar
                if any([2 4 6 14 20 21]==Ifitpar(e))
                    fprintf(textfile,' %e',fitresult(e));
                    fprintf(textfile,'\t');
                else
                    fprintf(textfile,' %f',fitresult(e));
                    fprintf(textfile,'\t');
                end
            end
    
            fprintf(textfile, '%.7f', Chi2_error);
    
            fprintf(textfile, '\n');
            fclose(textfile);
    
            disp(['Temperature: ' num2str(fix(aveTemp)) ' ' 'Voltage: ' num2str(Voltage)]);
            cd(currentFOLDER)
        end
    
    end

end

cd(runfolder)
figure('Visible','off');
yyaxis right
plot(allresults(:,1),allresults(:,end),'x')
ylabel('Chi^2 Value');

for i = 1:length(SolveListNames)
    len =length(SolveListNames);

    yyaxis left
    plot(allresults(:,1),allresults(:,i+1),'o')
    ylabel(par_names(Ifitpar(i)));

    xlabel('Temperature °C');
    param = char(SolveListNames(i));
    saveas(gcf,[sample, param, 'Solution.fig'])
    saveas(gcf,[sample, param, 'Solution.png'])
end

toc