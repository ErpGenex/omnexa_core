# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.branch_access import get_default_branch, get_default_company
from omnexa_core.omnexa_core.session_context import get_effective_company, get_view_context


def _merge_navbar_scope_into_report_filters(filters: dict) -> dict:
	"""Apply desk navbar company/branch to report filters (navbar is source of truth)."""
	if not isinstance(filters, dict):
		filters = {}

	# Consolidated / multi-company reports use `companies`, not `company`.
	if "companies" in filters and not filters.get("company"):
		return filters

	ctx = get_view_context()
	company = get_effective_company() or get_default_company()
	if company:
		filters["company"] = company

	if ctx.get("view_all_branches"):
		filters.pop("branch", None)
	elif company:
		branch = ctx.get("branch") or get_default_branch(company)
		if branch:
			filters["branch"] = branch

	return filters


def auto_apply_company_branch_report_filters():
	"""Inject default company, branch, from_date, to_date for Query Report API if unset.

	Company and branch always follow desk navbar context when set.
	Dates default to today (`frappe.utils.today()`).
	"""
	if frappe.session.user == "Guest":
		return

	cmd = (frappe.form_dict.get("cmd") or "").strip()
	path = (getattr(getattr(frappe.local, "request", None), "path", "") or "").strip()
	if cmd != "frappe.desk.query_report.run" and "/api/method/frappe.desk.query_report.run" not in path:
		return

	raw_filters = frappe.form_dict.get("filters")
	if raw_filters is None:
		filters: dict = {}
	elif isinstance(raw_filters, str):
		try:
			filters = json.loads(raw_filters) if raw_filters else {}
		except Exception:
			filters = {}
	elif isinstance(raw_filters, dict):
		filters = dict(raw_filters)
	else:
		filters = {}

	filters = _merge_navbar_scope_into_report_filters(filters)

	# Align with desk defaults: bounded date window defaults to Today when unset.
	td = frappe.utils.today()
	if not filters.get("from_date"):
		filters["from_date"] = td
	if not filters.get("to_date"):
		filters["to_date"] = td

	# Keep payload format stable for frappe.desk.query_report.run
	frappe.form_dict["filters"] = json.dumps(filters, separators=(",", ":"))
