# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe.utils import get_table_name

from omnexa_core.omnexa_core.activity_pqc import activity_permission_query_conditions
from omnexa_core.omnexa_core.branch_access import permission_query_conditions_for_branch_field


def global_branch_permission_query_conditions(user=None, doctype=None):
	"""Hook on '*' — branch/company + activity list filters for scoped DocTypes."""
	if not doctype:
		return ""

	activity_sql = activity_permission_query_conditions(user, doctype)
	if activity_sql == "1=0":
		return "1=0"

	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return activity_sql
	if meta.has_field("branch"):
		branch_sql = permission_query_conditions_for_branch_field(doctype, user)
	elif meta.has_field("company"):
		branch_sql = permission_query_conditions_for_company_field(doctype, user)
	else:
		branch_sql = ""

	parts = [part for part in (branch_sql, activity_sql) if part]
	if not parts:
		return ""
	if len(parts) == 1:
		return parts[0]
	return " AND ".join(f"({part})" for part in parts)


def permission_query_conditions_for_company_field(doctype: str, user: str | None = None) -> str:
	"""SQL fragment when DocType has company but no branch (e.g. Employee before branch row)."""
	from omnexa_core.omnexa_core.session_context import get_effective_company

	user = user or frappe.session.user
	company = get_effective_company(user)
	if not company:
		return ""

	table = get_table_name(doctype, wrap_in_backticks=True)
	return f"{table}.company = {frappe.db.escape(company)}"
