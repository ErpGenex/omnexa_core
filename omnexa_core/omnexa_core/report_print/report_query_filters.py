# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Shared filter → SQL / get_all helpers for Script Reports."""

from __future__ import annotations

import frappe
from frappe import _


def prepare_filters(filters=None) -> frappe._dict:
	return frappe._dict(filters or {})


def _meta(doctype: str):
	return frappe.get_meta(doctype)


def sql_conditions(
	filters: frappe._dict,
	doctype: str,
	*,
	date_field: str = "creation",
	company: bool = True,
	branch: bool = True,
	require_company: bool = False,
	table_alias: str | None = None,
	extra_links: dict[str, str] | None = None,
) -> tuple[list[str], dict]:
	"""Build WHERE fragments and params for frappe.db.sql."""
	filters = prepare_filters(filters)
	prefix = f"{table_alias}." if table_alias else ""
	conditions = ["1=1"]
	params: dict = {}

	meta = _meta(doctype)
	if company and meta.has_field("company"):
		if filters.get("company"):
			conditions.append(f"{prefix}company = %(company)s")
			params["company"] = filters.company
		elif require_company:
			frappe.throw(_("Company is required."), title=_("Filters"))

	if branch and meta.has_field("branch") and filters.get("branch"):
		conditions.append(f"{prefix}branch = %(branch)s")
		params["branch"] = filters.branch

	if date_field and meta.has_field(date_field):
		if filters.get("from_date"):
			conditions.append(f"{prefix}{date_field} >= %(from_date)s")
			params["from_date"] = filters.from_date
		if filters.get("to_date"):
			conditions.append(f"{prefix}{date_field} <= %(to_date)s")
			params["to_date"] = filters.to_date

	for fieldname, options in (extra_links or {}).items():
		if filters.get(fieldname) and meta.has_field(fieldname):
			conditions.append(f"{prefix}{fieldname} = %({fieldname})s")
			params[fieldname] = filters.get(fieldname)

	return conditions, params


def get_all_filters(
	filters: frappe._dict,
	doctype: str,
	*,
	date_field: str = "creation",
	company: bool = True,
	branch: bool = True,
	extra_links: dict[str, str] | None = None,
) -> dict:
	"""Build frappe.get_all filters dict."""
	filters = prepare_filters(filters)
	out: dict = {}
	meta = _meta(doctype)

	if company and meta.has_field("company") and filters.get("company"):
		out["company"] = filters.company
	if branch and meta.has_field("branch") and filters.get("branch"):
		out["branch"] = filters.branch

	if date_field and meta.has_field(date_field):
		if filters.get("from_date") and filters.get("to_date"):
			out[date_field] = ["between", [filters.from_date, filters.to_date]]
		elif filters.get("from_date"):
			out[date_field] = [">=", filters.from_date]
		elif filters.get("to_date"):
			out[date_field] = ["<=", filters.to_date]

	for fieldname in (extra_links or {}):
		if filters.get(fieldname) and meta.has_field(fieldname):
			out[fieldname] = filters.get(fieldname)

	return out


def policy_version_filters(filters: frappe._dict) -> dict:
	"""Governance Overview — optional status on *Policy Version doctypes."""
	filters = prepare_filters(filters)
	out: dict = {}
	if filters.get("policy_status"):
		out["status"] = filters.policy_status
	return out
