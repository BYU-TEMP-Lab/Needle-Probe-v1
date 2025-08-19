function [uniqueID,filename] = RunFlexPDE_StraightFile(par_vector,par_names,SolvNam,endtime)


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
r_samp = 0.00207;					% Sample Radius (in meters)
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

% Lumped heating wire properties
k_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*k_Alumina + (3.4381e-11 + L*5.5889e-9)*k_wire) / (4.119e-10 + L*8.1652e-8);
rho_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*rho_Alumina + (3.4381e-11 + L*5.5889e-9)*rho_wire) / (4.119e-10 + L*8.1652e-8);
cp_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*cp_Alumina + (3.4381e-11 + L*5.5889e-9)*cp_wire) / (4.119e-10 + L*8.1652e-8);
qgen_Heating_wires = ((3.4381e-11 + L*5.5889e-9)*q_gen_wire) / (4.119e-10 + L*8.1652e-8);


%%%%%%%% Run FlexPDE file and return the temp vs time list %%%%%%%%%%%%%%%%

% Specify the full path to the FlexPDE7 executable
flexPDEPath = 'C:\Program Files\FlexPDE7\FlexPDE7.exe'; % Update this path

% Construct the command string using the full path and filename

command = sprintf('%s -param TC_loc=0 -param rho_Al=%  Final_Axial_XSect-copy', flexPDEPath, k_Alumina);

% Run the command
system(command);

% Runs the program
% https://www.pdesolutions.com/help/runningflexpdefromthecommandli.html
pause(0.1) %Wait for program to run to see results 



end