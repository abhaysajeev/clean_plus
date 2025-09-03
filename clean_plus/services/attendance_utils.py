import frappe
def update_outpass_minutes(attendance, method):
    employee = attendance.employee
    att_date = attendance.attendance_date

    # get approved requests
    requests = frappe.get_all(
        "Outpass Request",
        filters={
            "employee": employee,
            "date": att_date,
            "request_status": "Approved"
        },
        fields=["name", "purpose_type"]
    )

    official, unofficial = 0, 0
    for req in requests:
        intervals = frappe.get_all(
            "Outpass Intervals",
            filters={"parent": req.name},
            fields=["duration"]
        )
        total = sum([row.duration for row in intervals])
        if req.purpose_type == "Official":
            official += total
        else:
            unofficial += total

    attendance.custom_official_movement_duration = official
    attendance.custom_unofficial_movement_duration = unofficial
    attendance.custom_net_working_duration = (
        (attendance.working_hours or 0) ## multiply with 60 for minutes
        + official - unofficial
    ) // 60  # store in hours if you prefer
