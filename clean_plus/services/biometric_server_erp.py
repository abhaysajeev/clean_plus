import frappe
from frappe.utils import get_datetime, getdate
from frappe import _
from frappe.model.naming import make_autoname

@frappe.whitelist(allow_guest=True)
def add_checkin(punchingcode, employee_name, time, device_id):
    # Get employee by biometric ID
    employee = frappe.db.get_value(
        "Employee",
        {"attendance_device_id": punchingcode},
        ["name", "employee_name"]
    )

    if not employee:
        frappe.throw(_("No Employee found for Biometric ID: {0}").format(punchingcode), frappe.DoesNotExistError)

    employee_id, full_name = employee
    checkin_time = get_datetime(time)
    checkin_date = getdate(checkin_time)

    # Determine log_type
    log_type = "IN"
    last_log_type = frappe.db.sql(
        """
        SELECT log_type FROM `tabEmployee Checkin`
        WHERE employee = %s AND DATE(time) = %s
        ORDER BY time DESC LIMIT 1
        """,
        (employee_id, checkin_date),
        as_dict=0
    )

    if last_log_type:
        log_type = "OUT" if last_log_type[0][0] == "IN" else "IN"

    # Generate name using naming series (e.g., CHKIN-00001)
    name = make_autoname('CHKIN-.#####')

    # Insert using SQL
    frappe.db.sql("""
        INSERT INTO `tabEmployee Checkin`
        (name, creation, modified, modified_by, owner, docstatus, idx,
         employee, employee_name, time, device_id, log_type)
        VALUES (%s, NOW(), NOW(), %s, %s, 0, 0,
         %s, %s, %s, %s, %s)
    """, (
        name, frappe.session.user, frappe.session.user,
        employee_id, full_name, checkin_time, device_id, log_type
    ))

    return {
        "status": "success",
        "name": name,
        "log_type": log_type,
        "checkin_time": checkin_time
    }
