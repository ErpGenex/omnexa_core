# Copyright (c) 2026, ErpGenEx
"""Audit vertical workcenter readiness."""

from __future__ import annotations

import frappe

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY


def audit_vertical_workcenters() -> dict:
	installed = set(frappe.get_installed_apps() or [])
	rows = []
	complete = 0
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		app = entry["app"]
		wc = entry["workcenter"]
		if entry.get("status") == "finance_group":
			continue
		inst = app in installed
		page_ok = bool(frappe.db.exists("Page", wc)) if inst else False
		if page_ok:
			complete += 1
		rows.append(
			{
				"app": app,
				"slug": entry["slug"],
				"workcenter": wc,
				"route": f"/app/{wc}",
				"installed": inst,
				"page_exists": page_ok,
				"status": entry.get("status"),
				"tier": entry.get("tier"),
				"reference": bool(entry.get("reference")),
			}
		)
	total = len([r for r in rows if r["installed"] and r["status"] != "finance_group"])
	score = round(complete / max(total, 1) * 100, 1)
	return {
		"ok": complete == total,
		"readiness_pct": score,
		"complete": complete,
		"total_installed": total,
		"apps": rows,
	}
