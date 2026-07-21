# Copyright (c) 2026, ErpGenEx
"""Sync desk sidebar nesting by business sector using Frappe native ``parent_page``."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.sector_registry import (
	ALWAYS_ROOT_WORKSPACES,
	PRESERVE_EXISTING_PARENT,
	SECTOR_DEFINITIONS,
	SIDEBAR_HIDDEN_WORKSPACES,
	build_workspace_sector_map,
	get_sector_legacy_titles,
	get_sector_parent_titles,
	get_sector_sidebar_title,
	resolve_workspace_name,
)

# Workspaces managed exclusively by finance_group_sidebar (verticals + governance).
_FINANCE_MANAGED: frozenset[str] | None = None


def _finance_managed_workspaces() -> frozenset[str]:
	global _FINANCE_MANAGED
	if _FINANCE_MANAGED is not None:
		return _FINANCE_MANAGED
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import (
			WORKSPACE_NAME,
			_finance_vertical_workspaces,
		)

		names = set(_finance_vertical_workspaces())
		names.add(WORKSPACE_NAME)
		_FINANCE_MANAGED = frozenset(names)
	except Exception:
		_FINANCE_MANAGED = frozenset({"Finance Group"})
	return _FINANCE_MANAGED


def _sidebar_parent_token(workspace_name: str) -> str:
	if not workspace_name or not frappe.db.exists("Workspace", workspace_name):
		return ""
	doc = frappe.get_doc("Workspace", workspace_name)
	return (getattr(doc, "title", None) or getattr(doc, "label", None) or doc.name or "").strip()


def _set_sector_parent_display(parent_name: str, sidebar_title: str, icon: str) -> None:
	"""Update sidebar display fields only — never touch unique ``label``."""
	frappe.db.sql(
		"""
		UPDATE `tabWorkspace`
		SET title = %s, icon = %s
		WHERE name = %s
		""",
		(sidebar_title, icon, parent_name),
	)


def _ensure_sector_parent_workspace(sector_id: str, spec: dict) -> str | None:
	parent_name = (spec.get("parent_workspace") or "").strip()
	if not parent_name:
		return None

	sidebar_title = get_sector_sidebar_title(spec)
	icon = spec.get("icon") or "folder-normal"

	if not frappe.db.exists("Workspace", parent_name):
		doc = frappe.get_doc(
			{
				"doctype": "Workspace",
				"name": parent_name,
				"label": parent_name,
				"title": sidebar_title,
				"module": "Omnexa Core",
				"public": 1,
				"is_hidden": 0,
				"icon": icon,
				"parent_page": "",
				"content": json.dumps(
					[
						{
							"id": f"sector-{sector_id}-header",
							"type": "header",
							"data": {
								"text": (
									f'<span class="h4"><b>{sidebar_title}</b></span><br>'
									f'<span class="text-muted">{spec.get("purpose") or ""}</span>'
								),
								"col": 12,
							},
						}
					]
				),
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_if_duplicate=True)
	else:
		_set_sector_parent_display(parent_name, sidebar_title, icon)

	# Sector hubs stay at root.
	frappe.db.set_value("Workspace", parent_name, "parent_page", "", update_modified=False)
	return parent_name


def _migrate_legacy_sector_titles() -> list[dict]:
	"""Rewrite ``parent_page`` when sector hubs use shorter sidebar titles."""
	updated: list[dict] = []
	for sector_id, spec in SECTOR_DEFINITIONS.items():
		parent_name = (spec.get("parent_workspace") or "").strip()
		if not parent_name or not frappe.db.exists("Workspace", parent_name):
			continue

		new_title = get_sector_sidebar_title(spec)
		legacy_titles = set(get_sector_legacy_titles(spec))
		current_title = (frappe.db.get_value("Workspace", parent_name, "title") or "").strip()
		if current_title and current_title != new_title:
			legacy_titles.add(current_title)

		for legacy in legacy_titles:
			children = frappe.get_all(
				"Workspace",
				filters={"parent_page": legacy},
				pluck="name",
				limit_page_length=500,
			)
			for child in children:
				if child == parent_name:
					continue
				frappe.db.set_value(
					"Workspace",
					child,
					"parent_page",
					new_title,
					update_modified=False,
				)
				updated.append({"workspace": child, "from": legacy, "to": new_title})

	return updated


def _count_sector_children(parent_title: str, workspace_map: dict[str, str]) -> int:
	count = 0
	for ws_name, sector_parent in workspace_map.items():
		if sector_parent != parent_title:
			continue
		if not frappe.db.exists("Workspace", ws_name):
			continue
		if frappe.db.get_value("Workspace", ws_name, "is_hidden"):
			continue
		count += 1
	return count


def sync_sector_sidebar(*, save: bool = True) -> dict:
	"""Assign ``parent_page`` for registered workspaces; never hide or delete app workspaces."""
	stats = {
		"ok": True,
		"parents_ensured": [],
		"reparented": [],
		"title_migrations": [],
		"skipped_preserved": [],
		"skipped_finance": [],
		"skipped_unmapped": [],
		"parents_visibility": [],
	}

	finance_managed = _finance_managed_workspaces()
	workspace_map = build_workspace_sector_map()
	sector_parents: dict[str, str] = {}
	sector_parent_titles = set(get_sector_parent_titles())
	for spec in SECTOR_DEFINITIONS.values():
		for legacy in get_sector_legacy_titles(spec):
			sector_parent_titles.add(legacy)

	stats["title_migrations"] = _migrate_legacy_sector_titles()

	# 1) Ensure sector parent workspaces exist and sit at root.
	for sector_id, spec in sorted(SECTOR_DEFINITIONS.items(), key=lambda s: s[1]["order"]):
		parent = _ensure_sector_parent_workspace(sector_id, spec)
		if parent:
			sector_parents[sector_id] = parent
			stats["parents_ensured"].append(parent)

	# 2) Reparent registered workspaces (only when they exist in DB).
	for ws_name, parent_title in workspace_map.items():
		if ws_name in ALWAYS_ROOT_WORKSPACES:
			continue
		if ws_name in sector_parents.values():
			continue
		if ws_name in PRESERVE_EXISTING_PARENT:
			stats["skipped_preserved"].append(ws_name)
			continue
		if ws_name in finance_managed:
			stats["skipped_finance"].append(ws_name)
			continue
		if not frappe.db.exists("Workspace", ws_name):
			continue

		parent_token = parent_title
		current = (frappe.db.get_value("Workspace", ws_name, "parent_page") or "").strip()

		if ws_name in PRESERVE_EXISTING_PARENT:
			stats["skipped_preserved"].append(ws_name)
			continue

		# Keep intentional sub-nesting (e.g. ZATCA → E-Invoice, Asset Insurance → Fixed Assets).
		if current and current not in sector_parent_titles:
			stats["skipped_preserved"].append(ws_name)
			continue

		if current == parent_token:
			continue

		frappe.db.set_value(
			"Workspace",
			ws_name,
			"parent_page",
			parent_token,
			update_modified=False,
		)
		stats["reparented"].append({"workspace": ws_name, "parent": parent_token})

	# 3) Sector parent visibility — hide empty sector containers only (not app workspaces).
	for sector_id, spec in SECTOR_DEFINITIONS.items():
		parent_title = spec.get("parent_workspace") or ""
		if not parent_title or not frappe.db.exists("Workspace", parent_title):
			continue
		if spec.get("managed_by") == "finance_group_sidebar":
			# Finance Group hub always visible when finance verticals exist.
			child_count = sum(
				1
				for ws in finance_managed
				if ws != parent_title
				and frappe.db.exists("Workspace", ws)
				and not frappe.db.get_value("Workspace", ws, "is_hidden")
			)
		else:
			child_count = _count_sector_children(get_sector_sidebar_title(spec), workspace_map)

		is_hidden = 0 if child_count > 0 else 1
		frappe.db.set_value(
			"Workspace",
			parent_title,
			"is_hidden",
			is_hidden,
			update_modified=False,
		)
		stats["parents_visibility"].append(
			{"parent": parent_title, "children": child_count, "is_hidden": is_hidden}
		)

	# 4) Hide duplicate or superseded workspaces from the sidebar.
	for ws_name in SIDEBAR_HIDDEN_WORKSPACES:
		if not frappe.db.exists("Workspace", ws_name):
			continue
		frappe.db.set_value("Workspace", ws_name, "is_hidden", 1, update_modified=False)
		frappe.db.set_value("Workspace", ws_name, "parent_page", "", update_modified=False)
		stats.setdefault("hidden_workspaces", []).append(ws_name)

	# 5) Order sector parents in sidebar (low sequence = higher position).
	base_seq = 2.0
	for sector_id, spec in sorted(SECTOR_DEFINITIONS.items(), key=lambda s: s[1]["order"]):
		parent_title = spec.get("parent_workspace") or ""
		if parent_title and frappe.db.exists("Workspace", parent_title):
			frappe.db.set_value(
				"Workspace",
				parent_title,
				"sequence_id",
				base_seq,
				update_modified=False,
			)
			base_seq += 1.0

	if save:
		frappe.db.commit()
	frappe.clear_cache(doctype="Workspace")
	return stats


def inject_sector_sidebar_boot(bootinfo) -> None:
	"""Expose sector parent titles to desk JS for styling."""
	try:
		by_workspace = {
			(spec.get("parent_workspace") or ""): {
				"sidebar_label": get_sector_sidebar_title(spec),
				"label_full": spec.get("label") or get_sector_sidebar_title(spec),
				"label_ar": spec.get("label_ar") or spec.get("label") or "",
				"purpose": spec.get("purpose") or "",
				"icon": spec.get("icon") or "folder-normal",
				"order": spec.get("order") or 0,
			}
			for spec in SECTOR_DEFINITIONS.values()
			if spec.get("parent_workspace")
		}
		bootinfo.omnexa_sector_by_workspace = by_workspace
		bootinfo.omnexa_sector_parents = get_sector_parent_titles()
		bootinfo.omnexa_sector_definitions = {
			get_sector_sidebar_title(spec): by_workspace.get(spec.get("parent_workspace") or "", {})
			for spec in SECTOR_DEFINITIONS.values()
			if spec.get("parent_workspace")
		}
	except Exception:
		bootinfo.omnexa_sector_parents = []
		bootinfo.omnexa_sector_by_workspace = {}
		bootinfo.omnexa_sector_definitions = {}


@frappe.whitelist()
def sync_sector_sidebar_api() -> dict:
	frappe.only_for("System Manager")
	result = sync_sector_sidebar()
	return result
