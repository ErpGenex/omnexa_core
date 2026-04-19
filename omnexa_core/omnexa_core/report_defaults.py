# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.branch_access import get_default_branch, get_default_company


def auto_apply_company_branch_report_filters():
	"""Inject default company/branch for query reports if user didn't set filters.

	This keeps report UX aligned with user context and avoids hard failures like:
	'Company filter is required.'
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

	if not filters.get("company"):
		company = get_default_company()
		if company:
			filters["company"] = company

	if not filters.get("branch") and filters.get("company"):
		branch = get_default_branch(filters["company"])
		if branch:
			filters["branch"] = branch

	# Keep payload format stable for frappe.desk.query_report.run
	frappe.form_dict["filters"] = json.dumps(filters, separators=(",", ":"))

