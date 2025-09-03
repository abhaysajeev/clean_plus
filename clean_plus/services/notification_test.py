import frappe

@frappe.whitelist(allow_guest=True)
def test_notification():
    try:
        target_user = "Administrator"
        
        # Create a notification that links to an Employee document
        # (You can change this to any existing document)
        notification = frappe.new_doc("Notification Log")
        
        notification.update({
            "for_user": target_user,
            "subject": "Test notification - Click to view Employee",
            "email_content": "Click this notification to open Employee form",
            "type": "Alert",
            "from_user": frappe.session.user or "Administrator",
            "read": 0,
            # These fields make it clickable and redirect to document
            "document_type": "Employee",  # The doctype to open
            "document_name": get_first_employee(),  # Specific document name
        })
        
        notification.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return f"SUCCESS: Clickable notification created linking to Employee"
        
    except Exception as e:
        frappe.log_error(f"Notification test failed: {str(e)}", "Test Notification Error")
        return f"ERROR: {str(e)}"

def get_first_employee():
    """Get the first employee from the system for testing"""
    employee = frappe.db.get_value("Employee", {}, "name")
    return employee