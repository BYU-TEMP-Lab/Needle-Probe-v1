function [par_vector,par_names] = Properties(crucible,sample,Temp,avgQ,MC)

if Temp < 20
    Temp = 20.01;
end

T=Temp;%+273.15;
%MC = 0;


%Probe Properties and Geometry%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Geometry%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Relevant radii
r_TC = .094313E-3; % radius of thermocouple
r_wires = .094313E-3; % radius of heating wires
r_wir_i = .297315E-3; % inside radius up to wires %Not needed right now, but may be needed later
r_wir_mid = .391629E-3; % middle of wires %Not needed right now, but may be needed later
r_wir_o = .485942E-3; % outside of wires
r_sheath_i = 0.8293E-3; % inside radius of sheath
r_sheath_o = 1.388E-3; % outside radius of the probe

% Lengths
L_probe = 0.1; % Length of the probe
L_cyl_wire = L_probe-0.01; % Length of heating wires (not including ends)
L_cyl_probe = L_probe-r_sheath_o;

% Volume of wire
V_wire_end = (pi^2 * r_wires^2 * r_wir_mid);
V_wire_cyl = 2*pi * r_wires^2*L_cyl_wire;
V_wire = V_wire_end + V_wire_cyl;

% Volume of thermocouple
V_TC = 2*pi*r_TC^2 * 0.05;

% Volume of alumina
V_alumina_end = 2/3 * pi * r_sheath_i^3;
V_alumina_cyl = pi*r_sheath_i^2*L_cyl_probe;
V_alumina = V_alumina_end + V_alumina_cyl - V_wire - V_TC;

% Volume of sheath
V_sheath_end = 2/3 * pi * r_sheath_o^3;
V_sheath_cyl = pi*r_sheath_i^2*L_cyl_probe;
V_sheath = V_sheath_end + V_sheath_cyl - V_alumina - V_wire - V_TC;

V_total = V_TC + V_wire + V_alumina + V_sheath; % Total volume

% Fractions of each volume
frac_TC = V_TC/V_total;
frac_wires = V_wire/V_total;
frac_alumina = V_alumina/V_total;
frac_sheath = V_sheath/V_total;


%Probe Materials%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%NICKEL 200: VALID UP TO 1273K (1000C)%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Thermal Conductivity- Nickel
if T >= 173 && T < 673
    k_Ni = 76.12158+0.02717507*T^1-2.126458E-4*T^2+1.876168E-7*T^3;
elseif T >= 673 && T <= 1273
    k_Ni = 40.623+0.02201643*T^1-3.571429E-7*T^2;
end

%Density- Nickel %Not needed right now, but may be needed later
rho_Ni = 8964.214-0.1681755*T^1-3.536041E-4*T^2+2.01714E-7*T^3-4.919056E-11*T^4; % 73 to 1373 K

%Heat Capacity- Nickel %Not needed right now, but may be needed later
if T >= 293 && T < 633
     cp_Ni = 292.88+0.50208*T^1;
elseif T >= 633 && T < 1726
     cp_Ni = 418.4+0.1284488*T^1;
end

% Thermal Diffusivity- Nickel
if T >= 293 && T < 633
    alpha_Ni = 3.044717E-5-5.149323E-8*T^1+3.129624E-11*T^2;
elseif T >= 633 && T < 676
    alpha_Ni = 4.81462E-5-1.036816E-7*T^1+7.54384E-11*T^2;
elseif T >= 676 && T <= 1273
    alpha_Ni = 1.087891E-5+2.600264E-9*T^1-2.279477E-13*T^2;
end

%ALUMINA: VALID UP TO 873K (600C)%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Thermal Conductivity- Alumina
if T >= 293 && T < 298
    k_Alumina = 37.1754;
elseif T >= 298 && T < 300
    k_Alumina = ((36.9601-37.1754)/(300-298))*(T-298)+37.1754;
elseif T >= 300 && T < 373
    k_Alumina = ((30.2503-36.9601)/(373-300))*(T-300)+36.9601;
elseif T >= 373 && T < 400
    k_Alumina = ((27.209-30.2503)/(400-373))*(T-373)+30.2503;
elseif T >= 400 && T < 473
    k_Alumina = ((22.5099-27.209)/(473-400))*(T-400)+27.209;
elseif T >= 473 && T < 500
    k_Alumina = ((20.93-22.5099)/(500-473))*(T-473)+22.5099;
elseif T >= 500 && T < 600
    k_Alumina = ((16.3045-20.93)/(600-500))*(T-500)+20.93;
elseif T >= 600 && T < 673
    k_Alumina = ((13.1378-16.3045)/(673-600))*(T-600)+16.3045;
elseif T >= 673 && T < 700
    k_Alumina = ((12.558-13.1378)/(700-673))*(T-673)+13.1378;
elseif T >= 700 && T < 873
    k_Alumina = ((9.1211-12.558)/(873-700))*(T-700)+12.558;
elseif T >= 873
    k_Alumina = ((9.1211-12.558)/(873-700))*(T-700)+12.558; %because I don't know what it would be. placeholder for now
end


% Porous Alumina
porosity_Al = 0;%7.38;
phi = porosity_Al/100;   % Volume fraction of voids (modelling cracked insulation), 7.38 correction from old files
k_Alumina = k_Alumina*exp((-1.5*phi)/(1-phi));  % (Z. Zivcoca et al, 2009)

% Density- Alumina
rho_Alumina = 3900;

% Heat Capacity- Alumina
if T >= 293 && T < 298
    cp_Alumina = 782.218;
elseif T >= 298 && T < 300
    cp_Alumina = ((785.025-782.218)/(300-298))*(T-298)+782.218;
elseif T >= 300 && T < 373
    cp_Alumina = ((901.3683-785.025)/(373-300))*(T-300)+785.025;
elseif T >= 373 && T < 400
    cp_Alumina = ((942.03-901.3683)/(400-373))*(T-373)+901.3683;
elseif T >= 400 && T < 473
    cp_Alumina = ((1016.802-942.03)/(473-400))*(T-400)+942.03;
elseif T >= 473 && T < 500
    cp_Alumina = ((1046.7-1016.802)/(500-473))*(T-473)+1016.802;
elseif T >= 500 && T < 600
    cp_Alumina = ((1109.502-1046.7)/(600-500))*(T-500)+1046.7;
elseif T >= 600 && T < 673
    cp_Alumina = ((1148.873-1109.502)/(673-600))*(T-600)+1109.502;
elseif T >= 673 && T < 700
    cp_Alumina = ((1151.37-1148.873)/(700-673))*(T-673)+1148.873;
elseif T >= 700 && T < 873
    cp_Alumina = ((1214.92-1151.37)/(873-700))*(T-700)+1151.37;
elseif T >= 873
    cp_Alumina = ((1214.92-1151.37)/(873-700))*(T-700)+1151.37; %because I don't know what it would be. placeholder for now
end

% Thermal Diffusivity- Alumina
alpha_Alumina = k_Alumina/(rho_Alumina*cp_Alumina);

%ALUMEL: VALID UP TO 450K (177C) (ASSUMPTIONS ALLOW USAGE BEYOND 450K)%%%%%
%Thermal Conductivity- Alumel Not needed right now, but may be needed
%later
if T>= 100 && T < 400
    k_Alumel = 9.346236+0.1204046*T^1-2.33021E-4*T^2+1.774554E-7*T^3;
elseif T >= 400 && T < 773
    k_Alumel = 39.91124-0.08021887*T^1+1.89707E-4*T^2-1.037644E-7*T^3;
elseif T >= 773
    k_Alumel = 39.91124-0.08021887*T^1+1.89707E-4*T^2-1.037644E-7*T^3; %out of COMSOL'S RANGE
end

% % Heat Capacity- Alumel Not needed right now, but may be needed later
if T >=100 && T < 410
    cp_Alumel = -120.397194+4.83234846*T^1-0.0141451249*T^2+0.0000151245324*T^3;
elseif T >=410 && T < 450
    cp_Alumel = 4215.99923-16.6533325*T^1+0.018666665*T^2;
elseif T >= 450
    cp_Alumel = 4215.99923-16.6533325*(T)^1+0.018666665*(T)^2; %out of COMSOL'S RANGE
end

% Thermal Diffusivity- Alumel
if T >= 100 && T < 175
    alpha_Alumel = 2.777243E-5-3.26281E-7*T^1+1.773714E-9*T^2-3.253333E-12*T^3;
elseif T >=175 && T < 422
    alpha_Alumel = 9.912174E-6-2.568489E-8*T^1+8.732857E-11*T^2-1.005653E-13*T^3;
elseif T >=422 && T < 450
    alpha_Alumel = -0.00007507129+0.0000003614333*T^1-0.0000000003952381*T^2;
elseif T >= 450
    alpha_Alumel = -0.00007507129+0.0000003614333*(T)^1-0.0000000003952381*(T)^2; %out of COMSOL'S RANGE
end

% Density- Alumel
rho_Alumel = 8600; %Not needed right now, but may be needed later

%CHROMEL: VALID UP TO 450K (177C) (ASSUMPTIONS ALLOW USAGE BEYOND 450K)%%%%
%Thermal Conductivity- Chromel Not needed right now, but may be needed
%later
if T >= 100 && T < 450
    k_Chromel = 13.1709-0.02474581*T^1+2.79175E-4*T^2-6.862022E-7*T^3+6.09438E-10*T^4; %100 to 450 K
elseif T >= 450
    k_Chromel = 13.1709-0.02474581*(T)^1+2.79175E-4*(T)^2-6.862022E-7*(T)^3+6.09438E-10*(T)^4; %out of COMSOL'S RANGE
end

% Heat Capacity- Chromel- Not needed right now, but may be later
if T >= 100 && T < 450
    cp_Chromel = -169.134351+5.88577506*T^1-0.0235877058*T^2+0.0000447834022*T^3-0.0000000321153924*T^4;
elseif T >= 450
    cp_Chromel = -169.134351+5.88577506*(T)^1-0.0235877058*(T)^2+0.0000447834022*(T)^3-0.0000000321153924*(T)^4; %out of COMSOL'S RANGE
end


% Thermal Diffusivity- Chromel
if T >= 100 && T < 175
    alpha_Chromel = 3.466E-5-6.301667E-7*T^1+5.119333E-9*T^2-1.893333E-11*T^3+2.666667E-14*T^4;
elseif T >= 175 && T < 450
    alpha_Chromel = 6.607453E-6-1.986064E-8*T^1+6.038939E-11*T^2-5.155141E-14*T^3;
elseif T >= 450
    alpha_Chromel = 6.607453E-6-1.986064E-8*(T)^1+6.038939E-11*(T)^2-5.155141E-14*(T)^3; %out of COMSOL'S RANGE
end

% Density- Chromel
rho_Chromel = 8670; %Not needed right now, but may be later

% Wire Properties:
k_wire = k_Chromel;
rho_wire = rho_Chromel;
cp_wire = cp_Chromel;

% Thermocouple Properties:
k_TC = 0.5*(k_Alumel+k_Chromel);
rho_TC = 0.5*(rho_Alumel+rho_Chromel);
cp_TC = (cp_Alumel*rho_Alumel+cp_Chromel*rho_Chromel)/(rho_Alumel+rho_Chromel);

% Convection coefficient
h_convection = 10; %just an assumption

% Thermal Contact Resistance - Alumina-Sheath - initial value
thcr_AlNi = 0.0052;

% Thermal Contact Resistance - Sheath-Sample - initial value
thcr_NiSample = 0.001;

% Total Radiative Emissivity- Nickel200, Nickel200 or Nickel Oxide?
if T < 473
    emissivity_probe = 0.35;    %0.35
elseif T >=473 && T < 1144
    %     emissivity_probe = 0.0007*T + 0.0316; %Why is this equation commented
    %     out, could we still use it?
    emissivity_probe = 0.86; %max emissivity of Nickel Oxide found in literature
elseif T >= 1144
    emissivity_probe = 0.86;
end
bias_emissitivy_probe = 0;
uncertainty_emissitivy_probe = .05; %LOOK INTO THIS

if MC == 1
    emissivity_probe = MonteCarloProp(uncertainty_emissitivy_probe,bias_emissitivy_probe,emissivity_probe);
end

%Sample Properties%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Air%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if strcmp(sample,'Air')
    k_air = 1E-11*(T^3) - 5E-8*(T^2) + 1E-4*T + .0003; %Made from data from engineeringtoolbox.com
    density_air = 355.1*T^-1.001; %Made from data from engineersedge.com
    cp_air = 1E-10*T^4 - 6E-07*T^3 + 0.001*T^2 - 0.3867*T + 1050; %Made from data from engineeringtoolbox.com
    
    alpha_air = k_air/(density_air*cp_air);

    k_sample = k_air;
    rho_sample = rho_air;
    cp_sample = cp_air;
    alpha_sample = alpha_air;
end
% 
% R=1;
% 
% k_Alumina = R*k_Alumina + (1-R)*k_air;
% alpha_Alumina = R*alpha_Alumina + (1-R)*alpha_air;

%Water%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if strcmp(sample,'Water')
    if T >= 273 && T < 533
        k_Water = -0.869083936+0.00894880345*T^1-0.0000158366345*T^2+0.00000000797543259*T^3;
    elseif T >= 533
        k_Water = 0; %Because I don't know what it would be. Placeholder for now
    end

    k_sample = k_Water;

    % Heat Capacity- Water
    if T >= 273 && T < 533
        cp_Water = 12010.1471-80.4072879*T^1+0.309866854*T^2-5.38186884E-4*T^3+3.62536437E-7*T^4; % 273 to 533
    elseif T >= 533
        cp_Water = 0; %because I don't know what it would be. Placeholder for now
    end

    cp_sample = cp_Water;

    % Density- Water
    if T >= 273 && T < 293
        rho_Water = 0.000063092789034*T^3-0.060367639882855*T^2+18.9229382407066*T-950.704055329848;
    elseif T >= 293 && T < 373
        rho_Water = 0.000010335053319*T^3-0.013395065634452*T^2+4.969288832655160*T+432.257114008512;
    elseif T >= 373
        rho_Water = 0; %because I don't know what it would be. placeholder for now
    end

    rho_sample = rho_Water;

    % Thermal Diffusivity- Water
    alpha_Water = k_Water/(rho_Water*cp_Water);

    alpha_sample = alpha_Water;
end

%Argon%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if strcmp(sample,'Argon')
    if T >= 273 && T < 750
        k_Argon = 0.0002678*T^0.7401; % Aggarwal, Springer, 1979
    elseif T >= 750
        k_Argon = 0.03594; %Because I don't know what it would be. Placeholder for now
    end

    k_sample = k_Argon;

    % Heat Capacity- Argon
    if T >= 273 && T < 533
        cp_Argon = 525;
    elseif T >= 533
        cp_Argon = 525; %because I don't know what it would be. Placeholder for now
    end

    cp_sample = cp_Argon;

    % Density- Argon
    if T >= 273 && T < 293
        rho_Argon = 1.77;
    elseif T >= 293 && T < 373
        rho_Argon = 1.77;
    elseif T >= 373
        rho_Argon = 1.77; %because I don't know what it would be. placeholder for now
    end

    rho_sample = rho_Argon;

    % Thermal Diffusivity- Argon
    alpha_Argon = k_Argon/(rho_Argon*cp_Argon);

    alpha_sample = alpha_Argon;
end

%Toluene%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 360k (87C)
% Thermal Conductivity- Toluene
if strcmp(sample, 'Toluene')
    if T >= 230 && T < 360
        k_Toluene = 0.2205-3.0E-4*T^1; % 230 to 360
    elseif T >= 360
        k_Toluene = 0; %because I don't know what it would be. placeholder for now
    end

    k_sample = k_Toluene;

%     Heat Capacity and Density not needed right now, but may be later. 
%     % Heat Capacity- Toluene
%     if T >= 179 && T < 505
%         cp_Toluene = 1377.31548+2.58418568*T^1-0.0272810691*T^2+9.87628598E-5*T^3-1.20802791E-8*T^4-3.3656506E-10*T^5+3.59255687E-13*T^6;
%     elseif T >= 505 && T < 565
%         cp_Toluene = 6310522.18-48043.826*T^1+137.240472*T^2-0.174290378*T^3+8.30421074E-5*T^4;
%     elseif T >= 565
%         cp_Toluene = 0; %because I don't know what it would be. placeholder for now
%     end
% 
%     % Density- Toluene
%     if T >= 263 && T < 383
%         rho_Toluene = 1065.619-0.4713105*T^1-7.132867E-4*T^2; % 263 to 383
%     elseif T >= 383
%         rho_Toluene = 0; %because I don't know what it would be. placeholder for now
%     end

    % Thermal Diffusivity- Toluene
    if T >= 263 && T < 383
        alpha_Toluene = 1.816021E-7-3.457821E-10*T^1+1.203682E-13*T^2; % 263 to 360
    elseif T >= 383
        alpha_Toluene = 0; %because I don't know what it would be. placeholder for now
    end

    alpha_sample = alpha_Toluene;
end

%NaNO3%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 690K (417C)
% Thermal Conductivity- NaNO3
if strcmp(sample,'NaNO3')
if T < 590
    T = 590;
end

    if T < 590
        k_NaNO3 = 0;
    elseif T>=590 && T < 625
        k_NaNO3 = (.513-.517)/(625-600) * (T-600) + .517;
    elseif T>=625 && T < 650
        k_NaNO3 = (.510-.513)/(650-625) * (T-625) + .513;
    elseif T>=650 && T < 675
        k_NaNO3 = (.507-.510)/(675-650) * (T-650) + .510;
    elseif T>=675 && T < 700
        k_NaNO3 = (.503-.507)/(700-675) * (T-675) + .507;
    elseif T >= 700
        k_NaNO3 = (.503-.507)/(700-675) * (T-675) + .507; %because I don't know what it would be. placeholder for now
    end

    k_sample = k_NaNO3;

    %Not sure the purpose of the COMSOL values are
    %     if T < 590
    %         k_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
    %     elseif T >= 590 && T < 740
    %         k_NaNO3_COMSOL = 0.4058875+2.624227E-4*T^1;
    %     elseif T >= 740
    %         k_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
    %     end

    % Heat Capacity- NaNO3
    cp_NaNO3 = 1805;
    % cp_NaNO3_COMSOL = 1821.38432;
    cp_sample = cp_NaNO3;

    % Density- NaNO3
    rho_NaNO3 = (1847.4-1878.6)/(360-320) * (T-(320+273)) + 1878.6;

%     if T < 590
%         rho_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
%     elseif T >= 590 && T < 690
%         rho_NaNO3_COMSOL = 2334.418-0.7672727*T^1;
%     elseif T >= 690
%         rho_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
%     end

    rho_sample = rho_NaNO3;

    % Thermal Diffusivity- NaNO3
    alpha_NaNO3 = k_NaNO3/(rho_NaNO3*cp_NaNO3);
%     if T < 590
%         alpha_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
%     elseif T >= 590 && T < 690
%         alpha_NaNO3_COMSOL = 1.007969E-7+6.976789E-11*T^1+6.217128E-14*T^2;
%     elseif T >= 690
%         alpha_NaNO3_COMSOL = 0; %because I don't know what it would be. placeholder for now
%     end

    alpha_sample = alpha_NaNO3;

end

%Propylene Glycol%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Thermal Conductivity
if strcmp(sample,'PropyleneGlycol')
    if T >= 294 && T <= 354
        k_PropyleneGlycol = 0.1549 + (1e-4)*T;
    else
        error('Invalid temperature');
    end

    k_sample = k_PropyleneGlycol;

    %Density
    if T >= 273 && T <= 393
        rho_PropyleneGlycol = 1352.128-1.775134*T^1+0.003661077*T^2-4.338143E-6*T^3;
    else
        error('Invalid temperature');
    end

    rho_sample = rho_PropyleneGlycol;

    %Heat Capacity
    if T >= 253 && T <= 373
        cp_PropyleneGlycol = 764.977874+5.85389298*T^1;
    else
        error('Invalid temperature');
    end

    cp_sample = cp_PropyleneGlycol;

    %Thermal Diffusivity
    alpha_PropyleneGlycol = k_PropyleneGlycol/(rho_PropyleneGlycol*cp_PropyleneGlycol);

    alpha_sample = alpha_PropyleneGlycol;
end

%Potassium Nitrate (KNO3)%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Thermal Conductivity
if strcmp(sample,'KNO3')
    if T >= 610 && T <= 710
        k_KNO3 = .4303-.000422*(T-610.15);
    else
        error('Invalid temperature');
    end

    k_sample = k_KNO3;

    %Density
    if T >= 610 && T <= 730
        rho_KNO3 = (1.865 - 0.000723*((T-273.15)-337))*1000;
    else
        error('Invalid temperature');
    end

    rho_sample = rho_KNO3;

    %Heat Capacity
    cp_KNO3 = 1518;

    cp_sample = cp_KNO3;

    %Thermal Diffusivity
    alpha_KNO3 = k_KNO3/(rho_KNO3*cp_KNO3);

    alpha_sample = alpha_KNO3;

end

%FLiNaK%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 910K (636C)
if strcmp(sample,'FLiNaK')
    % Thermal Conductivity- FLiNaK
    %     k_FLiNaK = 0.0006*T + 0.2852;
    k_LiF = 1.9 - 0.0004*T; %1118.5-1900K
    k_KF = 0.86 - 0.00025*T; %1129.15-1800K
    k_NaF = 1.3 - 0.00028*T; %1268.15-1800K
    k_FLiNaK = .115*k_NaF + .42*k_KF + .465*k_LiF; %k_FLiNaK weighted by molar composition of eutectic
    bias_kFLiNaK = 0;
    uncertainty_kFLiNaK = 0.05; %Defintely needs to be looked into.
    if MC == 1
        k_FLiNaK = MonteCarloProp(uncertainty_kFLiNaK,bias_kFLiNaK,k_FLiNaK);
    end

    k_sample = k_FLiNaK;

    % Heat Capacity- Flinak
    %cp_FLiNaK = 0.0108*T + 1896.1;%Don't know where this came from
    cp_FLiNaK = (40.3 + (4.39e-2)*T)/.0412911; %Rogers et al
    u_cp_FLiNaK = .02;

    if MC == 1
        cp_FLiNaK = MonteCarloProp(u_cp_FLiNaK,bias_kFLiNaK,cp_FLiNaK);
    end

    cp_sample = cp_FLiNaK;

    % Density- Flinak
    %rho_FLiNaK = -0.6141*T + 2585.7; %Not sure where this came from
    rho_FLiNaK = (2.5793 - T*(6.24e-4))*1000; %Cibulkova et al
    u_rho_FLiNaK = .01; %Cibulkova et al

    if MC == 1
        rho_FLiNaK = MonteCarloProp(u_rho_FLiNaK,bias_kFLiNaK,rho_FLiNaK);
    end

    rho_sample = rho_FLiNaK;

    % Thermal Diffusivity- Flinak
    alpha_FLiNaK= k_FLiNaK/(rho_FLiNaK*cp_FLiNaK);
    bias_alphaFLiNaK = 0;
    uncertainty_alphaFLiNaK = 0.05; %CHECK THIS VALUE
    if MC == 1
        alpha_FLiNaK = MonteCarloProp(uncertainty_alphaFLiNaK,bias_alphaFLiNaK,alpha_FLiNaK);
    end

    alpha_sample = alpha_FLiNaK;
end

%Flibe%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1070 (796C)
if strcmp(sample,'FLiBe')
    % Thermal Conductivity- Flibe
    %     k_FLiBe = 0.0003*T + 0.8721;
    k_LiF = 1.88 - (3.99e-4)*T; %1118.5-1900K Gheribi et al
    u_k_LiF = .20*k_LiF; %Gheribi et al
    k_BeF2 = 0.801 - (2.12e-6)*T; %1070.15K-? Gheribi et al
    u_k_BeF2 = .20*k_BeF2; %Gheribi et al

    k_FLiBe = .67*k_LiF + .33*k_BeF2; %k_FLiBe weighted by molar composition of eutectic
    u_k_FLiBe = sqrt((u_k_BeF2*.33)^2 + (u_k_LiF*.67)^2); %Propagation of uncertainty
    bias_FLiBe = 0;

    if MC == 1
        k_FLiBe = MonteCarloProp(u_k_FLiBe,bias_FLiBe,k_FLiBe);
    end

    k_sample = k_FLiBe;

    % Heat Capacity- Flibe
    %cp_FLiBe = 0.8241*T + 496.27; %No clue where this came from
    cp_LiF = 64.183/.0259394; %MSTDB-TC
    cp_BeF2 = (51.1 + 3.46e-2)/.047009; %MSTDB-TC
    cp_FLiBe = .67*cp_LiF + .33*cp_BeF2;
    u_cp_FLiBe = 0; %Both components labelled synthetic

    if MC == 1
        cp_FLiBe = MonteCarloProp(u_cp_FLiBe,bias_FLiBe,cp_FLiBe);
    end

    cp_sample = cp_FLiBe;

    % Density- Flibe
    %rho_FLiBe = -0.2618*T + 2194; %Don't know where this came from
    rho_FLiBe = 1000*(2.41-(4.88e-4)*T); %Cantor et al
    u_rho_FLiBe = .01;

    if MC == 1
        rho_FLiBe = MonteCarloProp(u_rho_FLiBe,bias_FLiBe,rho_FLiBe);
    end

    rho_sample = rho_FLiBe;

    % Thermal Diffusivity- Flibe
    alpha_FLiBe = k_FLiBe/(rho_FLiBe*cp_FLiBe);

    alpha_sample = alpha_FLiBe;
end

%FMgNaK%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1070K (796C)
if strcmp(sample,'FMgNaK')
    % Thermal Conductivity- FMgNaK
    Reference_correlation_NaF = 1.3 - 0.00028*T; %1268.15-1800K
    Reference_correlation_KF = 0.86 - 0.00025*T; %1129.15-1800K
    Reference_correlation_MgF2 = 0.87 - 0.00014*T; %1536.24K?
    k_FMgNaK = .345*Reference_correlation_NaF + .59*Reference_correlation_KF + .065*Reference_correlation_MgF2; %k_FMgNaK weighted by molar composition of eutectic
    bias_kFMgNaK = 0;
    uncertainty_kFMgNaK = 0.05;%CHECK THIS VALUE
    if MC == 1
        k_FMgNaK = MonteCarloProp(uncertainty_kFMgNaK,bias_kFMgNaK,k_FMgNaK);
    end

    k_sample = k_FMgNaK;

    % Heat Capacity- FMgNaK
    %     cp_FMgNaK = 0.0108*T + 1896.1; %cp_Flinak
    cp_NaF = 68.62;
    cp_KF = 70.6;
    cp_MgF2 = 94.43;
    cp_FMgNaK = 0.345*cp_NaF+0.59*cp_KF+0.065*cp_MgF2; %eutectic average of unaries from MSTDB

    cp_sample = cp_FMgNaK;

    % Density- FMgNaK
    rho_FMgNaK = -0.6318*T + 2711;

    rho_sample = rho_FMgNaK;

    % Thermal Diffusivity- FMgNaK
    alpha_FMgNaK= k_FMgNaK/(rho_FMgNaK*cp_FMgNaK);
    bias_alphaFMgNaK = 0;
    uncertainty_alphaFMgNaK = 0.05; %CHECK THIS
    if MC == 1
        alpha_FMgNaK = MonteCarloProp(uncertainty_alphaFMgNaK,bias_alphaFMgNaK,alpha_FMgNaK);
    end

    alpha_sample = alpha_FMgNaK;
end

%LiCl-KCl%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1023K (750C)
if strcmp(sample,'LiCl-KCl')
    % Thermal Conductivity- LiCl-KCl
    k_LiCl = 0.8821 + (-2.9e-4)*T; % Nagasaka et al.
    u_k_LiCl = .2*k_LiCl; %Nagasaka et al
    k_KCl = 0.5663 + (-1.7e-4)*T; % Nagsaka et al.
    u_k_KCl = .08*k_KCl; %Nagasaka et al

    k_LiCl_KCl = .582*k_LiCl + .418*k_KCl; %k_LiCl-KCl weighted by molar composition of eutectic
    bias_kLiCl_KCl = 0;
    uncertainty_LiCl_KCl = sqrt((.582*u_k_LiCl)^2 + (.418*u_k_KCl)^2); %Check this
    if MC == 1
        k_LiCl_KCl = MonteCarloProp(uncertainty_LiCl_KCl,bias_kLiCl_KCl,k_LiCl_KCl);
    end

    k_sample = k_LiCl_KCl;

    % Heat Capacity- LiCl-KCl
    %cp_LiCl_KCl = 1271.58672; % Redkin et al. No temperature depedence
    %recorded. Abandoning this value because the cited source doesn't
    %actually measure it for this mix. 
    %u_cp_LiCl_KCl = 0; %None reported

    cp_LiCl = 1/.042394*(73.3832+(-.0094726)*(T)); %I think These came from a model within the MSTDB-TC, since it's just for an initial guess it's good enough
    cp_KCl = 73.59656/.0745513; %Also a MSTDB-TC model
    cp_LiCl_KCl= .418*cp_KCl + .582*cp_LiCl;
    u_cp_LiCl_KCl = 0; %Both labelled as Synthetic in MSTDB

    if MC == 1 
        cp_LiCl_KCl = MonteCarloProp(u_cp_LiCl_KCl,bias_kLiCl_KCl,cp_LiCl_KCl);
    end

    cp_sample = cp_LiCl_KCl;

    % Density- LiCl-KCl
    rho_LiCl_KCl = 2008.2 - 0.5133*T; %Duemmler et al.
    u_rho_LiCl_KCl = .007; %Duemmlet et al.

    if MC == 1 
        rho_LiCl_KCl = MonteCarloProp(u_rho_LiCl_KCl,bias_kLiCl_KCl,rho_LiCl_KCl);
    end

    rho_sample = rho_LiCl_KCl;

    % Thermal Diffusivity- LiCl-KCl
    alpha_LiCl_KCl= k_LiCl_KCl/(rho_LiCl_KCl*cp_LiCl_KCl);
    bias_alphaLiCl_KCl = 0;
    uncertainty_alphaLiCl_KCl = 0.05;%guess what CHECK THIS
    if MC == 1
        alpha_LiCl_KCl = MonteCarloProp(uncertainty_alphaLiCl_KCl,bias_alphaLiCl_KCl,alpha_LiCl_KCl);
    end

    alpha_sample = alpha_LiCl_KCl;
end

%NaCl-KCl%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1023K (750C)
if strcmp(sample,'NaCl-KCl')
    % Thermal Conductivity- NaCl-KCl
    k_NaCl = 0.7121 + (-1.8e-4)*(T); % Nagasaka et al. Valid for 1170-1441K
    u_k_NaCl = .08*k_NaCl; %Nagasaka et al
    k_KCl = .5663 - (1.704e-4)*T;%Nagasaka et al
    u_k_KCl = .08*k_KCl; %Nagasaka et al

    bias_kNaCl_KCl = 0;
    k_NaCl_KCl = .4877*k_KCl + .5123*k_NaCl;
    uncertainty_kNaCl_KCl = sqrt((.4877*u_k_KCl)^2 + (.5123*u_k_NaCl)^2); %Propagation of uncertainty

    if MC == 1
        k_NaCl_KCl = MonteCarloProp(uncertainty_kNaCl_KCl,bias_kNaCl_KCl,k_NaCl_KCl);
    end

    k_sample = k_NaCl_KCl;

    % Heat Capacity- NaCl-KCl
    cp_NaCl = 1/.0584428*(77.7638+(-.0075312*T)); %I think These came from a model within the MSTDB-TC, since it's just for an initial guess it's good enough;
    u_cp_NaCl = 0; %Labelled as Synthetic in the MSTDB
    cp_KCl = 73.59656/.0745513; %Also a MSTDB-TC model
    u_cp_KCl = 0; %Labelled as Synthetic

    cp_NaCl_KCl = .4877*cp_KCl + .5123*cp_NaCl;
    u_cp_NaCl_KCl = sqrt((.4877*u_cp_KCl)^2 + (.5123*u_cp_NaCl)^2)/cp_NaCl_KCl;%Propagation of uncertainty

    if MC == 1
        cp_NaCl_KCl = MonteCarloProp(u_cp_NaCl_KCl,bias_kNaCl_KCl,cp_NaCl_KCl);
    end

    cp_sample = cp_NaCl_KCl;

    % Density- NaCl-KCl
    rho_NaCl_KCl = (2.13 - T*5.68e-4)*1000; %Van Artsdalen et al
    u_rho_NaCl_KCl = .01; %Van Artsdalen et al

    if MC == 1
        rho_NaCl_KCl = MonteCarloProp(u_rho_NaCl_KCl,bias_kNaCl_KCl,rho_NaCl_KCl);
    end

    rho_sample = rho_NaCl_KCl;

    % Thermal Diffusivity- NaCl-KCl
    alpha_NaCl_KCl= k_NaCl_KCl/(rho_NaCl_KCl*cp_NaCl_KCl);
    bias_alphaNaCl_KCl = 0;
    uncertainty_alphaNaCl_KCl = 0.05; %CHECK THIS FOOL, this might not be needed now with rho and cp being varied with the Monte Carlo
    if MC == 1
        alpha_NaCl_KCl = MonteCarloProp(uncertainty_alphaNaCl_KCl,bias_alphaNaCl_KCl,alpha_NaCl_KCl);
    end

    alpha_sample = alpha_NaCl_KCl;
end

%LiF-NaF 60-40%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO ?
if strcmp(sample,'LiF-NaF')
    % Thermal Conductivity- LiF-NaF
    k_LiF = 1.88 - (3.99e-4)*T; %Gheribi et al
    u_k_LiF = .20*k_LiF;
    k_NaF = 1.26 - (2.8e-4)*T; %Gheribi et al
    u_k_NaF = .20*k_NaF;

    k_LiF_NaF = .6*k_LiF + .4*k_NaF;
    bias_LiF_NaF = 0;
    uncertainty_LiF_NaF = sqrt((.6*u_k_LiF)^2 + (.4*u_k_NaF)^2); %Propagation of uncertainty

    if MC == 1
        k_LiF_NaF = MonteCarloProp(uncertainty_LiF_NaF,bias_LiF_NaF,k_LiF_NaF);
    end

    k_sample = k_LiF_NaF;

    % Heat Capacity- LiF-NaF
    cp_LiF_NaF = (125.1-.06661*T)/.0323589; %Powers et al
    u_cp_LiF_NaF = .10; %Powers et al

    if MC == 1
        cp_LiF_NaF = MonteCarloProp(u_cp_LiF_NaF,bias_LiF_NaF,cp_LiF_NaF);
    end

    cp_sample = cp_LiF_NaF;

    % Density- LiF-NaF
    rho_LiF_NaF = (2.533-(5.552e-4)*T)*1000; %Janz et al
    u_rho_LiF_NaF = .01;


    if MC == 1
        rho_LiF_NaF = MonteCarloProp(u_rho_LiF_NaF,bias_LiF_NaF,rho_LiF_NaF);
    end

    rho_sample = rho_LiF_NaF;

    % Thermal Diffusivity- LiF-NaF
    alpha_LiF_NaF= k_LiF_NaF/(rho_LiF_NaF*cp_LiF_NaF);
    bias_alphaLiF_NaF = 0;
    uncertainty_alphaLiF_NaF = 0.20; %CHECK THIS

    if MC == 1
        alpha_LiF_NaF = MonteCarloProp(uncertainty_alphaLiF_NaF,bias_alphaLiF_NaF,alpha_LiF_NaF);
    end

    alpha_sample = alpha_LiF_NaF;
end

%LiCl-NaCl%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1023K (750C)
if strcmp(sample,'LiCl-NaCl')
    % Thermal Conductivity- LiCl-KCl
    k_LiCl = 0.882 + (-2.9e-4)*(T); % Nagasaka et al. Valid for 967-1321K
    u_k_LiCl = .2*k_LiCl; %Nagasaka et al
    k_NaCl = 0.7121 + (-1.8e-4)*(T); % Nagasaka et al. Valid for 1170-1441K
    u_k_NaCl = .08*k_NaCl; %Nagasaka et al
    k_LiCl_NaCl = .72*k_LiCl + .28*k_NaCl; %k_LiCl-NaCl weighted by molar composition of eutectic
    bias_kLiCl_NaCl = 0;
    uncertainty_kLiCl_NaCl = sqrt((.72*u_k_LiCl)^2 + (.28*u_k_NaCl)^2)/k_LiCl_NaCl;%Propagation of uncertainty

   
    if MC == 1
        k_LiCl_NaCl = MonteCarloProp(uncertainty_kLiCl_NaCl,bias_kLiCl_NaCl,k_LiCl_NaCl);
    end
    

    k_sample = k_LiCl_NaCl;

    % Heat Capacity- LiCl-NaCl
    cp_LiCl = 1/.042394*(73.3832+(-.0094726)*(T)); %I think These came from a model within the MSTDB-TC, since it's just for an initial guess it's good enough
    %cp_NaCl = -2.66+(7.72e-2)*(T)+(4.03e7)*(T^-2)+(-1.79e-5)*(T^2); %where did this come from?
    cp_NaCl = 1/.0584428*(77.7638+(-.0075312*T)); %I think These came from a model within the MSTDB-TC, since it's just for an initial guess it's good enough
    cp_LiCl_NaCl = .72*cp_LiCl + .28*cp_NaCl;
    u_cp_LiCl_NaCl = 0; %Labelled Synthetic in the MSTDB

    if MC == 1
        cp_LiCl_NaCl = MonteCarloProp(u_cp_LiCl_NaCl,bias_kLiCl_NaCl,cp_LiCl_NaCl);
    end

    cp_sample = cp_LiCl_NaCl;

    % Density- LiCl-NaCl DO NOT USE FOR ACCURATE CP MEASUREMENTS
    rho_LiCl = (1.88 - (4.33e-4)*T)*1000; %Van Artsdalen et al. 893.2-1053.2K
    u_rho_LiCl = .01*rho_LiCl; %Van Arstdalen et al.
    rho_NaCl = (2.41 - (5.43e-4)*T)*(1000); %Van Artsdalen et al. 1076.2-1303.2K
    u_rho_NaCl = .01*rho_NaCl; %Van Arsdalen et al
    rho_LiCl_NaCl = .72*rho_LiCl + .28*rho_NaCl;
    u_rho_LiCl_NaCl = sqrt((.72*u_rho_LiCl)^2 + (.28*u_rho_NaCl)^2)/rho_LiCl_NaCl;

    if MC == 1
        rho_LiCl_NaCl = MonteCarloProp(u_rho_LiCl_NaCl,bias_kLiCl_NaCl,rho_LiCl_NaCl);
    end

    rho_sample = rho_LiCl_NaCl;

    % Thermal Diffusivity- LiCl-NaCl
    alpha_LiCl_NaCl= k_LiCl_NaCl/(rho_LiCl_NaCl*cp_LiCl_NaCl);
    bias_alphaLiCl_NaCl = 0;
    uncertainty_alphaLiCl_NaCl = sqrt((uncertainty_kLiCl_NaCl/(rho_LiCl_NaCl*cp_LiCl_NaCl))^2 + (k_LiCl_NaCl*u_rho_LiCl_NaCl/(cp_LiCl_NaCl*rho_LiCl_NaCl^2))^2 +(k_LiCl_NaCl*u_cp_LiCl_NaCl/(rho_LiCl_NaCl*cp_LiCl_NaCl^2))^2)/alpha_LiCl_NaCl; %Propgation of uncertainty
    
    if MC ==1
        alpha_LiCl_NaCl = MonteCarloProp(uncertainty_alphaLiCl_NaCl,bias_alphaLiCl_NaCl,alpha_LiCl_NaCl);
    end


    alpha_sample = alpha_LiCl_NaCl;

end

%KCl-ZnCl2%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if strcmp(sample,'KCl-ZnCl')
    %Thermal Conductivity
    k_ZnCl2 = 3.05; %Kornwell, maybe actually Turnbull1961?
    u_k_ZnCl2 = .05;
    k_KCl = .5663 - (1.704e-4)*T;%Nagasaka et al
    u_k_KCl = .08*k_KCl; %Nagasaka et al

    k_ZnCl2_KCl = .453*k_KCl + .547*k_ZnCl2;
    u_k_ZnCl2_KCl = sqrt((u_k_ZnCl2*.547)^2 + (u_k_KCl*.453)^2);

    if MC == 1
        k_ZnCl2_KCl = MonteCarloProp(u_k_ZnCl2_KCl,0,k_ZnCl2_KCl);
    end

    k_sample = k_ZnCl2_KCl;

    %Density
    rho_ZnCl2 = 2683-.511*Temp; %Smith and Smith
    u_rho_ZnCl2 = .01;
    rho_KCl = 2140 - .583*T; %Van ArtsDalen
    u_rho_KCl = .01;

    rho_ZnCl2_KCL = .453*rho_KCl*.547*rho_ZnCl2;
    u_rho_KCl_ZnCl2 = sqrt((u_rho_ZnCl2*.547)^2 + (u_rho_KCl*.453)^2);
    if MC == 1
        rho_ZnCl2_KCL = MonteCarloProp(u_rho_KCl_ZnCl2,0,rho_ZnCl2_KCL);
    end

    rho_sample = rho_ZnCl2_KCL;

    %Specific Heat
    cp_ZnCl2 = 24.1; %cal/mole, convert later, allegedly constant. Cubicciotti et al
    %cp_NiCl2 = 553.2; %J/kgK, from matweb. 
    cp_KCl = 73.59656/.0745513; %Also a MSTDB-TC model
    %u_cp_KCl = 0; %Labelled as Synthetic

    cp_ZnCl2_KCl = .453*cp_KCl + .547*cp_ZnCl2; %No uncertainty known. 

    cp_sample = cp_ZnCl2_KCl;

    %Thermal Diffusivity
    alpha_ZnCl2_KCl = k_ZnCl2_KCl/(rho_ZnCl2_KCL*cp_ZnCl2_KCl);

    alpha_sample = alpha_ZnCl2_KCl;

end

%Scatter and Index of Refraction%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
index_of_refraction = 1.462 - (1.4e-4)*T; %Solar salts (citation needed)
scatter = 0;

%Crucible Properties%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
r_sample = 0.00207;					% Sample Radius (in meters)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%STAINLESS STEEL 316 (SOLID/POLISHED/OXIDIZED): VALID UP TO 1220K (947C)
if strcmp(crucible,'Steel316')
    
    % Crucible radius (thermal expansivity)
    if T >= 0 && T < 100
        r_sample = r_sample + r_sample*( (8.9e-6)*0.0254*(5/9) ); %https://www.pennstainless.com/stainless-steel-plate-316-316l-astm-a240/#:~:text=Physical%20Properties%20of%20316%20and%20316L%20Stainless%20Steel%20Plate&text=The%20coefficient%20of%20thermal%20expansion,in%20x%2010%5E%2D6.
    elseif T >= 100 && T < 538
        r_sample = r_sample + r_sample*( (9.7e-6)*0.0254*(5/9) );
    elseif T >= 538 && T < 1220%815
        r_sample = r_sample + r_sample*( (11.1e-6)*0.0254*(5/9) );
    end
    
    % Thermal Conductivity- Steel316
    if T >= 4 && T < 9
        k_Steel316 = -0.9611905+0.5776587*T^1-0.08547619*T^2+0.004722222*T^3;
    elseif T >= 9 && T < 135
        k_Steel316 = -0.575597+0.1484296*T^1+1.184549E-5*T^2-6.696619E-6*T^3+2.25279E-8*T^4;
    elseif T >= 135 && T < 1220
        k_Steel316 = 7.956002+0.02084122*T^1-4.706772E-6*T^2+6.271478E-10*T^3-1.240772E-12*T^4;
    end

    k_crucible = k_Steel316;

    % Density- Steel316
    if T >= 4 && T < 114
        rho_Steel316 = 8042.496-0.01245121*T^1+3.834401E-5*T^2-7.363868E-6*T^3;
    elseif T >= 114 && T < 1273
        rho_Steel316 = 8058.746-0.1963973*T^1-4.830884E-4*T^2+4.114383E-7*T^3-1.337946E-10*T^4;
    end

    rho_crucible = rho_Steel316;

    % Specific Heat- Steel316
    if T >= 4 && T < 18
        cp_Steel316 = 0.363452365+0.26377074*T^1+0.0493134608*T^2-0.0038147097*T^3+1.19554913E-4*T^4;
    elseif T >= 18 && T < 50
        cp_Steel316 = -14.0795868+2.9024659*T^1-0.153359541*T^2+0.004588802*T^3-3.66629778E-5*T^4;
    elseif T >= 50 && T < 140
        cp_Steel316 = -20.5016084-0.832746541*T^1+0.0955618906*T^2-7.74522415E-4*T^3+1.944414E-6*T^4;
    elseif T >= 140 && T < 300
        cp_Steel316 = -75.5829977+5.00692586*T^1-0.0164947547*T^2+2.02748649E-5*T^3;
    elseif T >= 300 && T < 1500
        cp_Steel316 = 235.650788+1.30084242*T^1-0.00189052617*T^2+1.34841366E-6*T^3-3.43379416E-10*T^4;
    end

    cp_crucible = cp_Steel316;

    % Thermal Diffusivity- Steel316
    alpha_Steel316 = k_Steel316/(rho_Steel316*cp_Steel316);

    alpha_crucible = alpha_Steel316;

    % Total Radiative Emissivity- Steel316
    if T < 660
        emissivity_Steel316 = 0.38;
    elseif T >= 660 && T < 1138
        emissivity_Steel316 = 0.0005*T + 0.0569;
    elseif T >= 1075
        emissivity_Steel316 = 0.6;
    end
    
    emissivity_crucible = emissivity_Steel316;

end

%NICKEL 200%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%VALID UP TO 1273K (1000C)
if strcmp(crucible,'Nickel200')
    
    % Crucible radius (thermal expansivity) https://www.sandmeyersteel.com/images/Alloy200-201-SpecSheet-2.pdf
    if T >= 0 && T < 100
        r_sample = r_sample + r_sample*(1.33e-5); %https://www.pennstainless.com/stainless-steel-plate-316-316l-astm-a240/#:~:text=Physical%20Properties%20of%20316%20and%20316L%20Stainless%20Steel%20Plate&text=The%20coefficient%20of%20thermal%20expansion,in%20x%2010%5E%2D6.
    elseif T >= 100 && T < 200
        r_sample = r_sample + r_sample*(1.39e-5);
    elseif T >= 200 && T < 300
        r_sample = r_sample + r_sample*(1.42e-5);
    elseif T >= 300 && T < 400
        r_sample = r_sample + r_sample*(1.48e-5);
    elseif T >= 400 && T < 500
        r_sample = r_sample + r_sample*(1.53e-5);
    elseif T >= 500 && T < 600
        r_sample = r_sample + r_sample*(1.55e-5);
    elseif T >= 600 && T < 700
        r_sample = r_sample + r_sample*(1.58e-5);
    elseif T >= 700 && T < 800
        r_sample = r_sample + r_sample*(1.62e-5);
    elseif T >= 800 && T < 900
        r_sample = r_sample + r_sample*(1.66e-5);
    elseif T >= 900 && T < 1000
        r_sample = r_sample + r_sample*(1.69e-5);
    elseif T >= 1000 && T < 1100
        r_sample = r_sample + r_sample*(1.71e-5);
    end
    
    % Thermal Conductivity- Nickel200
    if T >= 173 && T < 673
        k_Ni = 76.12158+0.02717507*T^1-2.126458E-4*T^2+1.876168E-7*T^3;
        bias_kNickel200 = 0;
        uncertainty_kNickel200 = 0.05; %CHECK THIS
    elseif T >= 673 && T <= 1273
        k_Ni = 40.623+0.02201643*T^1-3.571429E-7*T^2;
        bias_kNickel200 = 0;
        uncertainty_kNickel200 = 0.05; %CHECK THIS
    end

    if MC == 1
        k_Ni = MonteCarloProp(uncertainty_kNickel200,bias_kNickel200,k_Ni);
    end

    k_crucible = k_Ni;

    % Density- Nickel200
    rho_Nickel200 = 8964.214-0.1681755*T^1-3.536041E-4*T^2+2.01714E-7*T^3-4.919056E-11*T^4; % 73 to 1373 K

    rho_crucible = rho_Nickel200;

    % Heat Capacity- Nickel200
        if T >= 293 && T < 633
            cp_Nickel200 = 292.88+0.50208*T^1;
        elseif T >= 633 && T < 1726
            cp_Nickel200 = 418.4+0.1284488*T^1;
        end
    
    cp_crucible = cp_Nickel200;

    % Thermal Diffusivity- Nickel200
    if T >= 293 && T < 633
        alpha_Nickel200 = 3.044717E-5-5.149323E-8*T^1+3.129624E-11*T^2;
        bias_alpha_Nickel200 = 0;
        uncertainty_alpha_Nickel200 = 0.05;
    elseif T >= 633 && T < 676
        alpha_Nickel200 = 4.81462E-5-1.036816E-7*T^1+7.54384E-11*T^2;
        bias_alpha_Nickel200 = 0;
        uncertainty_alpha_Nickel200 = 0.05; %CHECK THIS
    elseif T >= 676 && T <= 1273
        alpha_Nickel200 = 1.087891E-5+2.600264E-9*T^1-2.279477E-13*T^2;
        bias_alpha_Nickel200 = 0;
        uncertainty_alpha_Nickel200 = 0.05;
    end

    if MC == 1
        alpha_Nickel200 = MonteCarloProp(uncertainty_alpha_Nickel200,bias_alpha_Nickel200,alpha_Nickel200);
    end

    alpha_crucible = alpha_Nickel200;

    % Total Radiative Emissivity- Nickel200
    if T < 473
        emissivity_Nickel200 = 0.35;   
        bias_emissivity_Nickel200 = 0;
        uncertainty_emissivity_Nickel200 = 0.05; %CHECK THIS
    elseif T >=473 && T < 1144
        %     emissivity_Nickel200 = 0.0007*T + 0.0316; %Why are we not using this
        %     equation?
        emissivity_Nickel200 = 0.86; %max emissivity of Nickel Oxide found in literature
        bias_emissivity_Nickel200 = 0;
        uncertainty_emissivity_Nickel200 = 0.05; %CHECK THIS
    elseif T >= 1144
        emissivity_Nickel200 = 0.86;
        bias_emissivity_Nickel200 = 0;
        uncertainty_emissivity_Nickel200 = 0.05; %CHECK THIS
    end

    if MC == 1
        emissivity_Nickel200 = MonteCarloProp(uncertainty_emissivity_Nickel200,bias_emissivity_Nickel200,emissivity_Nickel200);
    end

    emissivity_crucible = emissivity_Nickel200;

end

%Inconel625%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Valid to who know's where. This section needs work.
if strcmp(crucible,'Inconel625')
    
    % Crucible radius (thermal expansivity) https://www.sandmeyersteel.com/images/Alloy200-201-SpecSheet-2.pdf
    if T >= 0 && T < 204
        r_sample = r_sample + r_sample*(1.31e-5); %https://www.pennstainless.com/stainless-steel-plate-316-316l-astm-a240/#:~:text=Physical%20Properties%20of%20316%20and%20316L%20Stainless%20Steel%20Plate&text=The%20coefficient%20of%20thermal%20expansion,in%20x%2010%5E%2D6.
    elseif T >= 204 && T < 316
        r_sample = r_sample + r_sample*(1.35e-5);
    elseif T >= 316 && T < 427
        r_sample = r_sample + r_sample*(1.39e-5);
    elseif T >= 427 && T < 538
        r_sample = r_sample + r_sample*(1.44e-5);
    elseif T >= 538 && T < 649
        r_sample = r_sample + r_sample*(1.51e-5);
    elseif T >= 649 && T < 760
        r_sample = r_sample + r_sample*(1.57e-5);
    elseif T >= 760 && T < 871
        r_sample = r_sample + r_sample*(1.66e-5);
    elseif T >= 871 && T < 982
        r_sample = r_sample + r_sample*(1.73e-5);
    end
    
    % Thermal conductivity
    if T >= 316 && T < 1093
        k_Inconel625 = 0.2435*(T) + 339.27;
        bias_kInconel625 = 0; %Assumption. This value needs to be looked up.
        uncertainty_kInconel625 = .05; %Assumption for now. Update before real use.
    end

    if MC == 1
        k_Inconel625 = MonteCarloProp(uncertainty_kInconel625,bias_kInconel625,k_Inconel625);
    end

    k_crucible = k_Inconel625;

    % Density- Inconel625
    rho_Inconel625 = 8440;

    rho_crucible = rho_Inconel625;

    % Heat Capacity- Inconel625
    if T >= 316 && T < 1093
        cp_Inconel625 = 0.0163*(T) + 4.23;
    end

    cp_crucible = cp_Inconel625;

    % Thermal Diffusivity- Nickel200

    if T >= 316 && T < 1093
        alpha_Inconel625 = k_Inconel625/(rho_Inconel625 * cp_Inconel625);
    end

    alpha_crucible = alpha_Inconel625;

    % Total Radiative Emissivity- Nickel200
    if T < 473
        emissivity_Inconel625 = 0.35;
    elseif T >=473 && T < 1144
        %     emissivity_Nickel200 = 0.0007*T + 0.0316;
        emissivity_Inconel625 = 0; %not sure
    elseif T >= 1144
        emissivity_Inconel625 = 0; %not sure
    end

    emissivity_crucible = emissivity_Inconel625;
end



par_vector(1) = k_TC;
par_vector(2) = rho_TC;
par_vector(3) = cp_TC;
par_vector(4) = k_wire;
par_vector(5) = rho_wire;
par_vector(6) = cp_wire;
par_vector(7) = k_Alumina;
par_vector(8) = rho_Alumina;
par_vector(9) = cp_Alumina;
par_vector(10) = k_Ni;
par_vector(11) = rho_Ni;
par_vector(12) = cp_Ni;
par_vector(13) = emissivity_probe;
par_vector(14) = k_crucible;
par_vector(15) = rho_crucible;
par_vector(16) = cp_crucible;
par_vector(17) = emissivity_crucible;
par_vector(18) = scatter;
par_vector(19) = h_convection;
par_vector(20) = avgQ;
par_vector(21) = porosity_Al;
par_vector(22) = thcr_AlNi;
par_vector(23) = thcr_NiSample;
par_vector(24) = k_sample;
par_vector(25) = rho_sample;
par_vector(26) = cp_sample;
par_vector(27) = rho_sample*cp_sample;
par_vector(28) = Temp;
par_vector(29) = r_sample;

par_names(1,1) = "k Thermocouple";
par_names(2,1) = "rho Thermocouple";
par_names(3,1) = "cp Thermocouple";
par_names(1,2) = "W/(m*K)";
par_names(2,2) = "kg/m^3";
par_names(3,2) = "J/(kg*K)";

par_names(4,1) = "k Wire";
par_names(5,1) = "rho Wire";
par_names(6,1) = "cp wire";
par_names(4,2) = "W/(m*K)";
par_names(5,2) = "kg/m^3";
par_names(6,2) = "J/(kg*K)";

par_names(7,1) = "k Insulation";
par_names(8,1) = "rho Insulation ";
par_names(9,1) = "cp Insulation";
par_names(7,2) = "W/(m*K)";
par_names(8,2) = "kg/m^3";
par_names(9,2) = "J/(kg*K)";

par_names(10,1) = "k Sheath";
par_names(11,1) = "rho Sheath";
par_names(12,1) = "cp Sheath";
par_names(13,1) = "Emissivity Sheath";
par_names(10,2) = "W/(m*K)";
par_names(11,2) = "kg/m^3";
par_names(12,2) = "J/(kg*K)";
par_names(13,2) = "emissivity units";

par_names(14,1) = "k Crucible";
par_names(15,1) = "rho Crucible";
par_names(16,1) = "cp Crucible";
par_names(17,1) = "Emissivity Crucible";
par_names(14,2) = "W/(m*K)";
par_names(15,2) = "kg/m^3";
par_names(16,2) = "J/(kg*K)";
par_names(17,2) = "emissivity units";

par_names(18,1) = "Scatter";
par_names(19,1) = "h Convection";
par_names(20,1) = "Wire Power";
par_names(18,2) = "scatter units";
par_names(19,2) = "W/(m^2*K)";
par_names(20,2) = "W";

par_names(21,1) = "Insulation Porosity";
par_names(22,1) = "Thermal Contact Resistance Sheath-Insulation";
par_names(23,1) = "Thermal Contact Resistance Sheath-Sample";
par_names(24,1) = "k Sample";
par_names(25,1) = "rho sample";
par_names(26,1) = "cp Sample";
par_names(27,1) = "Rhosample*cpsample";
par_names(28,1) = "Ambient Temperature";
par_names(29,1) = "Sample Radius";
par_names(21,2) = "porosity ratio";
par_names(22,2) = "K/W";
par_names(23,2) = "K/W";
par_names(24,2) = "W/(m*K)";
par_names(25,2) = "kg/m^3";
par_names(26,2) = "J/(kg*K)";
par_names(27,2) = "J/(m^3*K)";
par_names(28,2) = "K";
par_names(29,2) = "m";

end



function [MCvalue] = MonteCarloProp(uncertainty,bias,mean)

uncertaintyint = uncertainty*mean;
totaluncertainy = sqrt(uncertaintyint^2+bias^2);
std_dev = totaluncertainy/2;
MCvalue = normrnd(mean, std_dev);

end