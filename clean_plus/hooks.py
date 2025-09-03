app_name = "clean_plus"
app_title = "Clean Plus"
app_publisher = "Sil"
app_description = "ERP"
app_email = "sil@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "clean_plus",
# 		"logo": "/assets/clean_plus/logo.png",
# 		"title": "Clean Plus",
# 		"route": "/clean_plus",
# 		"has_permission": "clean_plus.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/clean_plus/css/splash_logo.css"
app_include_css = "/assets/clean_plus/css/employee.css"

# app_include_js = "/assets/clean_plus/js/clean_plus.js"

# include js, css files in header of web template
# web_include_css = "/assets/clean_plus/css/clean_plus.css"
# web_include_js = "/assets/clean_plus/js/clean_plus.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "clean_plus/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}

doctype_list_js = {
    "Employee": "public/js/employee_list.js"
}
doctype_js = {
    "Employee": "public/js/employee_form.js"

}

fixtures = [
    {
        "dt": "Custom Field",
         "filters": [["module", "=", "Clean Plus"]]
    },
    {
     "dt": "Client Script",
      "filters": [["module", "=", "Clean Plus"]]
    },
    {
        "dt": "DocType",
        "filters": [["module", "=", "Clean Plus"]]
    },
    {
    "dt": "Property Setter",
    "filters": [["module", "=", "Clean Plus"]]
    },
    {
     "dt": "Workspace",
     "filters": [["module", "=", "Clean Plus"]]   
    },
    {
     "dt": "Server Script",
      "filters": [["module", "=", "Clean Plus"]]
    },
    {
     "dt": "Role Profile",
     "filters": [["name", "=", "Management"]]
    },
    {
        "dt": "Role Profile",
        "filters": [["role_profile", "=", "Management"]]
    },    
    {
        "dt": "Workflow",
        "filters": [["document_type", "=", "Outpass Request"]]
    }
]


# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "clean_plus/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "clean_plus.utils.jinja_methods",
# 	"filters": "clean_plus.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "clean_plus.install.before_install"
# after_install = "clean_plus.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "clean_plus.uninstall.before_uninstall"
# after_uninstall = "clean_plus.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "clean_plus.utils.before_app_install"
# after_app_install = "clean_plus.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "clean_plus.utils.before_app_uninstall"
# after_app_uninstall = "clean_plus.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "clean_plus.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Salary Slip": {
		"before_save": "clean_plus.services.salaryslip.fetch_total_overtime",
        "before_save": "clean_plus.services.salaryslip.calculate_unofficial_outpass_hours"
	},
    "Attendance": {
        "validate": "clean_plus.services.attendance_utils.update_outpass_minutes"
    },
    "Outpass Request": {
        "on_submit": "clean_plus.services.movements.on_submit"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"clean_plus.tasks.all"
# 	],
# 	"daily": [
# 		"clean_plus.tasks.daily"
# 	],
# 	"hourly": [
# 		"clean_plus.tasks.hourly"
# 	],
# 	"weekly": [
# 		"clean_plus.tasks.weekly"
# 	],
# 	"monthly": [
# 		"clean_plus.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "clean_plus.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "clean_plus.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "clean_plus.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["clean_plus.utils.before_request"]
# after_request = ["clean_plus.utils.after_request"]

# Job Events
# ----------
# before_job = ["clean_plus.utils.before_job"]
# after_job = ["clean_plus.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"clean_plus.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

