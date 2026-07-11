{ 

This is the bare minimum section of the FlexPDE and matlab interfacing code. Above this line will be an ajoined file which contains
the information of the single run. Below this is the code which will always be repeated. Hence the bare minimum. MatLab will do
all of the calculations so flexPDE time is minimized.

}


TITLE 'Needle Probe Radial X-Section (non-lumped properties)'

COORDINATES YCYLINDER("R","Z") {Rotational Axis "y"}

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
h_max = 0.1													  ! Height of Testing Region of Probe (m)
h_cruc = 0.135
length = h_cruc - h_max 													  ! Length above heating wire
h_base = -0.01 + samp_probe                          ! Total area below the probe (Bottom Crucible + sample/probe separation)

{Materials defined in each region}
k														  				  ! Thermal conductivity of argon (W/mK)
rho													      			  ! Density of each layer (kg/m^3)
cp														  			  ! Specific heat of each layer (J/kgK)

{ Heating Wire q_gen Calculation Calculations }
phi =0/100													  	! Porosity of cracked alumina
V = 4.351542	                                                    ! Voltage going through heating wires
I = 0.87532                                                          ! Current going through heating wires
vol_wires = pi*r_wires^2*(h_max*2)       		  	! Calculating Volume of heating wires
L = h_max - ( r_Ni - r_Al + HW_Ni + HW_curve) ! Length of wires (Total length - spacing)       
k_wire=17.5704                                        	 	 	! Thermal Conductivity of heating wires
rho_wire=8670                                  				 	! Density of Heating Wires
cp_wire=427.07                           					 	! Specific Heat of heating wires
q_gen_wire = (V*I)/vol_wires                 			 	! Heat Generation of WIres
ramp_width = 0.0001

{ Alumina Thermo Properties Calculations }
k_Al = 35.8168*exp((-1.5*phi)/(1-phi))         	 	! Thermal Conductivity of Alumina
rho_Al=3900                                                	 	! Density of Alumina (SHOULD ADD POROSITY HERE)
cp_Al=804.8495   											 	! Specific Heat of Alumina (SHOULD ADD POROSITY)

{ General Heat transfer properties }
q_gen  = 0     													  ! Heat generation rate in the innermost cylinder (W/m^3)
h_conv = 10 													  ! Convective heat transfer coefficient (W/m^2K)
T_amb = 273+020											  ! Ambient temperature (K)
sigma = 5.67e-8												  ! Stefan-Boltzmann constant
e_Ni = 0.35														  ! Emmissivity of Nickel
e_SS = 0.38													  ! Emmissivity of Stainless Steel
rTh_sample_crucible = 1e-3							  ! Thermal contact resistance between sample and crucible
rTh_sheath_sample = 1e-3  							  ! Thermal contact resistance between dample and sheath
rTh_alumina_sheath = 0.001						  ! Thermal contact resistance between alumina and sheath
rTh_wires_alumina = 0.0052 							  ! Thermal contact resistance between alumina and wires

{ Lumped Probe Properties }
k_probe =  32.0966											! Calculated outside of flexPDE for simplicity sake (see below equations)
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
time_end = 100 									   		  ! Simulation end time (seconds)
t_step = .1													  ! Time step (seconds)

{Heat flux calculations} ! Multiply by 2 since we're only looking at half a probe
top_flux = 2*SURF_INTEGRAL((-k*dz(temp)), 'Top Surface')
bottom_flux = 2*SURF_INTEGRAL((k*dz(temp)), 'Bottom Surface')
cylindrical_flux = 2*SURF_INTEGRAL((-k*dr(temp)), 'Cylindrical Surface')

top_flux_all = 2*SURF_INTEGRAL((-k*dz(temp)), 'Top Surface All')
bottom_flux_all = 2*SURF_INTEGRAL((k*dz(temp)), 'Bottom Surface All')
cylindrical_flux_all = 2*SURF_INTEGRAL((-k*dr(temp)), 'Cylindrical Surface All')

AreaTopBottom = 2*SURF_INTEGRAL(1, 'Top Surface')
AreaTopBottomAll = 2*SURF_INTEGRAL(1, 'Top Surface All')
AreaCylinder = 2*SURF_INTEGRAL(1, 'Cylindrical Surface')
AreaCylinderAll = 2*SURF_INTEGRAL(1, 'Cylindrical Surface All')
AreaTotal = 2*SURF_INTEGRAL(1, 6)


total_flux = 2*SURF_INTEGRAL(normal(-k*grad(temp)),6)


{System modifiers}
!mesh_spacing = 0.5

{ Give Spec. Materials Spec. Variables }
MATERIALS!          Thermal Cond.    Density             Specific Heat            Q-Generation if applicable
	"Crucible" : 				k=13.3007 	rho=7977 			cp=474.5
    "Sample" : 				k=0.606 	rho=997 				cp=4184			! Water  20C
    "Atmosphere":			k=0.0262 	rho=1.77 				cp=525			! Argon
    "Sheath" : 				k=69.5763 	rho=8882.8 			cp=449.7494
    "Alumina" : 				k=k_Al 		rho=rho_Al 			cp=cp_Al
	"Heating_wires" :	k=k_lump	rho=rho_lump		cp=cp_lump	  		!q_gen = qgen_lump
    "Heating_wires_non" :	k=k_lump	rho=rho_lump		cp=cp_lump	  	
    "Thermocouple" : 	k=22.576 	rho=8640 			cp=450
    "Probe": 					k=k_probe 	rho=rho_probe 	cp=cp_probe			q_gen=qgen_probe



!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!                 											Below this is all of the Geometry File                                                                                    !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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
  USE MATERIAL "Crucible"							{ Makes a big rectanlge to fill entire system }
  	!mesh_spacing = 50									! Adjust mesh THIS DOES NOT WORK, TRY TO CHANGE FOR EFFICIENCY
    START (0, h_base)                           			{ Bottom Left }
    	value(temp) = T_amb  									! Set bottom of Crucible to constant temp 
        LINE to (r_cruc, h_base) 						{ Extends crucible from bottom left to bottom right }
        natural(temp) = h_conv*(T_amb - temp)  ! Set outer crucible boundary flux to dif./conv. equation 
        LINE to (r_cruc, h_cruc) 							{ Bottom right to top right }
        natural(temp) = h_conv*(T_amb - temp)  ! Set top crucible boundary flux to dif./conv. equation
        LINE to (0, h_cruc)     								{ Top right to top left }
        natural(temp) = 0										! Set inner surface to 0 Flux
        LINE to CLOSE     								 	{ Close Geometry with a line from top left to bottom left }
 
  { Atmosphere Above Sample Region }
  REGION 2
  USE MATERIAL "Atmosphere"							{ Makes a rectangular atmosphere which is inserted into crucible region }
    START(0, samp_probe) 							{ Sets bottom left of rectangle at variabled distance below probe tip }
        LINE to (r_samp, samp_probe)			{ Bottom Left to Bottom Right }
        LINE to (r_samp, h_cruc) 					{ Bottom Right to Top Right }
        natural(temp) = h_conv*(T_amb - temp)  ! Set Top  convection boundary
        LINE to (0, h_cruc)  							{ Top Right to Top Left }
        natural(temp) = 0									! Inner Flux to Zero
        LINE to CLOSE 									{ Close Geo with a line from Top Left to Bottom Left }
 
  { Sample Region }
  REGION 3
  USE MATERIAL "Sample"							{ Makes a rectangular sample which is inserted into crucible region }
    START(0, samp_probe) 							{ Sets bottom left of rectangle at variabled distance below probe tip }
        LINE to (r_samp, samp_probe)			{ Bottom Left to Bottom Right }
        LINE to (r_samp, h_max) 					{ Bottom Right to Top Right }
        LINE to (0, h_max)  							{ Top Right to Top Left }
        natural(temp) = 0									! Set Inner Flux to Zero
        LINE to CLOSE 									{ Close Geo with a line from Top Left to Bottom Left }


  { Sheath Shell Region }
  REGION 4
  USE MATERIAL "Sheath"									{ Forms 2D slice of sheath: bottom left going CCW }
    START(0, 0)      												{ Origin center as bottom left of probe}
        natural(temp) = q_rad									! Set Probe/Sample interfacing surfaces to have radiating flux
        !Contact(temp) = (1/rTh_sheath_sample) * JUMP(temp)
        ARC (center = 0,Ni_curve) to (r_Ni, Ni_curve)	{ Bottom Arc to reach outer straight of Probe }
        LINE to (r_Ni, h_cruc)									{ Sets Right Straight-Up Portion of Probe }
        natural(temp) = 0											! Set Top flux to zero
        LINE to (r_Al, h_cruc)  								{ Top Right to Top left of top surface }
        NOBC(temp)												! Leave undefined flux on inner surface of probe
        LINE to (r_Al, Ni_curve) 		        				{ Inner straight-down bound of Sheath }
        ARC (center = 0,Ni_curve) to (0, r_Ni - r_Al)		{ Inner sheath arc (thickness of sheath = (r_Ni - r_Al) }
        natural(temp) = 0                							! Inner 0 bound flux to zero
  		LINE to CLOSE											{ Close Geometry by connecting the arcs on the left zero border }

  { Alumina Region }
  REGION 5  
  USE MATERIAL "Alumina"									{ Creates Alumina inside to Ni sheath }
  	START(0, r_Ni - r_Al)                                           { Start Bottom left right above the inner sheath }
        Contact(temp) = (1/rTh_alumina_sheath) * JUMP(temp)	! Add thermal contact res. between Al and Ni
    	ARC (center = 0,Ni_curve) to (r_Al, Ni_curve)	{ Curves around bottom curve of inner sheath }
        LINE to (r_Al, h_cruc)        								{ Fixes far right bound of Al }
        natural(temp) = 0												! Set top and left bounds to zero flux
        LINE to (0, h_cruc)   										{ Top bound }
        LINE to CLOSE  												{ Close Geometry with a line from top left to bottom left }
  
  { Heating Wire Heating Region }
  REGION 6  
  USE MATERIAL "Heating_wires"											{ Forms 2D slice of HWs: Bottom left going CW }
    q_gen = qgen_lump*URAMP( -z+h_max, -z+(h_max-ramp_width) )		{ Cuts off heat generation at 10cm height }
    !q_gen = swage((z-h_max),qgen_lump ,0,ramp_width)	
  	START(0, r_Ni - r_Al + HW_Ni ) 			  								{ Bottom Left (Sheath thickness + HW/Ni Dist.) }
        natural(temp) = 0																! Set the left zero bound to zero flux
    	LINE to (0, r_Ni - r_Al + HW_Ni + r_wires*2)					{ Inner left zero bound of wire }
        NOBC(temp)																	! Reset BC for inner HW 
    	!Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)	! Add Contact Res. between HW and Al
        																						{ Inner arc of Heating wire }
        ARC (center = 0, r_Ni - r_Al + HW_Ni + HW_curve) to (r_wir_i, r_Ni - r_Al + HW_Ni + HW_curve)
        LINE to (r_wir_i, h_cruc)	 												{ Inner staight up bound of HW }
        natural(temp) = 0																! Set top bounds to 0 flux
        LINE to (r_wir_o, h_cruc)												{ Line Top Left to Top Right on HW top bounds }
        NOBC(temp)																	! Reset BC for inner HW     
        !Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)	! Add Contact Res. between HW and Al
		LINE to (r_wir_o, r_Ni - r_Al + HW_Ni + HW_curve)		{ Outer straight-down bound of HW }
        ARC (center = 0,  r_Ni - r_Al + HW_Ni + HW_curve) to CLOSE { Close Geo by using final arc to bot. Left }
        
  { Thermocouple Region }
  REGION 7       
  USE MATERIAL "Thermocouple"											{ Forms TC by rect. with arc bottom to create bead }
  	START(0, h_cruc) 																{ Start at the top left bound }
    	natural(temp) = 0																! Set top BC of TC to zero
    	LINE to (r_tc, h_cruc)														{ Top Left to Top Right }
        NOBC(temp)																	! Reset BC for outer TC
  		!Contact(temp) = (1/rTh_wires_alumina) * JUMP(temp)	! Cont Res. between TC and Al. FIX TO BE WITH CHROMEL
        LINE to (r_tc, TC_loc)														{ Outer straight-down bound of TC }
        ARC (center = 0, TC_loc)  to (0, TC_loc - 0.001)       		{ Arc to inner zero bound (TC Bead formation) }
        natural(temp) = 0																! Set inner zero-bound of TC to zero flux
        LINE to CLOSE																{ Close Geo by far left inner closing bot. left to top left }
  		
! Box enclosing heater portion
  FEATURE "Top Surface"
  	START(0, h_max+ramp_width) LINE to (r_wir_o, h_max+ramp_width)
    
  FEATURE "Bottom Surface"
  	START(0, r_Ni - r_Al + HW_Ni )  LINE to (r_wir_o, r_Ni - r_Al + HW_Ni )
    
 FEATURE "Cylindrical Surface"
  	START(r_wir_o, h_max+ramp_width)  LINE to (r_wir_o,  r_Ni - r_Al + HW_Ni )
    
    
!Surfaces enclosing heater portion, extending to end of everything
 
 FEATURE "Top Surface All"
  	START(r_cruc, h_max+ramp_width) LINE to (0, h_max+ramp_width)
    
  FEATURE "Bottom Surface All"
  	START(0, r_Ni - r_Al + HW_Ni )  LINE to (r_cruc, r_Ni - r_Al + HW_Ni )
    
 FEATURE "Cylindrical Surface All"
  	START(r_wir_o, h_cruc)  LINE to (r_wir_o, 0.001 )


{ Set the time bounds for plots monitors histories, etc. values are variables but this helps FlexPDE know }
TIME
0 BY t_step TO time_end 


!MONITORS 

! No needed Monitors at this time

PLOTS
	FOR t = 0 BY t_step TO time_end
	
    { Creating the Heat Flux Field: See zoom names for details on zoom }
    !vector(-K*dr(Temp), -K*dz(temp)) as "Overall Heat Flux Field"
	!vector(-K*dr(Temp), -K*dz(temp))  zoom(0.0,-0.001, 0.021,0.02) as "Heat Flux Probe Tip" 
	!vector(-K*dr(Temp), -K*dz(temp))  zoom(0.0,0.045, 0.0023,0.06) as "Heat Flux Sensing Region"
    vector(-K*dr(Temp), -K*dz(temp))  zoom(0.0, 0.0, .003, h_cruc) as "Heat Flux Total Probe"
	
    { Countour maps of heat: See zoom names for details on zoom }
    !CONTOUR(temp) as "Contour Temp"	
    !contour(Temp) zoom(0.0,-0.001, 0.021,0.02) as "Countour Temp Probe Tip"
	!contour(Temp) zoom(0.0,0.045, 0.0023,0.06) as "Countour Temp Sensing Region"
    contour(Temp) zoom(0.0, 0.0, .003, h_cruc) as "Countour Temp Total Probe"
    
    { Shows temperature profile at 0.05 cm (at TC Bead) from 0 (TC) into crucible (but not all the way) }
    elevation(Temp) from (0,0.05) to (0.0025,0.05) as "Temp Profile"
    
    elevation(-k*dr(Temp)) on "Cylindrical Surface" as "Flux Rad Profile"
    elevation(-k*dz(Temp)) on "Top Surface" as "Flux Top Ax Profile"
    elevation(-k*dz(Temp)) on "Bottom Surface" as "Flux Bottom Ax Profile"
    
    elevation(-k*dr(Temp)) on "Cylindrical Surface All" as "Flux Rad Profile All"
    elevation(-k*dz(Temp)) on "Top Surface All" as "Flux Top Ax Profile All"
    elevation(-k*dz(Temp)) on "Bottom Surface All" as "Flux Bottom Ax Profile All"
    
    
   {elevation(top_flux) as "Top Flux Over Time"
   elevation(bottom_flux) as "Bottom Flux Over Time"
   elevation(cylindrical_flux) as "Cylindrical Flux Over Time"
}

!REPORT(SURF_INTEGRAL(normal(-k*grad(temp)), "Cylindrical Surface")) AS "Cylindrical Heat Flux"



HISTORIES
   
   history(top_flux) as "Top Heat Flux (W)" export format "#t#r,#i" file="TopFlux.txt"  
   history(bottom_flux) as "Bottom Heat Flux (W)" export format "#t#r,#i" file="BottomFlux.txt"  
   history(cylindrical_flux) as "Cylindrical Heat Rate (W)" export format "#t#r,#i" file="Water_CylindricalFlux.txt"  
   history((cylindrical_flux_all/AreaCylinderAll)/((top_flux_all+bottom_flux_all)/AreaTopBottomAll)) as "Ratio Radial to Axial Flux (W/mK)" export format "#t#r,#i" file="Water_Radial_to_Axial_Flux.txt"  
   
   history(-k*dr(Temp)) at (r_Ni, TC_loc) as "Heat Flux at TC-Outer Probe, radial (W/mK)" export format "#t#r,#i" file="TC-ProbeFluxRad.txt"  
   history(-k*dz(Temp)) at (r_tc, TC_loc+0.00) as "Heat Flux at 0-TC, axial (W/mK)" export format "#t#r,#i" file="0-TCFluxAx.txt"  
   history((top_flux_all+bottom_flux_all)/AreaTopBottomAll) as "Avg Heat Flux, axial (W/mK)" export format "#t#r,#i" file="AvgFluxAx.txt"
   
   !history(bottom_flux/AreaTopBottom) as "Bottom Avg Heat Flux (W)" export format "#t#r,#i" file="TC-ProbeAvgFluxAx.txt"
   !history(-k*dz(Temp)) at (r_Ni, TC_loc) as "Heat Flux at TC-Outer Probe, axial (W/mK)" export format "#t#r,#i" file="TC-ProbeluxAx.txt"  
   
   history(-k*dr(Temp)) at (r_wir_o, TC_loc) as "Heat Flux at TC-Outer HW, radial (W/mK)" export format "#t#r,#i" file="TC-HWFluxRad.txt"  
   history(cylindrical_flux/AreaCylinder) as "Avg Heat Flux, radial (W/mK)" export format "#t#r,#i" file="AvgFluxRad.txt"  
   history(cylindrical_flux_all/AreaCylinderAll) as "Avg Heat Flux All, radial (W/mK)" export format "#t#r,#i" file="AvgFluxRadAll.txt"  
   
   
   !history(bottom_flux_all/AreaTopBottomAll) as "Bottom Avg Heat Flux (W)" export format "#t#r,#i" file="TC-ProbeAvgFluxAx.txt"
   !history(-k*dz(Temp)) at (r_wir_o, TC_loc) as "Heat Flux at TC-Outer HW, axial (W/mK)" export format "#t#r,#i" file="TC-HWFluxAx.txt"
   
   history(total_flux) as "Total Flux" export format "#t#r,#i" file="TotalFlux.txt"  

	{ History of Temps at the following points:
    a. TC
    b. Middle of HW
    c. Middle(ish) of Sample }
    History(Temp) AT (0.0, 0.05) export format "#t#r,#i" file="temp.txt"  

END
