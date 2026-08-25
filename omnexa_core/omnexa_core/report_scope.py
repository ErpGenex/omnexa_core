# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Default report filters from desk view context (§2.6)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.report_defaults import _merge_navbar_scope_into_report_filters
from omnexa_core.omnexa_core.session_context import get_effective_branch_list, get_effective_company, get_view_context


@frappe.whitelist()
def get_default_report_filters(doctype: str | None = None) -> dict:
	"""Return company/branch defaults for Query Reports and dashboards."""
	ctx = get_view_context()
	company = ctx.get("company") or get_effective_company()
	branch = ctx.get("branch")
	branches = get_effective_branch_list(frappe.session.user, company)
	filters = {}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	elif branches is not None and len(branches) == 1:
		filters["branch"] = branches[0]
	return {
		"filters": filters,
		"context": ctx,
		"doctype": doctype,
	}


def resolve_report_filters(filters=None) -> frappe._dict:
	"""Merge navbar company/branch into Script Report filters before execute()."""
	base = frappe._dict(filters or {})
	merged = _merge_navbar_scope_into_report_filters(dict(base))
	result = frappe._dict(base)
	for key, value in merged.items():
		if value not in (None, ""):
			result[key] = value
	if "branch" not in merged:
		result.pop("branch", None)
	return result


def inject_filters_into_report_dict(report_dict: dict) -> dict:
	filters = get_default_report_filters().get("filters") or {}
	existing = report_dict.get("filters") or {}
	for key, value in filters.items():
		if key not in existing and value:
			existing[key] = value
	report_dict["filters"] = existing
	return report_dict
