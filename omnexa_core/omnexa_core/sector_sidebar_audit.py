# Copyright (c) 2026, ErpGenEx
"""Audit desk sidebar — list root-level workspaces not assigned to any sector."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.sector_registry import (
	ALWAYS_ROOT_WORKSPACES,
	SECTOR_DEFINITIONS,
	get_sector_parent_titles,
)


@frappe.whitelist()
def audit_sidebar_coverage() -> dict:
	"""Return root-level public workspaces not mapped to a sector (must remain visible)."""
	sector_parents = set(get_sector_parent_titles())
	mapped: set[str] = set()
	for spec in SECTOR_DEFINITIONS.values():
		for ws in spec.get("workspaces") or []:
			mapped.add(ws)

	all_public = frappe.get_all(
		"Workspace",
		filters={"public": 1, "is_hidden": 0},
		fields=["name", "title", "parent_page", "module"],
		order_by="sequence_id asc",
		limit_page_length=500,
	)

	root_items = []
	nested_items = []
	for ws in all_public:
		parent = (ws.get("parent_page") or "").strip()
		name = ws.get("name") or ""
		if not parent:
			root_items.append(ws)
		else:
			nested_items.append(ws)

	unmapped_root = []
	for ws in root_items:
		name = ws.get("name") or ""
		title = ws.get("title") or name
		if name in ALWAYS_ROOT_WORKSPACES or title in ALWAYS_ROOT_WORKSPACES:
			continue
		if name in sector_parents or title in sector_parents:
			continue
		if name in mapped or title in mapped:
			continue
		unmapped_root.append({"name": name, "title": title, "module": ws.get("module")})

	return {
		"total_public": len(all_public),
		"root_count": len(root_items),
		"nested_count": len(nested_items),
		"sector_parents": sorted(sector_parents),
		"unmapped_root": unmapped_root,
		"unmapped_root_count": len(unmapped_root),
	}
