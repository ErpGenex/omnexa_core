# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared chart builders for Omnexa Script Reports."""

from __future__ import annotations

from frappe import _


def currency_bar_chart(rows: list[dict], *, label_field: str, value_field: str, title: str, limit: int = 12) -> dict:
	labels = [str(r.get(label_field) or "") for r in rows[:limit]]
	values = [float(r.get(value_field) or 0) for r in rows[:limit]]
	return {
		"data": {"labels": labels, "datasets": [{"name": title, "values": values}]},
		"type": "bar",
		"title": _(title),
		"height": 260,
	}


def grouped_sum_chart(
	rows: list[dict],
	*,
	group_field: str,
	value_field: str,
	title: str,
	limit: int = 10,
) -> dict:
	totals: dict[str, float] = {}
	for row in rows:
		key = str(row.get(group_field) or _("Unspecified"))
		totals[key] = totals.get(key, 0.0) + float(row.get(value_field) or 0)
	ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]
	return {
		"data": {
			"labels": [item[0] for item in ranked],
			"datasets": [{"name": _(title), "values": [item[1] for item in ranked]}],
		},
		"type": "bar",
		"title": _(title),
		"height": 280,
	}


def governance_policy_chart(*, pending: int, approved: int, rejected: int) -> dict:
	return {
		"data": {
			"labels": [_("Pending"), _("Approved"), _("Rejected")],
			"datasets": [{"name": _("Policy Versions"), "values": [pending, approved, rejected]}],
		},
		"type": "bar",
		"title": _("Policy Approval Status"),
		"height": 260,
	}


_NUMERIC = ("Currency", "Float", "Int", "Percent")
_DIMENSION = ("Data", "Link", "Select")
_GROUP_HINTS = ("status", "type", "category", "stage", "bucket", "band", "severity", "department", "branch", "section")
_VALUE_HINTS = ("count", "total", "amount", "revenue", "qty", "outstanding", "cases", "appointments", "balance", "profit")


def auto_chart_for_columns(rows: list[dict], columns: list[dict], *, title: str | None = None) -> dict | None:
	"""Pick a sensible bar chart from report rows + column metadata."""
	if not rows or not columns:
		return None

	group_field = None
	value_field = None
	for col in columns:
		fieldname = col.get("fieldname")
		fieldtype = col.get("fieldtype")
		if not fieldname:
			continue
		low = fieldname.lower()
		if fieldtype in _DIMENSION and group_field is None and any(h in low for h in _GROUP_HINTS):
			group_field = fieldname
		if fieldtype in _NUMERIC and value_field is None and any(h in low for h in _VALUE_HINTS):
			value_field = fieldname

	if not group_field:
		for col in columns:
			if col.get("fieldtype") in _DIMENSION and col.get("fieldname"):
				group_field = col["fieldname"]
				break
	if not value_field:
		for col in columns:
			fn = col.get("fieldname")
			if col.get("fieldtype") in _NUMERIC and fn not in ("idx",):
				value_field = fn
				break
	if not group_field or not value_field:
		return None

	chart_title = title or group_field.replace("_", " ").title()
	return grouped_sum_chart(rows, group_field=group_field, value_field=value_field, title=chart_title)
