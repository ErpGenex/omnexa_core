# Copyright (c) 2026, ErpGenEx
"""Audit portal/menu icon coverage across all vertical apps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe

from omnexa_core.omnexa_core.workspace_site_sync import _VERTICAL_WORKSPACE_MODULES
from omnexa_core.vertical_workcenter.portal_icon_resolver import (
	_LINK_TYPE_FALLBACK,
	resolve_portal_icon,
)
from omnexa_core.vertical_workcenter.registry import INFRASTRUCTURE_APP_REGISTRY, VERTICAL_WORKCENTER_REGISTRY


def _is_generic_icon(link_type: str, icon: str) -> bool:
	return icon == _LINK_TYPE_FALLBACK.get(link_type)


def _workspace_sections(app: str) -> list[tuple[str, list]]:
	mod_path = _VERTICAL_WORKSPACE_MODULES.get(app)
	if not mod_path:
		return []
	try:
		import importlib

		mod = importlib.import_module(mod_path)
		return getattr(mod, "WORKSPACE_SECTIONS", None) or []
	except Exception:
		return []


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "Workspace":
		return bool(frappe.db.exists("Workspace", link_to))
	return True


def audit_app_icons(app: str) -> dict[str, Any]:
	"""Return icon audit stats for one vertical app."""
	sections = _workspace_sections(app)
	items: list[dict] = []
	generic: list[dict] = []
	icons_seen: set[str] = set()

	for section_title, links in sections:
		for link in links or []:
			if not link or len(link) < 2:
				continue
			link_type, link_to = link[0], link[1]
			label = link[2] if len(link) > 2 else link_to
			if not _link_exists(link_type, link_to):
				continue
			icon = resolve_portal_icon(app, link_type, link_to, label)
			row = {
				"section": section_title,
				"link_type": link_type,
				"link_to": link_to,
				"label": label,
				"icon": icon,
			}
			items.append(row)
			icons_seen.add(icon)
			if _is_generic_icon(link_type, icon):
				generic.append(row)

	total = len(items)
	generic_count = len(generic)
	return {
		"app": app,
		"total_items": total,
		"distinct_icons": len(icons_seen),
		"generic_items": generic_count,
		"coverage_pct": round(((total - generic_count) / total * 100) if total else 100, 1),
		"generic": generic,
		"items": items,
	}


def audit_all_portal_icons(*, include_items: bool = False) -> dict[str, Any]:
	"""Audit icon coverage for all registered + installed vertical apps."""
	installed = set(frappe.get_installed_apps() or [])
	apps: list[str] = []
	for row in VERTICAL_WORKCENTER_REGISTRY:
		if row["app"] in installed:
			apps.append(row["app"])

	# Finance / infra apps with workspace modules
	for row in INFRASTRUCTURE_APP_REGISTRY:
		app = row["app"]
		if app in installed and app in _VERTICAL_WORKSPACE_MODULES and app not in apps:
			apps.append(app)

	results: list[dict] = []
	all_generic: list[dict] = []
	total_items = 0
	total_generic = 0

	for app in apps:
		audit = audit_app_icons(app)
		total_items += audit["total_items"]
		total_generic += audit["generic_items"]
		if not include_items:
			audit = {k: v for k, v in audit.items() if k != "items"}
		results.append(audit)
		for g in audit.get("generic") or []:
			all_generic.append({"app": app, **g})

	results.sort(key=lambda r: (r["generic_items"], -r["coverage_pct"]), reverse=True)

	return {
		"apps_audited": len(results),
		"total_menu_items": total_items,
		"total_generic_items": total_generic,
		"overall_coverage_pct": round(((total_items - total_generic) / total_items * 100) if total_items else 100, 1),
		"zero_generic_apps": [r["app"] for r in results if r["generic_items"] == 0 and r["total_items"] > 0],
		"apps_needing_work": [r["app"] for r in results if r["generic_items"] > 0],
		"by_app": results,
		"generic_samples": all_generic[:120],
	}


def export_portal_icon_audit(*, output_dir: str | None = None, include_items: bool = False) -> dict[str, Any]:
	"""Run audit and write JSON report."""
	report = audit_all_portal_icons(include_items=include_items)
	out_dir = Path(output_dir or frappe.get_site_path("private", "files", "portal-icon-audit"))
	out_dir.mkdir(parents=True, exist_ok=True)
	out_file = out_dir / "portal_icon_audit.json"
	out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
	report["output_file"] = str(out_file)
	return report
