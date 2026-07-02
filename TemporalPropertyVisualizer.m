clear

time = (0.00001:0.01:120)'; %linspace(0.02,40,4000);

[par_vector,par_names] = Properties("3A-IN718-01","Inconel625","MgNaCl",700,2.8,0,0.37,0,0);

par_test_list = [1,3,6,8,10];

figure;
for j = 1:length(par_test_list)
    parameter_varied = par_test_list(j);
    test_list = par_vector(parameter_varied) * (0.5:0.05:1.5);
    
    init_response = NeedleProbeModel(time,par_vector,1);
    temp_responses = zeros(length(test_list),length(time));
    diff_responses = zeros(length(test_list),length(time));
    % sum_diff = zeros(1,length(time));
    
    for i = 1:length(test_list)
        par_vector(parameter_varied) = test_list(i);
        result = NeedleProbeModel(time,par_vector,1);
        temp_responses(i,:) = result;
        diff_result_percent = (result - init_response)./init_response;
        diff_responses(i,:) = diff_result_percent;
        % sum_diff = sum_diff + abs(diff_responses(i,:));
    end
    % one_perc_reached = find(sum_diff > 0.01, 1 );
    [~,one_perc_reached] = find(diff_responses > 0.01, 1, "first");
    subplot(length(par_test_list),1,j)
    plot(time,diff_responses)
    if ~isempty(one_perc_reached)
        xline(time(one_perc_reached),'-',string(time(one_perc_reached)))
    end
    ylabel("Percent Difference"+newline+"from Nominal")
    xlabel("Time")
    xscale("log")
   
    title(par_names(parameter_varied,1))
end