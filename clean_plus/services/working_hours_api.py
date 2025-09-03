import frappe
from frappe.utils import today, getdate, now
from clean_plus.services.cron_api.dailyAvg import getDaily

@frappe.whitelist(allow_guest=True)
def generate_daily_working_hours_alerts():
    try:
        # Step 1: Get current date and fetch employees below threshold
        selected_date = getdate(today())
        employee_below_avg = getDaily(selected_date)
        
        # Step 2: Handle API errors
        if isinstance(employee_below_avg, dict) and "error" in employee_below_avg:
            return f"ERROR: {employee_below_avg['error']}"
        
        # Step 3: Check if any employees found
        if not employee_below_avg:
            return "SUCCESS: No employees below threshold today"
        
        # Step 4: Create the main Working Hours Alert document
        alert = frappe.get_doc({
            "doctype": "Working Hours Alert",
            "run_date": selected_date,
            "alert_type": "Daily",
            "threshold_hours": 8.0,
            "total_employees_below_threshold": len(employee_below_avg),
            "status": "New"
        })
        
        # Step 5: Add employees to child table (with department included)
        for employee_id, logs in employee_below_avg.items():
            for entry in logs:
                alert.append("working_hours_alert_detail", {
                    "employee": employee_id,
                    "department": entry["department"],  # Now department will be saved
                    "actual_hours": entry["daily_working_hours"],
                    "memo_generated": 0,
                })
        
        # Step 6: Save the alert document
        alert.insert(ignore_permissions=True)
        
        # Step 7: Get users with "Management" Role Profile
        management_users = frappe.get_all(
            "User",
            filters={
                "role_profile_name": "Management",
                "enabled": 1,
            },
            fields=["name"]
        )
        
        # Step 8: Create notifications for Management users (with deduplication)
        seen_users = set()
        notification_count = 0
        
        for user in management_users:
            if user["name"] not in seen_users:
                seen_users.add(user["name"])
                
                notification = frappe.new_doc("Notification Log")
                notification.update({
                    "for_user": user["name"],
                    "subject": f"Daily Working Hours Alert - {len(employee_below_avg)} employees below threshold",
                    "email_content": f"Alert generated for {selected_date}. {len(employee_below_avg)} employees worked less than 8 hours. Click to view details and generate memos.",
                    "type": "Alert",
                    "document_type": "Working Hours Alert",
                    "document_name": alert.name,
                    "from_user": frappe.session.user or "Administrator",
                    "read": 0
                })
                notification.insert(ignore_permissions=True)
                notification_count += 1
        
        # Step 9: Commit changes
        frappe.db.commit()
        
        return f"SUCCESS: Alert {alert.name} created with {len(employee_below_avg)} employees. Notifications sent to {notification_count} management users."
        
    except Exception as e:
        frappe.log_error(f"Alert generation failed: {str(e)}", "Daily Alert Error")
        return f"ERROR: {str(e)}"


