# Copyright (c) 2026, ErpGenEx
"""Logical app bundles for marketplace bulk uninstall and desk visibility."""

from __future__ import annotations

import frappe

# Apps listed here are candidates only — protected / dependency rules still apply at uninstall time.
APP_UNINSTALL_GROUPS: dict[str, dict] = {
	"finance": {
		"label": "Finance Group",
		"description": "Finance verticals (leasing, mortgage, consumer, ALM, credit, …). Platform Accounting stays installed.",
		"apps": [
			"omnexa_finance_engine",
			"omnexa_credit_engine",
			"omnexa_credit_risk",
			"omnexa_alm",
			"omnexa_consumer_finance",
			"omnexa_vehicle_finance",
			"omnexa_mortgage_finance",
			"omnexa_factoring",
			"omnexa_sme_retail_finance",
			"omnexa_leasing_finance",
			"omnexa_operational_risk",
		],
	},
	"healthcare": {
		"label": "Healthcare",
		"description": "Hospital and clinic vertical.",
		"apps": ["omnexa_healthcare"],
	},
	"education": {
		"label": "Education",
		"description": "Schools, K–12, and nursery.",
		"apps": ["omnexa_education", "omnexa_nursery"],
	},
	"construction": {
		"label": "Construction & Engineering",
		"description": "Construction, engineering consulting, and eng platform apps.",
		"apps": [
			"omnexa_construction",
			"omnexa_engineering_consulting",
			"omnexa_eng_document_control",
			"omnexa_eng_workflow_engine",
			"omnexa_eng_platform_integrations",
		],
	},
	"realestate": {
		"label": "Real Estate (ErpGenEx)",
		"description": "Property management, development, and sales.",
		"apps": [
			"erpgenex_property_mgmt",
			"erpgenex_realestate_dev",
			"erpgenex_realestate_sales",
			"erpgenex_maintenance_core",
		],
	},
	"hospitality": {
		"label": "Hospitality & Tourism",
		"description": "Tourism, restaurants, and car rental.",
		"apps": ["omnexa_tourism", "omnexa_restaurant", "omnexa_car_rental"],
	},
	"trading": {
		"label": "Trading & Manufacturing",
		"description": "Distribution, trading, and manufacturing verticals.",
		"apps": ["omnexa_trading", "omnexa_manufacturing", "omnexa_agriculture"],
	},
	"audit": {
		"label": "Audit & Compliance",
		"description": "Statutory audit and reporting compliance extensions.",
		"apps": ["omnexa_statutory_audit", "omnexa_reporting_compliance"],
	},
}


def get_group_spec(group_key: str) -> dict:
	key = (group_key or "").strip().lower()
	spec = APP_UNINSTALL_GROUPS.get(key)
	if not spec:
		frappe.throw(frappe._("Unknown app group: {0}").format(group_key))
	return {"key": key, **spec}


def get_group_apps(group_key: str) -> list[str]:
	return list(get_group_spec(group_key).get("apps") or [])


def get_uninstall_groups_summary() -> list[dict]:
	"""Catalog rows for marketplace UI (installed counts, uninstall eligibility)."""
	from omnexa_core.omnexa_core.marketplace import _bulk_uninstall_plan, _uninstall_protected_apps

	installed = set(frappe.get_installed_apps() or [])
	protected = _uninstall_protected_apps()
	out: list[dict] = []

	for key, spec in APP_UNINSTALL_GROUPS.items():
		apps = list(spec.get("apps") or [])
		installed_in_group = [a for a in apps if a in installed]
		uninstallable = [a for a in installed_in_group if a not in protected]
		plan = _bulk_uninstall_plan(uninstallable) if uninstallable else None
		hidden_count = 0
		try:
			from omnexa_core.omnexa_core.app_visibility import get_hidden_desk_apps

			hidden = get_hidden_desk_apps()
			hidden_count = sum(1 for a in installed_in_group if a in hidden)
		except Exception:
			pass

		out.append(
			{
				"key": key,
				"label": spec.get("label") or key,
				"description": spec.get("description") or "",
				"apps": apps,
				"installed": installed_in_group,
				"installed_count": len(installed_in_group),
				"uninstallable": uninstallable,
				"uninstall_count": len(plan["uninstall_order"]) if plan else 0,
				"can_uninstall": bool(plan and plan["can_uninstall"]),
				"desk_hidden_count": hidden_count,
			}
		)
	return out
