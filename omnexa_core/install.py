# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def after_install():
	ensure_omnexa_roles()


def after_migrate():
	ensure_omnexa_roles()


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
