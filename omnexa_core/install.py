# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def after_install():
	ensure_omnexa_roles()


def after_migrate():
	ensure_omnexa_roles()
	remove_legacy_people_workspace()
	remove_legacy_finance_workspace()
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import sync_all_workspace_kpi_layout

		sync_all_workspace_kpi_layout()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: sync_all_workspace_kpi_layout")


def remove_legacy_people_workspace():
	"""Single HR desk: drop duplicate Omnexa Core workspace `People` (use `/app/hr`)."""
	if not frappe.db.exists("Workspace", "People"):
		return
	try:
		frappe.delete_doc("Workspace", "People", force=1, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: remove_legacy_people_workspace")


def remove_legacy_finance_workspace():
	"""Single finance desk: `Finance` duplicated links already on Accounting (`/app/accounting`)."""
	if not frappe.db.exists("Workspace", "Finance"):
		return
	try:
		frappe.delete_doc("Workspace", "Finance", force=1, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: remove_legacy_finance_workspace")


def ensure_omnexa_roles():
	"""Create baseline roles referenced by Omnexa Core DocTypes (see Docs/specs)."""
	for role_name in ("Company Admin", "Tax Integration"):
		if frappe.db.exists("Role", role_name):
			continue
		doc = frappe.new_doc("Role")
		doc.role_name = role_name
		doc.desk_access = 1
		doc.is_custom = 1
		doc.insert(ignore_permissions=True)
