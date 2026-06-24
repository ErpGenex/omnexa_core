# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Append module Script Reports to app workspaces without duplicating sidebar links."""

from __future__ import annotations

import frappe


def _existing_report_links(ws) -> set[str]:
	out: set[str] = set()
	for row in ws.links or []:
		if row.link_type == "Report" and row.link_to:
			out.add(row.link_to)
	return out


def append_module_reports(
	workspace_name: str,
	module: str,
	*,
	section_label: str = "📈 Reports (auto)",
	save: bool = True,
) -> dict:
	"""Add Script Reports from *module* missing from workspace sidebar."""
	stats = {"added": 0, "skipped": workspace_name}
	if not workspace_name or not module or not frappe.db.exists("Workspace", workspace_name):
		return stats

	ws = frappe.get_doc("Workspace", workspace_name)
	seen = _existing_report_links(ws)
	reports = frappe.get_all(
		"Report",
		filters={"module": module, "disabled": 0},
		pluck="name",
		order_by="name asc",
	)
	missing = [r for r in reports if r not in seen]
	if not missing:
		return {"added": 0, "workspace": workspace_name}

	ws.append("links", {"type": "Card Break", "label": section_label, "link_type": "DocType"})
	for name in missing:
		row = {
			"type": "Link",
			"label": name,
			"link_type": "Report",
			"link_to": name,
			"is_query_report": 1,
		}
		ref = frappe.db.get_value("Report", name, "ref_doctype")
		if ref:
			row["report_ref_doctype"] = ref
		ws.append("links", row)
		stats["added"] += 1

	if save and stats["added"]:
		ws.flags.ignore_permissions = True
		ws.flags.ignore_version = True
		ws.save()
		frappe.clear_cache(doctype="Workspace")
	stats["workspace"] = workspace_name
	return stats


def sync_all_registered_workspace_reports(*, save: bool = True) -> dict:
	"""Walk control-tower app specs and ensure each workspace lists its module reports."""
	from omnexa_core.omnexa_core.workspace_control_tower import _APP_SPECS

	out: dict[str, dict] = {}
	for app_name, spec in (_APP_SPECS or {}).items():
		if app_name not in frappe.get_installed_apps():
			continue
		ws_name = (spec.get("workspace") or "").strip()
		module = (spec.get("module") or "").strip()
		if not ws_name or not module:
			continue
		try:
			out[app_name] = append_module_reports(ws_name, module, save=save)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: workspace report sync — {app_name}")
	return out
