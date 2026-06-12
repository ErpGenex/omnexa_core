# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Site-wide workspace audit + full desk sync (all Omnexa apps)."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.omnexa_core.workspace_control_tower import (
	_APP_SPECS,
	_app_installed,
	get_desk_sections_for_workspace,
	sync_all_workspace_kpi_layout,
)
from omnexa_core.omnexa_core.workspace_desk_layouts import resolve_desk_sections_for_workspace_doc


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "Workspace":
		return bool(frappe.db.exists("Workspace", link_to))
	return False


def _expected_links_for_workspace(ws_name: str) -> list[tuple[str, str, str]]:
	"""Return (link_type, link_to, label) tuples expected for a workspace."""
	if _app_installed("omnexa_construction") and ws_name == "Construction":
		from omnexa_construction.workspace.construction_workspace import WORKSPACE_SECTIONS

		out: list[tuple[str, str, str]] = []
		for _section, items in WORKSPACE_SECTIONS:
			for link_type, link_to, label, _icon, _is_report in items:
				out.append((link_type, link_to, label))
		# Standard commercial parties often preserved on desk
		out.append(("DocType", "Customer", "Customer (project owners)"))
		return out

	if frappe.db.exists("Workspace", ws_name):
		ws = frappe.get_doc("Workspace", ws_name)
		sections = resolve_desk_sections_for_workspace_doc(ws) or get_desk_sections_for_workspace(ws_name)
		if sections:
			out = []
			for _card, rows in sections:
				for label, link_type, link_to, _ref in rows:
					if (link_type or "").strip() == "URL":
						continue
					out.append((link_type, link_to, label))
			return out
	return []


def _actual_links(ws_name: str) -> set[tuple[str, str]]:
	if not frappe.db.exists("Workspace", ws_name):
		return set()
	rows = frappe.get_all(
		"Workspace Link",
		filters={"parent": ws_name, "type": "Link"},
		fields=["link_type", "link_to"],
	)
	return {(r.link_type, r.link_to) for r in rows if r.link_to and r.link_type}


def audit_all_workspaces(*, verbose: bool = False) -> dict[str, Any]:
	"""Compare desk catalog vs live Workspace Link rows per registered app."""
	report: dict[str, Any] = {
		"workspaces": [],
		"summary": {"checked": 0, "ok": 0, "missing_links": 0, "not_in_db": 0},
	}
	seen_ws: set[str] = set()

	for app_key, spec in _APP_SPECS.items():
		required = spec.get("_requires_app", app_key)
		if not _app_installed(required):
			continue
		ws_name = spec.get("workspace")
		if not ws_name or ws_name in seen_ws:
			continue
		seen_ws.add(ws_name)
		if not frappe.db.exists("Workspace", ws_name):
			report["workspaces"].append(
				{"workspace": ws_name, "app": app_key, "status": "missing_workspace", "missing": [], "extra": []}
			)
			report["summary"]["not_in_db"] += 1
			continue

		expected = _expected_links_for_workspace(ws_name)
		expected_keys = {(lt, lto) for lt, lto, _lbl in expected if _link_exists(lt, lto)}
		actual = _actual_links(ws_name)
		missing = sorted(expected_keys - actual)
		extra = sorted(actual - expected_keys) if verbose else []

		entry = {
			"workspace": ws_name,
			"app": app_key,
			"expected": len(expected_keys),
			"actual": len(actual),
			"missing": [{"link_type": a, "link_to": b} for a, b in missing],
			"extra_count": len(extra),
			"status": "ok" if not missing else "gaps",
		}
		report["workspaces"].append(entry)
		report["summary"]["checked"] += 1
		if missing:
			report["summary"]["missing_links"] += len(missing)
		else:
			report["summary"]["ok"] += 1

	frappe.logger("omnexa_core").info("Workspace audit: %s", report["summary"])
	return report


def _repair_empty_registered_workspaces() -> list[str]:
	"""Re-sync app desks that ended with zero sidebar links (failed save / hook race)."""
	from omnexa_core.omnexa_core.workspace_control_tower import sync_workspace_for_app

	repaired: list[str] = []
	for app_key, spec in _APP_SPECS.items():
		required = spec.get("_requires_app", app_key)
		if not _app_installed(required):
			continue
		if app_key in ("omnexa_construction", "omnexa_healthcare", "omnexa_education", "omnexa_car_rental"):
			continue
		ws_name = spec.get("workspace")
		if not ws_name or not frappe.db.exists("Workspace", ws_name):
			continue
		if frappe.db.count("Workspace Link", {"parent": ws_name, "type": "Link"}):
			continue
		try:
			sync_workspace_for_app(app_key)
			frappe.db.commit()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: repair empty workspace `{ws_name}`")
			continue
		if frappe.db.count("Workspace Link", {"parent": ws_name, "type": "Link"}):
			repaired.append(ws_name)
	return repaired


def run_full_workspace_sync() -> dict[str, Any]:
	"""Sync all control-tower desks, then app-owned vertical workspace menus."""
	from omnexa_core.install import run_workspace_desk_sync, sync_vertical_app_workspace_menus

	run_workspace_desk_sync()
	vertical_stats = sync_vertical_app_workspace_menus()

	repaired = _repair_empty_registered_workspaces()
	frappe.clear_cache(doctype="Workspace")
	audit = audit_all_workspaces()
	return {
		"vertical_workspaces": vertical_stats,
		"repaired_empty": repaired,
		"audit": audit["summary"],
		"gaps": [w for w in audit["workspaces"] if w.get("status") != "ok"],
	}
