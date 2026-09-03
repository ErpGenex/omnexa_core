# Copyright (c) 2026, ErpGenEx
"""Generic role portal desk context — workspace menus, icons, manager-complete view."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_logo_registry import get_logo_url
from omnexa_core.omnexa_core.workspace_site_sync import _VERTICAL_WORKSPACE_MODULES
from omnexa_core.vertical_workcenter.context import get_workcenter_context
from omnexa_core.vertical_workcenter.portal_role_policy import is_portal_admin
from omnexa_core.vertical_workcenter.portal_menu_item import build_portal_menu_item
from omnexa_core.vertical_workcenter.registry import get_registry_entry

_ROLE_SECTION_HINTS: dict[str, tuple[str, ...]] = {
	"executive-dashboard": ("dashboard", "executive", "📊", "overview"),
	"operations-desk": ("operations", "floor", "kitchen", "service", "order", "⚙", "🍽", "👨"),
	"finance-desk": ("finance", "journal", "payment", "invoice", "💰", "account"),
	"customer-portal": ("customer", "portal", "guest", "👤"),
	"analytics-dashboard": ("report", "analytics", "margin", "summary", "📈"),
}

_APP_ROLE_PORTAL_DELEGATES: dict[str, str] = {
	"erpgenex_legal": "erpgenex_legal.api.legal_role_portal.get_role_portal_context",
	"omnexa_trading": "omnexa_trading.pharma_portal_catalog.get_role_portal_context",
	"omnexa_hr": "omnexa_hr.omnexa_hr.api.hr_role_portal.get_role_portal_context",
}


def _delegate_role_portal_context(app: str, role_key: str) -> dict | None:
	handler = _APP_ROLE_PORTAL_DELEGATES.get(app)
	if not handler:
		return None
	return frappe.get_attr(handler)(role_key=role_key)


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


def _section_matches_role(section_title: str, role_key: str) -> bool:
	hints = _ROLE_SECTION_HINTS.get(role_key, ())
	title = (section_title or "").lower()
	return any(h.lower() in title for h in hints)


def _build_menu_sections(app: str, role_key: str, *, is_admin: bool) -> list[dict]:
	sections = _workspace_sections(app)
	if not sections:
		return []

	out: list[dict] = []
	for section_title, links in sections:
		if not is_admin and not _section_matches_role(section_title, role_key):
			continue
		items: list[dict] = []
		for link in links or []:
			if not link or len(link) < 2:
				continue
			link_type, link_to = link[0], link[1]
			label = link[2] if len(link) > 2 else link_to
			if not _link_exists(link_type, link_to):
				continue
			items.append(
				build_portal_menu_item(app, link_type, link_to, label, _route_for_link(link_type, link_to))
			)
		if items:
			out.append(
				{
					"title_en": section_title,
					"title_ar": section_title,
					"items": items,
				}
			)
	return out


def build_workcenter_menu_sections(app: str, *, is_admin: bool = True) -> list[dict]:
	"""All workspace sections for workcenter operational menus."""
	sections = _workspace_sections(app)
	if not sections:
		return []
	out: list[dict] = []
	for section_title, links in sections:
		items: list[dict] = []
		for link in links or []:
			if not link or len(link) < 2:
				continue
			link_type, link_to = link[0], link[1]
			label = link[2] if len(link) > 2 else link_to
			if not _link_exists(link_type, link_to):
				continue
			items.append(
				build_portal_menu_item(app, link_type, link_to, label, _route_for_link(link_type, link_to))
			)
		if items:
			out.append({"title_en": section_title, "title_ar": section_title, "items": items})
	return out


def _find_portal(groups: list[dict], role_key: str) -> dict | None:
	for group in groups or []:
		for portal in group.get("portals") or []:
			pid = portal.get("id") or ""
			if pid.endswith(role_key) or pid == role_key:
				return portal
	return None


@frappe.whitelist()
def get_role_portal_context(app: str, role_key: str) -> dict:
	"""Desk payload for default vertical role portals."""
	app = (app or "").strip()
	role_key = (role_key or "").strip()

	delegated = _delegate_role_portal_context(app, role_key)
	if delegated:
		return delegated

	entry = get_registry_entry(app)
	if not entry:
		frappe.throw(frappe._("Unknown vertical app: {0}").format(app))

	ctx = get_workcenter_context(app)
	groups = ctx.get("grouped_portals") or []
	portal = _find_portal(groups, role_key)
	is_admin = is_portal_admin()
	menu_sections = _build_menu_sections(app, role_key, is_admin=is_admin)

	quick_links: list[dict] = []
	for section in menu_sections:
		quick_links.extend(section.get("items") or [])

	sibling_portals: list[dict] = []
	for group in groups:
		for p in group.get("portals") or []:
			if p.get("allowed") is False:
				continue
			sibling_portals.append(p)

	return {
		"app": app,
		"role_key": role_key,
		"is_admin": is_admin,
		"portal": portal,
		"title_en": (portal or {}).get("label_en") or entry["title_en"],
		"title_ar": (portal or {}).get("label_ar") or entry["title_ar"],
		"role_en": (portal or {}).get("role_en") or role_key,
		"role_ar": (portal or {}).get("role_ar") or role_key,
		"icon": (portal or {}).get("icon") or "🌐",
		"logo_url": ctx.get("logo_url") or get_logo_url(app),
		"brand_name_en": ctx.get("brand_name_en"),
		"brand_name_ar": ctx.get("brand_name_ar"),
		"workcenter_route": ctx.get("workcenter_route"),
		"grouped_portals": groups,
		"sibling_portals": sibling_portals,
		"menu_sections": menu_sections,
		"quick_links": quick_links[:24],
		"dashboard": {
			"kpis": [
				{"title_en": "Role portals", "title_ar": "بوابات الأدوار", "value": len(sibling_portals), "icon": "🌐"},
				{"title_en": "Menu items", "title_ar": "عناصر القائمة", "value": len(quick_links), "icon": "📋"},
				{"title_en": "Workspace sections", "title_ar": "أقسام مساحة العمل", "value": len(menu_sections), "icon": "🏢"},
			],
			"quick_actions": quick_links[:6],
			"work_queue": [],
			"pending_tasks": [],
			"approvals": [],
			"charts": [
				{"title_en": "Activity Trend", "title_ar": "اتجاه النشاط", "type": "line"},
				{"title_en": "Operations", "title_ar": "العمليات", "type": "bar"},
			],
		},
		"kpis": [
			{"label_en": "Role portals", "label_ar": "بوابات الأدوار", "value": len(sibling_portals)},
			{"label_en": "Menu items", "label_ar": "عناصر القائمة", "value": len(quick_links)},
			{"label_en": "Workspace sections", "label_ar": "أقسام مساحة العمل", "value": len(menu_sections)},
		],
	}
