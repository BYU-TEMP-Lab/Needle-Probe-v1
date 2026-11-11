function chi2multi=Chi2Multi(fitparam,fixparam,Ifitpar,Ifixpar,Sstart,signal_array,manual_delay,iplotfit,IV)

    total_chi2 = 0;
    
    for signal_num = size(signal_array,2)
        
        chi2_iter = Chi2(fitparam,fixparam,Ifitpar,Ifixpar,Sstart,signal_array(signal_num),manual_delay,iplotfit,IV);
        
        total_chi2 = total_chi2 + chi2_iter;
    end
    
    chi2multi = total_chi2;

end