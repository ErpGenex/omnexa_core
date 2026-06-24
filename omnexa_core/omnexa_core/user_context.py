# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.branch_access import (
	get_allowed_branches,
	get_default_branch,
	get_default_company,
	user_can_access_all_branches,
)


def _branch_belongs_to_company(branch: str | None, company: str | None) -> bool:
	if not branch or not frappe.db.exists("Branch", branch):
		return False
	if not company:
		return True
	return frappe.db.get_value("Branch", branch, "company") == company


def _resolve_doc_branch(doc, company: str | None) -> str | None:
	if user_can_access_all_branches():
		from omnexa_core.omnexa_core.session_context import get_view_context

		ctx = get_view_context()
		if ctx.get("branch") and not ctx.get("view_all_branches"):
			candidate = ctx["branch"]
			if _branch_belongs_to_company(candidate, company or ctx.get("company")):
				return candidate
		if company:
			return get_default_branch(company)
		if ctx.get("company"):
			return get_default_branch(ctx["company"])
		return None

	if company:
		allowed = get_allowed_branches(company=company) or []
		if allowed:
			default = get_default_branch(company)
			if default and default in allowed:
				return default
			return allowed[0]
	return None


def apply_company_branch_defaults(doc, method=None):
	"""Populate company/branch from logged-in user context when missing (no manual entry)."""
	if frappe.flags.in_install:
		return
	if not getattr(frappe.local, "session", None):
		return
	if frappe.session.user == "Guest":
		return

	try:
		has_company = doc.meta.has_field("company")
		has_branch = doc.meta.has_field("branch")
	except Exception:
		return

	if not has_company and not has_branch:
		return

	if has_company and not doc.get("company"):
		doc.company = get_default_company()

	company = doc.get("company") if has_company else None

	if has_branch and doc.get("branch") and not _branch_belongs_to_company(doc.branch, company):
		doc.branch = None

	if has_branch and not doc.get("branch"):
		doc.branch = _resolve_doc_branch(doc, company)

	_apply_company_currency_default(doc)


def _apply_company_currency_default(doc) -> None:
	"""Set transaction currency from company before compliance / validate (field name: currency)."""
	try:
		if not doc.meta.has_field("currency") or (doc.get("currency") or "").strip():
			return
	except Exception:
		return
	company = doc.get("company") if doc.meta.has_field("company") else None
	if not company:
		return
	comp_curr = frappe.db.get_value("Company", company, "default_currency")
	if comp_curr:
		doc.currency = comp_curr


def get_allowed_branches_for_current_doc(doc) -> list[str] | None:
	company = getattr(doc, "company", None)
	if user_can_access_all_branches():
		from omnexa_core.omnexa_core.session_context import get_effective_branch_list

		allowed = get_effective_branch_list(company=company)
		return allowed
	return get_allowed_branches(company=company)
