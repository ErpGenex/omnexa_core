/**
 * Demo Wizard Controller
 * Enterprise-grade demo execution wizard for Branch Demo Data tab.
 * 
 * This controller manages the demo execution interface with:
 * - Dynamic dropdown loaded from registry
 * - Information panel with metadata
 * - Execution mode selection
 * - Progress tracking
 * - Confirmation dialogs
 * - Success/error handling
 */

frappe.ui.form.on('Branch', {
    refresh: function(frm) {
        // Initialize demo wizard when form refreshes
        if (frm.doc.__islocal) return;
        
        // Add custom demo wizard section
        init_demo_wizard(frm);
    },
    
    branch_demo_type: function(frm) {
        // Handle demo type selection
        on_demo_type_change(frm);
    }
});

// Demo Wizard State
let demoWizardState = {
    registry: [],
    selectedDemo: null,
    executionMode: null,
    isExecuting: false
};

/**
 * Initialize the demo wizard interface
 */
function init_demo_wizard(frm) {
    // Load demo registry
    load_demo_registry(frm);
    
    // Add custom HTML for demo wizard
    add_demo_wizard_html(frm);
    
    // Bind events
    bind_demo_wizard_events(frm);
}

/**
 * Load demo registry from backend
 */
function load_demo_registry(frm) {
    frappe.call({
        method: 'omnexa_core.api.demo_wizard.get_demo_registry',
        callback: function(r) {
            if (r.message && !r.message.error) {
                demoWizardState.registry = r.message;
                populate_demo_dropdown(frm);
            } else {
                frappe.msgprint(__('Error loading demo registry'), __('Error'));
            }
        }
    });
}

/**
 * Add custom HTML for demo wizard interface
 */
function add_demo_wizard_html(frm) {
    // Check if wizard already exists
    if ($(frm.wrapper).find('.demo-wizard-container').length) return;
    
    // Find the wizard HTML field wrapper
    const wizard_field = frm.fields_dict['branch_demo_wizard_html'];
    if (!wizard_field || !wizard_field.wrapper) {
        console.error('Demo wizard field not found');
        return;
    }
    
    const wizard_html = `
        <div class="demo-wizard-container">
            <div class="demo-wizard-layout">
                <!-- Left Side: Demo Configuration -->
                <div class="demo-config-section">
                    <div class="demo-config-card">
                        <div class="demo-config-header">
                            <h4>${__('Demo Configuration')}</h4>
                            <p class="text-muted">${__('Configure demo parameters before execution')}</p>
                        </div>
                        <div class="demo-config-body">
                            <!-- Existing configuration fields will be rendered here -->
                        </div>
                    </div>
                </div>
                
                <!-- Right Side: Demo Execution Center -->
                <div class="demo-execution-section">
                    <div class="demo-execution-card">
                        <div class="demo-execution-header">
                            <h4>${__('Demo Execution Center')}</h4>
                            <p class="text-muted">${__('Select and execute demo actions')}</p>
                        </div>
                        <div class="demo-execution-body">
                            <!-- Demo Action Dropdown -->
                            <div class="demo-field-group">
                                <label class="demo-field-label">${__('Demo Action')}</label>
                                <select id="demo-action-dropdown" class="demo-select form-control">
                                    <option value="">${__('Select a demo action...')}</option>
                                </select>
                            </div>
                            
                            <!-- Information Panel -->
                            <div id="demo-info-panel" class="demo-info-panel" style="display: none;">
                                <div class="demo-info-header">
                                    <span id="demo-info-icon" class="demo-info-icon"></span>
                                    <h5 id="demo-info-title"></h5>
                                </div>
                                <div class="demo-info-body">
                                    <p id="demo-info-description" class="demo-description"></p>
                                    
                                    <div class="demo-info-grid">
                                        <div class="demo-info-item">
                                            <span class="demo-info-label">${__('Estimated Time')}</span>
                                            <span id="demo-info-time" class="demo-info-value"></span>
                                        </div>
                                        <div class="demo-info-item">
                                            <span class="demo-info-label">${__('Estimated Records')}</span>
                                            <span id="demo-info-records" class="demo-info-value"></span>
                                        </div>
                                        <div class="demo-info-item">
                                            <span class="demo-info-label">${__('Risk Level')}</span>
                                            <span id="demo-info-risk" class="demo-info-badge"></span>
                                        </div>
                                        <div class="demo-info-item">
                                            <span class="demo-info-label">${__('Category')}</span>
                                            <span id="demo-info-category" class="demo-info-value"></span>
                                        </div>
                                    </div>
                                    
                                    <div class="demo-info-section">
                                        <span class="demo-info-label">${__('Required Modules')}</span>
                                        <div id="demo-info-modules" class="demo-info-tags"></div>
                                    </div>
                                    
                                    <div id="demo-warnings-container" class="demo-warnings" style="display: none;">
                                        <div class="demo-warning-header">
                                            <i class="fa fa-exclamation-triangle"></i>
                                            <span>${__('Warnings')}</span>
                                        </div>
                                        <ul id="demo-warnings-list" class="demo-warnings-list"></ul>
                                    </div>
                                    
                                    <div class="demo-info-section">
                                        <span class="demo-info-label">${__('Execution Mode')}</span>
                                        <select id="demo-execution-mode" class="demo-select form-control">
                                            <option value="create_missing">${__('Create Missing Records')}</option>
                                            <option value="update_existing">${__('Update Existing Records')}</option>
                                            <option value="replace_all">${__('Replace All Demo Data')}</option>
                                            <option value="reset_environment">${__('Reset Demo Environment')}</option>
                                            <option value="append_data">${__('Append New Data')}</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Execute Button -->
                            <button id="demo-execute-btn" class="btn btn-primary btn-lg demo-execute-btn" disabled>
                                <i class="fa fa-play"></i>
                                ${__('Execute Demo')}
                            </button>
                            
                            <!-- Progress Bar -->
                            <div id="demo-progress-container" class="demo-progress-container" style="display: none;">
                                <div class="demo-progress-header">
                                    <span id="demo-progress-status">${__('Executing...')}</span>
                                    <span id="demo-progress-percent">0%</span>
                                </div>
                                <div class="progress">
                                    <div id="demo-progress-bar" class="progress-bar progress-bar-striped active" 
                                         role="progressbar" style="width: 0%"></div>
                                </div>
                                <p id="demo-progress-message" class="demo-progress-message"></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Replace the mount point div with the wizard HTML
    $(wizard_field.wrapper).find('#demo-wizard-mount-point').replaceWith(wizard_html);
}

/**
 * Populate demo dropdown with registered actions
 */
function populate_demo_dropdown(frm) {
    const dropdown = $('#demo-action-dropdown');
    dropdown.empty();
    dropdown.append('<option value="">' + __('Select a demo action...') + '</option>');
    
    // Group by category
    const grouped = {};
    demoWizardState.registry.forEach(demo => {
        if (!grouped[demo.category]) {
            grouped[demo.category] = [];
        }
        grouped[demo.category].push(demo);
    });
    
    // Add options grouped by category
    Object.keys(grouped).sort().forEach(category => {
        const optgroup = $('<optgroup>').attr('label', category);
        grouped[category].forEach(demo => {
            const option = $('<option>')
                .attr('value', demo.key)
                .text(demo.title)
                .data('metadata', demo);
            optgroup.append(option);
        });
        dropdown.append(optgroup);
    });
    
    // Enable search if Select2 is available
    if ($.fn.select2) {
        dropdown.select2({
            placeholder: __('Select a demo action...'),
            width: '100%'
        });
    }
}

/**
 * Handle demo type selection change
 */
function on_demo_type_change(frm) {
    const selectedKey = $('#demo-action-dropdown').val();
    
    if (!selectedKey) {
        hide_demo_info_panel();
        disable_execute_button();
        return;
    }
    
    const selectedDemo = demoWizardState.registry.find(d => d.key === selectedKey);
    if (selectedDemo) {
        demoWizardState.selectedDemo = selectedDemo;
        show_demo_info_panel(selectedDemo);
        enable_execute_button();
        
        // Set default execution mode
        $('#demo-execution-mode').val(selectedDemo.default_execution_mode);
    }
}

/**
 * Show demo information panel
 */
function show_demo_info_panel(demo) {
    const panel = $('#demo-info-panel');
    panel.show();
    
    // Set icon and title
    $('#demo-info-icon').html(`<i class="fa ${demo.icon}"></i>`);
    $('#demo-info-title').text(demo.title);
    
    // Set description
    $('#demo-info-description').text(demo.description);
    
    // Set metadata
    $('#demo-info-time').text(demo.estimated_time);
    $('#demo-info-records').text(demo.estimated_records.toLocaleString());
    $('#demo-info-category').text(demo.category);
    
    // Set risk badge
    const riskBadge = $('#demo-info-risk');
    riskBadge.text(demo.risk_level.charAt(0).toUpperCase() + demo.risk_level.slice(1));
    riskBadge.removeClass('badge-success badge-warning badge-danger badge-dark');
    
    switch(demo.risk_level) {
        case 'low':
            riskBadge.addClass('badge-success');
            break;
        case 'medium':
            riskBadge.addClass('badge-warning');
            break;
        case 'high':
            riskBadge.addClass('badge-danger');
            break;
        case 'critical':
            riskBadge.addClass('badge-dark');
            break;
    }
    
    // Set modules
    const modulesContainer = $('#demo-info-modules');
    modulesContainer.empty();
    demo.required_modules.forEach(module => {
        const tag = $('<span>').addClass('demo-tag').text(module);
        modulesContainer.append(tag);
    });
    
    // Show warnings if any
    const warningsContainer = $('#demo-warnings-container');
    const warningsList = $('#demo-warnings-list');
    warningsList.empty();
    
    if (demo.warnings && demo.warnings.length > 0) {
        warningsContainer.show();
        demo.warnings.forEach(warning => {
            warningsList.append(`<li>${warning}</li>`);
        });
    } else {
        warningsContainer.hide();
    }
}

/**
 * Hide demo information panel
 */
function hide_demo_info_panel() {
    $('#demo-info-panel').hide();
}

/**
 * Enable execute button
 */
function enable_execute_button() {
    $('#demo-execute-btn').prop('disabled', false);
}

/**
 * Disable execute button
 */
function disable_execute_button() {
    $('#demo-execute-btn').prop('disabled', true);
}

/**
 * Bind demo wizard events
 */
function bind_demo_wizard_events(frm) {
    // Demo dropdown change
    $(frm.wrapper).on('change', '#demo-action-dropdown', function() {
        on_demo_type_change(frm);
    });
    
    // Execute button click
    $(frm.wrapper).on('click', '#demo-execute-btn', function() {
        if (!demoWizardState.selectedDemo) return;
        
        const executionMode = $('#demo-execution-mode').val();
        show_confirmation_dialog(frm, demoWizardState.selectedDemo, executionMode);
    });
}

/**
 * Show confirmation dialog before execution
 */
function show_confirmation_dialog(frm, demo, executionMode) {
    const dialog = frappe.confirm(
        `
        <div class="demo-confirmation-dialog">
            <h4>${__('Run Demo')}</h4>
            <p>${__('You are about to execute:')}</p>
            <div class="demo-confirmation-details">
                <strong>${demo.title}</strong>
            </div>
            <div class="demo-confirmation-info">
                <div><strong>${__('Estimated Time')}:</strong> ${demo.estimated_time}</div>
                <div><strong>${__('Estimated Records')}:</strong> ${demo.estimated_records.toLocaleString()}</div>
                <div><strong>${__('Execution Mode')}:</strong> ${executionMode.replace(/_/g, ' ').toUpperCase()}</div>
                <div><strong>${__('Risk Level')}:</strong> ${demo.risk_level.toUpperCase()}</div>
            </div>
            ${demo.warnings && demo.warnings.length > 0 ? `
            <div class="demo-confirmation-warnings">
                <strong>${__('Warnings')}:</strong>
                <ul>
                    ${demo.warnings.map(w => `<li>${w}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            <p>${__('Do you want to continue?')}</p>
        </div>
        `,
        function() {
            // User confirmed - execute demo
            execute_demo(frm, demo.key, executionMode);
        },
        function() {
            // User cancelled
            console.log('Demo execution cancelled');
        }
    );
    
    // Customize dialog
    $(dialog.wrapper).find('.modal-title').text(__('Confirm Demo Execution'));
}

/**
 * Execute demo action
 */
function execute_demo(frm, demoKey, executionMode) {
    if (demoWizardState.isExecuting) return;
    
    demoWizardState.isExecuting = true;
    disable_execute_button();
    show_progress();
    
    frappe.call({
        method: 'omnexa_core.api.demo_wizard.execute_demo_action',
        args: {
            demo_key: demoKey,
            execution_mode: executionMode,
            company: frm.doc.company,
            branch: frm.doc.name
        },
        callback: function(r) {
            demoWizardState.isExecuting = false;
            hide_progress();
            
            if (r.message && r.message.success) {
                show_success_dialog(r.message);
            } else {
                show_error_dialog(r.message);
            }
            
            enable_execute_button();
        },
        error: function(err) {
            demoWizardState.isExecuting = false;
            hide_progress();
            show_error_dialog({error: err.message || __('Unknown error occurred')});
            enable_execute_button();
        }
    });
}

/**
 * Show progress bar
 */
function show_progress() {
    $('#demo-progress-container').show();
    update_progress(0, __('Preparing...'));
}

/**
 * Hide progress bar
 */
function hide_progress() {
    $('#demo-progress-container').hide();
}

/**
 * Update progress bar
 */
function update_progress(percent, message) {
    $('#demo-progress-bar').css('width', percent + '%');
    $('#demo-progress-percent').text(percent + '%');
    $('#demo-progress-message').text(message);
}

/**
 * Show success dialog
 */
function show_success_dialog(result) {
    const dialog = frappe.msgprint({
        title: __('Execution Completed Successfully'),
        indicator: 'green',
        message: `
            <div class="demo-success-dialog">
                <div class="demo-success-item">
                    <strong>${__('Demo')}:</strong>
                    <span>${demoWizardState.selectedDemo.title}</span>
                </div>
                <div class="demo-success-item">
                    <strong>${__('Records Created')}:</strong>
                    <span>${(result.result?.records_created || 0).toLocaleString()}</span>
                </div>
                <div class="demo-success-item">
                    <strong>${__('Execution Time')}:</strong>
                    <span>${result.duration || 'N/A'}</span>
                </div>
                <div class="demo-success-item">
                    <strong>${__('Warnings')}:</strong>
                    <span>${result.result?.warnings || 0}</span>
                </div>
                <div class="demo-success-item">
                    <strong>${__('Errors')}:</strong>
                    <span>${result.result?.errors || 0}</span>
                </div>
            </div>
        `
    });
}

/**
 * Show error dialog
 */
function show_error_dialog(result) {
    const dialog = frappe.msgprint({
        title: __('Execution Failed'),
        indicator: 'red',
        message: `
            <div class="demo-error-dialog">
                <div class="demo-error-message">
                    <strong>${__('Error')}:</strong>
                    <span>${result.error || __('Unknown error')}</span>
                </div>
                ${result.execution_log ? `
                <div class="demo-error-log">
                    <strong>${__('Execution Log')}:</strong>
                    <span>${result.execution_log}</span>
                </div>
                ` : ''}
            </div>
        `
    });
}
