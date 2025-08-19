% Existing table
T = table([1; 2], [10; 20], 'VariableNames', {'Var1', 'Var2'});

% Display existing table
disp('Existing Table:');
disp(T);

% New data to be added
newData = table([3; 4], [30; 40], 'VariableNames', {'Var1', 'Var2'});

% Display new data
disp('New Data:');
disp(newData);

% Append new rows to the existing table
T = [T; newData];

% Display updated table
disp('Updated Table:');
disp(T);
