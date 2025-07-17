import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template

@frappe.whitelist()
def custom_employee_pdf(names, print_lang):
    import json
    # Parse the names
    names = json.loads(names)

    # Get employee records
    employees = frappe.get_all(
        "Employee",
        filters={"name": ["in", names]},
        fields=["name", "employee_name", "custom_aadhaar_number", "custom_referral_code", "image","cell_number", "custom_full_name_malayalam"]
    )

    # Convert images to base64
    for employee in employees:
        image_path = employee.get("image")
        if image_path:
            try:
                employee["image_base64"] = image_to_base64(image_path)
            except Exception as e:
                frappe.log_error(f"Image conversion failed for {employee['name']}: {str(e)}")
                employee["image_base64"] = ""  # fallback if conversion fails
        else:
            employee["image_base64"] = ""

    # Render the HTML with the base64 images

    template_path = "clean_plus/templates/employee_verification_en.html" \
    if print_lang == "Print English" else "clean_plus/templates/employee_verification_ml.html"

    html_template = frappe.render_template(
        template_path,
        {"employees": employees}
    )

    # Generate the PDF
    pdf = get_pdf(html_template)

    # Return PDF as a downloadable response
    frappe.response.filename = "CustomEmployees.pdf"
    frappe.response.filecontent = pdf
    frappe.response.type = "download"


def image_to_base64(img_path):
    import os
    import base64
    from frappe.utils import get_site_path
    import mimetypes

    if not img_path.startswith("/private/files"):
        raise ValueError("Only private file paths are supported. Path must start with /private/files")

    # Convert relative path to absolute path in the site
    full_path = get_site_path(img_path.lstrip("/"))

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Image not found: {full_path}")

    # Detect MIME type (e.g., image/jpeg, image/png)
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Read and encode the file
    with open(full_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode("utf-8")
        image_base64 = f"data:{mime_type};base64,{encoded_string}"

    return image_base64



