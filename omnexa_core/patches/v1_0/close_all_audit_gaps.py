# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Close remaining world-class audit gaps: workspace icons + hidden finance desks."""

from __future__ import annotations

import frappe

_FINANCE_ROLE_ICONS = {
	"Finance Executive": "es-line-dashboard",
	"Finance Credit Origination": "es-line-shield",
	"Finance Credit Risk": "es-line-trending-up",
	"Finance Treasury": "es-line-pie-chart",
	"Finance Consumer": "es-line-shopping-cart",
	"Finance Auto": "es-line-truck",
	"Finance Mortgage": "es-line-home",
	"Finance Factoring": "es-line-file-text",
	"Finance Leasing": "es-line-layers",
	"Finance Microfinance": "es-line-users",
	"Finance GRC": "es-line-shield",
	"Finance SME": "es-line-briefcase",
	"Finance Accounting": "es-line-book"
	}

_OTHER_ICONS = {
	"Healthcare Admin Lab": "es-line-flask",
	"Tax Countries": "es-line-globe",
	"ZATCA": "es-line-shield"
	}


def _default_icon_for_workspace(name: str) -> str:
	if name in _FINANCE_ROLE_ICONS:
		return _FINANCE_ROLE_ICONS[name]
	if name in _OTHER_ICONS:
		return _OTHER_ICONS[name]
	lower = name.lower()
	if "governance" in lower:
		return "es-line-shield"
	if "finance" in lower:
		return "es-line-bank"
	if "health" in lower:
		return "organization"
	if "tax" in lower or "zatca" in lower:
		return "es-line-shield"
	return "es-line-zap"


def execute():
	updated = 0
	for row in frappe.get_all("Workspace", filters={"public": 1
	}, fields=["name", "icon"]):
		icon = (row.icon or "").strip()
		if icon and icon not in ("folder-normal", "NULL"):
			continue
		new_icon = _default_icon_for_workspace(row.name)
		frappe.db.set_value("Workspace", row.name, "icon", new_icon, update_modified=False)
		updated += 1

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS, sync_role_workspace

		for spec in ROLE_SPECS:
			sync_role_workspace(spec)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "close_all_audit_gaps: finance role sync")

	try:
		from omnexa_core.omnexa_core.workspace_icon_enricher import enrich_all_workspace_visual_icons

		enrich_all_workspace_visual_icons(save=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "close_all_audit_gaps: icon enricher")

	for fn in (
		"omnexa_construction.workspace.construction_workspace.sync_construction_workspace_menu",
		"omnexa_edms.workspace.edms_workspace.sync_edms_workspace_menu",
	):
		try:
			frappe.get_attr(fn)()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"close_all_audit_gaps: {fn}")

	frappe.clear_cache(doctype="Workspace")
	frappe.db.commit()
	return {"workspace_icons_updated": updated
	}
