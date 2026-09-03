# Copyright (c) 2026, ErpGenEx
"""Build operational menu items with icon metadata for portal desks."""

from __future__ import annotations

from omnexa_core.vertical_workcenter.portal_icon_resolver import resolve_portal_icon_meta


def build_portal_menu_item(
	app: str,
	link_type: str,
	link_to: str,
	label: str,
	route: str,
) -> dict:
	meta = resolve_portal_icon_meta(app, link_type, link_to, label)
	return {
		"label_en": label,
		"label_ar": label,
		"route": route,
		"link_type": link_type,
		"link_to": link_to,
		**meta,
	}


def parse_portal_route(route: str) -> tuple[str, str, str]:
	route = (route or "").strip()
	if route.startswith("/app/List/"):
		link_to = route.replace("/app/List/", "").split("?")[0]
		return "DocType", link_to, route
	if route.startswith("/app/query-report/"):
		link_to = route.replace("/app/query-report/", "").split("?")[0]
		return "Report", link_to, route
	if route.startswith("/app/"):
		slug = route.replace("/app/", "").split("?")[0]
		return "Page", slug, route
	return "URL", route, route


def enrich_menu_sections(app: str, sections: list[dict]) -> list[dict]:
	"""Ensure every menu item has icon_svg + icon_color."""
	out: list[dict] = []
	for section in sections or []:
		items: list[dict] = []
		for item in section.get("items") or []:
			route = item.get("route") or ""
			label = item.get("label_en") or item.get("label") or route
			link_type, link_to, _ = parse_portal_route(route)
			meta = resolve_portal_icon_meta(app, link_type, link_to, label)
			merged = dict(item)
			merged.update(meta)
			items.append(merged)
		out.append({**section, "items": items})
	return out


def enrich_portal_groups(app: str, groups: list[dict]) -> list[dict]:
	"""Add icon_svg/icon_color to sidebar portal entries."""
	for group in groups or []:
		enriched = []
		for portal in group.get("portals") or []:
			page = portal.get("page") or portal.get("id") or ""
			label = portal.get("label_en") or portal.get("label") or page
			meta = resolve_portal_icon_meta(app, "Page", page, label)
			enriched.append({**portal, **meta})
		group["portals"] = enriched
	return groups
