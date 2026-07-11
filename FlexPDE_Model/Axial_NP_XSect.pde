{ 

 
This model is the Axial Model of the Needle Probe/Crucible Set-up. 
It takes an axial slice (disk) at the 5cm height of the sensing region of the probe. It extends from the TC
bead center (0,0) to the outside of the crucible in terms of its radius.. This slice is specifically at the bead
of the TC and therefore it does not have any chromel/alumel thermocouple difference, only the small circle
in the center.

It is important to note that although we are modeling Z-axis symmetric values, the model is not perfecly axially
symetric about the z-axis. The Radial corss section model shows us such. This model therefore is limited in its
scope but allows a great view of the heat flux/flow in the radial direction.

Its geometries use only variables so that an interface with MatLab is easily accomplished and can be modified
for sensitivity analyses and other testing procedures. 


Non-Exact Modeling Portions:
- 

To Fix:
- 

}


TITLE 'Needle Probe Axial x-Section (non-lumped properties)'     { the problem identification }

COORDINATES cartesian2  { 2D Coordinantes (x,y) }

VARIABLES        { system variables }
	temp              { finding temperature in experiment }
  
DEFINITIONS 
{Geometry Parameters}
r_tc = 0.1e-3 !0.094313e-3                                ! Radius of Thermocouple
TC_loc = 0.05													  ! Location of TC Bead w relation to probe tip (5 cm)
r_wires = 0.094313e-3									  ! Radius of heating wires
r_wir_o = 0.485942e-3									  ! Outside radius of heating wires
r_wir_i = 0.297315e-3										  ! Inside radius of heating wires
HW_curve = 4.85942e-4									  ! Depth of heating wire curve
HW_Ni = 0.002												  ! Distance between heating wire tip and inner Ni sheath
r_Al = 0.8293e-3 												  ! Alumina Layer (in meters)
r_Ni = 1.388E-3 												  ! Nickel Sheath (in meters) 
Ni_curve = 0.001											  ! Depth of Ni Sheath curved tip
samp_probe = -0.001										  ! Distance between Sample and Probe tip (negative due to it being BELOW probe tip)
r_samp = 0.00207											  ! Sample Radius (in meters)
r_cruc = 0.0127												  ! Radius of Crucible (in meters)
h_max = 0.1													  ! Heigh of Probe (m)
h_base = -0.01 + samp_probe                          ! Total area below the probe (Bottom Crucible + sample/probe separation)

{Materials defined in each region}
k														  				  ! Thermal conductivity of argon (W/mK)
rho													      			  ! Density of each layer (kg/m^3)
cp														  			  ! Specific heat of each layer (J/kgK)

{ Heating Wire q_gen Calculation Calculations }
phi = 7.38/100													  ! Porosity of cracked alumina
V = 4.346                                                             ! Voltage going through heating wires
I = 0.9428                                                            ! Current going through heating wires
vol_wires = pi*r_wires^2*(h_max*2)       		  ! Calculating Volume of heating wires
L = h_max - ( r_Ni - r_Al + HW_Ni + HW_curve)  ! Length of wires (Total length - spacing)       
k_wire=17.5704                                        	 	 ! Thermal Conductivity of heating wires
rho_wire=8670                                  				 ! Density of Heating Wires
cp_wire=427.07                           					 ! Specific Heat of heating wires
q_gen_wire = V*I/vol_wires                 			 ! Heat Generation of WIres

{ Alumina Thermo Properties Calculations }
k_Al = 35.8168*exp((-1.5*phi)/(1-phi))         	 ! Thermal Conductivity of Alumina
rho_Al=3900                                                	 ! Density of Alumina (SHOULD ADD POROSITY HERE)
cp_Al=804.8495   											 ! Specific Heat of Alumina (SHOULD ADD POROSITY)

{ General Heat transfer properties }
q_gen  = 0     													  ! Heat generation rate in the innermost cylinder (W/m^3)
h_conv = 10 													  ! Convective heat transfer coefficient (W/m^2K)
T_amb = 273+020											  ! Ambient temperature (K)
sigma = 5.67e-8												  ! Stefan-Boltzmann constant
e_Ni = 0.35														  ! Emmissivity of Nickel
e_SS = 0.38													  ! Emmissivity of Stainless Steel
rTh_sample_crucible = 1e-3							  ! Thermal contact resistance between sample and crucible
rTh_sheath_sample = 1e-3  							  ! Thermal contact resistance between dample and sheath
rTh_alumina_sheath = 0.0001						  ! Thermal contact resistance between alumina and sheath
rTh_wires_alumina = 0.0001 							  ! Thermal contact resistance between alumina and wires

{ Lumped Probe Properties }
k_probe =  32.0966
cp_probe =  784.4098
rho_probe =  3.8998e+03
qgen_probe =  1.9648e+08

{ Equations for finding the lumped properties }
! k_probe = (frac_sheath*k_sheath + frac_alumina*k_alumina + frac_wires*k_wires + frac_TC*k_TC)
! cp_probe = (frac_sheath*cp_sheath + frac_alumina*cp_alumina + frac_wires*cp_wires + frac_TC*cp_TC)
! rho_probe = (frac_sheath*rho_sheath + frac_alumina*rho_alumina + frac_wires*rho_wires + frac_TC*rho_TC)

{ Lumped Heating Wire Properties Calculation }
k_lump = ((2.0595e-10 + L*4.0826e-8)*k_Al + (3.4381e-11 + L*5.5889e-9)*k_wire) / (4.119e-10 + L*8.1652e-8)
rho_lump = ((2.0595e-10 + L*4.0826e-8)*rho_Al + (3.4381e-11 + L*5.5889e-9)*rho_wire) / (4.119e-10 + L*8.1652e-8)
cp_lump = ((2.0595e-10 + L*4.0826e-8)*cp_Al + (3.4381e-11 + L*5.5889e-9)*cp_wire) / (4.119e-10 + L*8.1652e-8)
qgen_lump = ((3.4381e-11 + L*5.5889e-9)*q_gen_wire) / (4.119e-10 + L*8.1652e-8)

{Radiation}
temp_r2 = EVAL(temp,r_Ni,TC_loc)
temp_r3 = EVAL(temp,r_samp,TC_loc)
q_rad = (sigma*(temp_r2^4 - temp_r3^4)/(1/e_Ni + (1-e_SS)/e_SS * r_Ni/r_samp))

{Time-related parameters}
time_end = 10 									   		  ! Simulation end time (seconds)
t_step = 0.1													  ! Time step (seconds)

{System modifiers}
!mesh_spacing = 0.5

{ Give Spec. Materials Spec. Variables }
MATERIALS!          Thermal Cond.    Density             Specific Heat            Q-Generation if applicable
	"Crucible" : 				k=13.3007 	rho=7977 			cp=474.5
    "Sample" : 				k=0.6 			rho=992.47 			cp=4176.6																! Water
    "Sheath" : 				k=69.5763 	rho=8882.8 			cp=449.7494
    "Alumina" : 				k=k_Al 		rho=rho_Al 			cp=cp_Al
	"Heating_wires" :	k=k_lump	rho=rho_lump		cp=cp_lump	  		q_gen = qgen_lump
    "Thermocouple" : 	k=22.576 	rho=8640 			cp=450
    "Probe": 					k=k_probe 	rho=rho_probe 	cp=cp_probe			q_gen=qgen_probe

{ Set initial temp: T_amb in definitions }
INITIAL VALUES
	temp = T_amb	

{ Heat Eqt with a Source (q_gen) }
EQUATIONS
temp:	div(k*grad(temp)) + q_gen = (rho*cp)*dt(temp)
  


{Defining the geometry}
BOUNDARIES 

  { Crucible Region }
  REGION 1
  USE MATERIAL "Crucible"
  !mesh_spacing = 1
    START (r_cruc,0) 
    	natural(temp) = h_conv*(T_amb - temp)   { Set flux to be the diffusion/convection equation }
    ARC (center = 0,0) ANGLE=360 TO CLOSE
 
  { Sample Region }
  REGION 2
  USE MATERIAL "Sample"
    START(0,r_samp)
    ARC (center = 0,0) ANGLE=360 TO CLOSE
 
  { Sheath Region }
  REGION 3
  USE MATERIAL "Sheath"
    START(0,r_Ni) 
  		natural(temp) = q_rad
    ARC (center = 0,0) ANGLE=360 TO CLOSE

  { Alumina Region }
  REGION 4   
  USE MATERIAL "Alumina"
  	START(0,r_Al)
  		Contact(temp) = (1/rTh_alumina_sheath) * JUMP(temp)
    ARC (center = 0,0) ANGLE=360 TO CLOSE


  { Heating Wire Region 1 (right) }
  REGION 5  
  USE MATERIAL "Heating_wires"
  	START(r_wir_i + r_wires, r_wires) 
  		Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)
  	ARC (center = (r_wir_i + r_wires),0) ANGLE = 360 TO CLOSE

  { Heating Wire Region 2 (left) }
  REGION 6
  USE MATERIAL "Heating_wires"
  	START(-(r_wir_i + r_wires), r_wires) 
  		Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)
  	ARC (center = -(r_wir_i + r_wires),0) ANGLE=360 TO CLOSE

  { TC Region }
  REGION 7       
  USE MATERIAL "Thermocouple"
  	START(r_tc,0) !0.094313e-3,0) 
  		Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)	! Should change for alumel
  	ARC (center = 0,0) ANGLE=360 TO CLOSE

    
    
{ Set the time bounds for plots monitors histories, etc. values are variables but this helps FlexPDE know }
TIME
0 BY t_step TO time_end 


!MONITORS 
! No needed Monitors at this time

PLOTS
	FOR t = 0 BY t_step TO time_end

	{ Creating the Heat Flux Field: See zoom names for details on zoom }
    vector(-K*dx(temp), -K*dy(temp)) as "Overall Heat Flux Field"
	vector(-K*dx(temp),-K*dy(temp)) zoom(-0.00207,-0.00207,0.00414,0.00414) as "Heat Flow Zoomed"
    
	{ Countour maps of heat: See zoom names for details on zoom }
    CONTOUR(temp) as "Contour Temp"	
    contour(temp) zoom(-0.00207,-0.00207,0.00414,0.00414) as "Countour Temp Zoomed"
 
 	{ Shows temperature profile at 0.05 cm (at TC Bead) from 0 (TC) into crucible (but not all the way) }
    elevation(temp) from (0,0.0) to (0.0025,0.0) as "Temp Profile"


HISTORIES
	{ History of Temps at the following points:
    a. TC
    b. Middle of HW
    c. Middle(ish) of Sample }
    History(Temp) AT (0.0, 0.0) (0.391629e-3, 0.0) (0.0017,0.0) as "Temp w/ time (therm, HW, Samp)" export format "#t#r,#i"

END
