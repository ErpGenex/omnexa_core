# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Reports + control-tower desk sync for Erpgenex real-estate / maintenance verticals."""

from __future__ import annotations

import json

import frappe


def ensure_erpgenex_realty_workspace_experience():
	"""Idempotent; builds Accounting-style desks via workspace_control_tower."""
	if frappe.flags.in_install or frappe.flags.in_uninstall:
		return
	try:
		_ensure_vertical_reports()
		from omnexa_core.omnexa_core.workspace_control_tower import sync_workspace_for_app

		for app_key in (
			"erpgenex_property_mgmt",
			"erpgenex_realestate_dev",
			"erpgenex_realestate_sales",
			"erpgenex_maintenance_core",
		):
			sync_workspace_for_app(app_key)
	finally:
		frappe.clear_cache()


def _report_rb_json(columns: list[tuple[str, str]]) -> str:
	payload = {
		"filters": [],
		"columns": [[fname, dt] for fname, dt in columns],
		"sort_by": columns[0][0] if columns else "modified",
		"sort_order": "desc",
		"sort_by_next": None,
		"sort_order_next": "desc",
	}
	return json.dumps(payload, separators=(",", ":"))


def _upsert_report(*, module: str, name: str, ref_doctype: str, columns: list[tuple[str, str]]) -> None:
	if frappe.db.exists("Report", name):
		return
	frappe.get_doc(
		{
			"doctype": "Report",
			"name": name,
			"module": module,
			"ref_doctype": ref_doctype,
			"report_name": name,
			"report_type": "Report Builder",
			"is_standard": "Yes",
			"json": _report_rb_json(columns),
			"disabled": 0,
			"add_total_row": 0,
		}
	).insert(ignore_permissions=True)


def _ensure_vertical_reports() -> None:
	_upsert_report(
		module="Erpgenex Property Mgmt",
		name="PMC Rental Contract Register",
		ref_doctype="Rental Contract",
		columns=[
			("name", "Rental Contract"),
			("status", "Rental Contract"),
			("tenant_name", "Rental Contract"),
			("pmc_property_unit", "Rental Contract"),
			("monthly_rent", "Rental Contract"),
		],
	)
	_upsert_report(
		module="Erpgenex Property Mgmt",
		name="PMC Rent Billing Register",
		ref_doctype="Rent Billing Run",
		columns=[
			("name", "Rent Billing Run"),
			("status", "Rent Billing Run"),
			("billing_period_start", "Rent Billing Run"),
			("grand_total", "Rent Billing Run"),
		],
	)
	_upsert_report(
		module="Erpgenex Realestate Dev",
		name="Development Project Register",
		ref_doctype="Development Project",
		columns=[
			("name", "Development Project"),
			("status", "Development Project"),
			("project_name", "Development Project"),
		],
	)
	_upsert_report(
		module="Erpgenex Realestate Dev",
		name="RE Unit Inventory Overview",
		ref_doctype="RE Unit Inventory",
		columns=[
			("name", "RE Unit Inventory"),
			("status", "RE Unit Inventory"),
			("unit_number", "RE Unit Inventory"),
		],
	)
	_upsert_report(
		module="Erpgenex Realestate Sales",
		name="Property Sales Booking Register",
		ref_doctype="Sales Booking",
		columns=[
			("name", "Sales Booking"),
			("status", "Sales Booking"),
			("customer", "Sales Booking"),
			("agreement_value", "Sales Booking"),
		],
	)
	_upsert_report(
		module="Erpgenex Realestate Sales",
		name="Unit Reservation Register",
		ref_doctype="Unit Reservation",
		columns=[
			("name", "Unit Reservation"),
			("status", "Unit Reservation"),
			("re_unit_inventory", "Unit Reservation"),
			("reservation_until", "Unit Reservation"),
		],
	)
