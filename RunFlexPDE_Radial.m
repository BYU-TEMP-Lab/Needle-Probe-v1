function [uniqueID,filename] = RunFlexPDE_Radial(par_vector,par_names,SolvNam,endtime)


%%%%%%%% Prepare geometry of model %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

r_tc = 0.094313e-3;  			    % Radius of Thermocouple
TC_loc = 0.05;						% Location of TC Bead w relation to probe tip (5 cm)
r_wires = 0.094313e-3;				% Radius of heating wires
r_wir_o = 0.485942e-3;				% Outside radius of heating wires
r_wir_i = 0.297315e-3;				% Inside radius of heating wires
r_wir_mid = .391629E-3;             % middle of wires
HW_curve = 4.85942e-4;				% Depth of heating wire curve
HW_Ni = 0.002;						% Distance between heating wire tip and inner Ni sheath
r_Al = 0.8293e-3; 					% Alumina Layer (in meters)
r_Ni = 1.388E-3; 					% Nickel Sheath (in meters) 
Ni_curve = 0.001;					% Depth of Ni Sheath curved tip
samp_probe = -0.001;				% Distance between Sample and Probe tip (negative due to it being BELOW probe tip)
%r_samp = 0.00207;					% Sample Radius (in meters)
r_cruc = 0.0127;					% Radius of Crucible (in meters)
h_max = 0.1;						% Height of Probe (m)
h_base = -0.01 + samp_probe;        % Total area below the probe (Bottom Crucible + sample/probe separation)
vol_wires = pi*r_wires^2*(h_max*2) + (pi^2 * r_wires^2 * r_wir_mid);    % Calculating Volume of heating wires
L = h_max - ( r_Ni - r_Al + HW_Ni + HW_curve) + 2*pi*r_wir_mid;         % Length of wires (Total length - spacing)  

% for i=1:length(par_names)
%     if ismember(par_names(i,1), SolvParam)
%         par_vector(i) = 
%     end
% end

%%%%%%%% Assign values using parameter inputs %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

k_Thermocouple = par_vector(1);             % Thermal conductivity of thermocouple
rho_Thermocouple = par_vector(2);           % Density of thermocouple
cp_Thermocouple = par_vector(3);            % Soecific heat of thermocouple

k_wire = par_vector(4);                     % Thermal Conductivity of heating wires
rho_wire = par_vector(5);                   % Density of Heating Wires
cp_wire = par_vector(6);                    % Specific Heat of heating wires

k_Alumina = par_vector(7)*exp((-1.5*(par_vector(21)/100))/(1-(par_vector(21)/100)));     % Thermal Conductivity of Alumina, par_vector(21) is porosity percentage
rho_Alumina = par_vector(8);                      % Density of Alumina (SHOULD ADD POROSITY HERE)
cp_Alumina = par_vector(9);  					 % Specific Heat of Alumina (SHOULD ADD POROSITY)

k_Sheath = par_vector(10);                   % Thermal conductivity of Ni sheath
rho_Sheath = par_vector(11);                 % Density of Ni sheath
cp_Sheath = par_vector(12);                  % Specific Heat of Ni sheath
e_Ni = par_vector(13);						 % Emmissivity of Ni sheath

k_Crucible = par_vector(14);                 % Thermal conductivity of crucible
rho_Crucible = par_vector(15);               % Density of crucible
cp_Crucible = par_vector(16);                % Specific Heat of crucible
e_Crucible = par_vector(17);				 % Emmissivity of Crucible

k_Sample = par_vector(24);                   % Thermal conductivity of sample
if ismember(par_names(27,1), SolvNam)
    rho_cp_Sample = par_vector(27);          % rho*cp of sample 
    rho_Sample = 1;                          
    cp_Sample = rho_cp_Sample/rho_Sample;    % Allows solving for product of rho*cp
else
    rho_Sample = par_vector(25);             % Density of sample
    cp_Sample = par_vector(26);              % Specific Heat of sample
end
scatter = par_vector(18);                    % Coefficient of scatter in sample

h_conv = par_vector(19); 					 % Convective heat transfer coefficient (W/m^2K)
q_gen_wire = par_vector(20)/vol_wires;       % Volumetric heat generation in wires (W/m^3)
rTh_alumina_sheath = par_vector(22);		 % Thermal contact resistance between alumina and sheath
rTh_sheath_sample = par_vector(23);		 % Thermal contact resistance between alumina and sheath
T_amb = par_vector(28);						 % Ambient temperature (K)

r_samp = par_vector(29);                     % Sample Radius (in meters)

% Lumped heating wire properties
k_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*k_Alumina + (3.4381e-11 + L*5.5889e-9)*k_wire) / (4.119e-10 + L*8.1652e-8);
rho_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*rho_Alumina + (3.4381e-11 + L*5.5889e-9)*rho_wire) / (4.119e-10 + L*8.1652e-8);
cp_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*cp_Alumina + (3.4381e-11 + L*5.5889e-9)*cp_wire) / (4.119e-10 + L*8.1652e-8);
qgen_Heating_wires = ((3.4381e-11 + L*5.5889e-9)*q_gen_wire) / (4.119e-10 + L*8.1652e-8);


%%%%%%%% Write FlexPDE file %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Define a random filename for current iteration
uniqueID = num2str(randi([1000, 9999])); % Generate a unique identifier
filename = ['Flex_' uniqueID '.pde'];

% Open the file for writing
fileID = fopen(filename, 'w');

% Write content to the file
fprintf(fileID, 'TITLE ''Needle Probe Radial X-Section (non-lumped properties)''\n');
fprintf(fileID, 'COORDINATES YCYLINDER("R","Z")\n\n');

fprintf(fileID, 'VARIABLES\n');
fprintf(fileID, 'temp\n\n');

fprintf(fileID, 'DEFINITIONS\n');
fprintf(fileID, 'time_end = %8.4f\n',endtime);
fprintf(fileID, 't_step = .001\n');
fprintf(fileID, 'T_amb = %8.4f\n',T_amb);
fprintf(fileID, 'k\n');
fprintf(fileID, 'rho\n');
fprintf(fileID, 'cp\n');
fprintf(fileID, 'q_gen  = 0\n\n');

fprintf(fileID, 'temp_r2 = EVAL(temp,%8.4f,0)\n', r_Ni);
fprintf(fileID, 'temp_r3 = EVAL(temp,%8.4f,0)\n', r_samp);
%CHECK THIS LINE WITH JAKE
fprintf(fileID, 'q_rad = (5.67e-8*((temp)^4 - temp_r3^4)/(1/%8.4f + (1-%8.4f)/%8.4f * %8.4f/%8.4f))\n\n', e_Ni, e_Crucible, e_Crucible, r_Ni, r_samp);

fprintf(fileID, 'MATERIALS\n');
fprintf(fileID, '"Crucible" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f\n', k_Crucible, rho_Crucible, cp_Crucible);
fprintf(fileID, '"Sample" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f\n', k_Sample, rho_Sample, cp_Sample);
fprintf(fileID, '"Sheath" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f\n', k_Sheath, rho_Sheath, cp_Sheath);
fprintf(fileID, '"Alumina" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f\n', k_Alumina, rho_Alumina, cp_Alumina);
fprintf(fileID, '"Heating_wires" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f \t\tq_gen=%8.4f\n', k_Heating_wires, rho_Heating_wires, cp_Heating_wires, qgen_Heating_wires);
fprintf(fileID, '"Thermocouple" : \tk=%8.4f \trho=%8.4f \tcp=%8.4f\n\n', k_Thermocouple, rho_Thermocouple, cp_Thermocouple);

fprintf(fileID, 'INITIAL VALUES\n');
fprintf(fileID, 'temp = T_amb\n\n');

fprintf(fileID, 'EQUATIONS\n');
fprintf(fileID, 'temp: \tdiv(k*grad(temp)) + q_gen = (rho*cp)*dt(temp)\n\n');

fprintf(fileID, 'BOUNDARIES\n\n');

fprintf(fileID, 'REGION 1\n');
fprintf(fileID, 'USE MATERIAL "Crucible"\n');
fprintf(fileID, 'START (0, %8.4f)\n', h_base);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_cruc, h_base);
fprintf(fileID, 'natural(temp) = %8.4f*(T_amb - temp)\n', h_conv);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_cruc, h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (0, %8.4f)\n', h_max);
fprintf(fileID, 'LINE to CLOSE\n\n');

fprintf(fileID, 'REGION 2\n');
fprintf(fileID, 'USE MATERIAL "Sample"\n');
fprintf(fileID, 'START(0, %8.4f)\n', samp_probe);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_samp, samp_probe);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_samp, h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (0, %8.4f)\n', h_max);
fprintf(fileID, 'LINE to CLOSE\n\n');

fprintf(fileID, 'REGION 3\n');
fprintf(fileID, 'USE MATERIAL "Sheath"\n');
fprintf(fileID, 'START(0, 0)\n');
fprintf(fileID, 'natural(temp) = q_rad\n');
fprintf(fileID, 'Contact(temp) = (1/%8.8f) * JUMP(temp)\n', rTh_sheath_sample);
fprintf(fileID, 'ARC (center = 0, %8.4f) to (%8.4f, %8.4f)\n', Ni_curve, r_Ni, Ni_curve);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_Ni, h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_Al, h_max);
fprintf(fileID, 'NOBC(temp)\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_Al, Ni_curve);
fprintf(fileID, 'ARC (center = 0, %8.4f) to (0, %8.4f)\n', Ni_curve, (r_Ni-r_Al));
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to CLOSE\n\n');

fprintf(fileID, 'REGION 4\n');
fprintf(fileID, 'USE MATERIAL "Alumina"\n');
fprintf(fileID, 'START(0, %8.4f)\n', r_Ni - r_Al);
fprintf(fileID, 'Contact(temp) = (1/%8.8f) * JUMP(temp)\n', rTh_alumina_sheath);
fprintf(fileID, 'ARC (center = 0, %8.4f) to (%8.4f, %8.4f)\n', Ni_curve, r_Al, Ni_curve);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_Al, h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (0, %8.4f)\n', h_max);
fprintf(fileID, 'LINE to CLOSE\n\n');

fprintf(fileID, 'REGION 5\n');
fprintf(fileID, 'USE MATERIAL "Heating_wires"\n');
fprintf(fileID, 'START(0, %8.4f)\n', r_Ni - r_Al + HW_Ni);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (0, %8.4f)\n', r_Ni - r_Al + HW_Ni + r_wires * 2);
fprintf(fileID, 'NOBC(temp)\n');
fprintf(fileID, 'ARC (center = 0, %8.4f) to (%8.4f, %8.4f)\n', r_Ni - r_Al + HW_Ni + HW_curve, r_wir_i, r_Ni - r_Al + HW_Ni + HW_curve);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_wir_i, h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_wir_o, h_max);
fprintf(fileID, 'NOBC(temp)\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_wir_o, r_Ni - r_Al + HW_Ni + HW_curve);
fprintf(fileID, 'ARC (center = 0, %8.4f) to CLOSE\n\n', r_Ni - r_Al + HW_Ni + HW_curve);

fprintf(fileID, 'REGION 6\n');
fprintf(fileID, 'USE MATERIAL "Thermocouple"\n');
fprintf(fileID, 'START(0, %8.4f)\n', h_max);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_tc, h_max);
fprintf(fileID, 'LINE to (%8.4f, %8.4f)\n', r_tc, TC_loc);
fprintf(fileID, 'ARC (center = 0, %8.4f) to (0, %8.4f)\n', TC_loc, TC_loc - 0.001);
fprintf(fileID, 'natural(temp) = 0\n');
fprintf(fileID, 'LINE to CLOSE\n\n');

fprintf(fileID, 'TIME\n');
fprintf(fileID, '0 BY t_step TO time_end\n\n');

fprintf(fileID, 'HISTORIES\n');
fprintf(fileID, 'History(Temp) AT (0.0, 0.05) export format "#t#r,#i" file="temp.txt"\n\n');

fprintf(fileID, 'END\n');

% Close the file
fclose(fileID);


%%%%%%%% Run FlexPDE file and return the temp vs time list %%%%%%%%%%%%%%%%

% Specify the full path to the FlexPDE7 executable
flexPDEPath = 'C:\Program Files\FlexPDE7\FlexPDE7.exe'; % Update this path

% Construct the command string using the full path and filename

%sfilename = ['Flex_' uniqueID];
%command = fprintf('flexpde7 -param h_max=100 %s', filename);
%command = sprintf('"%s" /r -param TC_loc=0 -param h_max=100 "%s"', flexPDEPath, filename);
command = sprintf('"%s" "%s" /r -S', flexPDEPath, filename);

% Run the command
system(command);

% Runs the program
% https://www.pdesolutions.com/help/runningflexpdefromthecommandli.html
pause(0.1) %Wait for program to run to see results 



end