frappe.ui.form.on('Working Hours Alert', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.working_hours_alert_detail?.length) {
            frm.add_custom_button('Generate Memos', () => open_generate_memo_dialog(frm), 'Actions');
        }
    }
});

function open_generate_memo_dialog(frm) {
    // Build HTML with checkboxes for each child row that doesn't have memo_generated = 1
    const rows = (frm.doc.working_hours_alert_detail || []).map((r) => {
        const disabled = r.memo_generated ? 'disabled' : '';
        const checked = !r.memo_generated ? 'checked' : '';
        // Store the original employee ID without HTML escaping to preserve spaces
        return `
            <tr>
                <td style="text-align:center;">
                    <input type="checkbox" class="memo-emp" data-employee="${r.employee || ''}" ${checked} ${disabled} />
                </td>
                <td>${frappe.utils.escape_html(r.employee || '')}</td>
                <td>${frappe.utils.escape_html(r.department || '')}</td>
                <td style="text-align:right;">${(r.actual_hours ?? '').toString()}</td>
                <td>${r.memo_generated ? '<span class="text-success">Yes</span>' : 'No'}</td>
            </tr>
        `;
    }).join('');

    const html = `
        <div style="max-height:360px; overflow:auto; border:1px solid var(--border-color); border-radius:8px;">
            <table class="table table-bordered" style="margin:0;">
                <thead>
                    <tr>
                        <th style="width:48px; text-align:center;">
                            <input type="checkbox" id="memo-select-all" />
                        </th>
                        <th>Employee</th>
                        <th>Department</th>
                        <th style="text-align:right;">Actual Hours</th>
                        <th>Memo Generated</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
        <div class="mt-3 text-muted">
            <small>Tip: Already generated memos are disabled.</small>
        </div>
    `;

    const d = new frappe.ui.Dialog({
        title: 'Generate Memos for Selected Employees',
        fields: [
            { fieldtype: 'HTML', fieldname: 'list_html' }
        ],
        primary_action_label: 'Generate Memo',
        primary_action: () => {
            // FIXED: Collect only SELECTED employee IDs from checked checkboxes
            const selected_checkboxes = d.$wrapper.find('input.memo-emp:checked');
            const emp_ids = [];
            
            selected_checkboxes.each(function() {
                const emp_id = $(this).data('employee');
                if (emp_id) {
                    emp_ids.push(emp_id);
                }
            });

            console.log('Selected employee IDs:', emp_ids);

            if (!emp_ids.length) {
                frappe.msgprint('Please select at least one employee.');
                return;
            }

            // Call server-side method
            frappe.call({
                method: 'clean_plus.services.working_hours_detail.memo.generate_memos_for_alert',
                freeze: true,
                freeze_message: 'Generating memos...',
                args: {
                    alert_name: frm.doc.name,
                    employee_ids: emp_ids // Send as array directly, no JSON.stringify needed
                },
                callback: (r) => {
                    if (r.message && r.message.summary) {
                        const s = r.message.summary;
                        frappe.msgprint(`
                            <b>Memo generation complete</b><br>
                            Created: ${s.created} &nbsp;|&nbsp; 
                            Skipped (already generated): ${s.skipped} &nbsp;|&nbsp; 
                            Errors: ${s.errors}
                        `);
                    }
                    frm.reload_doc();
                    d.hide();
                },
                error: (r) => {
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Failed to generate memos. Please check the error log for details.',
                        indicator: 'red'
                    });
                    console.error('Memo generation error:', r);
                }
            });
        }
    });

    d.fields_dict.list_html.$wrapper.html(html);

    // Select All toggle functionality
    d.$wrapper.find('#memo-select-all').on('change', function () {
        const checked = this.checked;
        d.$wrapper.find('input.memo-emp:not(:disabled)').prop('checked', checked);
    });

    d.show();
}