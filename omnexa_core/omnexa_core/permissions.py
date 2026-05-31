# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.branch_access import permission_query_conditions_for_branch_field


def global_branch_permission_query_conditions(user=None, doctype=None):
	"""Hook on '*' — branch/company list filters for every DocType that has a branch field."""
	if not doctype:
		return ""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return ""
	if not meta.has_field("branch"):
		return ""
	return permission_query_conditions_for_branch_field(doctype, user)
