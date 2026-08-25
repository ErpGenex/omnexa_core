# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared desk company/branch resolution for all Omnexa vertical apps."""

from __future__ import annotations

import frappe


def resolve_effective_company(user: str | None = None, *, fallback_first: bool = True) -> str | None:
	try:
		from omnexa_core.omnexa_core.session_context import get_effective_company

		company = get_effective_company(user)
		if company and frappe.db.exists("Company", company):
			return company
	except Exception:
		pass
	try:
		company = frappe.defaults.get_user_default("Company", user=user)
	except Exception:
		company = None
	if company and frappe.db.exists("Company", company):
		return company
	if fallback_first:
		return frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	return None


def resolve_effective_branch(company: str | None = None, user: str | None = None) -> str | None:
	user = user or frappe.session.user
	company = company or resolve_effective_company(user, fallback_first=False)
	try:
		from omnexa_core.omnexa_core.session_context import get_view_context

		ctx = get_view_context(user)
		branch = ctx.get("branch")
		if branch and frappe.db.exists("Branch", branch):
			if not company or frappe.db.get_value("Branch", branch, "company") == company:
				return branch
	except Exception:
		pass
	try:
		branch = frappe.defaults.get_user_default("Branch", user=user)
	except Exception:
		branch = None
	if branch and frappe.db.exists("Branch", branch):
		if not company or frappe.db.get_value("Branch", branch, "company") == company:
			return branch
	if company:
		return frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc")
	return None


def allowed_branch_names(user: str | None = None, company: str | None = None) -> list[str] | None:
	try:
		from omnexa_core.omnexa_core.session_context import get_effective_branch_list

		return get_effective_branch_list(user, company)
	except Exception:
		return None
