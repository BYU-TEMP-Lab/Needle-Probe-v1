function [plotfolder, datafolderUSE, aveTemp_vector] = ExtractData(run_name,raw_plot,runfolder,timewindow)

currentfolder = pwd;
starttime = timewindow(1);%set to 0 to start at the beginning. Make sure values are a multiple of the sampling period. 
timesend = timewindow(2); % Comment

% PUT RAW DATA INTO USABLE FORMAT
prompt = 'Select a raw data folder ';
m = 1;
while m == 1
    disp(prompt);
    datafolder = uigetdir;
    if datafolder == 0
        datafolder = 'd';
    end

    if ~exist(datafolder, 'dir')
        disp('404d. Folder not found.')
        image404 = imread("404d.jpg");
        imshow(image404)
        return
    else
        m = 0;
    end
end


plot = [run_name ' Plots'];
plotfolder = [runfolder '\' plot];
if ~exist(plotfolder, 'dir')
    mkdir(plotfolder);
end

rawplotfolder = [plotfolder '\raw data'];
if ~exist(rawplotfolder, 'dir')
    mkdir(rawplotfolder);
end


use =  [run_name ' Useable Data'];
datafolderUSE = [runfolder '\' use];

i = 1;
while i ~= 0
    if ~exist(datafolderUSE, 'dir')
        mkdir(datafolderUSE);
        i = 0;
    else
        datafolderUSE = [runfolder '\' use num2str(i)];
        i = i+1;
    end
end

% Retrieve the name of the files only
cd(datafolder);
names = dir();
cd(runfolder);

aveTemp_vector = 1:numel(names)-2;
for n = 3:numel(names)

    [~, filename] = fileparts(names(n).name);


    %[x, y, aveTemp] = GraphData(filename, plotfolder, datafolder, currentfolder);
    cd(datafolder);
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

    %Determines if voltage has been applied to the wire and uses this to
    % establish time=0 and T=0
    if N(2) >= 3
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

        %aveTemp = mean(temp(1:(Vcheck-1)));
        %Change to how many temperatures before the power is applied to
        %average
        aveTemp = mean(temp(1:(Vcheck-2))); %Original: aveTemp = mean(temp((Vcheck-3):(Vcheck-1))); I noticed a spike when the voltage was applied, this averages everything up to just before the spike
        temp = temp - aveTemp;
        time = time(Vcheck:end); 
        time = time - time(1) + dt; %inverse laplace can't handle t = 0, so we need to get rid of the first datapoint.
        temp = temp(Vcheck:end);
        Voltage = Voltage((Vcheck-1):(end-1)); % Adjusted from "Voltage(Vcheck:end)" b/c voltage data is 1 ms behind temp data
        if N(2) >= 4
            Current = Current(Vcheck:end);
        end
    else
        aveTemp = mean(temp(1:3));
        temp = temp - aveTemp;
        temp = temp(2:end); %inverse laplace can't handle t = 0, so we need to get rid of the first datapoint.
        time = time(2:end);
    end

    if raw_plot == 1
        figure
        semilogx(time,temp,'o');
        xlabel('Time (s)');
        ylabel('Temperature (°C)');
        f = gcf;
        [~, name, ~] = fileparts(filename);
        cd (rawplotfolder);
        name1 = [name '.png'];
        saveas(f,name1);
        name1 = [name '.fig'];
        saveas(f,name1);
        close
    end

    cd (currentfolder);

    aveTemp_vector(n-2) = aveTemp;
    if starttime == 0
        time_start_index = 1;
    else
        time_start_index = find(time>=starttime,1);
    end
    time_cutoff_index = find(time>=timesend,1);
    cd(datafolderUSE);
    fid = fopen([filename '.txt'],'wt');
    for j=time_start_index:time_cutoff_index
        fprintf(fid,'%f ',time(j));
        fprintf(fid,'\t');
        fprintf(fid,'%f ',temp(j));
        if N(2) >= 3
            fprintf(fid,'\t');
            fprintf(fid,'%f ',Voltage(j));
        end
        if N(2) >= 4
            fprintf(fid,'\t');
            fprintf(fid,'%f ',Current(j));
        end
        fprintf(fid,'\n');

    end
    fclose(fid);
    cd(currentfolder);

end
end