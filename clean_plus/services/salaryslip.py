import frappe

def fetch_total_overtime(slip, method=None):
    if not slip.employee or not slip.start_date or not slip.end_date:
        return

    overtime_entries = frappe.get_all(
        "Overtime Checkin",
        filters={
            "employee": slip.employee,
            "date": ["between", [slip.start_date, slip.end_date]]
        },
        fields=["total_overtime"]
    )

    total_seconds = 0
    for entry in overtime_entries:
        if entry.total_overtime:
            try:
                h, m, s = map(int, entry.total_overtime.split(":"))
                total_seconds += h * 3600 + m * 60 + s
            except ValueError:
                continue

    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    total_secs = total_seconds % 60

    time_str = f"{total_hours:02}:{total_minutes:02}:{total_secs:02}"
    float_hours = total_seconds / 3600  # <-- Corrected

    slip.custom_total_overtime_worked = time_str
    slip.custom_total_overtime_in_hours = float_hours

    # # Refresh the earnings child table
    # frappe.publish_realtime(
    #     event="refresh_field",
    #     message={
    #         "doctype": slip.doctype,
    #         "docname": slip.name,
    #         "field": "earnings"
    #     },
    #     user=frappe.session.user
    # )

def calculate_unofficial_outpass_hours(doc, method=None):
    total_hours = frappe.db.sql("""
        SELECT SUM(total_duration)
        FROM `tabOutpass Request`
        WHERE employee = %s
          AND docstatus = 1
          AND `request_status` = 'Approved'
          AND purpose_type = 'Unofficial'
          AND `date` BETWEEN %s AND %s
    """, (doc.employee, doc.start_date, doc.end_date))[0][0] or 0

    doc.custom_unofficial_outpass_hours = total_hours