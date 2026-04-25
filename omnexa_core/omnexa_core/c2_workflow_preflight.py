# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""E6.1 / G3 — بادئة C2: تغطية **Workflow** ووجود **Version** كمسار تدقيق تقني.

لا يُغني عن سياسة موافقات معتمدة أو مراجعة Audit؛ يُظهر فقط ما هو مفعّل في قاعدة البيانات.

Run::

    bench --site <site> execute omnexa_core.omnexa_core.c2_workflow_preflight.print_c2_workflow_preflight_report
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_to_date, cint, now_datetime


def _default_critical_doctypes() -> list[str]:
	raw = frappe.conf.get("omnexa_c2_preflight_doctypes")
	if isinstance(raw, list) and raw:
		return [str(x).strip() for x in raw if str(x).strip()]
	return [
		"Sales Invoice",
		"Purchase Invoice",
		"Journal Entry",
		"Payment Entry",
	]


def collect_c2_workflow_preflight() -> dict[str, Any]:
	now = now_datetime()
	since_30d = add_to_date(now, days=-30, as_datetime=True)
	since_7d = add_to_date(now, days=-7, as_datetime=True)

	doctypes = _default_critical_doctypes()
	workflow_rows: list[dict[str, Any]] = []
	if frappe.db.has_table("Workflow"):
		for dt in doctypes:
			if not frappe.db.exists("DocType", dt):
				continue
			wf = frappe.db.get_value(
				"Workflow",
				{"document_type": dt, "is_active": 1},
				["name", "workflow_state_field"],
				as_dict=True,
			)
			workflow_rows.append(
				{
					"doctype": dt,
					"active_workflow": wf.name if wf else None,
					"state_field": (wf or {}).get("workflow_state_field"),
				}
			)

	version_7d = 0
	if frappe.db.has_table("Version"):
		version_7d = cint(
			frappe.db.count(
				"Version",
				{"creation": (">", since_7d)},
			)
		)

	submitted_counts: dict[str, int | None] = {}
	for dt in doctypes:
		if not frappe.db.exists("DocType", dt):
			submitted_counts[dt] = None
			continue
		meta = frappe.get_meta(dt)
		if not meta.is_submittable:
			submitted_counts[dt] = frappe.db.count(dt, {"creation": (">", since_30d)})
		else:
			submitted_counts[dt] = frappe.db.count(
				dt,
				{"docstatus": 1, "creation": (">", since_30d)},
			)

	return {
		"site": getattr(frappe.local, "site", None),
		"critical_doctypes": doctypes,
		"workflow_coverage": workflow_rows,
		"version_rows_7d": version_7d,
		"documents_touch_30d": submitted_counts,
		"notes": "Configure omnexa_c2_preflight_doctypes in site_config to extend the checklist.",
	}


@frappe.whitelist()
def print_c2_workflow_preflight_report() -> str:
	frappe.only_for("System Manager")
	return json.dumps(collect_c2_workflow_preflight(), ensure_ascii=False, sort_keys=True, default=str)
