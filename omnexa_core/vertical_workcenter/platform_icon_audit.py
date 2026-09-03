# Copyright (c) 2026, ErpGenEx
"""Full-platform portal icon audit — workspace menus, portal catalogs, SVG coverage."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import frappe

from omnexa_core.omnexa_core.workspace_site_sync import _VERTICAL_WORKSPACE_MODULES
from omnexa_core.vertical_workcenter.default_portal_catalog import (
	_app_portal_catalog_hook,
)
from omnexa_core.vertical_workcenter.portal_icon_resolver import (
	_LINK_TYPE_FALLBACK,
	_LINK_TYPE_SVG,
	resolve_portal_icon,
	resolve_portal_icon_meta,
)
from omnexa_core.vertical_workcenter.portal_menu_item import build_portal_menu_item
from omnexa_core.vertical_workcenter.registry import INFRASTRUCTURE_APP_REGISTRY, VERTICAL_WORKCENTER_REGISTRY


def _installed_apps() -> set[str]:
	return set(frappe.get_installed_apps() or [])


def _audited_vertical_apps() -> list[str]:
	installed = _installed_apps()
	apps: list[str] = []
	for row in VERTICAL_WORKCENTER_REGISTRY:
		if row["app"] in installed:
			apps.append(row["app"])
	for row in INFRASTRUCTURE_APP_REGISTRY:
		app = row["app"]
		if app in installed and app in _VERTICAL_WORKSPACE_MODULES and app not in apps:
			apps.append(app)
	return apps


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


def _route_for_link(link_type: str, link_to: str) -> str:
	if link_type == "Page":
		return f"/app/{link_to}"
	if link_type == "DocType":
		return f"/app/List/{link_to}"
	if link_type == "Report":
		return f"/app/query-report/{link_to}"
	if link_type == "Workspace":
		return f"/app/{link_to}"
	return f"/app/{link_to}"


def _parse_route(route: str) -> tuple[str, str, str]:
	route = (route or "").strip()
	if route.startswith("/app/List/"):
		return "DocType", route.replace("/app/List/", ""), route
	if route.startswith("/app/query-report/"):
		return "Report", route.replace("/app/query-report/", ""), route
	if route.startswith("/app/"):
		slug = route.replace("/app/", "").split("?")[0]
		if slug:
			return "Page", slug, route
	return "URL", route, route


def _is_weak_emoji(link_type: str, icon: str) -> bool:
	return icon in (_LINK_TYPE_FALLBACK.get(link_type), "•", "▫️", "📄", "📋", "📊")


def _is_weak_icon(item: dict, link_type: str) -> bool:
	"""Flag items that still use generic DocType/Page SVG fallbacks."""
	svg = (item.get("icon_svg") or "").strip()
	if not svg:
		return True
	if link_type == "Report" and svg == "es-line-chart":
		return False
	if link_type == "Dashboard" and svg in {"es-line-dashboard", "es-line-chart"}:
		return False
	generic = _LINK_TYPE_SVG.get(link_type, ("es-line-filetype",))[0]
	if svg != generic:
		return False
	return _is_weak_emoji(link_type, item.get("icon") or "")


def _audit_workspace_menus(app: str) -> dict[str, Any]:
	items: list[dict] = []
	weak: list[dict] = []
	duplicate_svg: list[dict] = []
	sections = _workspace_sections(app)
	svg_by_section: dict[str, dict[str, list[str]]] = {}

	for section_title, links in sections:
		sec_key = section_title or "—"
		svg_by_section.setdefault(sec_key, {})
		for link in links or []:
			if not link or len(link) < 2:
				continue
			link_type, link_to = link[0], link[1]
			label = link[2] if len(link) > 2 else link_to
			item = build_portal_menu_item(app, link_type, link_to, label, _route_for_link(link_type, link_to))
			item["section"] = section_title
			items.append(item)
			if _is_weak_icon(item, link_type):
				weak.append(item)
			svg = item.get("icon_svg") or ""
			svg_by_section[sec_key].setdefault(svg, []).append(label)

	for sec, svg_map in svg_by_section.items():
		for svg, labels in svg_map.items():
			if svg and len(labels) > 1 and svg in {
				"es-line-filetype",
				"es-line-table-view",
				"es-line-chart",
				"es-line-web",
			}:
				duplicate_svg.append({"section": sec, "icon_svg": svg, "labels": labels})

	return {
		"app": app,
		"source": "workspace_menu",
		"total_items": len(items),
		"weak_items": len(weak),
		"duplicate_svg_groups": len(duplicate_svg),
		"items": items,
		"weak": weak,
		"duplicate_svg": duplicate_svg,
	}


def _portal_groups_for_app(app: str) -> list[dict]:
	groups = _app_portal_catalog_hook(app)
	if groups:
		return groups
	try:
		from omnexa_core.vertical_workcenter.default_portal_catalog import DEFAULT_ROLE_PORTALS
		from omnexa_core.vertical_workcenter.registry import get_registry_entry

		entry = get_registry_entry(app)
		if not entry:
			return []
		slug = entry["slug"]
		portals = [
			{
				"id": f"{slug}-{role['key']}",
				"page": f"{slug}-{role['key']}",
				"label_en": role["label_en"],
				"label_ar": role["label_ar"],
				"icon": role["icon"],
			}
			for role in DEFAULT_ROLE_PORTALS
		]
		return [{"label_en": "Role Portals", "label_ar": "بوابات الأدوار", "portals": portals}]
	except Exception:
		return []


def _audit_portal_catalog(app: str) -> dict[str, Any]:
	items: list[dict] = []
	weak: list[dict] = []
	for group in _portal_groups_for_app(app):
		for portal in group.get("portals") or []:
			page = portal.get("page") or portal.get("id") or ""
			label = portal.get("label_en") or portal.get("label") or page
			meta = resolve_portal_icon_meta(app, "Page", page, label)
			row = {
				"app": app,
				"group": group.get("label_en") or group.get("category"),
				"label": label,
				"page": page,
				**meta,
			}
			items.append(row)
			if _is_weak_icon(row, "Page"):
				weak.append(row)
	return {
		"app": app,
		"source": "portal_catalog",
		"total_items": len(items),
		"weak_items": len(weak),
		"items": items,
		"weak": weak,
	}


def _audit_pharma_menus() -> dict[str, Any]:
	if "omnexa_trading" not in _installed_apps():
		return {"source": "pharma_menus", "total_items": 0, "weak_items": 0, "items": [], "weak": []}
	try:
		from omnexa_trading.pharma_portal_catalog import PHARMA_ROLE_PORTALS
	except Exception:
		return {"source": "pharma_menus", "total_items": 0, "weak_items": 0, "items": [], "weak": []}

	items: list[dict] = []
	weak: list[dict] = []
	seen: set[str] = set()
	for portal in PHARMA_ROLE_PORTALS or []:
		for section in portal.get("menu_sections") or []:
			for menu_item in section.get("items") or []:
				route = menu_item.get("route") or ""
				label = menu_item.get("label_en") or menu_item.get("label") or route
				key = f"{label}|{route}"
				if key in seen:
					continue
				seen.add(key)
				link_type, link_to, _ = _parse_route(route)
				meta = resolve_portal_icon_meta("omnexa_trading", link_type, link_to, label)
				row = {
					"portal": portal.get("id"),
					"section": section.get("title_en"),
					"label": label,
					"route": route,
					"catalog_icon": menu_item.get("icon"),
					**meta,
				}
				items.append(row)
				if _is_weak_icon(row, link_type):
					weak.append(row)
	return {
		"source": "pharma_menus",
		"total_items": len(items),
		"weak_items": len(weak),
		"items": items,
		"weak": weak,
	}


def audit_full_platform_icons(*, include_items: bool = False) -> dict[str, Any]:
	"""Audit workspace menus + portal catalogs + pharma menus across installed apps."""
	installed = _installed_apps()
	menu_audits = [_audit_workspace_menus(app) for app in _audited_vertical_apps()]
	catalog_audits = [_audit_portal_catalog(app) for app in _audited_vertical_apps() if _portal_groups_for_app(app)]
	pharma_audit = _audit_pharma_menus()

	total_menu = sum(a["total_items"] for a in menu_audits)
	weak_menu = sum(a["weak_items"] for a in menu_audits)
	total_catalog = sum(a["total_items"] for a in catalog_audits)
	weak_catalog = sum(a["weak_items"] for a in catalog_audits)
	total_pharma = pharma_audit["total_items"]
	weak_pharma = pharma_audit["weak_items"]
	total_all = total_menu + total_catalog + total_pharma
	weak_all = weak_menu + weak_catalog + weak_pharma

	duplicate_issues = []
	for a in menu_audits:
		for d in a.get("duplicate_svg") or []:
			duplicate_issues.append({"app": a["app"], **d})

	summary_by_app: dict[str, dict] = {}
	for a in menu_audits:
		summary_by_app.setdefault(a["app"], {})["workspace_menu"] = {
			"total": a["total_items"],
			"weak": a["weak_items"],
			"duplicate_svg_groups": a["duplicate_svg_groups"],
		}
	for a in catalog_audits:
		summary_by_app.setdefault(a["app"], {})["portal_catalog"] = {
			"total": a["total_items"],
			"weak": a["weak_items"],
		}

	report: dict[str, Any] = {
		"installed_apps_count": len(installed),
		"vertical_apps_audited": len(menu_audits),
		"summary_ar": (
			f"تم فحص {total_all} عنصراً (قوائم + بوابات + pharma) عبر {len(menu_audits)} تطبيقاً — "
			f"التغطية {round(((total_all - weak_all) / total_all * 100) if total_all else 100, 2)}%"
		),
		"totals": {
			"all_items": total_all,
			"weak_items": weak_all,
			"workspace_menu_items": total_menu,
			"portal_catalog_items": total_catalog,
			"pharma_menu_items": total_pharma,
		},
		"coverage_pct": round(((total_all - weak_all) / total_all * 100) if total_all else 100, 2),
		"svg_fallback_types": _LINK_TYPE_SVG,
		"apps_with_weak_icons": sorted(
			{app for app, s in summary_by_app.items() if any(v.get("weak", 0) > 0 for v in s.values())}
		),
		"duplicate_svg_warnings": duplicate_issues[:80],
		"by_app": summary_by_app,
		"pharma_audit": {
			"total": total_pharma,
			"weak": weak_pharma,
		},
	}

	if include_items:
		report["workspace_menus"] = menu_audits
		report["portal_catalogs"] = catalog_audits
		report["pharma_menus"] = pharma_audit
	else:
		report["weak_samples"] = []
		for a in menu_audits:
			for w in (a.get("weak") or [])[:3]:
				report["weak_samples"].append({"source": "workspace", "app": a["app"], **w})
		for a in catalog_audits:
			for w in (a.get("weak") or [])[:2]:
				report["weak_samples"].append({"source": "catalog", **w})
		for w in (pharma_audit.get("weak") or [])[:10]:
			report["weak_samples"].append({"source": "pharma", **w})

	return report


@frappe.whitelist()
def export_full_platform_icon_audit(*, include_items: bool = False) -> dict[str, Any]:
	report = audit_full_platform_icons(include_items=bool(int(include_items)) if isinstance(include_items, str) else include_items)
	out_dir = Path(frappe.get_site_path("private", "files", "portal-icon-audit"))
	out_dir.mkdir(parents=True, exist_ok=True)
	out_file = out_dir / "full_platform_icon_audit.json"
	out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
	report["output_file"] = str(out_file)
	# Human-readable summary for console
	report["summary_ar"] = (
		f"تم فحص {report['totals']['all_items']} عنصراً عبر {report['vertical_apps_audited']} تطبيقاً — "
		f"التغطية {report['coverage_pct']}% — عناصر ضعيفة: {report['totals']['weak_items']}"
	)
	return report


# Backward-compatible exports
def audit_all_portal_icons(*, include_items: bool = False) -> dict[str, Any]:
	from omnexa_core.vertical_workcenter.portal_icon_audit import audit_all_portal_icons as _legacy

	return _legacy(include_items=include_items)


def export_portal_icon_audit(*, output_dir: str | None = None, include_items: bool = False) -> dict[str, Any]:
	from omnexa_core.vertical_workcenter.portal_icon_audit import export_portal_icon_audit as _legacy

	return _legacy(output_dir=output_dir, include_items=include_items)
