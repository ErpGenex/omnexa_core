# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_table_name


PRIVILEGED_ROLES = {"System Manager", "Company Admin"}


def user_can_access_all_branches(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Administrator",):
		return True
	roles = set(frappe.get_roles(user))
	return bool(PRIVILEGED_ROLES & roles)


def get_allowed_branches(user: str | None = None, company: str | None = None) -> list[str] | None:
	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		return None
	filters = {"user": user}
	if company:
		filters["company"] = company
	return frappe.get_all("User Branch Access", filters=filters, pluck="branch")


def get_default_company(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	# 1) explicit defaults (user then global)
	row = frappe.db.sql(
		"""
		SELECT defvalue
		FROM `tabDefaultValue`
		WHERE parent IN (%s, '__default')
		  AND defkey IN ('company', 'Company')
		ORDER BY CASE WHEN parent = %s THEN 0 ELSE 1 END
		LIMIT 1
		""",
		(user, user),
	)
	if row and row[0][0]:
		return row[0][0]

	# 2) derive from user branch access if single-company
	if not user_can_access_all_branches(user):
		companies = frappe.get_all(
			"User Branch Access",
			filters={"user": user},
			fields=["company"],
			distinct=True,
		)
		if len(companies) == 1:
			return companies[0].company

	# 3) exactly one company on the site (common single-tenant installs)
	cos = frappe.get_all("Company", pluck="name", limit=2)
	if len(cos) == 1:
		return cos[0]

	return None


def get_default_branch(company: str, user: str | None = None) -> str | None:
	user = user or frappe.session.user
	# 1) explicit defaults
	row = frappe.db.sql(
		"""
		SELECT defvalue
		FROM `tabDefaultValue`
		WHERE parent IN (%s, '__default')
		  AND defkey IN ('branch', 'Branch')
		ORDER BY CASE WHEN parent = %s THEN 0 ELSE 1 END
		LIMIT 1
		""",
		(user, user),
	)
	if row and row[0][0]:
		branch = row[0][0]
		branch_company = frappe.db.get_value("Branch", branch, "company")
		if branch_company == company:
			return branch

	# 2) branch access grants for normal users
	if not user_can_access_all_branches(user):
		entries = frappe.get_all(
			"User Branch Access",
			filters={"user": user, "company": company},
			fields=["branch", "is_default"],
			order_by="is_default desc, modified asc",
		)
		if entries:
			return entries[0].branch
		return None

	# 3) privileged users: head office fallback
	head_office = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
	if head_office:
		return head_office
	return frappe.db.get_value("Branch", {"company": company}, "name")


def enforce_branch_access(doc, user: str | None = None):
	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		return
	branch = getattr(doc, "branch", None)
	company = getattr(doc, "company", None)
	if not branch:
		return
	allowed = set(get_allowed_branches(user, company) or [])
	if branch not in allowed:
		frappe.throw(_("You are not allowed to access this branch."), title=_("Branch Access"))


def permission_query_conditions_for_branch_field(doctype: str, user: str | None = None) -> str:
	"""Return a SQL fragment for list permission matching `branch` on `doctype` (or allow all if unrestricted)."""
	user = user or frappe.session.user
	allowed = get_allowed_branches(user)
	if allowed is None:
		return ""
	if not allowed:
		return "1=0"
	table = get_table_name(doctype, wrap_in_backticks=True)
	quoted = ", ".join([frappe.db.escape(v) for v in allowed])
	return f"({table}.branch in ({quoted}) or {table}.branch is null or {table}.branch = '')"
