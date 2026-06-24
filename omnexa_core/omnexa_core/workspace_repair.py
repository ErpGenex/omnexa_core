# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Repair public workspaces that have sidebar links but missing desk shortcuts."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.vertical_workspace_sync import (
	build_content_from_link_rows,
	build_shortcuts_from_link_rows,
	drop_missing_workspace_dashboard_links,
)


def _links_to_rows(ws) -> list[dict]:
	rows: list[dict] = []
	for link in ws.links or []:
		if link.type == "Card Break":
			rows.append({"label": link.label, "type": "Card Break", "link_type": link.link_type or "DocType"})
		elif link.type == "Link":
			row = {
				"type": "Link",
				"label": link.label,
				"link_type": link.link_type,
				"link_to": link.link_to,
				"is_query_report": link.is_query_report or 0,
			}
			if link.report_ref_doctype:
				row["report_ref_doctype"] = link.report_ref_doctype
			rows.append(row)
	return rows


def repair_workspace_shortcuts(ws_name: str, *, save: bool = True) -> dict:
	if not frappe.db.exists("Workspace", ws_name):
		return {"workspace": ws_name, "repaired": False, "reason": "missing"}
	ws = frappe.get_doc("Workspace", ws_name)
	rows = _links_to_rows(ws)
	link_rows = [r for r in rows if r.get("type") == "Link"]
	if not link_rows:
		return {"workspace": ws_name, "repaired": False, "reason": "no_links"}

	shortcuts = build_shortcuts_from_link_rows(rows)
	ws.set("shortcuts", [])
	for sc in shortcuts:
		ws.append("shortcuts", sc)
	drop_missing_workspace_dashboard_links(ws)
	slug = frappe.scrub(ws_name)[:12]
	ws.content = build_content_from_link_rows(rows, ws, title=ws.title or ws_name, slug=slug)
	if save:
		ws.flags.ignore_permissions = True
		ws.flags.ignore_version = True
		ws.save()
	return {"workspace": ws_name, "repaired": True, "shortcuts": len(shortcuts), "links": len(link_rows)}


def repair_all_empty_public_workspaces(*, save: bool = True) -> dict:
	"""Rebuild shortcuts/content for every public workspace with links but zero shortcuts."""
	stats = {"scanned": 0, "repaired": 0, "skipped": 0, "details": []}
	for row in frappe.get_all("Workspace", filters={"public": 1}, fields=["name"]):
		stats["scanned"] += 1
		shortcut_count = frappe.db.count("Workspace Shortcut", {"parent": row.name})
		link_count = frappe.db.count("Workspace Link", {"parent": row.name, "type": "Link"})
		if shortcut_count > 0 or link_count == 0:
			stats["skipped"] += 1
			continue
		result = repair_workspace_shortcuts(row.name, save=save)
		if result.get("repaired"):
			stats["repaired"] += 1
			stats["details"].append(result)
	frappe.clear_cache(doctype="Workspace")
	return stats
