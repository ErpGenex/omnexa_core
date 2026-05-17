app_name = "omnexa_core"
app_title = "ERPGENEX — Core"
app_publisher = "ErpGenEx"
app_description = "Core platform for ERPGENEX (omnexa_core)"
app_email = "dev@erpgenex.com"
app_license = "mit"

# Apps
# ------------------

# NOTE:
# Do not set required_apps here, because many dependent apps already require omnexa_core.
# Setting a reverse dependency causes recursive install loops (omnexa_core <-> omnexa_accounting, etc.).
#
# Full stack (``sites/apps.txt`` + optional GitHub org discovery) is installed automatically by default
# after ``bench install-app omnexa_core`` and on each migrate via ``install_required_site_apps``.
# Opt out of full-stack bootstrap with ``OMNEXA_AUTO_INSTALL_FULL_STACK_ON_CORE=0`` (core mandatory set only).
# After batch installs: optional full ``SiteMigration`` (``OMNEXA_AUTO_FINAL_MIGRATE_AFTER_STACK_BOOTSTRAP``)
# then desk sync; optional ``bench build`` (``OMNEXA_AUTO_BENCH_BUILD_AFTER_CORE_BOOTSTRAP``) for assets.
# On sites where core is already installed and apps are missing: ``bench --site <site> execute omnexa_core.install.sync_stack``
#
# Engineering: ``omnexa_engineering_consulting`` depends on core + PM only; ``omnexa_eng_*`` stub apps are optional.

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "omnexa_core",
# 		"logo": "/assets/omnexa_core/logo.png",
# 		"title": "Omnexa Core",
# 		"route": "/omnexa_core",
# 		"has_permission": "omnexa_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/omnexa_core/css/omnexa_core.css",
	"/assets/omnexa_core/css/workspace_help_panel.css",
	"/assets/omnexa_core/css/classic_form_tabs.css",
]
app_include_js = [
	"/assets/omnexa_core/js/frappe_ready_shim.js",
	"/assets/omnexa_core/js/model_with_doctype_guard.js",
	"/assets/omnexa_core/js/workspace_shortcut_icons.js",
	"/assets/omnexa_core/js/workspace_desk_get_data_charts.js",
	"/assets/omnexa_core/js/form_layout_optimizer.js",
	"/assets/omnexa_core/js/erpgenex_brand_desk.js",
	"/assets/omnexa_core/js/desk_license_guard.js",
	"/assets/omnexa_core/js/global_long_ops_progress.js",
	"/assets/omnexa_core/js/sell_pos_quick_action.js",
	"/assets/omnexa_core/js/query_report_date_range_defaults.js",
	"/assets/omnexa_core/js/query_report_ux_enhancements.js",
	"/assets/omnexa_core/js/branch_eta_signing.js",
]

# Fallback logo URL if Navbar Settings has no app_logo value.
app_logo_url = "/assets/omnexa_core/images/erpgenex-logo.svg"

# include js, css files in header of web template
# web_include_css = "/assets/omnexa_core/css/omnexa_core.css"
# web_include_js = "/assets/omnexa_core/js/omnexa_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omnexa_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Event Dead Letter": "public/js/event_dead_letter.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "omnexa_core/public/icons.svg"

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
# 	"methods": "omnexa_core.utils.jinja_methods",
# 	"filters": "omnexa_core.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "omnexa_core.install.before_install"
after_install = "omnexa_core.install.after_install"
before_migrate = "omnexa_core.install.before_migrate"
after_migrate = "omnexa_core.install.after_migrate"
setup_wizard_requires = ["/assets/omnexa_core/js/omnexa_core_setup_wizard.js"]
setup_wizard_complete = "omnexa_core.install.setup_wizard_create_core_masters"

# Uninstallation
# ------------

# before_uninstall = "omnexa_core.uninstall.before_uninstall"
# after_uninstall = "omnexa_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "omnexa_core.utils.before_app_install"
after_app_install = "omnexa_core.install.after_any_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "omnexa_core.utils.before_app_uninstall"
# after_app_uninstall = "omnexa_core.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "omnexa_core.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
	"*": {
		"before_validate": [
			"omnexa_core.omnexa_core.user_context.apply_company_branch_defaults",
			"omnexa_core.omnexa_core.compliance_guard.enforce_global_enterprise_compliance",
		],
	}
}

_event_overlay_doctypes = [
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Stock Entry",
	"Delivery Note",
	"Purchase Receipt",
	"Journal Entry",
]

for _dt in _event_overlay_doctypes:
	doc_events.setdefault(_dt, {})
	doc_events[_dt]["before_submit"] = "omnexa_core.omnexa_core.compliance_guard.enforce_global_submit_compliance"
	doc_events[_dt]["on_submit"] = "omnexa_core.omnexa_core.event_dispatcher.on_submit_emit"
	doc_events[_dt]["on_cancel"] = "omnexa_core.omnexa_core.event_dispatcher.on_cancel_emit"

# Default event subscribers (overlay-safe; can be extended by other apps).
omnexa_core_event_handlers = [
	"omnexa_core.omnexa_core.default_event_handlers.accounting_audit_handler",
	"omnexa_core.omnexa_core.default_event_handlers.inventory_audit_handler",
]

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"omnexa_core.omnexa_core.event_dispatcher.monitor_event_pipeline",
	],
	"daily": [
		"omnexa_core.erpgenex_scheduler.run_erpgenex_daily_jobs",
	],
}

# Testing
# -------

# before_tests = "omnexa_core.install.before_tests"

# Overriding Methods
# ------------------------------
override_whitelisted_methods = {
	"frappe.desk.query_report.run": "omnexa_core.omnexa_core.report_link_titles.query_report_run_with_link_titles",
	"frappe.desk.search.get_link_title": "omnexa_core.omnexa_core.link_titles.get_link_title",
	# Some deployments ship with `frappe.sessions.get` not registered as whitelisted.
	# Desk relies on it for boot; we route it to an Omnexa-managed endpoint.
	"frappe.sessions.get": "omnexa_core.session_boot.sessions_get",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "omnexa_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = [
	"omnexa_core.omnexa_core.license_gate.before_request",
	"omnexa_core.omnexa_core.report_defaults.auto_apply_company_branch_report_filters",
]
# after_request = ["omnexa_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["omnexa_core.utils.before_job"]
# after_job = ["omnexa_core.utils.after_job"]

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
# 	"omnexa_core.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# Desk boot: replace legacy product name in Success Action / notes payloads.
boot_session = "omnexa_core.erpgenex_brand.boot_session"

