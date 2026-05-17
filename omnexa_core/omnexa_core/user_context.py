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

	if has_branch and not doc.get("branch"):
		company = doc.get("company")
		if company:
			doc.branch = get_default_branch(company)
			if not doc.branch:
				branches = frappe.get_all(
					"Branch",
					filters={"company": company},
					pluck="name",
					limit=1,
					order_by="is_head_office desc, creation asc",
				)
				if branches:
					doc.branch = branches[0]

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
		return None
	return get_allowed_branches(company=company)
