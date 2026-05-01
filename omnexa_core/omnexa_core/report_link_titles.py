# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Populate frappe.response["_link_titles"] for Query Report runs so Link columns show titles (not raw IDs)."""

from __future__ import annotations

from collections import defaultdict

import frappe

from omnexa_core.omnexa_core.link_titles import get_link_title

# When reports wrongly declare Link fields as Data/Autocomplete, still resolve titles.
_HINT_FIELD_TO_DOCTYPE = {
	"customer": "Customer",
	"supplier": "Supplier",
	"employee": "Employee",
	"item": "Item",
	"item_code": "Item",
	"account": "GL Account",
	"gl_account": "GL Account",
}


def _chunks(names: list[str], size: int = 400):
	for i in range(0, len(names), size):
		yield names[i : i + size]


def build_link_title_map_for_report(columns: list | None, rows: list | None) -> dict[str, str]:
	"""Map ``Doctype::name`` → display string for Link / Dynamic Link columns."""
	out: dict[str, str] = {}
	if not columns or not rows:
		return out

	link_pairs: dict[str, set[str]] = defaultdict(set)
	dyn_pairs: list[tuple[str, str]] = []

	for col in columns:
		if not isinstance(col, dict):
			continue
		ft = col.get("fieldtype")
		fn = col.get("fieldname")
		if not fn:
			continue

		if ft == "Link":
			dt = (col.get("options") or "").strip()
			if not dt or dt == "Currency":
				continue
			for row in rows:
				if not isinstance(row, dict):
					continue
				val = row.get(fn)
				if val:
					link_pairs[dt].add(str(val))

		elif ft == "Dynamic Link":
			opt_fn = col.get("options")
			if not opt_fn:
				continue
			for row in rows:
				if not isinstance(row, dict):
					continue
				dt = row.get(opt_fn)
				val = row.get(fn)
				if dt and val:
					dyn_pairs.append((str(dt), str(val)))

		elif ft in ("Data", "Autocomplete"):
			hint_dt = _HINT_FIELD_TO_DOCTYPE.get(fn)
			if not hint_dt:
				continue
			for row in rows:
				if not isinstance(row, dict):
					continue
				val = row.get(fn)
				if val:
					link_pairs[hint_dt].add(str(val))

	for dt, names in link_pairs.items():
		for chunk in _chunks(list(names)):
			for nm in chunk:
				key = f"{dt}::{nm}"
				if key in out:
					continue
				try:
					out[key] = get_link_title(dt, nm) or nm
				except Exception:
					out[key] = nm

	for dt, nm in dyn_pairs:
		key = f"{dt}::{nm}"
		if key in out:
			continue
		try:
			out[key] = get_link_title(dt, nm) or nm
		except Exception:
			out[key] = nm

	return out


@frappe.whitelist()
@frappe.read_only()
def query_report_run_with_link_titles(
	report_name,
	filters=None,
	user=None,
	ignore_prepared_report=False,
	custom_columns=None,
	is_tree=False,
	parent_field=None,
	are_default_filters=True,
):
	from frappe.desk import query_report as qr

	result = qr.run(
		report_name,
		filters=filters,
		user=user,
		ignore_prepared_report=ignore_prepared_report,
		custom_columns=custom_columns,
		is_tree=is_tree,
		parent_field=parent_field,
		are_default_filters=are_default_filters,
	)

	try:
		if isinstance(result, dict):
			cols = result.get("columns") or []
			data = result.get("result")
			if cols and isinstance(data, list):
				lt = build_link_title_map_for_report(cols, data)
				if lt:
					prev = frappe.response.get("_link_titles") or {}
					prev.update(lt)
					frappe.response["_link_titles"] = prev
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: report_link_titles")

	return result
