# extend desk_shell with home executive summary

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.api.desk_module_registry import get_all_modules
from omnexa_core.omnexa_core.api.desk_shell import get_desk_context  # noqa: F401
from omnexa_core.omnexa_core.session_context import get_effective_company, get_view_context


@frappe.whitelist()
def get_home_executive_summary():
	"""Cross-module executive launcher for Next.js home page."""
	ctx = get_desk_context()
	company = get_effective_company()
	view = get_view_context()

	modules = []
	for mod in get_all_modules():
		card = {
			"id": mod["slug"],
			"label": mod["label"],
			"description": _module_description(mod),
			"href": mod["href"],
			"icon": mod["icon"],
			"color": mod.get("color", "blue"),
		}
		if mod["slug"] == "hr":
			card["kpis"] = _hr_kpis()
		modules.append(card)

	return {
		"welcome": {
			"title": frappe._("Welcome to ErpGenEx"),
			"subtitle": view.get("label") or company or frappe._("Enterprise desk"),
		},
		"modules": modules,
		"scope": ctx.get("scope"),
		"user": ctx.get("user"),
	}


def _module_description(mod: dict) -> str:
	descriptions = {
		"hr": "Employees, attendance, leave, payroll",
		"accounting": "Finance, GL, invoices",
		"crm": "Leads, customers, opportunities",
		"stock": "Inventory, warehouses, items",
		"healthcare": "Patients, beds, appointments",
		"education": "Enrollments, attendance, fees",
		"trading": "POS, inventory, transactions",
		"construction": "Projects, sites, safety",
		"manufacturing": "Work orders, OEE, production",
	}
	return descriptions.get(mod["slug"], mod["label"])


def _hr_kpis():
	try:
		from omnexa_hr.omnexa_hr.api.hr_dashboard import get_hr_dashboard_catalog

		c = get_hr_dashboard_catalog()
		return [{"label": k["label"], "value": k["value"]} for k in (c.get("kpis") or [])[:3]]
	except Exception:
		return []
