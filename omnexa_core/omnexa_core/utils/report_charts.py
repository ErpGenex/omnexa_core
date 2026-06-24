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
