function f=NeedleProbeModel(t,par_vector,cp,IV)
%Seeks to solve for Probe thermocouple temperature when the liquid sample is surrounded by a crucible

%Transient, multilayered analytic model using the quadrupoles method
%3 Layers: Probe(TC+insulation+wires+sheath), Sample, and Crucible
%Determine temperature v. time of needle probe

par_vector = abs(par_vector);
f=invlap('identity',t,0,1e-9);%calculate the Laplace inverse
f = f - f(1);

%%%%%%%% INVLAP numerical inverse Laplace transform %%%%%%%%%%%%%%%%%%
% f = invlap(F, t, alpha, tol, P1,P2,P3,P4,P5,P6,P7,P8,P9);
%
% F laplace-space function (string refering to an m-file),
% must have form F(s, P1,..,P9), where s is the Laplace parameter,
% and return column vector as result
% t column vector of times for which real-space function values are
% sought
% alpha largest pole of F (default zero)
% tol numerical tolerance of approaching pole (default 1e-9)
% P1-P9 optional parameters to be passed on to F
% f vector of real-space values f(t)
%
% example: identity function in Laplace space:
% function F = identity(s); % save these two lines
% F = 1./(s.^2); % ... as "identity.m"
% invlap('identity', [1;2;3]) % gives [1;2;3]
%
% algorithm: de Hoog et al's quotient difference method with accelerated
% convergence for the continued fraction expansion
% [de Hoog, F. R., Knight, J. H., and Stokes, A. N. (1982). An improved
% method for numerical inversion of Laplace transforms. S.I.A.M. J. Sci.
% and Stat. Comput., 3, 357-366.]
% Modification: The time vector is split in segments of equal magnitude
% which are inverted individually. This gives a better overall accuracy.
% details: de Hoog et al's algorithm f4 with modifications (T->2*T and
% introduction of tol). Corrected error in formulation of z.
%
% Copyright: Karl Hollenbeck
% Department of Hydrodynamics and Water Resources
% Technical University of Denmark, DK-2800 Lyngby
% email: karl@isv16.isva.dtu.dk
% 22 Nov 1996, MATLAB 5 version 27 Jun 1997 updated 1 Oct 1998
% IF YOU PUBLISH WORK BENEFITING FROM THIS M-FILE, PLEASE CITE IT AS:
% Hollenbeck, K. J. (1998) INVLAP.M: A matlab function for numerical
% inversion of Laplace transforms by the de Hoog algorithm,
% http://www.isva.dtu.dk/staff/karl/invlap.htm
    function f = invlap(F, t, alpha, tol)
        if nargin <= 2
            alpha = 0;
        elseif isempty(alpha)
            alpha = 0;
        end
        if nargin <= 3
            tol = 1e-9;
        elseif isempty(tol)
            tol = 1e-9;
        end
        f = [];
        % split up t vector in pieces of same order of magnitude, invert one piece
        % at a time. simultaneous inversion for times covering several orders of
        % magnitudes gives inaccurate results for the small times.
        allt = t; % save full times vector
        logallt = log10(allt);
        iminlogallt = floor(min(logallt));
        imaxlogallt = ceil(max(logallt));
        for ilogt = iminlogallt:imaxlogallt % loop through all pieces
            t = allt(find((logallt>=ilogt) & (logallt<(ilogt+1))));
            if ~isempty(t) % maybe no elements in that magnitude
                T = max(t)*2;
                gamma = alpha-log(tol)/(2*T);
                % NOTE: The correction alpha -> alpha-log(tol)/(2*T) is not in de Hoog's
                % paper, but in Mathematica's Mathsource (NLapInv.m) implementation of
                % inverse transforms
                nt = length(t);
                M = 20;
                run = 0:1:2*M; % so there are 2M+1 terms in Fourier seriesexpansion
                run = run';
                % find F argument, call F with it, get 'a' coefficients in power series
                s = gamma + 1i*pi*run/T;
%                 command = ['a = ' F '(s'];
%                 if nargin > 4 % pass on parameters
%                     for iarg = 1:nargin-4
%                         command = [command ',P' int2str(iarg)];
%                     end
%                 end
%                 command = [command ');'];
%                 eval(command); %%This whole sections was a really clever
%                 way of passing parameters to the function, but we don't
%                 really need it, so I got rid of it for speed and
%                 effeciency-Ryan 
                a = eval([F '(s)']);

                a(1) = a(1)/2; % zero term is halved
                % build up e and q tables. superscript is now row index, subscript column
                % CAREFUL: paper uses null index, so all indeces are shifted by 1 here
                e = zeros(2*M+1, M+1);
                q = zeros(2*M , M+1); % column 0 (here: 1) does not exist
                e(:,1) = zeros(2*M+1,1);
                q(:,2) = a(2:2*M+1,1)./a(1:2*M,1);
                for r = 2:M+1 % step through columns (called r...)
                    e(1:2*(M-r+1)+1,r) = ...
                        q(2:2*(M-r+1)+2,r) - q(1:2*(M-r+1)+1,r) + e(2:2*(M-r+1)+2,r-1);
                    if r<M+1 % one column fewer for q
                        rq = r+1;
                        q(1:2*(M-rq+1)+2,rq) = ...
                            q(2:2*(M-rq+1)+3,rq-1).*e(2:2*(M-rq+1)+3,rq-1)./e(1:2*(M-rq+1)+2,rq-1);
                    end
                end
                % build up d vector (index shift: 1)
                d = zeros(2*M+1,1);
                d(1,1) = a(1,1);
                d(2:2:2*M,1) = -q(1,2:M+1).'; % these 2 lines changed after niclas
                d(3:2:2*M+1,1) = -e(1,2:M+1).'; % ...
                % build up A and B vectors (index shift: 2)
                % - now make into matrices, one row for each time
                A = zeros(2*M+2,nt);
                B = zeros(2*M+2,nt);
                A(2,:) = d(1,1)*ones(1,nt);
                B(1:2,:) = ones(2,nt);
                z = exp(1i*pi*t'/T); % row vector
                % after niclas back to the paper (not: z = exp(-i*pi*t/T)) !!!
                for n = 3:2*M+2
                    A(n,:) = A(n-1,:) + d(n-1,1)*ones(1,nt).*z.*A(n-2,:); % different index
                    B(n,:) = B(n-1,:) + d(n-1,1)*ones(1,nt).*z.*B(n-2,:); % shift for d!
                end
                % double acceleration
                h2M = .5 * ( ones(1,nt) + ( d(2*M,1)-d(2*M+1,1) )*ones(1,nt).*z );
                R2Mz = -h2M.*(ones(1,nt) - ...
                    (ones(1,nt)+d(2*M+1,1)*ones(1,nt).*z/(h2M).^2).^.5);
                A(2*M+2,:) = A(2*M+1,:) + R2Mz .* A(2*M,:);
                B(2*M+2,:) = B(2*M+1,:) + R2Mz .* B(2*M,:);
                % inversion, vectorized for times, make result a column vector
                fpiece = ( 1/T * exp(gamma*t') .* real(A(2*M+2,:)./B(2*M+2,:)) )';
                f = [f; fpiece]; % put pieces together
            end % if not empty time piece
        end % loop through time vector pieces
    end
%Original properties
%Needle probe - Thermal contact resistance - Sample - Convection

    function F = identity(s)

        k_eff_wire = par_vector(1);
        alpha_eff_wire = par_vector(2);
        k_insulation = par_vector(3);
        alpha_insulation = par_vector(4);
        RthInsShth = par_vector(5);
        k_sheath = par_vector(6);
        alpha_sheath = par_vector(7);
        ksample = par_vector(8);
        alphasample = par_vector(9);
        kcrucible = par_vector(10);
        alphacrucible = par_vector(11);
        emissivity1 = par_vector(12);
        emissivity2 = par_vector(13);
        index = par_vector(14);
        scatter = par_vector(15);
        T0 = par_vector(16);
        V = par_vector(17);
        Resistance = par_vector(18);
        rwires = par_vector(19);
        rsheath_inner = par_vector(20);
        rsheath = par_vector(21);
        rsample = par_vector(22);
        rcrucible = par_vector(23);
        L = par_vector(24);
        h_convec = par_vector(25);
        rhosample = par_vector(26);
        cpsample = abs(par_vector(27));
        rhocp = abs(par_vector(28));
        I = par_vector(29);

        if cp == 1
            alphasample = ksample/(rhosample*cpsample);
        elseif cp == 2
            alphasample = ksample/rhocp;
        end

        area_convection=2*pi*rcrucible*L;   %outer crucible surface area [m^2]

        if IV == 1
            Q0 = V*I;   % If we recorded data on current 
        else
            Q0 = (V^2) / Resistance; %power [W]
        end

        %Area_wires = 2*pi*rwires*L;
        Area_sheath = 2*pi*rsheath*L;
        %Area_sample = 2*pi*rsample*L;
        Boltzmann = 5.670374419e-8;

        R_dimensional = ((1/emissivity1)+((1/emissivity2)-1)*(rsheath/rsample)+scatter*(rsample-rsheath)*(rsheath/rsample))/(4*(index^2)*Boltzmann*(T0^3)*Area_sheath); %multiply scatter by rsheath/rsample?


        q1=rwires.*sqrt(s/alpha_eff_wire);          %alpha1 for effective wire layer (material 1)

        q21=rwires.*sqrt(s/alpha_insulation);       %alpha1 for insulation (material 2)
        q22=rsheath_inner.*sqrt(s/alpha_insulation);%alpha2 for insulation (material 2)

        q31=rsheath_inner.*sqrt(s/alpha_sheath);    %alpha2 for sheath (material 3)
        q32=rsheath.*sqrt(s/alpha_sheath);          %alpha1 for sheath (material 3)

        q41=rsheath.*sqrt(s/alphasample);           %alpha2 for sample (material 4)
        q42=rsample.*sqrt(s/alphasample);           %alpha1 for sample (material 4)

        q51=rsample.*sqrt(s/alphacrucible);         %alpha2 for crucible (material 5)
        q52=rcrucible.*sqrt(s/alphacrucible);       %alpha1 for crucible (material 5)

        % Effective wire layer
        A1=1;
        B1=(1/(2.*pi.*k_eff_wire.*L)).*besseli(0,q1)./(q1.*besseli(1,q1))-1./((k_eff_wire/alpha_eff_wire).*pi.*L*(rwires^2).*s);
        C1=((k_eff_wire/alpha_eff_wire).*pi.*L*rwires^2.*s);
        D1=(q1./2).*besseli(0,q1)./besseli(1,q1);

        % Insulation
        A2=q21.*((besseli(0,q21).*besselk(1,q22))+(besseli(1,q22).*besselk(0,q21)));
        B2=(1/(2.*pi.*k_insulation.*L)).*((besseli(0,q22).*besselk(0,q21))-(besseli(0,q21).*besselk(0,q22)));
        C2=2.*pi.*k_insulation.*L.*q21.*q22.*((besseli(1,q22).*besselk(1,q21))-(besseli(1,q21).*besselk(1,q22)));
        D2=q21.*((besseli(0,q22).*besselk(1,q21))+(besseli(1,q21).*besselk(0,q22)));

        % Thermal contact resistance (already accounted for in equation)
        %A_23=1;
        %B_23= RthInsShth;
        %C_23=0;
        %D_23=1;
        
        % Sheath
        A3=q31.*((besseli(0,q31).*besselk(1,q32))+(besseli(1,q32).*besselk(0,q31)));
        B3=(1/(2.*pi.*k_sheath.*L)).*((besseli(0,q32).*besselk(0,q31))-(besseli(0,q31).*besselk(0,q32)));
        C3=2.*pi.*k_sheath.*L.*q31.*q32.*((besseli(1,q32).*besselk(1,q31))-(besseli(1,q31).*besselk(1,q32)));
        D3=q31.*((besseli(0,q32).*besselk(1,q31))+(besseli(1,q31).*besselk(0,q32)));

        % Sample
        A4_c=q41.*((besseli(0,q41).*besselk(1,q42))+(besseli(1,q42).*besselk(0,q41)));
        B4_c=(1/(2.*pi.*ksample.*L)).*((besseli(0,q42).*besselk(0,q41))-(besseli(0,q41).*besselk(0,q42)));
        C4_c=2.*pi.*ksample.*L.*q41.*q42.*((besseli(1,q42).*besselk(1,q41))-(besseli(1,q41).*besselk(1,q42)));
        D4_c=q41.*((besseli(0,q42).*besselk(1,q41))+(besseli(1,q41).*besselk(0,q42)));
        %non-symmetric, so A4 (planar) becomes D4 (cylindrical)
        A4 = (B4_c + R_dimensional.*A4_c)./(B4_c + R_dimensional);
        B4 = (B4_c.*R_dimensional)./(B4_c + R_dimensional);
        C4 = (A4_c + D4_c + R_dimensional.*C4_c - 2)./(B4_c + R_dimensional);
        D4 = (B4_c + R_dimensional.*D4_c)./(B4_c + R_dimensional); 
        
        % Crucible
        A5=q51.*((besseli(0,q51).*besselk(1,q52))+(besseli(1,q52).*besselk(0,q51)));
        B5=(1/(2.*pi.*kcrucible.*L)).*((besseli(0,q52).*besselk(0,q51))-(besseli(0,q51).*besselk(0,q52)));
        C5=2.*pi.*kcrucible.*L.*q51.*q52.*((besseli(1,q52).*besselk(1,q51))-(besseli(1,q51).*besselk(1,q52)));
        D5=q51.*((besseli(0,q52).*besselk(1,q51))+(besseli(1,q51).*besselk(0,q52)));

        % Convection (already accounted for
        %A_convection=1;
        %B_convection=0;
        C_convection=h_convec*area_convection;
        %D_convection=1;

        theta1 = (Q0./s).* (C_convection.*B5.*A4.*C3.*RthInsShth.*A1.*A2+C_convection.*B5.*A4.*C3.*RthInsShth.*B1.*C2+C_convection.*B5.*C4.*D3.*RthInsShth.*A1.*A2+C_convection.*B5.*C4.*D3.*RthInsShth.*B1.*C2+C_convection.*D5.*B4.*C3.*RthInsShth.*A1.*A2+C_convection.*D5.*B4.*C3.*RthInsShth.*B1.*C2+C_convection.*D5.*D4.*D3.*RthInsShth.*A1.*A2+C_convection.*D5.*D4.*D3.*RthInsShth.*B1.*C2+A5.*A4.*C3.*RthInsShth.*A1.*A2+A5.*A4.*C3.*RthInsShth.*B1.*C2+A5.*C4.*D3.*RthInsShth.*A1.*A2+A5.*C4.*D3.*RthInsShth.*B1.*C2+C5.*B4.*C3.*RthInsShth.*A1.*A2+C5.*B4.*C3.*RthInsShth.*B1.*C2+C5.*D4.*D3.*RthInsShth.*A1.*A2+C5.*D4.*D3.*RthInsShth.*B1.*C2+C_convection.*B5.*C4.*B3.*B1.*C2+C_convection.*B5.*C4.*D3.*A1.*B2+C_convection.*B5.*C4.*D3.*B1.*D2+C_convection.*D5.*B4.*A3.*A1.*A2+C_convection.*D5.*B4.*A3.*B1.*C2+C_convection.*D5.*B4.*C3.*A1.*B2+C_convection.*D5.*B4.*C3.*B1.*D2+C_convection.*D5.*D4.*B3.*A1.*A2+C_convection.*D5.*D4.*B3.*B1.*C2+C_convection.*D5.*D4.*D3.*A1.*B2+C_convection.*D5.*D4.*D3.*B1.*D2+C_convection.*B5.*A4.*A3.*A1.*A2+C_convection.*B5.*A4.*A3.*B1.*C2+C_convection.*B5.*A4.*C3.*A1.*B2+C_convection.*B5.*A4.*C3.*B1.*D2+C_convection.*B5.*C4.*B3.*A1.*A2+A5.*A4.*A3.*A1.*A2+A5.*A4.*A3.*B1.*C2+A5.*A4.*C3.*A1.*B2+A5.*A4.*C3.*B1.*D2+A5.*C4.*B3.*A1.*A2+A5.*C4.*B3.*B1.*C2+A5.*C4.*D3.*A1.*B2+A5.*C4.*D3.*B1.*D2+C5.*B4.*A3.*A1.*A2+C5.*B4.*A3.*B1.*C2+C5.*B4.*C3.*A1.*B2+C5.*B4.*C3.*B1.*D2+C5.*D4.*B3.*A1.*A2+C5.*D4.*B3.*B1.*C2+C5.*D4.*D3.*A1.*B2+C5.*D4.*D3.*B1.*D2)./(C_convection.*B5.*A4.*A3.*C1.*A2+C_convection.*B5.*A4.*A3.*D1.*C2+C_convection.*B5.*A4.*C3.*C1.*B2+C_convection.*B5.*A4.*C3.*D1.*D2+C_convection.*B5.*C4.*B3.*C1.*A2+C_convection.*B5.*C4.*B3.*D1.*C2+C_convection.*B5.*C4.*D3.*C1.*B2+C_convection.*B5.*C4.*D3.*D1.*D2+C_convection.*D5.*B4.*A3.*C1.*A2+C_convection.*D5.*B4.*A3.*D1.*C2+C_convection.*D5.*B4.*C3.*C1.*B2+C_convection.*D5.*B4.*C3.*D1.*D2+C_convection.*D5.*D4.*B3.*C1.*A2+C_convection.*D5.*D4.*B3.*D1.*C2+C_convection.*D5.*D4.*D3.*C1.*B2+C_convection.*D5.*D4.*D3.*D1.*D2+C_convection.*B5.*A4.*C3.*RthInsShth.*C1.*A2+C_convection.*B5.*A4.*C3.*RthInsShth.*D1.*C2+C_convection.*B5.*C4.*D3.*RthInsShth.*C1.*A2+C_convection.*B5.*C4.*D3.*RthInsShth.*D1.*C2+C_convection.*D5.*B4.*C3.*RthInsShth.*C1.*A2+C_convection.*D5.*B4.*C3.*RthInsShth.*D1.*C2+C_convection.*D5.*D4.*D3.*RthInsShth.*C1.*A2+C_convection.*D5.*D4.*D3.*RthInsShth.*D1.*C2+A5.*A4.*A3.*C1.*A2+A5.*A4.*A3.*D1.*C2+A5.*A4.*C3.*C1.*B2+A5.*A4.*C3.*D1.*D2+A5.*C4.*B3.*C1.*A2+A5.*C4.*B3.*D1.*C2+A5.*C4.*D3.*C1.*B2+A5.*C4.*D3.*D1.*D2+C5.*B4.*A3.*C1.*A2+C5.*B4.*A3.*D1.*C2+C5.*B4.*C3.*C1.*B2+C5.*B4.*C3.*D1.*D2+C5.*D4.*B3.*C1.*A2+C5.*D4.*B3.*D1.*C2+C5.*D4.*D3.*C1.*B2+C5.*D4.*D3.*D1.*D2+A5.*A4.*C3.*RthInsShth.*C1.*A2+A5.*A4.*C3.*RthInsShth.*D1.*C2+A5.*C4.*D3.*RthInsShth.*C1.*A2+A5.*C4.*D3.*RthInsShth.*D1.*C2+C5.*B4.*C3.*RthInsShth.*C1.*A2+C5.*B4.*C3.*RthInsShth.*D1.*C2+C5.*D4.*D3.*RthInsShth.*C1.*A2+C5.*D4.*D3.*RthInsShth.*D1.*C2);        
        
        F = theta1;
    end
end