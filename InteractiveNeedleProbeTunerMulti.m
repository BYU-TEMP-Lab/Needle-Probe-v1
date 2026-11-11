function InteractiveNeedleProbeTunerMulti()
% INTERACTIVENEEDLEPROBETUNERMULTI
% Interactive GUI for selecting experimental needle probe files, plotting
% the analytical quadrupole model (MatrixNeedleProbeModel / ChatNeedleProbeModel)
% over experimental data, and live-tuning all 34 parameters from Properties.m
% via paired sliders, manual numeric entry boxes, live percent-difference
% boxes, individual reset buttons, and horizontal row dividers.

    clc;
    close all;
    fclose all;

    currentFOLDER = pwd;
    todayStr = char(datetime('now', 'Format', 'MM,dd,yy,HH-mm'));

    %% --- STEP 0: Experimental Configuration Menus ---
    % Matches configuration workflow from PropertyFitting.m
    m_test = menu('Calibration or Sample Test?', ...
        'Probe Calibration (0.01 - 7 s)', ...
        'Heat and Cool (0.1 - 180 s)', ...
        'Sample Test (0.01 - 60 s)', ...
        'Cancel');
    switch m_test
        case 1, timewindow = [0.01, 7];
        case 2, timewindow = [0.1, 180];
        case 3, timewindow = [0.01, 60];
        otherwise
            disp('No test type selected. Program terminated.');
            return;
    end

    probeList = {'2A-SS-03', '2A-SS-04', '3A-IN718-01', 'INL'};
    m_probe = menu('Select Probe:', [probeList, {'Cancel'}]);
    if m_probe < 1 || m_probe > numel(probeList)
        disp('No probe selected. Program terminated.');
        return;
    end
    probe = probeList{m_probe};

    crucibleList = {'Steel316', 'Nickel200', 'Inconel625'};
    m_cruc = menu('Select Crucible Material:', [crucibleList, {'Cancel'}]);
    if m_cruc < 1 || m_cruc > numel(crucibleList)
        disp('No crucible selected. Program terminated.');
        return;
    end
    crucible = crucibleList{m_cruc};

    sampleMenuLabels = { ...
        'H2O', 'NaNO3', 'Toluene', 'KNO3', 'Propylene Glycol', ...
        'FLiNaK', 'FLiBe', 'FMgNaK', 'LiCl-KCl', 'NaCl-KCl', ...
        'LiF-NaF', 'LiCl-NaCl', 'ZnCl-KCl', 'NaNO3-KNO3', ...
        '1npNaNO3-KNO3', 'Ar', 'MgNaCl'};
    sampleInternalNames = { ...
        'H2O', 'NaNO3', 'Toluene', 'KNO3', 'PropyleneGlycol', ...
        'FLiNaK', 'FLiBe', 'FMgNaK', 'LiCl-KCl', 'NaCl-KCl', ...
        'LiF-NaF', 'LiCl-NaCl', 'KCl-ZnCl', 'NaNO3-KNO3', ...
        '1npNaNO3-KNO3-T1', 'Ar', 'MgNaCl'};
    m_samp = menu('Select Sample Material:', [sampleMenuLabels, {'Cancel'}]);
    if m_samp < 1 || m_samp > numel(sampleInternalNames)
        disp('No sample selected. Program terminated.');
        return;
    end
    sample = sampleInternalNames{m_samp};

    %% --- STEPS 1 & 2: Select Directory via uigetdir & Process with ExtractData ---
    run_name = [sample ' ' probe ' ' crucible ' ' todayStr '_ManualTune'];
    runfolder = fullfile(currentFOLDER, 'Analysis_Results', run_name);
    if ~exist(runfolder, 'dir')
        mkdir(runfolder);
    end

    raw_plot = 0;
    [~, datafolderUSE, aveTemp_vector, ~] = ExtractData(raw_plot, runfolder, timewindow);
    cd(currentFOLDER);

    % Gather processed files in the exact order ExtractData created them
    dirEntries = dir(datafolderUSE);
    fileEntries = dirEntries(~[dirEntries.isdir]); % Preserve dir() ordering
    if isempty(fileEntries)
        errordlg('No processed data files were found in the Useable Data folder.', 'No Files Found');
        return;
    end
    fileNames = {fileEntries.name};
    if numel(aveTemp_vector) ~= numel(fileNames)
        error('NeedleProbeTuner:FileCount', ...
            'Processed files do not match the temperatures returned by ExtractData.');
    end

    %% --- STEP 3: Select the Initial Active Files ---
    [selectedIdx, ok] = listdlg( ...
        'PromptString', 'Select one or more processed files to view and tune:', ...
        'SelectionMode', 'multiple', ...
        'ListSize', [420, 300], ...
        'ListString', fileNames);

    if ~ok || isempty(selectedIdx)
        disp('No file selected. Program terminated.');
        return;
    end

    %% --- File Cache and Persistent Shared Parameter Overrides ---
    appState = struct();
    appState.runfolder = runfolder;
    appState.run_name = run_name;
    appState.datafolderUSE = datafolderUSE;
    appState.fileNames = fileNames;
    appState.aveTemp_vector = aveTemp_vector;
    appState.probe = probe;
    appState.crucible = crucible;
    appState.sample = sample;
    appState.currentFileIdx = selectedIdx(1);
    appState.activeFileIdx = selectedIdx(:)';
    appState.multiView = numel(selectedIdx) > 1;
    appState.separateMainPlots = false;
    appState.separateResPlots = false;
    appState.layoutDirty = true;
    appState.coupleAlphaSample = false;
    appState.alphaBasis = 'rhoCp';
    appState.files = cell(1, numel(fileNames));

    firstFile = getFile(appState.currentFileIdx);
    appState.par_init = firstFile.par_init;
    appState.par_current = firstFile.par_init;
    appState.par_names = firstFile.par_names;
    numParams = numel(appState.par_init);
    appState.overrideMask = false(1, numParams);
    appState.overrideValues = appState.par_init;

    %% --- STEPS 4 & 5: Build Interactive UIFigure with Plot & 34 Controls ---
    fig = uifigure('Name', ['Needle Probe Multi-File Parameter Tuner - ' run_name], ...
        'Position', [40, 50, 1560, 860], 'Visible', 'off');

    try
        % Main 1x2 layout: Left = Plots + Top Bar, Right = Scrollable Parameter Controls
        mainGrid = uigridlayout(fig, [1, 2]);
        mainGrid.ColumnWidth = {'1.25x', '1x'};
        mainGrid.RowHeight = {'1x'};
        mainGrid.Padding = [10, 10, 10, 10];
        mainGrid.ColumnSpacing = 12;

        % --- LEFT COLUMN: Controls Bar + Plots ---
        leftGrid = uigridlayout(mainGrid, [3, 1]);
        leftGrid.Layout.Row = 1;
        leftGrid.Layout.Column = 1;
        leftGrid.RowHeight = {116, '2.2x', '1x'};
        leftGrid.Padding = [0, 0, 0, 0];
        leftGrid.RowSpacing = 8;

        % Toolbar: control file, multi-file view options, and tuning tools
        topBar = uigridlayout(leftGrid, [3, 6]);
        topBar.Layout.Row = 1;
        topBar.Layout.Column = 1;
        topBar.ColumnWidth = {'fit', 'fit', 'fit', '1x', 'fit', 'fit'};
        topBar.RowHeight = {28, 28, 28};
        topBar.Padding = [4, 4, 4, 4];
        topBar.RowSpacing = 6;

        fileLabel = uilabel(topBar, 'Text', 'Control file:', 'FontWeight', 'bold');
        fileLabel.Layout.Row = 1;
        fileLabel.Layout.Column = 1;
        fileDropdown = uidropdown(topBar, ...
            'Items', fileNames, 'ItemsData', 1:numel(fileNames), ...
            'Value', appState.currentFileIdx, ...
            'Tooltip', 'Select the single-view file or the active file whose parameter defaults are shown', ...
            'ValueChangedFcn', @(dd, ~) onFileChanged(dd.Value));
        fileDropdown.Layout.Row = 1;
        fileDropdown.Layout.Column = [2, 6];

        multiCheckbox = uicheckbox(topBar, 'Text', 'Multiple files', ...
            'Value', appState.multiView, ...
            'Tooltip', 'Toggle between the control file and the remembered active files; tuning persists', ...
            'ValueChangedFcn', @(cb, ~) onViewChanged(cb.Value));
        multiCheckbox.Layout.Row = 2;
        multiCheckbox.Layout.Column = 1;

        separateMainCheckbox = uicheckbox(topBar, 'Text', 'Separate data plots', ...
            'Value', appState.separateMainPlots, ...
            'Enable', onOff(appState.multiView), ...
            'Tooltip', 'Show each active file''s temperature response in its own subplot using single-file colors', ...
            'ValueChangedFcn', @(cb, ~) onSeparateMainChanged(cb.Value));
        separateMainCheckbox.Layout.Row = 2;
        separateMainCheckbox.Layout.Column = 2;

        separateResCheckbox = uicheckbox(topBar, 'Text', 'Separate residual plots', ...
            'Value', appState.separateResPlots, ...
            'Enable', onOff(appState.multiView), ...
            'Tooltip', 'Show each active file''s residuals in its own subplot instead of the pooled mean residual plot', ...
            'ValueChangedFcn', @(cb, ~) onSeparateResChanged(cb.Value));
        separateResCheckbox.Layout.Row = 2;
        separateResCheckbox.Layout.Column = 3;

        activeLabel = uilabel(topBar, 'Text', '', 'HorizontalAlignment', 'right');
        activeLabel.Layout.Row = 2;
        activeLabel.Layout.Column = 4;

        chooseButton = uibutton(topBar, 'Text', 'Choose files...', ...
            'ButtonPushedFcn', @(~, ~) onChooseFiles());
        chooseButton.Layout.Row = 2;
        chooseButton.Layout.Column = [5, 6];

        scaleCheckbox = uicheckbox(topBar, 'Text', 'Log Time Axis', ...
            'Value', true, 'ValueChangedFcn', @(cb, ~) onScaleChanged(cb.Value));
        scaleCheckbox.Layout.Row = 3;
        scaleCheckbox.Layout.Column = 1;

        coupleCheckbox = uicheckbox(topBar, 'Text', 'Couple alpha = k/(rho Cp)', ...
            'Value', false, ...
            'Tooltip', 'Recalculate sample diffusivity for each file when sample properties change', ...
            'ValueChangedFcn', @(cb, ~) onCoupleChanged(cb.Value));
        coupleCheckbox.Layout.Row = 3;
        coupleCheckbox.Layout.Column = [2, 4];

        resetButton = uibutton(topBar, 'Text', 'Reset All', ...
            'Tooltip', 'Release all shared overrides and restore each file''s Properties.m values', ...
            'ButtonPushedFcn', @(~, ~) onResetAll());
        resetButton.Layout.Row = 3;
        resetButton.Layout.Column = 5;

        exportButton = uibutton(topBar, 'Text', 'Export par_vector', ...
            'Tooltip', 'Save changed parameters and tuned parameter vectors to new files in the ManualTune folder and MATLAB workspace', ...
            'ButtonPushedFcn', @(~, ~) onExportParams());
        exportButton.Layout.Row = 3;
        exportButton.Layout.Column = 6;

        % Containers for Main Response Plot(s) and Residual Plot(s)
        mainPlotPanel = uipanel(leftGrid, 'BorderType', 'none');
        mainPlotPanel.Layout.Row = 2;
        mainPlotPanel.Layout.Column = 1;

        resPlotPanel = uipanel(leftGrid, 'BorderType', 'none');
        resPlotPanel.Layout.Row = 3;
        resPlotPanel.Layout.Column = 1;

        axMainList = gobjects(0);
        axResList = gobjects(0);
        hExp = gobjects(0);
        hInit = gobjects(0);
        hLive = gobjects(0);
        hResInit = gobjects(0);
        hResLive = gobjects(0);

        % --- RIGHT COLUMN: Scrollable Panel for All 34 Parameters ---
        rightPanel = uipanel(mainGrid, ...
            'Title', 'Shared Tuned Values (% Diff from Control File Defaults)', ...
            'FontWeight', 'bold', ...
            'Scrollable', 'on');
        rightPanel.Layout.Row = 1;
        rightPanel.Layout.Column = 2;

        % Interleave parameter rows (38 px) with 1 px horizontal divider rows
        totalGridRows = 2 * numParams - 1;
        rowHeights = repmat({38, 1}, 1, numParams - 1);
        rowHeights{end + 1} = 38;

        % 5 Columns: [Label | Slider | Manual Edit Box | % Diff Box | Individual Reset Button]
        paramGrid = uigridlayout(rightPanel, [totalGridRows, 5]);
        paramGrid.RowHeight = rowHeights;
        paramGrid.ColumnWidth = {'1.15x', '1.25x', 95, 80, 52};
        paramGrid.RowSpacing = 5;
        paramGrid.ColumnSpacing = 8;
        paramGrid.Padding = [10, 10, 25, 10];
        paramGrid.Scrollable = 'on';

        labels = gobjects(numParams, 1);
        sliders = gobjects(numParams, 1);
        editBoxes = gobjects(numParams, 1);
        pctBoxes = gobjects(numParams, 1);
        resetBtns = gobjects(numParams, 1);

        for idx = 1:numParams
            controlRow = 2 * idx - 1;

            rawName = strrep(char(appState.par_names(idx, 1)), '\_', '_');
            rawUnit = strrep(char(appState.par_names(idx, 2)), '\_', '_');
            labelStr = sprintf('%2d. %s [%s]', idx, rawName, rawUnit);

            val0 = appState.par_init(idx);
            lims = getInitialSliderLimits(val0, idx);

            % 1. Parameter Label
            lbl = uilabel(paramGrid, ...
                'Text', labelStr, ...
                'Interpreter', 'none', ...
                'FontSize', 11, ...
                'Tooltip', sprintf('Initial value: %.6g %s', val0, rawUnit));
            lbl.Layout.Row = controlRow;
            lbl.Layout.Column = 1;
            labels(idx) = lbl;

            % 2. Parameter Slider
            sld = uislider(paramGrid, ...
                'Limits', lims, ...
                'Value', val0, ...
                'MajorTicks', linspace(lims(1), lims(2), 3), ...
                'MinorTicks', [], ...
                'ValueChangedFcn', @(s, ~) onParamUpdated(idx, s.Value, 'slider'));
            sld.Layout.Row = controlRow;
            sld.Layout.Column = 2;
            sliders(idx) = sld;

            % 3. Manual Numeric Entry Box
            edt = uieditfield(paramGrid, 'numeric', ...
                'Value', val0, ...
                'ValueDisplayFormat', '%.6g', ...
                'Tooltip', 'Set a shared value for every file (slider limits auto-expand); Reset restores file defaults', ...
                'ValueChangedFcn', @(e, ~) onParamUpdated(idx, e.Value, 'edit'));
            edt.Layout.Row = controlRow;
            edt.Layout.Column = 3;
            editBoxes(idx) = edt;

            % 4. Percent Difference Display Box
            pctBox = uieditfield(paramGrid, 'text', ...
                'Value', '0.00%', ...
                'Editable', 'off', ...
                'HorizontalAlignment', 'center', ...
                'FontSize', 11, ...
                'BackgroundColor', [0.96, 0.96, 0.96], ...
                'Tooltip', 'Percent difference from initial Properties.m value');
            pctBox.Layout.Row = controlRow;
            pctBox.Layout.Column = 4;
            pctBoxes(idx) = pctBox;

            % 5. Individual Parameter Reset Button
            rstBtn = uibutton(paramGrid, ...
                'Text', 'Reset', ...
                'FontSize', 10, ...
                'Tooltip', sprintf('Reset %s to %.6g %s', rawName, val0, rawUnit), ...
                'ButtonPushedFcn', @(~, ~) onResetSingle(idx));
            rstBtn.Layout.Row = controlRow;
            rstBtn.Layout.Column = 5;
            resetBtns(idx) = rstBtn;

            % 6. Horizontal Divider Line between parameters (spans all 5 columns)
            if idx < numParams
                dividerLine = uipanel(paramGrid, ...
                    'BorderType', 'none', ...
                    'BackgroundColor', [0.72, 0.72, 0.72]);
                dividerLine.Layout.Row = controlRow + 1;
                dividerLine.Layout.Column = [1, 5];
            end
        end

        updateFileSelector();
        refreshControls();
        recomputeAndPlot();
        fig.Visible = 'on';
    catch initializationError
        if isgraphics(fig)
            delete(fig);
        end
        rethrow(initializationError);
    end

    %% --- Nested Callback & Helper Functions ---

    function onParamUpdated(paramIdx, newValue, sourceType)
        if ~isfinite(newValue)
            editBoxes(paramIdx).Value = appState.par_current(paramIdx);
            return;
        end

        appState.par_current(paramIdx) = newValue;
        appState.overrideMask(paramIdx) = true;
        appState.overrideValues(paramIdx) = newValue;

        if strcmp(sourceType, 'edit')
            currLims = sliders(paramIdx).Limits;
            if newValue < currLims(1) || newValue > currLims(2)
                newLims = expandSliderLimits(currLims, newValue);
                sliders(paramIdx).Limits = newLims;
                sliders(paramIdx).MajorTicks = linspace(newLims(1), newLims(2), 3);
            end
            sliders(paramIdx).Value = newValue;
        else
            editBoxes(paramIdx).Value = newValue;
        end

        updatePctBox(paramIdx);
        applySampleAlphaCoupling(paramIdx);
        recomputeAndPlot();
    end

    function onResetSingle(paramIdx)
        appState.overrideMask(paramIdx) = false;
        applySampleAlphaCoupling(paramIdx);
        refreshControls();
        recomputeAndPlot();
    end

    function updatePctBox(idx)
        val0 = appState.par_init(idx);
        valCurr = appState.par_current(idx);

        if val0 == 0
            if abs(valCurr) < 1e-15
                pctBoxes(idx).Value = '0.00%';
                pctBoxes(idx).FontWeight = 'normal';
                pctBoxes(idx).BackgroundColor = [0.96, 0.96, 0.96];
            else
                pctBoxes(idx).Value = 'N/A (0 init)';
                pctBoxes(idx).FontWeight = 'bold';
                pctBoxes(idx).BackgroundColor = [1.0, 0.95, 0.85];
            end
        else
            pctDiff = ((valCurr - val0) / abs(val0)) * 100;
            if abs(pctDiff) < 1e-9
                pctBoxes(idx).Value = '0.00%';
                pctBoxes(idx).FontWeight = 'normal';
                pctBoxes(idx).BackgroundColor = [0.96, 0.96, 0.96];
            else
                pctBoxes(idx).Value = sprintf('%+.2f%%', pctDiff);
                pctBoxes(idx).FontWeight = 'bold';
                pctBoxes(idx).BackgroundColor = [1.0, 0.95, 0.85];
            end
        end
    end

    function applySampleAlphaCoupling(changedIdx)
        if any(changedIdx == [8, 26, 27])
            appState.alphaBasis = 'rhoCp';
        elseif changedIdx == 28
            appState.alphaBasis = 'rhocp';
        end
        if appState.coupleAlphaSample
            refreshControls();
        end
    end

    function file = getFile(fileIdx)
        if isempty(appState.files{fileIdx})
            file = struct();
            file.name = appState.fileNames{fileIdx};
            [file.Time, file.dTemp, file.Voltage, file.VoltageSTD, ...
             file.Current, file.CurrentSTD, file.IV, file.aveTemp] = ...
                loadProcessedFile(appState.datafolderUSE, file.name, ...
                    appState.aveTemp_vector(fileIdx));
            [p0, names] = Properties(appState.probe, appState.crucible, ...
                appState.sample, file.aveTemp, file.Voltage, file.VoltageSTD, ...
                file.Current, file.CurrentSTD, 0);
            p0(isnan(p0)) = 0;
            file.par_init = p0(:)';
            file.par_names = names;
            file.S_init = evaluateModel(file.Time, file.par_init, file.IV);
            appState.files{fileIdx} = file;
        else
            file = appState.files{fileIdx};
        end
    end

    function p = tunedParameters(file)
        p = file.par_init;
        p(appState.overrideMask) = appState.overrideValues(appState.overrideMask);
        if appState.coupleAlphaSample
            if strcmp(appState.alphaBasis, 'rhoCp')
                if p(26) > 0 && p(27) > 0
                    p(28) = p(26) * p(27);
                    p(9) = p(8) / p(28);
                end
            elseif p(28) > 0
                p(9) = p(8) / p(28);
            end
        end
    end

    function indices = visibleFileIndices()
        if appState.multiView
            indices = appState.activeFileIdx;
        else
            indices = appState.currentFileIdx;
        end
    end

    function refreshControls()
        file = getFile(appState.currentFileIdx);
        appState.par_init = file.par_init;
        appState.par_current = tunedParameters(file);
        for k = 1:numParams
            v0 = appState.par_init(k);
            value = appState.par_current(k);
            lims = getInitialSliderLimits(v0, k);
            lims = expandSliderLimits(lims, value);
            sliders(k).Limits = lims;
            sliders(k).MajorTicks = linspace(lims(1), lims(2), 3);
            sliders(k).Value = value;
            editBoxes(k).Value = value;
            updatePctBox(k);
            rawName = strrep(char(appState.par_names(k, 1)), '\_', '_');
            rawUnit = strrep(char(appState.par_names(k, 2)), '\_', '_');
            labels(k).Tooltip = sprintf('Control-file default: %.6g %s', v0, rawUnit);
            resetBtns(k).Tooltip = sprintf('Release shared override for %s; control-file default: %.6g %s', ...
                rawName, v0, rawUnit);
        end
    end

    function rebuildPlotLayout(files)
        delete(mainPlotPanel.Children);
        delete(resPlotPanel.Children);

        nFiles = numel(files);
        useSeparateMain = appState.multiView && appState.separateMainPlots && nFiles > 1;
        useSeparateRes  = appState.multiView && appState.separateResPlots && nFiles > 1;

        if scaleCheckbox.Value
            xScaleMode = 'log';
        else
            xScaleMode = 'linear';
        end

        nCols = ceil(sqrt(nFiles));
        nRows = ceil(nFiles / nCols);

        % --- 1. Build Main Temperature Response Panel ---
        if useSeparateMain
            tMain = tiledlayout(mainPlotPanel, nRows, nCols, ...
                'TileSpacing', 'compact', 'Padding', 'compact');
            axMainList = gobjects(nFiles, 1);
            hExp = gobjects(nFiles, 1);
            hInit = gobjects(nFiles, 1);
            hLive = gobjects(nFiles, 1);

            for j = 1:nFiles
                file = files{j};
                axM = nexttile(tMain, j);
                hold(axM, 'on');
                grid(axM, 'on');
                axM.XScale = xScaleMode;
                hExp(j) = plot(axM, file.Time, file.dTemp, 'ko', ...
                    'MarkerSize', 3.5, 'DisplayName', 'Exp. Data');
                hInit(j) = plot(axM, file.Time, file.S_init, 'b--', ...
                    'LineWidth', 1.2, 'DisplayName', 'Initial Model');
                hLive(j) = plot(axM, file.Time, file.S_current, 'r-', ...
                    'LineWidth', 1.8, 'DisplayName', 'Tuned Model');
                xlabel(axM, 'Time (s)');
                ylabel(axM, '\DeltaT (K)');
                if j == 1
                    legend(axM, 'Location', 'northwest', 'Interpreter', 'none');
                end
                axMainList(j) = axM;
            end
        else
            tMain = tiledlayout(mainPlotPanel, 1, 1, ...
                'TileSpacing', 'compact', 'Padding', 'compact');
            axM = nexttile(tMain, 1);
            hold(axM, 'on');
            grid(axM, 'on');
            axM.XScale = xScaleMode;
            xlabel(axM, 'Time (s)');
            ylabel(axM, '\DeltaT (K)');
            axMainList = axM;

            hExp = gobjects(nFiles, 1);
            hInit = gobjects(nFiles, 1);
            hLive = gobjects(nFiles, 1);

            if nFiles == 1
                file = files{1};
                hExp(1) = plot(axM, file.Time, file.dTemp, 'ko', ...
                    'MarkerSize', 4, 'DisplayName', [file.name ' | data']);
                hInit(1) = plot(axM, file.Time, file.S_init, 'b--', ...
                    'LineWidth', 1.4, 'DisplayName', [file.name ' | initial model']);
                hLive(1) = plot(axM, file.Time, file.S_current, 'r-', ...
                    'LineWidth', 2.0, 'DisplayName', [file.name ' | tuned model']);
            else
                for j = 1:nFiles
                    file = files{j};
                    [cData, cInit, cLive, markerSym] = getMultiFileStyle(j, nFiles);
                    hExp(j) = plot(axM, file.Time, file.dTemp, markerSym, ...
                        'Color', cData, 'MarkerSize', 4, ...
                        'DisplayName', [file.name ' | data']);
                    hInit(j) = plot(axM, file.Time, file.S_init, '--', ...
                        'Color', cInit, 'LineWidth', 1.3, ...
                        'DisplayName', [file.name ' | initial model']);
                    hLive(j) = plot(axM, file.Time, file.S_current, '-', ...
                        'Color', cLive, 'LineWidth', 2.2, ...
                        'DisplayName', [file.name ' | tuned model']);
                end
                axM.Children = [flipud(hLive); flipud(hInit); flipud(hExp)];
            end
            legend(axM, 'Location', 'northwest', 'Interpreter', 'none');
        end

        % --- 2. Build Residuals Panel ---
        if useSeparateRes
            tRes = tiledlayout(resPlotPanel, nRows, nCols, ...
                'TileSpacing', 'compact', 'Padding', 'compact');
            axResList = gobjects(nFiles, 1);
            hResInit = gobjects(nFiles, 1);
            hResLive = gobjects(nFiles, 1);

            for j = 1:nFiles
                file = files{j};
                axR = nexttile(tRes, j);
                hold(axR, 'on');
                grid(axR, 'on');
                axR.XScale = xScaleMode;
                yline(axR, 0, 'k:', 'HandleVisibility', 'off');
                hResInit(j) = plot(axR, file.Time, file.dTemp - file.S_init, 'b--', ...
                    'LineWidth', 1.0, 'DisplayName', 'Initial Residual');
                hResLive(j) = plot(axR, file.Time, file.dTemp - file.S_current, 'r-', ...
                    'LineWidth', 1.4, 'DisplayName', 'Tuned Residual');
                xlabel(axR, 'Time (s)');
                ylabel(axR, 'Residual (K)');
                if j == 1
                    legend(axR, 'Location', 'northwest', 'Interpreter', 'none');
                end
                axResList(j) = axR;
            end
        else
            tRes = tiledlayout(resPlotPanel, 1, 1, ...
                'TileSpacing', 'compact', 'Padding', 'compact');
            axR = nexttile(tRes, 1);
            hold(axR, 'on');
            grid(axR, 'on');
            axR.XScale = xScaleMode;
            xlabel(axR, 'Time (s)');
            ylabel(axR, 'Residual \DeltaT_{exp} - \DeltaT_{model} (K)');
            yline(axR, 0, 'k:', 'HandleVisibility', 'off');
            axResList = axR;

            [resTime, resInit, resLive] = averageResiduals(files);
            if isempty(resTime)
                hResInit = gobjects(0);
                hResLive = gobjects(0);
                legend(axR, 'off');
            else
                if nFiles == 1
                    prefix = '';
                else
                    prefix = 'Mean ';
                end
                hResInit = plot(axR, resTime, resInit, 'b--', 'LineWidth', 1.0, ...
                    'DisplayName', [prefix 'Initial Residual']);
                hResLive = plot(axR, resTime, resLive, 'r-', 'LineWidth', 1.5, ...
                    'DisplayName', [prefix 'Tuned Residual']);
                legend(axR, 'Location', 'northwest', 'Interpreter', 'none');
            end
        end

        appState.layoutDirty = false;
    end

    function recomputeAndPlot()
        try
            indices = visibleFileIndices();
            nFiles = numel(indices);
            files = cell(1, nFiles);
            initSSE = 0;
            liveSSE = 0;
            count = 0;

            for j = 1:nFiles
                file = getFile(indices(j));
                p = tunedParameters(file);
                file.par_current = p;
                if isequal(p, file.par_init)
                    file.S_current = file.S_init;
                else
                    file.S_current = evaluateModel(file.Time, p, file.IV);
                end
                files{j} = file;
                initSSE = initSSE + sum((file.dTemp - file.S_init).^2);
                liveSSE = liveSSE + sum((file.dTemp - file.S_current).^2);
                count = count + numel(file.Time);
            end

            if appState.layoutDirty || isempty(axMainList) || any(~isgraphics(axMainList)) || ...
               isempty(axResList) || any(~isgraphics(axResList))
                rebuildPlotLayout(files);
            end

            useSeparateMain = appState.multiView && appState.separateMainPlots && nFiles > 1;
            useSeparateRes  = appState.multiView && appState.separateResPlots && nFiles > 1;

            % --- Update Main Plot(s) ---
            if useSeparateMain
                for j = 1:nFiles
                    file = files{j};
                    hLive(j).YData = file.S_current;
                    rmseInit_j = sqrt(mean((file.dTemp - file.S_init).^2));
                    rmseLive_j = sqrt(mean((file.dTemp - file.S_current).^2));
                    title(axMainList(j), sprintf('%s | Tavg = %.1f C | RMSE: %.4f K (Init: %.4f K)', ...
                        file.name, file.aveTemp, rmseLive_j, rmseInit_j), 'Interpreter', 'none');
                end
            else
                for j = 1:nFiles
                    hLive(j).YData = files{j}.S_current;
                end
                if nFiles == 1
                    file = files{1};
                    title(axMainList(1), sprintf('%s | Tavg = %.1f C | RMSE: %.4f K (Init: %.4f K)', ...
                        file.name, file.aveTemp, sqrt(liveSSE / count), sqrt(initSSE / count)), ...
                        'Interpreter', 'none');
                else
                    title(axMainList(1), sprintf('%d active files | Pooled RMSE: %.4f K (Init: %.4f K)', ...
                        nFiles, sqrt(liveSSE / count), sqrt(initSSE / count)), ...
                        'Interpreter', 'none');
                end
            end

            % --- Update Residual Plot(s) ---
            if useSeparateRes
                for j = 1:nFiles
                    file = files{j};
                    resLive_j = file.dTemp - file.S_current;
                    hResLive(j).YData = resLive_j;
                    sseLive_j = sum(resLive_j.^2);
                    title(axResList(j), sprintf('%s | Tuned SSE = %.5g K^2', ...
                        file.name, sseLive_j), 'Interpreter', 'none');
                end
            else
                [resTime, resInit, resLive] = averageResiduals(files);
                if isempty(resTime)
                    title(axResList(1), 'No shared time interval for averaging residuals', 'Interpreter', 'none');
                else
                    if ~isempty(hResLive) && isgraphics(hResLive)
                        hResInit.XData = resTime;
                        hResInit.YData = resInit;
                        hResLive.XData = resTime;
                        hResLive.YData = resLive;
                    end
                    if nFiles > 1
                        title(axResList(1), sprintf('Mean residuals of %d files | Shared interval: %.4g to %.4g s', ...
                            nFiles, resTime(1), resTime(end)), 'Interpreter', 'none');
                    else
                        title(axResList(1), sprintf('Residuals | Tuned SSE = %.5g K^2', liveSSE), ...
                            'Interpreter', 'none');
                    end
                end
            end

            activeLabel.Text = sprintf('%d visible / %d total', nFiles, numel(fileNames));
            drawnow limitrate;
        catch ME
            if ~isempty(axMainList) && isgraphics(axMainList(1))
                title(axMainList(1), 'Plot not updated: model evaluation failed', 'Interpreter', 'none');
            end
            if ~isempty(axResList) && isgraphics(axResList(1))
                title(axResList(1), 'Residuals not updated: model evaluation failed', 'Interpreter', 'none');
            end
            uialert(fig, ME.message, 'Model Evaluation Error');
        end
    end

    function updateFileSelector()
        if appState.multiView
            indices = appState.activeFileIdx;
            if ~ismember(appState.currentFileIdx, indices)
                appState.currentFileIdx = indices(1);
            end
        else
            indices = 1:numel(fileNames);
        end
        fileDropdown.ItemsData = [];
        fileDropdown.Items = fileNames(indices);
        fileDropdown.ItemsData = indices;
        fileDropdown.Value = appState.currentFileIdx;
        multiCheckbox.Value = appState.multiView;
        separateMainCheckbox.Value = appState.separateMainPlots;
        separateMainCheckbox.Enable = onOff(appState.multiView);
        separateResCheckbox.Value = appState.separateResPlots;
        separateResCheckbox.Enable = onOff(appState.multiView);
    end

    function onFileChanged(newFileIdx)
        try
            getFile(newFileIdx);
        catch ME
            fileDropdown.Value = appState.currentFileIdx;
            uialert(fig, ME.message, 'File Loading Error');
            return;
        end
        appState.currentFileIdx = newFileIdx;
        if ~appState.multiView
            appState.layoutDirty = true;
        end
        refreshControls();
        recomputeAndPlot();
    end

    function onViewChanged(isMultiple)
        appState.multiView = isMultiple;
        appState.layoutDirty = true;
        updateFileSelector();
        refreshControls();
        recomputeAndPlot();
    end

    function onSeparateMainChanged(isSeparateMain)
        appState.separateMainPlots = isSeparateMain;
        appState.layoutDirty = true;
        recomputeAndPlot();
    end

    function onSeparateResChanged(isSeparateRes)
        appState.separateResPlots = isSeparateRes;
        appState.layoutDirty = true;
        recomputeAndPlot();
    end

    function onChooseFiles()
        [indices, accepted] = listdlg('PromptString', 'Choose active data files:', ...
            'SelectionMode', 'multiple', 'ListString', fileNames, ...
            'InitialValue', appState.activeFileIdx, 'ListSize', [520, 360]);
        if ~accepted || isempty(indices)
            return;
        end
        try
            for fileIdx = indices(:)'
                getFile(fileIdx);
            end
        catch ME
            uialert(fig, ME.message, 'File Loading Error');
            return;
        end
        appState.activeFileIdx = indices(:)';
        appState.layoutDirty = true;
        onViewChanged(true);
    end

    function onResetAll()
        appState.overrideMask(:) = false;
        appState.alphaBasis = 'rhoCp';
        refreshControls();
        recomputeAndPlot();
    end

    function onScaleChanged(isLog)
        if isLog
            scaleStr = 'log';
        else
            scaleStr = 'linear';
        end
        for k = 1:numel(axMainList)
            if isgraphics(axMainList(k))
                axMainList(k).XScale = scaleStr;
            end
        end
        for k = 1:numel(axResList)
            if isgraphics(axResList(k))
                axResList(k).XScale = scaleStr;
            end
        end
    end

    function onCoupleChanged(isCoupled)
        appState.coupleAlphaSample = isCoupled;
        if isCoupled
            sliders(9).Enable = 'off';
            editBoxes(9).Enable = 'off';
        else
            sliders(9).Enable = 'on';
            editBoxes(9).Enable = 'on';
        end
        refreshControls();
        recomputeAndPlot();
    end

    function onExportParams()
        % 1. Gather current tuned vectors for all visible files
        indices = visibleFileIndices();
        nVis = numel(indices);
        vectors = zeros(nVis, numParams);
        ivModes = zeros(nVis, 1);
        voltages = zeros(nVis, 1);
        temps = zeros(nVis, 1);

        for j = 1:nVis
            file = getFile(indices(j));
            vectors(j, :) = tunedParameters(file);
            ivModes(j) = file.IV;
            voltages(j) = file.Voltage;
            temps(j) = file.aveTemp;
        end

        tuned_par_vector = appState.par_current;
        tuned_par_names = appState.par_names;
        tuned_par_vectors = vectors;
        tuned_file_names = appState.fileNames(indices);
        tuned_IV = ivModes;
        tuned_override_mask = appState.overrideMask;
        tuned_override_values = appState.overrideValues;

        % Identify changed parameters (either explicitly overridden or coupled)
        changedIdx = find(appState.overrideMask | ...
            abs(appState.par_current - appState.par_init) > 1e-12 * max(1, abs(appState.par_init)));

        % 2. Export to MATLAB base workspace
        assignin('base', 'tuned_par_vector', tuned_par_vector);
        assignin('base', 'tuned_par_names', tuned_par_names);
        assignin('base', 'tuned_par_vectors', tuned_par_vectors);
        assignin('base', 'tuned_file_names', tuned_file_names);
        assignin('base', 'tuned_IV', tuned_IV);
        assignin('base', 'tuned_override_mask', tuned_override_mask);
        assignin('base', 'tuned_override_values', tuned_override_values);

        % 3. Determine non-overwriting .txt and .mat filenames in the ManualTune folder
        if ~exist(appState.runfolder, 'dir')
            mkdir(appState.runfolder);
        end

        baseExportName = [appState.run_name '_TunedParameters'];
        txtFilePath = fullfile(appState.runfolder, [baseExportName '.txt']);
        matFilePath = fullfile(appState.runfolder, [baseExportName '.mat']);

        exportIdx = 1;
        while exist(txtFilePath, 'file') || exist(matFilePath, 'file')
            suffixedName = sprintf('%s_%d', baseExportName, exportIdx);
            txtFilePath = fullfile(appState.runfolder, [suffixedName '.txt']);
            matFilePath = fullfile(appState.runfolder, [suffixedName '.mat']);
            exportIdx = exportIdx + 1;
        end

        exportTimestamp = char(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss'));

        save(matFilePath, 'tuned_par_vector', 'tuned_par_names', ...
            'tuned_par_vectors', 'tuned_file_names', 'tuned_IV', ...
            'tuned_override_mask', 'tuned_override_values', 'changedIdx', ...
            'exportTimestamp');

        fid = fopen(txtFilePath, 'wt');
        if fid == -1
            uialert(fig, sprintf('Could not open file for writing:\n%s', txtFilePath), 'File Write Error');
            return;
        end

        fprintf(fid, '=== Manual Tune Export: %s ===\n', appState.run_name);
        fprintf(fid, 'Export Timestamp: %s\n', exportTimestamp);
        fprintf(fid, 'Control File: %s\n', appState.fileNames{appState.currentFileIdx});
        fprintf(fid, 'Couple Alpha_Sample = k/(rho*Cp): %s\n\n', onOff(appState.coupleAlphaSample));

        % Section A: Changed Parameters Summary
        fprintf(fid, '--- Changed Parameters (Relative to Control File Defaults) ---\n');
        if isempty(changedIdx)
            fprintf(fid, 'No parameters were modified from their initial Properties.m values.\n');
        else
            fprintf(fid, '%-4s\t%-24s\t%-16s\t%-16s\t%-12s\t%-15s\n', ...
                'Idx', 'Parameter', 'Initial_Value', 'Tuned_Value', 'Pct_Diff', 'Units');
            for cIdx = changedIdx(:)'
                val0 = appState.par_init(cIdx);
                valCurr = appState.par_current(cIdx);
                rawName = strrep(char(appState.par_names(cIdx, 1)), '\_', '_');
                rawUnit = strrep(char(appState.par_names(cIdx, 2)), '\_', '_');
                if val0 ~= 0
                    pctStr = sprintf('%+.2f%%', ((valCurr - val0) / abs(val0)) * 100);
                else
                    pctStr = 'N/A (0 init)';
                end
                fprintf(fid, '%2d\t%-24s\t%16.6g\t%16.6g\t%-12s\t%-15s\n', ...
                    cIdx, rawName, val0, valCurr, pctStr, rawUnit);
            end
        end

        % Section B: All 34 Parameters for Control File
        fprintf(fid, '\n--- Full Control File Parameter Vector (%s) ---\n', ...
            appState.fileNames{appState.currentFileIdx});
        fprintf(fid, '%-4s\t%-24s\t%-16s\t%-16s\t%-15s\t%s\n', ...
            'Idx', 'Parameter', 'Initial_Value', 'Tuned_Value', 'Units', 'Status');
        for k = 1:numParams
            val0 = appState.par_init(k);
            valCurr = appState.par_current(k);
            rawName = strrep(char(appState.par_names(k, 1)), '\_', '_');
            rawUnit = strrep(char(appState.par_names(k, 2)), '\_', '_');
            if ismember(k, changedIdx)
                if val0 ~= 0
                    statusStr = sprintf('*MODIFIED (%+.2f%%)*', ((valCurr - val0) / abs(val0)) * 100);
                else
                    statusStr = '*MODIFIED (from 0)*';
                end
            else
                statusStr = '';
            end
            fprintf(fid, '%2d\t%-24s\t%16.6g\t%16.6g\t%-15s\t%s\n', ...
                k, rawName, val0, valCurr, rawUnit, statusStr);
        end

        % Section C: Tab-Delimited Table Across All Visible Files
        fprintf(fid, '\n--- Tuned Parameter Vectors for All Visible Files ---\n');
        fprintf(fid, 'File\tVoltage(V)\tTemp(C)\tIV_Flag');
        for k = 1:numParams
            rawName = strrep(char(appState.par_names(k, 1)), '\_', '_');
            rawUnit = strrep(char(appState.par_names(k, 2)), '\_', '_');
            fprintf(fid, '\t%s(%s)', rawName, rawUnit);
        end
        fprintf(fid, '\n');

        for j = 1:nVis
            fprintf(fid, '%s\t%.6g\t%.6g\t%d', ...
                tuned_file_names{j}, voltages(j), temps(j), ivModes(j));
            fprintf(fid, '\t%.6g', vectors(j, :));
            fprintf(fid, '\n');
        end

        fclose(fid);

        % 4. Print summary to Command Window and notify user
        fprintf('\n=== Exported Tuned Parameters for %s ===\n', appState.fileNames{appState.currentFileIdx});
        fprintf('Saved to ManualTune folder:\n  %s\n  %s\n\n', txtFilePath, matFilePath);
        for k = 1:numParams
            val0 = appState.par_init(k);
            valCurr = appState.par_current(k);
            if ismember(k, changedIdx)
                if val0 ~= 0
                    marker = sprintf('*MODIFIED (%+.2f%%)*', ((valCurr - val0) / abs(val0)) * 100);
                else
                    marker = '*MODIFIED (from 0)*';
                end
            else
                marker = '';
            end
            fprintf('%2d. %-24s : %14.6g %-15s %s\n', ...
                k, strrep(char(appState.par_names(k,1)), '\_', '_'), ...
                valCurr, ...
                strrep(char(appState.par_names(k,2)), '\_', '_'), marker);
        end

        uialert(fig, sprintf('Saved tuned parameters to the ManualTune folder:\n\n%s\n%s\n\nAlso exported variables to the MATLAB base workspace.', ...
            txtFilePath, matFilePath), 'Export Complete', 'Icon', 'success');
    end
end

%% --- Local Utility Functions ---

function stateStr = onOff(flag)
    if flag
        stateStr = 'on';
    else
        stateStr = 'off';
    end
end

function [cData, cInit, cLive, markerSym] = getMultiFileStyle(fileOrderIdx, totalActiveFiles)
    % High-variation base palette with strong intra-file luminance/saturation
    % contrast so experimental markers, initial model (--), and tuned model (-)
    % are clearly distinguishable both within a file and across files.
    basePalette = [
        0.00, 0.38, 0.85;  % 1. Royal Blue
        0.85, 0.12, 0.15;  % 2. Crimson Red
        0.05, 0.60, 0.22;  % 3. Forest Green
        0.58, 0.12, 0.72;  % 4. Vivid Purple
        0.88, 0.44, 0.00;  % 5. Burnt Orange
        0.00, 0.62, 0.68;  % 6. Deep Teal
        0.82, 0.10, 0.52;  % 7. Magenta
        0.52, 0.44, 0.00;  % 8. Olive Gold
        0.18, 0.18, 0.66;  % 9. Indigo
        0.65, 0.24, 0.18;  % 10. Rust Brown
        0.08, 0.45, 0.38;  % 11. Pine Green
        0.45, 0.08, 0.35   % 12. Plum
    ];

    if fileOrderIdx <= size(basePalette, 1)
        baseColor = basePalette(fileOrderIdx, :);
    else
        % Golden-ratio hue spacing for >12 active files
        hue = mod(0.61803398875 * (fileOrderIdx - 1), 1);
        sat = 0.82 - 0.15 * mod(fileOrderIdx, 2);
        val = 0.78 - 0.12 * mod(floor(fileOrderIdx / 2), 2);
        baseColor = hsv2rgb([hue, sat, max(totalActiveFiles*0 + 0.55, val)]);
    end

    % Light/pastel tint for dense experimental markers so they don't obscure curves
    cData = 0.45 * baseColor + 0.55 * [1.0, 1.0, 1.0];

    % Darkened/muted shade for initial model dashed curve
    cInit = 0.55 * baseColor;

    % Full-saturation vivid shade for live tuned model curve drawn on top
    cLive = min(1.0, 0.90 * baseColor);

    markers = {'o', 's', '^', 'd', 'v', '>', '<', 'p', 'h'};
    markerSym = markers{mod(fileOrderIdx - 1, numel(markers)) + 1};
end

function [Time, dTemp, Voltage, VoltageSTD, Current, CurrentSTD, IV, aveTemp] = ...
    loadProcessedFile(datafolderUSE, fileName, aveTemp)
    fullFilePath = fullfile(datafolderUSE, fileName);
    signal = load(fullFilePath);
    [~, fn, ~] = fileparts(fileName);

    M = size(signal);
    if ~isnumeric(signal) || size(signal, 2) < 2 || size(signal, 1) < 2
        error('NeedleProbeTuner:InvalidData', '%s must contain at least two rows of time and temperature data.', fileName);
    end
    Time = signal(:, 1);
    dTemp = signal(:, 2);
    if any(~isfinite(Time)) || any(Time <= 0) || any(diff(Time) <= 0) || any(~isfinite(dTemp))
        error('NeedleProbeTuner:InvalidData', ...
            '%s needs finite data with positive, strictly increasing times.', fileName);
    end

    if M(2) >= 3
        Voltage = median(signal(:, 3));
        VoltageSTD = std(signal(:, 3));
    else
        Voltage = 0.85 * str2double(fn(end));
        VoltageSTD = Voltage * 0.05 / 2;
    end

    if M(2) >= 4
        Current = median(signal(:, 4), 'omitnan');
        CurrentSTD = std(signal(:, 4), 'omitnan');
        if Current > 10 % Convert mA to A if recorded in mA
            Current = Current / 1000;
            CurrentSTD = CurrentSTD / 1000;
        end
        IV = 1;
        if isnan(Current)
            Current = 0;
            CurrentSTD = 0;
            IV = 0;
        end
    else
        Current = 0;
        CurrentSTD = 0;
        IV = 0;
    end
end

function lims = getInitialSliderLimits(val0, idx)
    if idx == 12 || idx == 13 || idx == 34
        low = max(1e-4, min(0.01, val0 * 0.2));
        high = max(1.0, val0 * 1.2);
        lims = [min(low, val0), max(high, val0)];
    elseif any(idx == [19, 20, 21, 22, 23, 24])
        if val0 > 0
            lims = [0.75 * val0, 1.25 * val0];
        else
            lims = [min(0, val0), 1e-2];
        end
    elseif val0 == 0
        if any(idx == [5, 32, 33])
            lims = [0, 0.5];
        else
            lims = [0, 1.0];
        end
    elseif val0 > 0
        lims = [0.9 * val0, 1.1 * val0];
    else
        lims = [1.1 * val0, 0.9 * val0];
    end
end

function newLims = expandSliderLimits(currLims, newValue)
    low = currLims(1);
    high = currLims(2);
    if newValue < low
        if newValue >= 0
            low = 0.9 * newValue;
        else
            low = 1.1 * newValue;
        end
    elseif newValue > high
        if newValue > 0
            high = 1.1 * newValue;
        else
            high = 0.9 * newValue;
        end
    end
    if low == high
        high = low + 1;
    end
    newLims = [low, high];
end

function response = evaluateModel(time, parameters, iv)
    if exist('MatrixNeedleProbeModel', 'file')
        response = MatrixNeedleProbeModel(time, parameters, iv);
    else
        response = ChatNeedleProbeModel(time, parameters, iv);
    end
    response = response(:);
    if numel(response) ~= numel(time) || ~isreal(response) || any(~isfinite(response))
        error('NeedleProbeTuner:InvalidModel', ...
            'Model must return one finite real temperature for every time point. Check parameter values.');
    end
end

function [time, meanInitial, meanTuned] = averageResiduals(files)
    first = files{1};
    if numel(files) == 1
        time = first.Time;
        meanInitial = first.dTemp - first.S_init;
        meanTuned = first.dTemp - first.S_current;
        return;
    end
    lower = max(cellfun(@(f) f.Time(1), files));
    upper = min(cellfun(@(f) f.Time(end), files));
    if lower > upper
        time = [];
        meanInitial = [];
        meanTuned = [];
        return;
    end
    grids = cellfun(@(f) f.Time(f.Time >= lower & f.Time <= upper), ...
        files, 'UniformOutput', false);
    time = unique(vertcat(grids{:}));
    meanInitial = zeros(size(time));
    meanTuned = zeros(size(time));
    for j = 1:numel(files)
        file = files{j};
        initial = file.dTemp - file.S_init;
        tuned = file.dTemp - file.S_current;
        if isequal(time, file.Time)
            meanInitial = meanInitial + initial;
            meanTuned = meanTuned + tuned;
        else
            meanInitial = meanInitial + interp1(file.Time, initial, time, 'linear');
            meanTuned = meanTuned + interp1(file.Time, tuned, time, 'linear');
        end
    end
    meanInitial = meanInitial / numel(files);
    meanTuned = meanTuned / numel(files);
end