# Copyright (c) 2026, ErpGenEx
"""Finance Group sidebar — reparent verticals only; Accounting/E-Invoice stay in Core."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_uninstall_groups import get_group_apps

WORKSPACE_NAME = "Finance Group"

# Platform workspaces — NOT nested under Finance Group (shared across all apps).
CORE_PLATFORM_WORKSPACES: frozenset[str] = frozenset(
	{
		"Accounting",
		"E-Invoice",
	}
)

# Valid Frappe timeless sprite icons (icon-{name} in sidebar).
FINANCE_WORKSPACE_ICONS: dict[str, str] = {
	"Finance Engine": "accounting",
	"Credit Engine": "crm",
	"Credit Risk": "chart",
	"ALM": "chart",
	"Consumer Finance": "sell",
	"Vehicle Finance": "assets",
	"Mortgage Finance": "organization",
	"Factoring": "loan",
	"SME Retail Finance": "organization",
	"SME Microfinance": "users",
	"Leasing Finance": "project",
	"Operational Risk": "quality",
	"Finance Engine Governance": "quality",
	"Credit Engine Governance": "quality",
	"Credit Risk Governance": "quality",
	"Consumer Finance Governance": "quality",
	"Vehicle Finance Governance": "quality",
	"Mortgage Finance Governance": "quality",
	"Operational Risk Governance": "quality",
	"Factoring Governance": "quality",
	"Leasing Finance Governance": "quality"
	}

# Workspace → omnexa app (for brand logo URL in desk JS).
WORKSPACE_APP_LOGO: dict[str, str] = {
	"Finance Engine": "omnexa_finance_engine",
	"Credit Engine": "omnexa_credit_engine",
	"Credit Risk": "omnexa_credit_risk",
	"ALM": "omnexa_alm",
	"Consumer Finance": "omnexa_consumer_finance",
	"Vehicle Finance": "omnexa_vehicle_finance",
	"Mortgage Finance": "omnexa_mortgage_finance",
	"Factoring": "omnexa_factoring",
	"SME Retail Finance": "omnexa_sme_retail_finance",
	"SME Microfinance": "omnexa_sme_microfinance",
	"Leasing Finance": "omnexa_leasing_finance",
	"Operational Risk": "omnexa_operational_risk"
	}


def _finance_vertical_workspaces() -> list[str]:
	from omnexa_core.omnexa_core.workspace_control_tower import _APP_SPECS

	names: list[str] = []
	for app in get_group_apps("finance"):
		spec = _APP_SPECS.get(app) or {}
		ws = spec.get("workspace")
		if ws:
			names.append(ws)
		# governance child desks
		gov = (spec.get("governance_workspace") or "").strip()
		if gov:
			names.append(gov)
	return names


def sync_finance_group_sidebar(*, save: bool = True) -> dict:
	"""Reparent finance verticals under Finance Group; lift Accounting/E-Invoice to Core root."""
	parent = frappe.db.get_value("Workspace", WORKSPACE_NAME, "title") or WORKSPACE_NAME
	stats = {"reparented": [], "lifted_to_core": [], "icons_fixed": []
	}

	for ws_name in CORE_PLATFORM_WORKSPACES:
		if not frappe.db.exists("Workspace", ws_name):
			continue
		current = frappe.db.get_value("Workspace", ws_name, "parent_page") or ""
		if current:
			frappe.db.set_value("Workspace", ws_name, "parent_page", "", update_modified=False)
			stats["lifted_to_core"].append(ws_name)
		icon = FINANCE_WORKSPACE_ICONS.get(ws_name) or (
			"accounting" if ws_name == "Accounting" else "file"
		)
		frappe.db.set_value("Workspace", ws_name, "icon", icon, update_modified=False)
		stats["icons_fixed"].append(ws_name)

	for ws_name in _finance_vertical_workspaces():
		if not frappe.db.exists("Workspace", ws_name):
			continue
		current = frappe.db.get_value("Workspace", ws_name, "parent_page") or ""
		if current != parent:
			frappe.db.set_value("Workspace", ws_name, "parent_page", parent, update_modified=False)
			stats["reparented"].append(ws_name)
		icon = FINANCE_WORKSPACE_ICONS.get(ws_name, "loan")
		frappe.db.set_value("Workspace", ws_name, "icon", icon, update_modified=False)
		stats["icons_fixed"].append(ws_name)

	if save:
		frappe.db.commit()
	return {"ok": True, **stats}


@frappe.whitelist()
def get_finance_sidebar_brand_map() -> dict[str, str]:
	"""Workspace title → logo URL for desk sidebar brand overlay."""
	out: dict[str, str] = {}
	for ws, app in WORKSPACE_APP_LOGO.items():
		if frappe.db.exists("Workspace", ws):
			out[ws] = f"/assets/{app}/logo.png"
	return out
