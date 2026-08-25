# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Add branch Custom Fields to company-scoped DocTypes missing branch isolation."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from omnexa_core.omnexa_core.branch_access import get_default_branch
from omnexa_core.omnexa_core.branch_audit import scan_branch_coverage
from omnexa_core.omnexa_core.isolation_settings import should_skip_branch_sweep


@frappe.whitelist()
def sweep_branch_fields(app: str | None = None, dry_run: int | str = 0, backfill: int | str = 1) -> dict:
	"""Add branch Link field to DocTypes with company but no branch (MISSING_BRANCH)."""
	frappe.only_for("System Manager")
	dry_run = int(dry_run or 0)
	backfill = int(backfill or 0)

	rows = scan_branch_coverage(app)
	targets = [r["doctype"] for r in rows if r["status"] == "MISSING_BRANCH"]
	targets = [dt for dt in targets if not should_skip_branch_sweep(dt)]

	created_fields: list[str] = []
	skipped: list[str] = []
	backfilled = 0

	custom_fields_map: dict[str, list[dict]] = {}
	for dt in targets:
		if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": "branch"}):
			skipped.append(dt)
			continue
		meta = frappe.get_meta(dt)
		insert_after = "company" if meta.has_field("company") else None
		if not insert_after:
			skipped.append(dt)
			continue
		custom_fields_map.setdefault(dt, []).append(
			{
				"fieldname": "branch",
				"label": "Branch",
				"fieldtype": "Link",
				"options": "Branch",
				"insert_after": insert_after,
				"in_list_view": 0,
				"reqd": 0,
			}
		)
		created_fields.append(dt)

	if custom_fields_map and not dry_run:
		create_custom_fields(custom_fields_map, update=False)
		frappe.db.commit()
		frappe.clear_cache()

	if backfill and not dry_run:
		backfilled = _backfill_branch_values(created_fields)

	return {
		"dry_run": bool(dry_run),
		"targets": len(targets),
		"fields_created": len(created_fields),
		"created": created_fields,
		"skipped_existing": skipped,
		"backfilled_rows": backfilled,
	}


def _backfill_branch_values(doctypes: list[str]) -> int:
	total = 0
	for dt in doctypes:
		if not frappe.db.has_column(dt, "branch"):
			continue
		if not frappe.db.has_column(dt, "company"):
			continue
		names = frappe.get_all(
			dt,
			filters={"branch": ["in", ["", None]]},
			pluck="name",
			limit=5000,
		)
		for name in names:
			company = frappe.db.get_value(dt, name, "company")
			if not company:
				continue
			branch = get_default_branch(company) or frappe.db.get_value(
				"Branch", {"company": company}, "name"
			)
			if branch:
				frappe.db.set_value(dt, name, "branch", branch, update_modified=False)
				total += 1
	if total:
		frappe.db.commit()
	return total


def sweep_branch_fields_for_apps(apps: list[str] | None = None) -> dict:
	"""Run sweep per app cluster (§2.3 checklist)."""
	apps = apps or _default_sweep_apps()
	results = {}
	for app in apps:
		try:
			results[app] = sweep_branch_fields(app=app, dry_run=0, backfill=1)
		except Exception:
			frappe.log_error(title=f"Branch sweep failed: {app}")
			results[app] = {"error": True}
	return results


def _default_sweep_apps() -> list[str]:
	return [
		"omnexa_healthcare",
		"omnexa_accounting",
		"omnexa_hr",
		"omnexa_trading",
		"omnexa_education",
		"omnexa_construction",
		"omnexa_manufacturing",
		"omnexa_restaurant",
		"omnexa_tourism",
		"omnexa_agriculture",
		"omnexa_car_rental",
		"omnexa_services",
		"erpgenex_realestate_dev",
		"erpgenex_property_mgmt",
		"erpgenex_realestate_sales",
		"omnexa_leasing_finance",
		"omnexa_mortgage_finance",
		"omnexa_factoring",
		"omnexa_vehicle_finance",
		"omnexa_sme_microfinance",
		"omnexa_sme_retail_finance",
		"omnexa_consumer_finance",
		"omnexa_credit_engine",
		"omnexa_engineering_consulting",
		"omnexa_eng_document_control",
		"omnexa_eng_platform_integrations",
		"omnexa_eng_workflow_engine",
	]
