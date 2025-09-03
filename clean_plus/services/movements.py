import frappe
@frappe.whitelist()
def get_employee_checkins(employee, date):
    logs = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
        },
        fields=["name", "time", "log_type"],
        order_by="time asc"
    )
    return logs

def on_submit(doc, method):
    """Link selected Employee Checkins to this Outpass Request"""
    for row in doc.outpass_intervals:
        if row.out_checkin:
            frappe.db.set_value("Employee Checkin", row.out_checkin, "custom_linked_movement", doc.name)
        if row.in_checkin:
            frappe.db.set_value("Employee Checkin", row.in_checkin, "custom_linked_movement", doc.name)
