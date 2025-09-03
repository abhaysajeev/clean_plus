import io
import frappe
from frappe.utils import nowdate, formatdate, cint, escape_html
from frappe.utils.pdf import get_pdf
import json

@frappe.whitelist()
def generate_memos_for_alert(alert_name, employee_ids=None):
    """
    Generate memo PDFs for selected employees from a Working Hours Alert.
    """
    
    print("#"*50)
    print(f"Received employee_ids: {employee_ids}")
    print(f"Type of employee_ids: {type(employee_ids)}")

    # FIXED: Proper parameter handling - employee_ids comes as a list from frappe.call
    if not employee_ids:
        employee_ids = []
    elif isinstance(employee_ids, str):
        try:
            employee_ids = json.loads(employee_ids)
        except:
            employee_ids = [employee_ids]  # Single employee ID as string
    
    print(f"Processed employee_ids: {employee_ids}")

    # --- Fetch the alert doc ---
    try:
        alert = frappe.get_doc('Working Hours Alert', alert_name)
    except frappe.DoesNotExistError:
        frappe.throw(f"Working Hours Alert '{alert_name}' not found")
        
    if not alert.working_hours_alert_detail:
        return {"ok": True, "summary": {"created": 0, "skipped": 0, "errors": 0}}

    # --- Map employee -> child row ---
    child_by_emp = {row.employee: row for row in alert.working_hours_alert_detail if row.employee}
    print(f"Available employees in alert: {list(child_by_emp.keys())}")

    created = 0
    skipped = 0
    errors = 0
    memo_date = nowdate()

    for emp in employee_ids:
        print(f"Processing employee: '{emp}'")
        
        child = child_by_emp.get(emp)
        if not child:
            print(f"Child row not found for employee: {emp}")
            skipped += 1
            continue
            
        if cint(child.memo_generated):
            print(f"Memo already generated for employee: {emp}")
            skipped += 1
            continue

        try:
            # FIXED: Fetch employee details with proper error handling
            employee_doc = frappe.get_doc('Employee', emp)
            emp_name = employee_doc.employee_name or emp
            emp_company = employee_doc.company or frappe.defaults.get_global_default('company') or 'Company'
            department = child.department or employee_doc.department or ''
            hours = child.actual_hours or 0
            
            print(f"Employee details - Name: {emp_name}, Company: {emp_company}, Dept: {department}")

            # --- Render Memo HTML ---
            html = _render_memo_html(
                company=emp_company,
                employee_id=emp,
                employee_name=emp_name,
                department=department,
                memo_date=memo_date,
                run_date=str(alert.run_date),
                actual_hours=hours,
                threshold=alert.threshold_hours or 8.0,
                alert_name=alert.name
            )

            # --- Convert HTML to PDF ---
            pdf_content = get_pdf(html)
            print(f"PDF generated for employee: {emp}")

            # --- Create Memo Reference doc ---
            memo_doc = frappe.get_doc({
                'doctype': 'Memo Reference',
                'custom_employee': emp,
                'custom_memo_date': memo_date,
            })
            memo_doc.insert(ignore_permissions=True)
            print(f"Memo Reference created: {memo_doc.name}")

            # --- Attach PDF ---
            filename = f"Memo_{emp.replace(' ', '_')}_{memo_date}.pdf"
            file_doc = _attach_pdf_to_doc(
                doctype='Memo Reference',
                docname=memo_doc.name,
                filename=filename,
                content=pdf_content
            )
            
            print(f"PDF attached with filename: {filename}")

            # --- Update memo reference field ---
            if file_doc and file_doc.file_url:
                memo_doc.db_set('custom_memo_reference', file_doc.file_url, update_modified=False)
                print(f"Memo reference field updated: {file_doc.file_url}")

            # --- Mark child row as memo_generated ---
            child.db_set('memo_generated', 1, update_modified=False)
            print(f"Child row marked as memo_generated for employee: {emp}")

            created += 1

        except Exception as e:
            errors += 1
            error_msg = f"Memo generation failed for {emp}: {str(e)}"
            print(f"ERROR: {error_msg}")
            frappe.log_error(frappe.get_traceback(), error_msg)

    # Commit all changes
    frappe.db.commit()

    summary = {"created": created, "skipped": skipped, "errors": errors}
    print(f"Final summary: {summary}")
    return {"ok": True, "summary": summary}


def _attach_pdf_to_doc(doctype, docname, filename, content):
    """Create a File record and attach it to the given document."""
    try:
        file_doc = frappe.get_doc({
            'doctype': 'File',
            'file_name': filename,
            'attached_to_doctype': doctype,
            'attached_to_name': docname,
            'content': content,
            'is_private': 1
        })
        file_doc.save(ignore_permissions=True)
        print(f"File document saved: {file_doc.name}")
        return file_doc
    except Exception as e:
        print(f"Error attaching file: {str(e)}")
        raise


def _render_memo_html(company, employee_id, employee_name, department,
                      memo_date, run_date, actual_hours, threshold,
                      alert_name):
    """Return a minimal, clean HTML for memo PDF."""
    memo_date_fmt = formatdate(memo_date)
    run_date_fmt = formatdate(run_date)
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Memo - {escape_html(employee_name)}</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; font-size: 12px; color: #111; }}
    .wrap {{ padding: 24px; }}
    .hdr {{ display:flex; justify-content:space-between; align-items:flex-start; }}
    .company {{ font-size: 16px; font-weight: 600; }}
    .meta {{ text-align:right; }}
    h1 {{ font-size: 18px; margin: 16px 0 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    td, th {{ border: 1px solid #ddd; padding: 8px; }}
    .muted {{ color:#555; }}
    .note {{ margin-top: 18px; background:#f8f8f8; padding:12px; border:1px solid #eee; }}
    .sign {{ margin-top: 40px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr">
      <div class="company">{escape_html(company)}</div>
      <div class="meta">
        <div><b>Memo Date:</b> {escape_html(memo_date_fmt)}</div>
        <div><b>Alert Ref:</b> {escape_html(alert_name)}</div>
      </div>
    </div>

    <h1>Working Hours Memo</h1>

    <table>
      <tr><th>Employee ID</th><td>{escape_html(employee_id)}</td></tr>
      <tr><th>Employee Name</th><td>{escape_html(employee_name)}</td></tr>
      <tr><th>Department</th><td>{escape_html(department or '-')}</td></tr>
      <tr><th>Alert Run Date</th><td>{escape_html(run_date_fmt)}</td></tr>
      <tr><th>Actual Working Hours</th><td>{actual_hours:.2f}</td></tr>
      <tr><th>Threshold (Hours)</th><td>{threshold:.2f}</td></tr>
    </table>

    <div class="note">
      This memo is issued to record that the working hours on {escape_html(run_date_fmt)}
      were below the threshold of {threshold:.2f} hours. Please ensure adherence to the prescribed
      working hours. If there are any extenuating circumstances, contact your reporting manager.
    </div>

    <div class="sign">
      <div class="muted">Authorized Signatory</div>
      <div style="margin-top:48px;border-top:1px solid #ccc;width:200px;"></div>
    </div>
  </div>
</body>
</html>
    """