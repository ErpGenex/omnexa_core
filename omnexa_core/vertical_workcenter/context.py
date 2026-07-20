# Copyright (c) 2026, ErpGenEx
"""Generic workcenter context — workspace links + portal pages."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.app_logo_registry import get_logo_url
from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY, get_registry_entry


def _app_installed(app: str) -> bool:
	return app in (frappe.get_installed_apps() or [])


def _workspace_page_portals(app: str) -> list[dict]:
	"""All Page links from vertical workspace catalog (dashboards + journey)."""
	from omnexa_core.omnexa_core.workspace_site_sync import _VERTICAL_WORKSPACE_MODULES

	mod_path = _VERTICAL_WORKSPACE_MODULES.get(app)
	if not mod_path:
		return []
	try:
		import importlib

		mod = importlib.import_module(mod_path)
		sections = getattr(mod, "WORKSPACE_SECTIONS", None) or []
		seen: set[str] = set()
		portals: list[dict] = []
		for _title, links in sections:
			for link_type, link_to, label in links:
				if link_type != "Page":
					continue
				if link_to in seen or link_to.endswith("-workcenter") or "demo-hub" in link_to:
					continue
				seen.add(link_to)
				portals.append(
					{
						"id": link_to,
						"label_en": label,
						"label_ar": label,
						"route": f"/app/{link_to
	}",
						"icon": "🌐",
						"exists": bool(frappe.db.exists("Page", link_to))}
				)
		return portals
	except Exception:
		return []


def _journey_pages(app: str, slug: str) -> list[dict]:
	"""Pages matching {slug}-* with optional portal catalog in app."""
	pages = frappe.get_all(
		"Page",
		filters={"name": ["like", f"{slug}-%"]},
		fields=["name", "title"],
		limit=40,
		order_by="title asc",
	)
	out = []
	for p in pages:
		if p.name.endswith("-workcenter") or p.name.endswith("-demo-hub"):
			continue
		out.append(
			{
				"id": p.name,
				"label_en": p.title or p.name,
				"label_ar": p.title or p.name,
				"route": f"/app/{p.name
	}",
				"icon": "🌐",
				"exists": True
	}
		)
	return out


def _workspace_journey_links(app: str) -> list[dict]:
	"""Try vertical workspace module for curated journey links."""
	from omnexa_core.omnexa_core.workspace_site_sync import _VERTICAL_WORKSPACE_MODULES

	mod_path = _VERTICAL_WORKSPACE_MODULES.get(app)
	if not mod_path:
		return []
	try:
		import importlib

		mod = importlib.import_module(mod_path)
		sections = getattr(mod, "WORKSPACE_SECTIONS", None) or []
		for title, links in sections:
			if "Journey" in title or "journey" in title.lower() or "Omnexa" in title:
				portals = []
				for link_type, link_to, label in links:
					if link_type != "Page":
						continue
					if "demo" in link_to.lower() and "hub" in link_to.lower():
						continue
					portals.append(
						{
							"id": link_to,
							"label_en": label,
							"label_ar": label,
							"route": f"/app/{link_to
	}",
							"icon": "🌐",
							"exists": bool(frappe.db.exists("Page", link_to))}
					)
				return portals
	except Exception:
		return []
	return []


@frappe.whitelist()
def get_workcenter_context(app: str | None = None) -> dict:
	"""Generic workcenter payload for any registered vertical app."""
	app = (app or "").strip()
	entry = get_registry_entry(app)
	if not entry:
		frappe.throw(_("Unknown vertical app: {0}").format(app))
	if not _app_installed(app):
		frappe.throw(_("App {0} is not installed").format(app))

	slug = entry["slug"]
	wc_page = entry["workcenter"]
	from omnexa_core.vertical_workcenter.default_portal_catalog import get_grouped_portal_catalog_for_app

	groups = get_grouped_portal_catalog_for_app(app)
	if not groups:
		portals = _workspace_page_portals(app) or _journey_pages(app, slug)
		groups = [
			{
				"label_en": "Role Portals",
				"label_ar": "بوابات الأدوار",
				"portals": portals
	}
		]
	portals = []
	for g in groups:
		portals.extend(g.get("portals") or [])
	company = frappe.defaults.get_user_default("Company") or ""
	branch = frappe.defaults.get_user_default("Branch") or ""
	is_admin = frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()

	return {
		"app": app,
		"slug": slug,
		"workcenter_page": wc_page,
		"workcenter_route": f"/app/{wc_page
	}",
		"title_en": entry["title_en"],
		"title_ar": entry["title_ar"],
		"logo_url": get_logo_url(app),
		"grouped_portals": groups,
		"portal_count": len(portals),
		"company": company,
		"branch": branch,
		"is_admin": is_admin,
		"can_simulate": is_admin,
		"status": entry.get("status"),
		"branch_demo_hint": _("Branch → Demo data → set activity → run simulation for this vertical")
	}


@frappe.whitelist()
def audit_all_workcenters() -> dict:
	from omnexa_core.vertical_workcenter.audit import audit_vertical_workcenters

	return audit_vertical_workcenters()
