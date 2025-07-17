frappe.listview_settings['Employee'] = {
    onload: function (listview) {
        listview.page.add_inner_button(__('Employee Verification'), function () {
            open_employee_verification_dialog();
        });
    }
};

function open_employee_verification_dialog(listview) {
    let selected_employees = new Set();
    let filtered_employees = [];

    const dialog = new frappe.ui.Dialog({
        title: __('Employee Verification'),
        size: 'large',
    fields: [
        { fieldtype: 'HTML', fieldname: 'filter_section' },
        { fieldtype: 'HTML', fieldname: 'bulk_action_section' },
        { fieldtype: 'HTML', fieldname: 'table_html' },

        // { fieldtype: 'Section Break' },

        {
            fieldtype: 'Select',
            fieldname: 'action_choice',
            label: __(' '),
            options: [
                { label: 'Print Malayalam', value: 'Print Malayalam' },
                { label: 'Print English', value: 'Print English' }
            ],
            default: 'Print Malayalam',
            
        }
    ],
        primary_action_label: 'Print Selected',
        primary_action: () => {
            if (selected_employees.size === 0) {
                frappe.msgprint(__('Please select at least one employee.'));
                return;
            }


            frappe.confirm(
                'Are you sure you want to print verification documents for the selected employees?',
                function () {
                    let selected_action = dialog.get_value('action_choice');
                    const employee_names = [...selected_employees];
                    const names_json = JSON.stringify(employee_names);
                    const encoded_names = encodeURIComponent(names_json);
                    console.log(names_json);

                    const url = `/api/method/clean_plus.services.employee_verification.custom_employee_pdf?names=${encoded_names}&print_lang=${selected_action}`;
                    window.open(url, '_blank');

                    employee_names.forEach(name => {
                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "Employee",
                                name: name,
                                fieldname: {
                                    custom_verification_printed: 1
                                }
                            },
                            callback: function () {
                                console.log(`Updated: ${name}`);
                            },
                            error: function (err) {
                                console.error(`Error updating ${name}:`, err);
                                frappe.msgprint("Error updating Employee verification print status.");
                            }
                        });
                    });

                    dialog.hide();
                    if (listview && listview.refresh) {
                        listview.refresh();
                    }

                    // frappe.set_route("List", "Employee");
                },
                function () {
                    // Cancelled — do nothing
                }
            );
        }

    });

    dialog.show();

    //print selection css
setTimeout(() => {
    let $field = $(dialog.fields_dict.action_choice.$wrapper);

    // Reduce the width of the entire field (label + input)
    $field.css({
                'display': 'flex',
        'justify-content': 'flex-end', 
        'max-width': '160px'  // or any smaller value you prefer
    });

    // Specifically reduce the <select> element width
    $field.find('select').css({
        'width': '160px',
        'font-weight': 'bold'
    });
}, 100);

    // Render filter controls
    const filter_section = dialog.get_field('filter_section').$wrapper;
    filter_section.html(`<div class="filters" style="display: flex; gap: 15px; margin-bottom: 10px;"></div>`);

    // Branch Filter
    const branch_filter = frappe.ui.form.make_control({
        df: {
            fieldname: 'branch_filter',
            label: 'Branch',
            fieldtype: 'Link',
            options: 'Branch',
            change: () => fetch_employees()
        },
        parent: filter_section.find('.filters'),
        render_input: true
    });
    branch_filter.make();

    // Department Filter
    const dept_filter = frappe.ui.form.make_control({
        df: {
            fieldname: 'department_filter',
            label: 'Department',
            fieldtype: 'Link',
            options: 'Department',
            change: () => fetch_employees()
        },
        parent: filter_section.find('.filters'),
        render_input: true
    });
    dept_filter.make();

    // Verification Status Filter
    const status_filter = frappe.ui.form.make_control({
        df: {
            fieldname: 'status_filter',
            label: 'Verification Status',
            fieldtype: 'Select',
            options: [
                { label: 'Select', value: '' },
                { label: 'Joining', value: 'Joining' },
                { label: 'Relieving', value: 'Relieving' }
            ],
            change: () => fetch_employees()
        },
        parent: filter_section.find('.filters'),
        render_input: true
    });
    status_filter.make();

    // Bulk Action Section Title
    const bulk_action_html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0 5px;">
            <h5 style="margin: 0;">Employee List</h5>
        </div>
    `;
    dialog.get_field('bulk_action_section').$wrapper.html(bulk_action_html);

    // Initial fetch
    fetch_employees();

    function fetch_employees() {
        const branch = branch_filter.get_value();
        const department = dept_filter.get_value();
        const verification_status = status_filter.get_value();

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Employee',
                filters: {
                    custom_needs_employee_verification: 1,
                    custom_verification_printed: 0,
                    ...(branch && { branch }),
                    ...(department && { department })
                },
                fields: ['name', 'employee_name', 'custom_referral_code', 'custom_aadhaar_number', 'status'],
                limit: 100
            },
            callback: function (r) {
                filtered_employees = r.message
                    .map(emp => ({
                        name: emp.name,
                        employee_name: emp.employee_name,
                        aadhar: emp.custom_aadhaar_number,
                        referral: emp.custom_referral_code,
                        status: emp.status === 'Active' ? 'Joining' : 'Relieving'
                    }))
                    .filter(emp => {
                        if (!verification_status) return true;
                        return emp.status === verification_status;
                    });

                render_table();
            }
        });
    }

    function render_table() {
        const wrapper = dialog.get_field('table_html').$wrapper;
        let html = `
            <div class="table-responsive" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 6px;">
                <table class="table table-hover" style="margin-bottom: 0;">
                    <thead style="position: sticky; top: 0; background: #f5f5f5; z-index: 1;">
                        <tr style="border-bottom: 1px solid #ccc;">
                            <th style="width:30px;"><input type="checkbox" id="select_all" ${selected_employees.size === filtered_employees.length ? 'checked' : ''}></th>
                            <th style="padding: 10px;">Employee Name</th>
                            <th style="padding: 10px;">Aadhar No</th>
                            <th style="padding: 10px;">Joining or Relieving</th>
                            <th style="padding: 10px;">Referral Code</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const emp of filtered_employees) {
            const checked = selected_employees.has(emp.name) ? 'checked' : '';
            html += `
                <tr style="transition: background 0.2s;">
                    <td style="padding: 8px 12px;"><input type="checkbox" class="emp-checkbox" data-name="${emp.name}" ${checked}></td>
                    <td style="padding: 8px 12px;">${emp.employee_name}</td>
                    <td style="padding: 8px 12px;">${emp.aadhar || ''}</td>
                    <td style="padding: 8px 12px;">${emp.status}</td>
                    <td style="padding: 8px 12px;">${emp.referral || ''}</td>
                </tr>
            `;
        }

        html += `
                    </tbody>
                </table>
            </div>
        `;

        wrapper.html(html);

        // Select all checkbox
        wrapper.find('#select_all').on('change', function () {
            if (this.checked) {
                filtered_employees.forEach(emp => selected_employees.add(emp.name));
            } else {
                selected_employees.clear();
            }
            render_table(); // Re-render to reflect changes
        });

        // Individual checkbox selection
        wrapper.find('.emp-checkbox').on('change', function () {
            const name = $(this).data('name');
            if (this.checked) {
                selected_employees.add(name);
            } else {
                selected_employees.delete(name);
            }
        });
    }
}
